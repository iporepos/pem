# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
This is the complete API reference for the ``publish`` python module of the ``pem`` system.

This module assembles the final published results for a scenario run: it
publishes the grid and units layers to a single GeoPackage, warps the
scenario's raster maps (benefit, risk, conflict, performance, and any
user-activity maps) to the target CRS, computes zonal statistics of each
map over the grid, joins those statistics back onto the grid (normalized
to the ``[0, 1]`` range), and finally aggregates the grid statistics by
unit, via a non-spatial group-by on the unit id, joining the resulting
means back onto each unit layer.

This module is intended to be run from within the QGIS Python
environment, since it relies on the ``processing``, ``osgeo``, and
``qgis.core`` packages for raster warping and zonal statistics.

.. dropdown:: Script example
    :icon: code-square
    :open:

    .. code-block:: python

        # !WARNING: run this in QGIS Python Environment
        import importlib.util as iu

        # define the paths to the module file
        # ------------------------------------------------------
        file = "path/to/publish.py"  # change here

        # define the project folder
        # ------------------------------------------------------
        folder = "path/to/project_folder"  # change here

        # define scenario
        # ------------------------------------------------------
        scenario = "baseline"

        # define grid layer name
        # ------------------------------------------------------
        grid = "grid"

        # define units layers
        # ------------------------------------------------------
        units = {
            "units_micro": {
                "layer": "upg_micro",
                "id": "id"
            },

            "units_macro": {
                "layer": "upg_macro",
                "id": "id"
            },
        }

        # call the function
        # ------------------------------------------------------
        # do not change here
        spec = iu.spec_from_file_location("module", file)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        ls_output = module.publish_results(
            folder_project=folder,
            scenario=scenario,
            grid_layer=grid,
            units_layers=units,
            grid_id_field="h3_index",
            crs_epsg=4326
        )

        print(" ----- DONE -----")

