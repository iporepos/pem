#!/usr/bin/env python3
"""
post_assessment.py

Gera visualizações de avaliação pós-processamento do PEM: scatter plots 2D e
3D coloridos pela distância euclidiana ao canto ótimo (benefício=1,
conflito=0, risco=0), e exporta um GeoPackage com as colunas normalizadas e
a distância calculada.

A versão com escala teórica completa (0 a sqrt(3)) é sempre gerada com sufixo
"_full". Se "clip" for true no config, uma segunda versão com escala ajustada
ao intervalo amostral é gerada com sufixo "_clip".

Uso:
    python -m pem.post_assessment --config path/to/config.json

Config JSON:
    {
        "db_file":   "path/to/pem_outputs.gpkg",
        "layer":     "pem_indices_upg_micro",
        "out_dir":   "path/to/output",
        "out_gpkg":  "assessment_upg.gpkg",
        "out_layer": "upg_micro",
        "scenario":  "a0",
        "show":      false,
        "cmap":      "Spectral_r",
        "clip":      false,
        "elev":      30,
        "azim":      -60,
        "step":      0.2
    }
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.ticker import FormatStrFormatter


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_CM = 1 / 2.54
_CBAR_THICKNESS = 0.032   # colorbar height as fraction of figure height
_CBAR_BOTTOM    = 0.055   # colorbar bottom edge as fraction of figure height
_CBAR_LABEL_FS  = 9
_CBAR_TICK_FS   = 9


def _add_horizontal_cbar(fig, sm, label, ticks, cbar_bottom=_CBAR_BOTTOM):
    fig_w_cm = fig.get_size_inches()[0] * 2.54
    cbar_w = 5.0 / fig_w_cm
    cbar_l = (1.0 - cbar_w) / 2.0
    cax = fig.add_axes([cbar_l, cbar_bottom, cbar_w, _CBAR_THICKNESS])
    cbar = fig.colorbar(sm, cax=cax, orientation="horizontal", ticks=ticks)
    cbar.ax.xaxis.set_major_formatter(FormatStrFormatter("%.1f"))
    cbar.set_label(label, fontsize=_CBAR_LABEL_FS)
    cbar.ax.tick_params(labelsize=_CBAR_TICK_FS)
    return cbar


def _save_plots(
    gdf,
    xs, ys, zs,
    distances,
    d_min: float,
    d_max: float,
    suffix: str,
    pairs: list,
    cmap,
    ideal: np.ndarray,
    out_dir: Path,
    scenario: str,
    elev: float,
    azim: float,
    show: bool,
) -> None:
    d_norm = (distances - d_min) / (d_max - d_min)
    norm = Normalize(vmin=0, vmax=1)
    sm = ScalarMappable(cmap=cmap, norm=Normalize(vmin=d_min, vmax=d_max))
    sm.set_array([])

    # --- 2D scatter plots ---------------------------------------------------
    fig, axes = plt.subplots(1, 3, figsize=(17 * _CM, 8 * _CM))
    for ax, (x_field, y_field, x_label, y_label) in zip(axes, pairs):
        ax.scatter(gdf[x_field], gdf[y_field], c=d_norm, cmap=cmap, norm=norm, marker="o", s=20)
        ax.set_title(f"{x_label} vs {y_label}")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_xlim(0, 1.1)
        ax.set_ylim(0, 1.1)
        ax.set_aspect("equal")
        ax.set_facecolor((0.925, 0.925, 0.925))
        ax.set_axisbelow(True)
        ax.grid(True, color=(0.85, 0.85, 0.85), linewidth=0.4, alpha=0.4)

    # Reserve bottom fraction for the colorbar, then read the middle axis
    # position to align the colorbar width with one plot.
    ticks = np.linspace(d_min, d_max, 5)
    plt.tight_layout(rect=[0, 0.20, 1, 1])
    _add_horizontal_cbar(fig, sm, "Distância ótima", ticks)

    fig.savefig(out_dir / f"scatter2d_{scenario}_{suffix}.jpg", dpi=300, bbox_inches="tight")
    if show:
        plt.show()
    plt.close(fig)

    # --- 3D scatter plot ----------------------------------------------------
    fig3d = plt.figure(figsize=(12 * _CM, 12 * _CM))  # width and height fixed at 12 cm
    ax3d = fig3d.add_subplot(111, projection="3d")

    ax3d.scatter(xs, ys, zs, c=d_norm, cmap=cmap, norm=norm,
                 marker="o", s=30, alpha=0.8, depthshade=False, zorder=5)

    for x, y, z in zip(xs, ys, zs):
        ax3d.plot([x, ideal[0]], [y, ideal[1]], [z, ideal[2]],
                  color="grey", linewidth=0.5, alpha=0.3, zorder=1)

    ax3d.set_title("Benefício / Conflito / Risco")
    ax3d.set_xlabel("Risco")
    ax3d.set_ylabel("Conflito")
    ax3d.set_zlabel("Benefício", labelpad=14)
    ax3d.zaxis.set_rotate_label(False)
    ax3d.zaxis.label.set_rotation(90)
    ax3d.set_xlim(0, 1.1)
    ax3d.set_ylim(0, 1.1)
    ax3d.set_zlim(0, 1.1)
    for axis in [ax3d.xaxis, ax3d.yaxis, ax3d.zaxis]:
        axis._axinfo["grid"]["color"] = (0.85, 0.85, 0.85, 0.4)
        axis._axinfo["grid"]["linewidth"] = 0.4
    ax3d.view_init(elev=elev, azim=azim)

    fig3d.subplots_adjust(left=0.05, right=0.80, bottom=0.28, top=0.95)
    _add_horizontal_cbar(fig3d, sm, "Distância ótima", ticks, cbar_bottom=0.12)

    fig3d.savefig(out_dir / f"scatter3d_{scenario}_{suffix}.jpg", dpi=300)
    if show:
        plt.show()
    plt.close(fig3d)


def _save_space_plot(
    step: float,
    cmap,
    ideal: np.ndarray,
    out_dir: Path,
    elev: float,
    azim: float,
    show: bool,
) -> None:
    vals = np.arange(0, 1.0 + step / 2, step)
    rr, cc, bb = np.meshgrid(vals, vals, vals)
    xs_g = rr.ravel()  # risco
    ys_g = cc.ravel()  # conflit
    zs_g = bb.ravel()  # benefit

    distances = np.sqrt(
        (xs_g - ideal[0]) ** 2 + (ys_g - ideal[1]) ** 2 + (zs_g - ideal[2]) ** 2
    )
    d_min, d_max = 0.0, np.sqrt(3)
    d_norm = distances / d_max

    norm = Normalize(vmin=0, vmax=1)
    sm = ScalarMappable(cmap=cmap, norm=Normalize(vmin=d_min, vmax=d_max))
    sm.set_array([])
    ticks = np.linspace(d_min, d_max, 5)

    fig = plt.figure(figsize=(12 * _CM, 12 * _CM))
    ax = fig.add_subplot(111, projection="3d")

    ax.scatter(xs_g, ys_g, zs_g, c=d_norm, cmap=cmap, norm=norm,
               marker="o", s=8, alpha=0.7, depthshade=False)

    ax.set_xlabel("Risco")
    ax.set_ylabel("Conflito")
    ax.set_zlabel("Benefício", labelpad=14)
    ax.zaxis.set_rotate_label(False)
    ax.zaxis.label.set_rotation(90)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.0)
    ax.set_zlim(0, 1.0)
    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis._axinfo["grid"]["color"] = (0.85, 0.85, 0.85, 0.4)
        axis._axinfo["grid"]["linewidth"] = 0.4
    ax.view_init(elev=elev, azim=azim)

    step_str = f"{step:.2f}".replace(".", "p")
    fig.subplots_adjust(left=0.05, right=0.80, bottom=0.28, top=0.95)
    _add_horizontal_cbar(fig, sm, "Distância ótima", ticks, cbar_bottom=0.12)

    fig.savefig(out_dir / f"space3d_step{step_str}.jpg", dpi=300)
    if show:
        plt.show()
    plt.close(fig)


def run(cfg: dict) -> None:
    db_file = Path(cfg["db_file"])
    out_dir = Path(cfg["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    layer     = cfg["layer"]
    out_gpkg  = cfg.get("out_gpkg",  "assessment_upg.gpkg")
    out_layer = cfg.get("out_layer", "upg_micro")
    scenario  = cfg.get("scenario",  "a0")
    show      = cfg.get("show",  False)
    cmap_name = cfg.get("cmap",  "Spectral_r")
    clip      = cfg.get("clip",  False)
    elev      = cfg.get("elev",  30)
    azim      = cfg.get("azim", -60)
    step      = cfg.get("step", 0.2)

    plt.rcParams.update({"font.family": "Arial", "font.size": 9})

    gdf = gpd.read_file(db_file, layer=layer)
    print(gdf.info())

    benefit_field = f"benefic_{scenario}"
    conflit_field = f"conflit_{scenario}"
    risco_field   = f"risco_{scenario}"

    benefit_norm = benefit_field + "_norm"
    conflit_norm = conflit_field + "_norm"
    risco_norm   = risco_field   + "_norm"

    for field, norm_field in [
        (benefit_field, benefit_norm),
        (conflit_field, conflit_norm),
        (risco_field,   risco_norm),
    ]:
        col = gdf[field]
        gdf[norm_field] = (col - col.min()) / (col.max() - col.min())

    xs = gdf[risco_norm].values
    ys = gdf[conflit_norm].values
    zs = gdf[benefit_norm].values

    ideal = np.array([0.0, 0.0, 1.0])  # risco=0, conflit=0, benefit=1
    distances = np.sqrt(
        (xs - ideal[0]) ** 2 + (ys - ideal[1]) ** 2 + (zs - ideal[2]) ** 2
    )

    gdf[f"dist_otima_{scenario}"] = distances
    gdf.to_file(out_dir / out_gpkg, layer=out_layer, driver="GPKG")

    cmap = plt.get_cmap(cmap_name)
    pairs = [
        (benefit_norm, conflit_norm, "Benefício", "Conflito"),
        (benefit_norm, risco_norm,   "Benefício", "Risco"),
        (conflit_norm, risco_norm,   "Conflito",  "Risco"),
    ]
    plot_kwargs = dict(
        gdf=gdf, xs=xs, ys=ys, zs=zs, distances=distances,
        pairs=pairs, cmap=cmap, ideal=ideal,
        out_dir=out_dir, scenario=scenario, elev=elev, azim=azim, show=show,
    )

    _save_plots(d_min=0.0, d_max=np.sqrt(3), suffix="full", **plot_kwargs)

    if clip:
        _save_plots(
            d_min=np.nanmin(distances), d_max=np.nanmax(distances),
            suffix="clip", **plot_kwargs,
        )

    _save_space_plot(
        step=step, cmap=cmap, ideal=ideal,
        out_dir=out_dir, elev=elev, azim=azim, show=show,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, metavar="PATH")
    args = parser.parse_args()
    cfg = load_config(Path(args.config))
    run(cfg)


if __name__ == "__main__":
    main()
