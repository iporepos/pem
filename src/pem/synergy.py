# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
This is the API reference for the ``synergy`` python module of the ``pem`` system.

It mirrors the ``conflict`` module. The spatial method is the same
(pairwise overlap of ocean-user rasters, weighted by a lower-triangular
matrix, summed and normalized to 0-1); only the weight matrix changes.
The synergy map is an analytical result: it is **not** a component of the
IDUSE-Mar performance index.

Typical workflow:

1. :func:`build_synergy_weights` -- workshop table -> ``synergy.csv``
   (plus the max / mean / difference pairwise matrices);
2. :func:`get_synergy_index` -- ``synergy.csv`` + user rasters ->
   ``outputs/<scenario>/<scenario>_synergy.tif``;
3. ``publish.publish_results`` -- samples the raster on the hexagonal grid
   and aggregates it to MicroUPGs and MacroUPGs (needs the one-line change
   in ``publish.py`` that picks up ``<scenario>_synergy.tif``);
4. :func:`plot_pairwise_heatmap` -- table-style figure of a weight matrix.

Only :func:`get_synergy_index` needs GDAL (``osgeo``, present in the QGIS
Python environment). The other functions run in plain Python
(pandas / numpy / matplotlib).

"""

# Native imports
# =======================================================================
import glob
from pathlib import Path

# External imports
# =======================================================================
import numpy as np
import pandas as pd

NODATA = -99999

# FUNCTIONS
# ***********************************************************************


def _message(msg):
    print(f" >>> pem @ synergy: {msg}")


def _message_end():
    _message("DONE")


def _heading():
    print(80 * "=")


def _get_users_maps(folder_users):
    """
    Get user activity rasters (same rule as the ``conflict`` module:
    file stems with an underscore, e.g. ``*_footprint``, are skipped).

    :param folder_users: Path to the users raster folder
    :type folder_users: str or pathlib.Path
    :return: sorted list of paths to the ocean-user rasters
    :rtype: list
    """
    folder_users = Path(folder_users)
    ls_files = sorted(glob.glob(f"{folder_users}/*.tif"))
    return [Path(f) for f in ls_files if "_" not in Path(f).stem]


# ---------------------------------------------------------------------------
# 1. Weights from the workshop tables
# ---------------------------------------------------------------------------


def _read_table(file_raw, sheet_name=0, sep=";"):
    file_raw = Path(file_raw)
    if file_raw.suffix.lower() in (".xlsx", ".xlsm", ".xls", ".ods"):
        df = pd.read_excel(file_raw, sheet_name=sheet_name, index_col=0)
    else:
        df = pd.read_csv(file_raw, sep=sep, index_col=0)
    df.index = [str(i).strip() for i in df.index]
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _pairwise(mat):
    """From a square matrix (rows = target, columns = perspective) derive the
    three pairwise matrices of the report, as full square arrays in which only
    the lower triangle is filled (everything else NaN).

    * max  -- larger of the two directions (A->B, B->A)
    * mean -- mean of the two directions
    * diff -- absolute difference between the two directions (asymmetry)

    A missing direction (NaN) is ignored for max and mean, and makes diff NaN.
    """
    a = mat
    b = mat.T
    a_f = np.where(np.isnan(a), b, a)
    b_f = np.where(np.isnan(b), a, b)
    both_nan = np.isnan(a) & np.isnan(b)

    mx = np.fmax(a, b)
    mean = (a_f + b_f) / 2.0
    mean[both_nan] = np.nan
    diff = np.abs(a - b)

    lower = np.tril(np.ones(a.shape, dtype=bool), k=-1)
    out = {}
    for key, arr in (("max", mx), ("mean", mean), ("diff", diff)):
        arr = arr.astype(float).copy()
        arr[~lower] = np.nan
        out[key] = arr
    return out


def build_synergy_weights(
    file_raw,
    folder_out,
    rename=None,
    keep=None,
    n_valid=None,
    normalize=True,
    stat="max",
    perspective="columns",
    sheet_name=0,
    sep=";",
    prefix="synergy",
):
    """
    Build the lower-triangular synergy weight matrix from the workshop table.

    The raw table is a square matrix of sectors in which **each column is the
    perspective of one sector** (one workshop) and **each row is a target
    sector**; cells are the score (mentions) that the workshop gave to the
    target sector as having the highest synergy potential. This is the layout
    described in section 2.3.2 of the report for the conflict matrix; use
    ``perspective="rows"`` if your table is transposed.

    Steps (same as for the conflict matrix):

    1. clean labels and apply ``rename``;
    2. normalize each workshop (column) to a share: score divided by the
       workshop's total of valid responses (``n_valid``; if ``None`` the column
       sum is used) -- skipped when ``normalize=False``;
    3. keep only the sectors in ``keep`` (normalization happens *before* this,
       so shares are relative to the full workshop);
    4. derive the pairwise matrices (max, mean, difference), lower triangle;
    5. write them next to each other, plus the normalized original matrix.

    :param file_raw: path to the raw workshop table (``.csv`` with ``sep``, or ``.xlsx`` / ``.ods``)
    :type file_raw: str or pathlib.Path
    :param folder_out: folder to write to. Use ``inputs/users/<scenario>`` so ``synergy.csv`` is found by :func:`get_synergy_index`
    :type folder_out: str or pathlib.Path
    :param rename: optional dict ``{label in table: raster file stem}``; the stems must match the user raster names (without ``.tif``)
    :type rename: dict
    :param keep: optional list of raster stems to retain (sectors with no raster are dropped)
    :type keep: list
    :param n_valid: optional dict / Series ``{perspective label: number of valid responses}``
    :type n_valid: dict
    :param normalize: set ``False`` if the table already holds shares
    :type normalize: bool
    :param stat: pairwise statistic written as the weights file, ``"max"`` (analogue of the conflict index, "best case") or ``"mean"``
    :type stat: str
    :param perspective: ``"columns"`` (default) or ``"rows"``
    :type perspective: str
    :param prefix: file name prefix. Default value = ``synergy``
    :type prefix: str
    :return: dict with the paths written (``weights``, ``max``, ``mean``, ``diff``, ``normalized``)
    :rtype: dict
    """
    _heading()
    _message("Build synergy weights")

    if stat not in ("max", "mean"):
        raise ValueError("stat must be 'max' or 'mean'")
    if perspective not in ("columns", "rows"):
        raise ValueError("perspective must be 'columns' or 'rows'")

    df = _read_table(file_raw, sheet_name=sheet_name, sep=sep)
    if perspective == "rows":
        df = df.T

    if rename:
        df = df.rename(index=rename, columns=rename)

    # common, ordered list of sectors (rows first, then columns not in rows)
    sectors = list(df.index) + [c for c in df.columns if c not in df.index]
    df = df.reindex(index=sectors, columns=sectors)
    df = df.apply(pd.to_numeric, errors="coerce")

    # a sector does not nominate itself
    mat = df.values.astype(float)
    np.fill_diagonal(mat, np.nan)
    df = pd.DataFrame(mat, index=sectors, columns=sectors)

    if normalize:
        if n_valid is None:
            _message("Normalizing each workshop by its column sum (n_valid not given)")
            tot = df.sum(axis=0, skipna=True)
        else:
            tot = pd.Series(n_valid, dtype=float).reindex(sectors)
            _message("Normalizing each workshop by n_valid")
        tot = tot.replace(0, np.nan)
        df = df.div(tot, axis=1)
    else:
        _message("Table taken as already normalized")

    if keep is not None:
        dropped = [s for s in sectors if s not in keep]
        absent = [s for s in keep if s not in sectors]
        if absent:
            raise ValueError(
                f"Sectors in 'keep' not found in the table (check 'rename'): {absent}"
            )
        if dropped:
            _message(f"Dropping sectors without raster: {dropped}")
        sectors = [s for s in keep]
        df = df.loc[sectors, sectors]

    pw = _pairwise(df.values.astype(float))

    folder_out = Path(folder_out)
    folder_out.mkdir(parents=True, exist_ok=True)
    paths = {}

    def _save(arr, name, fill):
        out = pd.DataFrame(arr, index=sectors, columns=sectors)
        if fill is not None:
            out = out.fillna(fill)
        out.index.name = "users"
        fo = folder_out / name
        out.to_csv(fo, sep=";", index=True)
        return fo

    # weights file: same layout as conflict.csv (lower triangle, zeros elsewhere)
    paths["weights"] = _save(pw[stat], f"{prefix}.csv", fill=0.0)
    paths["max"] = _save(pw["max"], f"{prefix}_max.csv", fill=None)
    paths["mean"] = _save(pw["mean"], f"{prefix}_mean.csv", fill=None)
    paths["diff"] = _save(pw["diff"], f"{prefix}_diff.csv", fill=None)
    paths["normalized"] = _save(df.values, f"{prefix}_normalized.csv", fill=None)

    _message(f"Weights = pairwise {stat}; written to {paths['weights']}")
    _message_end()
    return paths


# ---------------------------------------------------------------------------
# 2. Synergy raster
# ---------------------------------------------------------------------------


def _get_pair_weight(df, a, b):
    """Lower-triangle lookup, as in ``conflict.get_conflict_index``."""
    if a == b:
        return 0.0
    i = df.index.get_loc(a)
    j = df.index.get_loc(b)
    w = df.iloc[i, j] if i > j else df.iloc[j, i]
    return 0.0 if pd.isna(w) else float(w)


def _weighted_overlap_sum(layers, df, verbose=True):
    """Core of the method, on numpy arrays.

    Same steps as ``conflict.get_conflict_index``:

    1. for every unique pair of users, overlap = layer_a x layer_b;
    2. each overlap is divided by its own maximum (linear membership 0 -> max);
    3. weighted by the pair weight and summed;
    4. the sum is divided by its maximum (0-1).

    :param layers: ``{user name: 2D array}``; NaN is NoData
    :type layers: dict
    :param df: weights, square, lower triangle used
    :type df: pandas.DataFrame
    :return: 2D array in 0-1 (NaN where every pair is NoData)
    :rtype: numpy.ndarray
    """
    names = list(layers)
    shape = layers[names[0]].shape
    wsum = np.zeros(shape, dtype=np.float64)
    valid = np.zeros(shape, dtype=bool)

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            w = _get_pair_weight(df, a, b)
            if verbose:
                _message(f"{a} x {b}: weight = {w:.3f}")

            ov = layers[a].astype(np.float64) * layers[b].astype(np.float64)
            ok = ~np.isnan(ov)
            valid |= ok
            vmax = float(np.nanmax(ov)) if ok.any() else 0.0
            if vmax <= 0:
                vmax = 1.0  # same guard as the fuzzify step in conflict.py
            ov_n = np.clip(ov / vmax, 0.0, 1.0)
            wsum += np.where(ok, ov_n * w, 0.0)

    smax = float(wsum[valid].max()) if valid.any() else 0.0
    if smax <= 0:
        smax = 1.0
    out = wsum / smax
    out[~valid] = np.nan
    return out


def _util_read_raster(file_input, n_band=1):
    from osgeo import gdal

    ds = gdal.Open(str(file_input))
    band = ds.GetRasterBand(n_band)
    data = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()
    if nodata is not None:
        data[np.isclose(data, nodata)] = np.nan
    meta = {
        "projection": ds.GetProjection(),
        "geotransform": ds.GetGeoTransform(),
    }
    ds = None
    return data, meta


def _util_write_raster(grid_output, meta, file_output, nodata_value=NODATA):
    from osgeo import gdal

    driver = gdal.GetDriverByName("GTiff")
    ny, nx = grid_output.shape
    ds = driver.Create(str(file_output), nx, ny, 1, gdal.GDT_Float32)
    ds.SetProjection(meta["projection"])
    ds.SetGeoTransform(meta["geotransform"])
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(nodata_value)
    band.WriteArray(np.nan_to_num(grid_output, nan=nodata_value).astype(np.float32))
    band.FlushCache()
    ds = None
    return str(file_output)


def get_synergy_index(folder_project, scenario, matrix_name="synergy.csv"):
    """
    Calculate the spatial synergy map by weighted pairwise overlaps between
    user activity rasters (analogue of ``conflict.get_conflict_index``).

    Reads ``inputs/users/<scenario>/<matrix_name>`` (``;``-separated,
    lower triangle, names equal to the raster file stems) and writes
    ``outputs/<scenario>/<scenario>_synergy.tif`` (0-1, normalized per scenario).

    :param folder_project: Path to the root project directory
    :type folder_project: str or pathlib.Path
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :param matrix_name: file name of the weights, in the scenario users folder
    :type matrix_name: str
    :return: list with the path to the output raster
    :rtype: list
    """
    _heading()
    _message(f"Get Synergy Index at {scenario}")

    folder_project = Path(folder_project)
    folder_users = folder_project / "inputs" / "users" / scenario
    folder_output = folder_project / "outputs" / scenario
    f_matrix = folder_users / matrix_name

    for p in (folder_users, f_matrix):
        if not Path(p).exists():
            raise FileNotFoundError(f" >>> check for {p}")

    df = pd.read_csv(f_matrix, sep=";", index_col=0)
    df.index = [str(i).strip() for i in df.index]
    df.columns = [str(c).strip() for c in df.columns]

    ls_files = _get_users_maps(folder_users)
    items = [p.stem for p in ls_files]
    if len(items) < 2:
        raise ValueError(f"Need at least two user rasters in {folder_users}")

    missing = [n for n in items if n not in df.index or n not in df.columns]
    if missing:
        raise ValueError(
            f"User rasters without a row/column in {matrix_name}: {missing}. "
            f"Matrix sectors: {list(df.index)}"
        )
    # rows and columns in the file's own order; only its lower triangle is read
    # (do NOT reorder to the raster order: that would move weights to the
    # unused upper triangle)
    df = df[list(df.index)]
    upper = np.triu(df.apply(pd.to_numeric, errors="coerce").fillna(0).values, k=1)
    if np.abs(upper).sum() > 0:
        _message(
            f"WARNING: {matrix_name} has non-zero values above the diagonal; "
            "they are ignored (only the lower triangle is used)"
        )

    _message("Reading user rasters ...")
    layers = {}
    meta = None
    for name, f in zip(items, ls_files):
        data, m = _util_read_raster(f)
        if meta is None:
            meta = m
            shape = data.shape
        elif data.shape != shape:
            raise ValueError(f"{f.name} has shape {data.shape}, expected {shape}")
        layers[name] = data

    _message("Weighted overlaps ...")
    out = _weighted_overlap_sum(layers, df)

    folder_output.mkdir(parents=True, exist_ok=True)
    fo = folder_output / f"{scenario}_synergy.tif"
    _message("Saving ...")
    _util_write_raster(out, meta, fo)

    _message_end()
    return [fo]


# ---------------------------------------------------------------------------
# 3. Table-style figure
# ---------------------------------------------------------------------------


def plot_pairwise_heatmap(
    file_csv,
    file_png,
    labels=None,
    cmap="YlGnBu",
    title=None,
    vmax=None,
    dpi=300,
):
    """
    Draw a pairwise matrix as a lower-triangle heatmap table, in the layout of
    Tabela 1 of the report (decimal comma, short sector names on the columns,
    "-" on the diagonal).

    :param file_csv: matrix written by :func:`build_synergy_weights` (e.g. ``synergy_max.csv``)
    :type file_csv: str or pathlib.Path
    :param file_png: output image
    :type file_png: str or pathlib.Path
    :param labels: optional dict ``{stem: (row label, column abbreviation)}``
    :type labels: dict
    :param cmap: matplotlib colormap. Default value = ``YlGnBu``
    :type cmap: str
    :param title: optional title
    :type title: str
    :param vmax: upper bound of the colour scale. If ``None`` the matrix maximum is used; set the same value on two figures to compare them
    :type vmax: float
    :param dpi: resolution. Default value = ``300``
    :type dpi: int
    :return: path of the saved image
    :rtype: str
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    df = pd.read_csv(file_csv, sep=";", index_col=0)
    names = list(df.index)
    n = len(names)
    mat = df.values.astype(float)

    lower = np.tril(np.ones((n, n), dtype=bool), k=-1)
    shown = np.where(lower, mat, np.nan)
    vmax = float(np.nanmax(shown)) if vmax is None else vmax

    row_lab = [labels[s][0] if labels and s in labels else s for s in names]
    col_lab = [labels[s][1] if labels and s in labels else s[:3].upper() for s in names]

    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    cm = plt.get_cmap(cmap).copy()
    cm.set_bad("white")
    im = ax.imshow(np.ma.masked_invalid(shown), cmap=cm, vmin=0, vmax=vmax)

    for i in range(n):
        for j in range(n):
            if i == j:
                ax.text(j, i, "—", ha="center", va="center", fontsize=8, color="#666")
            elif lower[i, j] and not np.isnan(mat[i, j]):
                v = mat[i, j]
                color = "white" if v > 0.6 * vmax else "black"
                ax.text(
                    j,
                    i,
                    f"{v:.2f}".replace(".", ","),
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color=color,
                    fontweight="bold",
                )

    ax.set_xticks(range(n))
    ax.set_xticklabels(col_lab, fontsize=8, fontweight="bold")
    ax.xaxis.tick_top()
    ax.set_yticks(range(n))
    ax.set_yticklabels(row_lab, fontsize=8)
    ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
    ax.grid(which="minor", color="#dddddd", linewidth=0.6)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)

    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cb.set_ticks([])
    cb.ax.text(
        0.5,
        1.02,
        "Maior intensidade\nrelativa",
        ha="center",
        va="bottom",
        fontsize=7.5,
        transform=cb.ax.transAxes,
    )
    cb.ax.text(
        0.5,
        -0.02,
        "Menor intensidade\nrelativa",
        ha="center",
        va="top",
        fontsize=7.5,
        transform=cb.ax.transAxes,
    )
    cb.outline.set_visible(False)

    if title:
        fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(file_png, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(file_png)


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    print("Hello")