"""

# Native imports
# =======================================================================
import glob
from pathlib import Path
import os, pprint
import shutil

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# qgis stuff
import processing
from osgeo import gdal
from qgis.core import QgsRasterLayer, QgsRasterBandStats, QgsCoordinateReferenceSystem


def _file_checker(ls):
    for f in ls:
        p = Path(f)
        if not p.is_file():
            raise FileNotFoundError(f" >>> check for {p}")


def _folder_checker(ls):
    for f in ls:
        p = Path(f)
        if not p.is_dir():
            raise FileNotFoundError(f" >>> check for {p}")


def _message(msg):
    print(f" >>> pem @ publish: {msg}")


def _message_end():
    _message("DONE")


def _heading():
    print(80 * "=")


def _get_project_vars(folder_project):
    pvars = {}

    folder_project = Path(folder_project)
    pvars["folder_project"] = folder_project
    pvars["folder_inputs"] = folder_project / "inputs"
    pvars["folder_outputs"] = folder_project / "outputs"

    # infer input database
    # ----------------------------------------
    pvars["vectors"] = pvars["folder_inputs"] / "vectors.gpkg"

    # infer reference raster
    # ----------------------------------------
    pvars["refraster"] = pvars["folder_inputs"] / "bathymetry.tif"

    # run checks
    # ----------------------------------------
    ls = [folder_project]
    _folder_checker(ls)

    ls = [pvars["vectors"], pvars["refraster"]]
    _file_checker(ls)

    # get extra parameters
    # ===============================================
    pvars["crs"] = _util_get_raster_crs(pvars["refraster"], code_only=True)

    return pvars


def _util_get_raster_crs(file_input, code_only=True):
    """
    Extracts the Coordinate Reference System (CRS) from a raster file.

    :param file_input: The file path to the raster source.
    :type file_input: str
    :param code_only: Whether to return only the numerical ID (e.g., ``31983``) or the full authority ID (e.g., ``EPSG:31983``). Default value = ``True``
    :type code_only: bool
    :return: The CRS identifier as a string.
    :rtype: str

    """
    rlayer = QgsRasterLayer(str(file_input), "Raster Layer")
    crs = rlayer.crs()
    # Returns string like 'EPSG:31983'
    epsg_authid = crs.authid()
    if code_only:
        return crs.authid().split(":")[1]
    else:
        return epsg_authid


def _load_and_reproject(input_db, layer, crs_epsg):
    """Load a vector layer and reproject it to ``crs_epsg`` if needed.

    Raises ValueError if the layer has no CRS defined.
    """
    gdf = gpd.read_file(input_db, layer=layer)

    if gdf.crs is None:
        raise ValueError(f"Layer '{layer}' has no CRS defined.")

    if gdf.crs.to_epsg() != crs_epsg:
        gdf = gdf.to_crs(epsg=crs_epsg)

    return gdf


def _assign_unit_ids(grid, unit_layer_name, unit_gdf, id_field):
    """Append a column to ``grid`` with the id of the unit polygon that
    contains each grid polygon's centroid.

    The new column is named after ``unit_layer_name``. Grid rows whose
    centroid does not fall inside any unit polygon are left as NaN.
    """
    centroids = gpd.GeoDataFrame(
        grid[[]].copy(),
        geometry=grid.geometry.centroid,
        crs=grid.crs,
    )

    joined = gpd.sjoin(
        centroids,
        unit_gdf[[id_field, "geometry"]],
        how="left",
        predicate="within",
    )

    # guard against centroids matching more than one unit polygon
    joined = joined[~joined.index.duplicated(keep="first")]

    grid[unit_layer_name] = joined[id_field].reindex(grid.index).values

    return grid


def _normalize_minmax(series, lower_pct=5, upper_pct=95):
    """Normalize a numeric Series to the [0, 1] range using percentiles.

    The scaling range is defined by the ``lower_pct`` and ``upper_pct``
    percentiles of ``series`` (default 5th/95th) rather than the
    absolute min/max, so a handful of extreme outliers won't compress
    the bulk of the data into a narrow band. Values are clipped to
    [0, 1] after scaling, so anything below the lower percentile maps
    to 0.0 and anything above the upper percentile maps to 1.0.

    If the resulting range is zero (e.g. all values equal), every
    non-null entry is mapped to 0.0 rather than producing a
    division-by-zero NaN.
    """
    col_min = series.quantile(lower_pct / 100)
    col_max = series.quantile(upper_pct / 100)
    col_range = col_max - col_min

    if col_range == 0:
        return series.where(series.isna(), 0.0)

    normalized = (series - col_min) / col_range
    return normalized.clip(lower=0.0, upper=1.0)


def _join_zonal_stats(grid, grid_id_field, stats_db, stats_layers, normalize=True):
    """Join zonal-statistics columns back onto ``grid``.

    Each entry in ``stats_layers`` is the name of a layer in ``stats_db``
    that holds one stats column (e.g. ``"<map>_mean"``) plus geometry,
    sharing the same row alignment as ``grid`` via ``grid_id_field``.
    The stat column name is derived from the layer name and merged onto
    ``grid`` under the plain map name (e.g. ``"benefit"``).

    :param grid: the grid GeoDataFrame to receive the stat columns
    :type grid: geopandas.GeoDataFrame
    :param grid_id_field: name of the stable unique id column present in
        both ``grid`` and each layer in ``stats_layers``
    :type grid_id_field: str
    :param stats_db: path to the geopackage holding the stats layers
    :type stats_db: str or Path
    :param stats_layers: layer names to read from ``stats_db``
    :type stats_layers: list
    :param normalize: if True, min-max normalize each joined stat column
        to the [0, 1] range, in place, using the grid's own min/max
    :type normalize: bool
    :return: ``grid`` with one new column per entry in ``stats_layers``
    :rtype: geopandas.GeoDataFrame
    """
    for layer in stats_layers:
        stats = gpd.read_file(stats_db, layer=layer)

        stat_col = layer.split("_")[1] + "_mean"

        nm = stat_col.split("_")[0]

        stats = stats[[grid_id_field, stat_col]].rename(columns={stat_col: nm})

        grid = grid.merge(stats, on=grid_id_field, how="left")

        if normalize:
            grid[nm] = _normalize_minmax(grid[nm])

    return grid


def _aggregate_stats_by_unit(grid, grid_unit_field, unit_gdf, unit_id_field, stat_cols):
    """Aggregate grid-level stat columns by unit, via a non-spatial
    groupby, and left-join the means onto ``unit_gdf``.

    The join is non-destructive: every row and column already in
    ``unit_gdf`` is preserved, and only the new per-stat mean columns
    are added (NaN for any unit with no matching grid rows).

    :param grid: grid GeoDataFrame, already carrying ``grid_unit_field``
        (e.g. from ``_assign_unit_ids``) and the stat columns to
        aggregate
    :type grid: geopandas.GeoDataFrame
    :param grid_unit_field: name of the column on ``grid`` holding each
        row's unit id (named after the unit layer, per
        ``_assign_unit_ids``)
    :type grid_unit_field: str
    :param unit_gdf: the unit GeoDataFrame to receive the aggregated
        mean columns
    :type unit_gdf: geopandas.GeoDataFrame
    :param unit_id_field: name of the id column on ``unit_gdf`` itself
        (the unit layer's own id field, e.g. ``"mun_id"``)
    :type unit_id_field: str
    :param stat_cols: names of the grid stat columns to average per
        unit
    :type stat_cols: list
    :return: ``unit_gdf`` with one new mean column per entry in
        ``stat_cols``
    :rtype: geopandas.GeoDataFrame
    """
    means = grid.groupby(grid_unit_field)[stat_cols].mean()
    means = means.reset_index()
    means = means.rename(columns={grid_unit_field: unit_id_field})

    return unit_gdf.merge(means, on=unit_id_field, how="left")


def _get_users_maps(folder_users):
    """
    Get user activity rasters maps from user activity rasters.

    :param folder_users: Path to the users raster folder
    :type folder_users: str
    :return: A list containing the paths to the ocean users rasters
    :rtype: list

    """
    folder_users = Path(folder_users)

    ls_files = glob.glob(f"{folder_users}/*.tif")
    ls_files_filter = []
    for f in ls_files:
        p = Path(f)
        nm = p.stem
        if "_" not in nm:
            ls_files_filter.append(p)

    return ls_files_filter


def publish_results(
    folder_project, scenario, grid_layer, units_layers, grid_id_field, crs_epsg=4326
):
    """Assemble and publish the final results of a scenario run.

    This is the top-level entry point of the module. For a given
    project and scenario it builds a single output GeoPackage
    (``outputs/<scenario>/results.gpkg``) holding the grid layer, the
    units layers, and a set of derived statistics, by running the
    following steps in order:

    1. Load the grid layer and each unit layer from the project's
       input vector database, reprojecting both to ``crs_epsg`` if
       needed (see :func:`_load_and_reproject`).
    2. For each unit layer, tag every grid row with the id of the unit
       polygon that contains its centroid (see :func:`_assign_unit_ids`),
       then publish both the grid and the unit layers to the output
       GeoPackage.
    3. Warp the scenario's raster maps (``benefit``, ``risk``,
       ``conflict``, ``performance``, plus any user-activity maps found
       under ``inputs/users/<scenario>``) to ``crs_epsg``.
    4. Compute zonal statistics (mean) of each warped map over the grid,
       then join the resulting per-map mean back onto the grid,
       normalized to the ``[0, 1]`` range (see :func:`_join_zonal_stats`
       and :func:`_normalize_minmax`), and republish the grid layer.
    5. Aggregate the grid's per-map statistics by unit, via a
       non-spatial group-by on each unit's id, and join the resulting
       means back onto each unit layer non-destructively (see
       :func:`_aggregate_stats_by_unit`), republishing each unit layer.

    :param folder_project: path to the project folder. Must contain an
        ``inputs/vectors.gpkg`` (holding the grid and unit layers) and
        an ``inputs/bathymetry.tif`` reference raster; see
        :func:`_get_project_vars`.
    :type folder_project: str or pathlib.Path
    :param scenario: name of the scenario to publish. Used to locate
        the scenario's raster maps (``<scenario>_<map>.tif``) and the
        ``inputs/users/<scenario>`` folder, and as the output
        subfolder name under ``outputs/``.
    :type scenario: str
    :param grid_layer: name of the grid layer in ``vectors.gpkg``. Also
        used as the name under which the grid is published in the
        output GeoPackage.
    :type grid_layer: str
    :param units_layers: mapping of unit layer name (as published in
        the output GeoPackage) to a dict with the keys ``"layer"``
        (the source layer name in ``vectors.gpkg``) and ``"id"`` (the
        name of that unit layer's unique id field), e.g.::

            {
                "units_micro": {"layer": "upg_micro", "id": "id"},
                "units_macro": {"layer": "upg_macro", "id": "id"},
            }

    :type units_layers: dict
    :param grid_id_field: name of the stable unique id field on the
        grid layer, used to join the zonal statistics back onto it.
    :type grid_id_field: str
    :param crs_epsg: EPSG code of the target CRS that the grid, unit
        layers, and raster maps are reprojected/warped to. Defaults to
        ``4326``.
    :type crs_epsg: int
    :return: None. All results are written to
        ``outputs/<scenario>/results.gpkg`` in ``folder_project``.
    :rtype: None
    """
    _heading()
    _message(f"Publish results at scenario = {scenario}")

    pvars = _get_project_vars(folder_project=folder_project)

    input_db = pvars["vectors"]

    users_folder = pvars["folder_inputs"] / f"users/{scenario}"

    output_folder = pvars["folder_outputs"] / scenario
    output_folder_intermediate = output_folder / "intermediate"

    output_folder.mkdir(parents=True, exist_ok=True)
    output_folder_intermediate.mkdir(parents=True, exist_ok=True)

    output_db = output_folder / "results.gpkg"

    # ===========================================================
    _heading()
    _message(f"Load grid layer")
    # Load grid layer and reproject to the target CRS if needed
    grid = _load_and_reproject(input_db, grid_layer, crs_epsg)

    # ===========================================================
    # ===========================================================
    _heading()
    _message(f"Publish units layers")

    for unit_layer in units_layers:
        unit = _load_and_reproject(
            input_db, units_layers[unit_layer]["layer"], crs_epsg
        )
        unit.to_file(output_db, layer=unit_layer, driver="GPKG")

        # tag grid rows with this unit's id, based on centroid containment
        id_field = units_layers[unit_layer]["id"]
        grid = _assign_unit_ids(grid, unit_layer, unit, id_field)

    # ===========================================================
    # ===========================================================
    _heading()
    _message(f"Publish grid layer")
    grid.to_file(output_db, layer=grid_layer, driver="GPKG")

    # ===========================================================
    # Handle maps
    _heading()
    _message(f"Warp maps")

    folder_maps = output_folder_intermediate / "warped"
    folder_maps.mkdir(parents=True, exist_ok=True)

    # make an intermediate copy
    output_warp_db = folder_maps / "warp.gpkg"
    shutil.copy(output_db, output_warp_db)

    # handle users
    ls_users_maps = _get_users_maps(folder_users=users_folder)

    # handle main maps
    ls_main = ["benefit", "risk", "conflict", "performance"]
    ls_main_maps = [output_folder / f"{scenario}_{i}.tif" for i in ls_main]

    ls_maps = ls_users_maps + ls_main_maps

    maps_dc = {}
    for raster_map in ls_maps:
        _message(f"Warping: {raster_map.stem}")

        nm = raster_map.stem
        if "_" in raster_map.stem:
            nm = raster_map.stem.split("_")[1]

        fo = str(folder_maps / f"{nm}.tif")
        parameters = {
            "INPUT": str(raster_map),
            "SOURCE_CRS": QgsCoordinateReferenceSystem("EPSG:{}".format(pvars["crs"])),
            "TARGET_CRS": QgsCoordinateReferenceSystem(f"EPSG:{crs_epsg}"),
            "RESAMPLING": 1,
            "NODATA": None,
            "TARGET_RESOLUTION": None,
            "OPTIONS": None,
            "DATA_TYPE": 0,
            "TARGET_EXTENT": None,
            "TARGET_EXTENT_CRS": None,
            "MULTITHREADING": False,
            "EXTRA": "",
            "OUTPUT": fo,
        }
        processing.run("gdal:warpreproject", parameters)
        maps_dc[nm] = fo

    ls_layers = []
    for m in maps_dc:
        _message(f"Collecting stats: {m}")
        map_file = maps_dc[m]
        lcl_grid = f"{grid_layer}_{m}"
        parameters = {
            "INPUT": f"{output_db}|layername={grid_layer}",
            "INPUT_RASTER": str(map_file),
            "RASTER_BAND": 1,
            "COLUMN_PREFIX": f"{m}_",
            "STATISTICS": [2],
            "OUTPUT": "ogr:dbname='"
            + str(output_warp_db)
            + "' "
            + f'table="{lcl_grid}" (geom)',
            # 'OUTPUT': 'ogr:dbname=\'C:/data/losalamos/A001/inputs/data/pemsul/outputs/baseline/results.gkg\' table="grid" (geom)'
        }

        processing.run("native:zonalstatisticsfb", parameters)
        ls_layers.append(lcl_grid)

    # ===========================================================
    # ===========================================================
    _heading()
    _message(f"Join zonal stats back to grid")
    grid = _join_zonal_stats(
        grid=grid,
        grid_id_field=grid_id_field,
        stats_db=output_warp_db,
        stats_layers=ls_layers,
    )

    grid.to_file(output_db, layer=grid_layer, driver="GPKG")

    # ===========================================================
    # ===========================================================
    _heading()
    _message(f"Aggregate stats by unit")

    stat_cols = list(maps_dc.keys())

    for unit_layer in units_layers:
        unit_id_field = units_layers[unit_layer]["id"]

        # read back the unit layer as already published, so the join is
        # non-destructive (existing unit attributes are preserved)
        unit_gdf = gpd.read_file(output_db, layer=unit_layer)

        unit_gdf = _aggregate_stats_by_unit(
            grid=grid,
            grid_unit_field=unit_layer,
            unit_gdf=unit_gdf,
            unit_id_field=unit_id_field,
            stat_cols=stat_cols,
        )

        unit_gdf.to_file(output_db, layer=unit_layer, driver="GPKG")

    _message_end()


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":
    # Test doctests
    # ===================================================================
    print("Hello")

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
