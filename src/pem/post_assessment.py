#!/usr/bin/env python3
"""
post_assessment.py

Gera visualizações de avaliação pós-processamento do PEM: scatter plots 2D e
3D coloridos pela distância euclidiana ao canto ótimo (benefício=1,
conflito=0, risco=0).

Os valores dos três índices são usados diretamente, sem normalização.

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
        "scenario":  "a0",            (or ["a0", "a1", ...])
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
from matplotlib.ticker import (
    FixedLocator,
    FormatStrFormatter,
    FuncFormatter,
    MultipleLocator,
)


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_CM = 1 / 2.54
_TICK_LABELS = (0.0, 0.5, 1.0)
_SCENARIO_COLORS = {
    "a1": "blue",
    "a2": "magenta",
    "a3": "indigo",
}


def _sparse_fmt(val, pos):
    return f"{val:.1f}" if any(abs(val - v) < 1e-9 for v in _TICK_LABELS) else ""


_CBAR_THICKNESS = 0.032  # colorbar height as fraction of figure height
_CBAR_BOTTOM = 0.055  # colorbar bottom edge as fraction of figure height
_CBAR_LABEL_FS = 9
_CBAR_TICK_FS = 9


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
    xs,
    ys,
    zs,
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
        ax.scatter(
            gdf[x_field], gdf[y_field], c=d_norm, cmap=cmap, norm=norm, marker="o", s=8
        )
        ax.set_title(f"{x_label} vs {y_label}")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_xlim(0, 1.1)
        ax.set_ylim(0, 1.1)
        ax.set_aspect("equal")
        ax.set_facecolor((0.925, 0.925, 0.925))
        ax.set_axisbelow(True)
        ax.xaxis.set_major_locator(FixedLocator(_TICK_LABELS))
        ax.yaxis.set_major_locator(FixedLocator(_TICK_LABELS))
        ax.xaxis.set_minor_locator(MultipleLocator(0.1))
        ax.yaxis.set_minor_locator(MultipleLocator(0.1))
        ax.grid(True, which="both", color=(0.85, 0.85, 0.85), linewidth=0.4, alpha=0.4)

    # Reserve bottom fraction for the colorbar, then read the middle axis
    # position to align the colorbar width with one plot.
    ticks = np.linspace(d_min, d_max, 6)
    fig.suptitle(f"Cenário {scenario.upper()}")
    plt.tight_layout(rect=[0, 0.20, 1, 0.93])
    _add_horizontal_cbar(fig, sm, "Distância Euclidiana Absoluta", ticks)

    fig.savefig(
        out_dir / f"2d_scatter_{scenario}_{suffix}.jpg", dpi=300, bbox_inches="tight"
    )
    if show:
        plt.show()
    plt.close(fig)

    # --- 3D scatter plot ----------------------------------------------------
    fig3d = plt.figure(figsize=(12 * _CM, 9.6 * _CM))  # width and height fixed at 12 cm
    ax3d = fig3d.add_subplot(111, projection="3d")

    ax3d.scatter(
        xs,
        ys,
        zs,
        c=d_norm,
        cmap=cmap,
        norm=norm,
        marker="o",
        s=8,
        alpha=0.8,
        depthshade=False,
        zorder=5,
    )

    for x, y, z in zip(xs, ys, zs):
        ax3d.plot(
            [x, ideal[0]],
            [y, ideal[1]],
            [z, ideal[2]],
            color="#b8a8c8",
            linewidth=0.5,
            alpha=0.3,
            zorder=1,
        )

    ax3d.set_title(f"Cenário {scenario.upper()} – Benefício / Conflito / Risco")
    ax3d.set_xlabel("Risco", labelpad=-3)
    ax3d.set_ylabel("Conflito", labelpad=-3)
    ax3d.set_zlabel("Benefício", labelpad=6)
    ax3d.zaxis.set_rotate_label(False)
    ax3d.zaxis.label.set_rotation(90)
    ax3d.tick_params(axis="x", pad=-3)
    ax3d.tick_params(axis="y", pad=-3)
    ax3d.tick_params(axis="z", pad=1)
    ax3d.set_xlim(0, 1.1)
    ax3d.set_ylim(0, 1.1)
    ax3d.set_zlim(0, 1.1)
    for axis in [ax3d.xaxis, ax3d.yaxis, ax3d.zaxis]:
        axis.set_major_locator(MultipleLocator(0.1))
        axis.set_major_formatter(FuncFormatter(_sparse_fmt))
        axis._axinfo["grid"]["color"] = (0.85, 0.85, 0.85, 0.4)
        axis._axinfo["grid"]["linewidth"] = 0.4
    ax3d.view_init(elev=elev, azim=azim)

    fig3d.subplots_adjust(left=0.0, right=0.97, bottom=0.16, top=0.90)
    _add_horizontal_cbar(
        fig3d, sm, "Distância Euclidiana Absoluta", ticks, cbar_bottom=0.12
    )

    fig3d.savefig(out_dir / f"3d_scatter_{scenario}_{suffix}.jpg", dpi=300)
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
    ticks = np.linspace(d_min, d_max, 6)

    fig = plt.figure(figsize=(12 * _CM, 9.6 * _CM))
    ax = fig.add_subplot(111, projection="3d")

    ax.scatter(
        xs_g,
        ys_g,
        zs_g,
        c=d_norm,
        cmap=cmap,
        norm=norm,
        marker="o",
        s=8,
        alpha=0.7,
        depthshade=False,
    )

    ax.set_title("Espaço de soluções")
    ax.set_xlabel("Risco", labelpad=-3)
    ax.set_ylabel("Conflito", labelpad=-3)
    ax.set_zlabel("Benefício", labelpad=6)
    ax.zaxis.set_rotate_label(False)
    ax.zaxis.label.set_rotation(90)
    ax.tick_params(axis="x", pad=-3)
    ax.tick_params(axis="y", pad=-3)
    ax.tick_params(axis="z", pad=1)
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0, 1.1)
    ax.set_zlim(0, 1.1)
    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.set_major_locator(MultipleLocator(0.1))
        axis.set_major_formatter(FuncFormatter(_sparse_fmt))
        axis._axinfo["grid"]["color"] = (0.85, 0.85, 0.85, 0.4)
        axis._axinfo["grid"]["linewidth"] = 0.4
    ax.view_init(elev=elev, azim=azim)

    step_str = f"{step:.2f}".replace(".", "p")
    fig.subplots_adjust(left=0.0, right=0.97, bottom=0.16, top=0.90)
    _add_horizontal_cbar(
        fig, sm, "Distância Euclidiana Absoluta", ticks, cbar_bottom=0.12
    )

    fig.savefig(out_dir / f"space3d_step{step_str}.jpg", dpi=300)
    if show:
        plt.show()
    plt.close(fig)


def _save_trajectory_plot(
    gdf,
    scenario: str,
    baseline: str,
    cmap,
    ideal: np.ndarray,
    out_dir: Path,
    elev: float,
    azim: float,
    show: bool,
) -> None:
    xs_base = gdf[f"risco_{baseline}"].values
    ys_base = gdf[f"conflit_{baseline}"].values
    zs_base = gdf[f"benefic_{baseline}"].values

    xs = gdf[f"risco_{scenario}"].values
    ys = gdf[f"conflit_{scenario}"].values
    zs = gdf[f"benefic_{scenario}"].values

    d_min, d_max = 0.0, np.sqrt(3)
    distances = np.sqrt(
        (xs - ideal[0]) ** 2 + (ys - ideal[1]) ** 2 + (zs - ideal[2]) ** 2
    )
    d_norm = distances / d_max
    norm = Normalize(vmin=0, vmax=1)
    sm = ScalarMappable(cmap=cmap, norm=Normalize(vmin=d_min, vmax=d_max))
    sm.set_array([])
    ticks = np.linspace(d_min, d_max, 6)

    fig = plt.figure(figsize=(12 * _CM, 9.6 * _CM))
    ax = fig.add_subplot(111, projection="3d")

    ax.scatter(
        xs,
        ys,
        zs,
        c=d_norm,
        cmap=cmap,
        norm=norm,
        marker="o",
        s=8,
        alpha=0.8,
        depthshade=False,
        zorder=5,
    )

    n = len(xs)
    lx = np.empty(n * 3)
    lx[::3] = xs_base
    lx[1::3] = xs
    lx[2::3] = np.nan
    ly = np.empty(n * 3)
    ly[::3] = ys_base
    ly[1::3] = ys
    ly[2::3] = np.nan
    lz = np.empty(n * 3)
    lz[::3] = zs_base
    lz[1::3] = zs
    lz[2::3] = np.nan
    ax.plot(lx, ly, lz, color="grey", linewidth=0.5, alpha=0.3, zorder=1)

    ax.set_title(f"{scenario.upper()} – Trajetória desde {baseline.upper()}")
    ax.set_xlabel("Risco", labelpad=-3)
    ax.set_ylabel("Conflito", labelpad=-3)
    ax.set_zlabel("Benefício", labelpad=6)
    ax.zaxis.set_rotate_label(False)
    ax.zaxis.label.set_rotation(90)
    ax.tick_params(axis="x", pad=-3)
    ax.tick_params(axis="y", pad=-3)
    ax.tick_params(axis="z", pad=1)
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0, 1.1)
    ax.set_zlim(0, 1.1)
    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.set_major_locator(MultipleLocator(0.1))
        axis.set_major_formatter(FuncFormatter(_sparse_fmt))
        axis._axinfo["grid"]["color"] = (0.85, 0.85, 0.85, 0.4)
        axis._axinfo["grid"]["linewidth"] = 0.4
    ax.view_init(elev=elev, azim=azim)

    fig.subplots_adjust(left=0.0, right=0.97, bottom=0.16, top=0.90)
    _add_horizontal_cbar(
        fig, sm, "Distância Euclidiana Absoluta", ticks, cbar_bottom=0.12
    )
    fig.savefig(out_dir / f"3d_trajectory_{baseline}_{scenario}.jpg", dpi=300)
    if show:
        plt.show()
    plt.close(fig)


def _save_synthesis_plot(
    gdf,
    scenarios: list,
    baseline: str,
    cmap,
    ideal: np.ndarray,
    out_dir: Path,
    elev: float,
    azim: float,
    show: bool,
) -> None:
    xs_base = gdf[f"risco_{baseline}"].values
    ys_base = gdf[f"conflit_{baseline}"].values
    zs_base = gdf[f"benefic_{baseline}"].values

    d_min, d_max = 0.0, np.sqrt(3)
    distances = np.sqrt(
        (xs_base - ideal[0]) ** 2
        + (ys_base - ideal[1]) ** 2
        + (zs_base - ideal[2]) ** 2
    )
    d_norm = distances / d_max
    norm = Normalize(vmin=0, vmax=1)
    sm = ScalarMappable(cmap=cmap, norm=Normalize(vmin=d_min, vmax=d_max))
    sm.set_array([])
    ticks = np.linspace(d_min, d_max, 6)

    non_baseline = [s for s in scenarios if s != baseline]
    palette = plt.get_cmap("tab10")

    fig = plt.figure(figsize=(12 * _CM, 9.6 * _CM))
    ax = fig.add_subplot(111, projection="3d")

    for i, scenario in enumerate(non_baseline):
        color = _SCENARIO_COLORS.get(scenario, palette(i))
        xs = gdf[f"risco_{scenario}"].values
        ys = gdf[f"conflit_{scenario}"].values
        zs = gdf[f"benefic_{scenario}"].values

        n = len(xs_base)
        lx = np.empty(n * 3)
        lx[::3] = xs_base
        lx[1::3] = xs
        lx[2::3] = np.nan
        ly = np.empty(n * 3)
        ly[::3] = ys_base
        ly[1::3] = ys
        ly[2::3] = np.nan
        lz = np.empty(n * 3)
        lz[::3] = zs_base
        lz[1::3] = zs
        lz[2::3] = np.nan
        ax.plot(
            lx,
            ly,
            lz,
            color=color,
            linewidth=0.5,
            alpha=0.3,
            zorder=1,
            label=scenario.upper(),
        )

    ax.scatter(
        xs_base,
        ys_base,
        zs_base,
        c=d_norm,
        cmap=cmap,
        norm=norm,
        marker="o",
        s=8,
        alpha=0.8,
        depthshade=False,
        zorder=5,
    )

    ax.set_title(f"{baseline} – Síntese de cenários")
    ax.set_xlabel("Risco", labelpad=-3)
    ax.set_ylabel("Conflito", labelpad=-3)
    ax.set_zlabel("Benefício", labelpad=6)
    ax.zaxis.set_rotate_label(False)
    ax.zaxis.label.set_rotation(90)
    ax.tick_params(axis="x", pad=-3)
    ax.tick_params(axis="y", pad=-3)
    ax.tick_params(axis="z", pad=1)
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0, 1.1)
    ax.set_zlim(0, 1.1)
    for axis in [ax.xaxis, ax.yaxis, ax.zaxis]:
        axis.set_major_locator(MultipleLocator(0.1))
        axis.set_major_formatter(FuncFormatter(_sparse_fmt))
        axis._axinfo["grid"]["color"] = (0.85, 0.85, 0.85, 0.4)
        axis._axinfo["grid"]["linewidth"] = 0.4
    ax.view_init(elev=elev, azim=azim)
    leg = ax.legend(
        title="Cenário",
        fontsize=8,
        title_fontsize=8,
        loc="lower left",
        bbox_to_anchor=(0.82, 0.10),
        bbox_transform=fig.transFigure,
        borderaxespad=0,
    )
    for handle in leg.get_lines():
        handle.set_linewidth(2.0)

    fig.subplots_adjust(left=0.0, right=0.97, bottom=0.16, top=0.90)
    _add_horizontal_cbar(
        fig, sm, "Distância Euclidiana Absoluta", ticks, cbar_bottom=0.12
    )
    fig.savefig(out_dir / f"3d_synthesis_{baseline}.jpg", dpi=300)
    if show:
        plt.show()
    plt.close(fig)


def run(cfg: dict) -> None:
    db_file = Path(cfg["db_file"])
    out_dir = Path(cfg["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    layer = cfg["layer"]
    raw_scenarios = cfg.get("scenario", "a0")
    scenarios = [raw_scenarios] if isinstance(raw_scenarios, str) else raw_scenarios
    baseline = cfg.get("baseline", "a0")
    show = cfg.get("show", False)
    cmap_name = cfg.get("cmap", "Spectral_r")
    clip = cfg.get("clip", False)
    elev = cfg.get("elev", 30)
    azim = cfg.get("azim", -60)
    step = cfg.get("step", 0.2)

    plt.rcParams.update({"font.family": "Arial", "font.size": 9})

    print(f"Reading layer '{layer}' from {db_file}")
    gdf = gpd.read_file(db_file, layer=layer)
    print(f"  {len(gdf)} features loaded")

    cmap = plt.get_cmap(cmap_name)
    ideal = np.array([0.0, 0.0, 1.0])  # risco=0, conflit=0, benefit=1

    print(f"Processing {len(scenarios)} scenario(s): {', '.join(scenarios)}")

    for scenario in scenarios:
        print(f"\n[{scenario}] Computing distances...")
        benefit_field = f"benefic_{scenario}"
        conflit_field = f"conflit_{scenario}"
        risco_field = f"risco_{scenario}"

        xs = gdf[risco_field].values
        ys = gdf[conflit_field].values
        zs = gdf[benefit_field].values

        distances = np.sqrt(
            (xs - ideal[0]) ** 2 + (ys - ideal[1]) ** 2 + (zs - ideal[2]) ** 2
        )
        n_nan = int(np.isnan(distances).sum())
        print(
            f"  dist_otima range: [{np.nanmin(distances):.4f}, {np.nanmax(distances):.4f}]  (NaN: {n_nan}/{len(distances)})"
        )
        for dim_name, dim_arr in [("beneficio", zs), ("conflito", ys), ("risco", xs)]:
            n = int(np.isnan(dim_arr).sum())
            if n:
                print(f"    WARNING: {dim_name} has {n} NaN value(s)")
        gdf[f"dist_otima_{scenario}"] = distances

        pairs = [
            (benefit_field, conflit_field, "Benefício", "Conflito"),
            (benefit_field, risco_field, "Benefício", "Risco"),
            (conflit_field, risco_field, "Conflito", "Risco"),
        ]
        plot_kwargs = dict(
            gdf=gdf,
            xs=xs,
            ys=ys,
            zs=zs,
            distances=distances,
            pairs=pairs,
            cmap=cmap,
            ideal=ideal,
            out_dir=out_dir,
            scenario=scenario,
            elev=elev,
            azim=azim,
            show=show,
        )

        print(f"[{scenario}] Saving 2D/3D scatter plots (full scale)...")
        _save_plots(d_min=0.0, d_max=np.sqrt(3), suffix="full", **plot_kwargs)

        if clip:
            print(f"[{scenario}] Saving 2D/3D scatter plots (clipped scale)...")
            _save_plots(
                d_min=np.nanmin(distances),
                d_max=np.nanmax(distances),
                suffix="clip",
                **plot_kwargs,
            )

    if baseline in scenarios and len(scenarios) > 1:
        non_bl = [s for s in scenarios if s != baseline]
        for s in non_bl:
            print(f"\nSaving trajectory plot ({baseline} → {s})...")
            _save_trajectory_plot(
                gdf=gdf,
                scenario=s,
                baseline=baseline,
                cmap=cmap,
                ideal=ideal,
                out_dir=out_dir,
                elev=elev,
                azim=azim,
                show=show,
            )
            print("  Done.")

        print(f"\nSaving synthesis plot ({baseline} + {', '.join(non_bl)})...")
        _save_synthesis_plot(
            gdf=gdf,
            scenarios=scenarios,
            baseline=baseline,
            cmap=cmap,
            ideal=ideal,
            out_dir=out_dir,
            elev=elev,
            azim=azim,
            show=show,
        )
        print("  Done.")

    print("\nSaving solution space plot...")
    _save_space_plot(
        step=step,
        cmap=cmap,
        ideal=ideal,
        out_dir=out_dir,
        elev=elev,
        azim=azim,
        show=show,
    )
    print("  Done.")
    print(f"\nAll outputs written to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, metavar="PATH")
    args = parser.parse_args()
    cfg = load_config(Path(args.config))
    run(cfg)


if __name__ == "__main__":
    main()
