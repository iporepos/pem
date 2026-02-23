# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
This is the complete API reference for the ``conflict`` python module of the ``pem`` system.


"""
import glob

# Native imports
# =======================================================================
from pathlib import Path
import os, pprint
import shutil

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import pandas as pd

# qgis stuff
import processing
from osgeo import gdal
from qgis.core import (
    QgsRasterLayer,
    QgsRasterBandStats,
)


# FUNCTIONS
# ***********************************************************************


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
    print(f" >>> pem @ conflict: {msg}")


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
    pvars["ext"] = _util_get_raster_extent(pvars["refraster"])
    res_dc = _util_get_raster_resolution(pvars["refraster"])
    pvars["res"] = res_dc["xres"]

    return pvars


def get_conflict_index(folder_project, scenario):
    """
    Calculate the spatial conflict index by performing
    weighted pairwise overlaps between user activity rasters.

    :param folder_project: Path to the root project directory
    :type folder_project: str
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :return: A list containing the path to the final normalized conflict raster
    :rtype: list

    .. dropdown:: Extra notes
        :icon: bookmark-fill
        :open:

        The function identifies all unique pairs of user activities and computes their intersection
        using raster multiplication. Each resulting overlap is normalized and then weighted based
        on a conflict matrix (CSV) before being aggregated into a final, normalized conflict map.

    .. include:: includes/examples/conflict_get_conflict.rst

    """

    def get_lower_value(df, a, b):
        if a == b:
            return 0  # diagonal

        # Get positional indices
        i = df.index.get_loc(a)
        j = df.index.get_loc(b)

        # Ensure we access lower triangle
        if i > j:
            return df.iloc[i, j]
        else:
            return df.iloc[j, i]

    _heading()
    _message(f"Get Conflict Index at {scenario}")

    pvars = _get_project_vars(folder_project=folder_project)

    folder_project = pvars["folder_project"]
    folder_inputs = pvars["folder_inputs"]
    folder_output = pvars["folder_outputs"] / f"{scenario}"
    folder_output_sub = folder_output / "intermediate/conflict"
    folder_output_sub.mkdir(exist_ok=True)

    folder_users = folder_inputs / f"users/{scenario}"

    ls_files = list(folder_users.glob("*.tif"))
    items = [Path(f).stem for f in ls_files]
    dc = {}

    for i in range(len(items)):
        dc[items[i]] = ls_files[i]

    # -----------------------------------------------------
    ls_conflicts = list()
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            nm1 = items[i]
            nm2 = items[j]

            _message(f"Processing {nm1} vs {nm2} ...")

            fi1 = dc[nm1]
            fi2 = dc[nm2]

            pair = f"{nm1}_{nm2}"
            fo_sub = folder_output_sub / f"conflict_{pair}.tif"

            dc_parameters = {
                "LAYERS": [str(fi1), str(fi2)],
                "EXPRESSION": '"{}@1" * "{}@1"'.format(nm1, nm2),
                "EXTENT": None,
                "CELL_SIZE": None,
                "CRS": None,
                "OUTPUT": str(fo_sub),
            }
            processing.run("native:rastercalc", dc_parameters)
            ls_conflicts.append(fo_sub)

    _message(f"Normalizing ...")
    ls_conflicts_fz = _util_normalize_rasters(ls_conflicts)

    _message(f"Loading conflict table ...")
    f_df = folder_users / "conflict.csv"
    df = pd.read_csv(f_df, sep=";", index_col=0)

    _message(f"Sum all conflicts ...")
    weighted_sum = None
    out_metadata = None

    for f in ls_conflicts_fz:

        nm = Path(f).stem
        a = nm.split("_")[1]
        b = nm.split("_")[2]

        w = get_lower_value(df, a, b)

        raster_dict = _util_read_raster(f)

        # 2. Extract data and convert to float32
        data = raster_dict["data"].astype(np.float32)

        if weighted_sum is None:
            weighted_sum = np.zeros_like(data)
            out_metadata = raster_dict.get("metadata")

        # Multiply the map by its weight and add it to the running total
        weighted_sum += data * w

    file_output = folder_output_sub / "conflict_wsum.tif"

    _message(f"Saving sum ...")
    _util_write_raster(
        grid_output=weighted_sum,  # Pass the cleaned data, not the array with NaNs
        dc_metadata=out_metadata,
        file_output=str(file_output),
    )
    _message(f"Normalizing sum ...")
    ls = _util_normalize_rasters([str(file_output)])

    fo = folder_output / f"{scenario}_conflict.tif"
    shutil.copy(src=ls[0], dst=fo)

    return [fo]


def setup_conflict_matrix(folder_project, scenario):
    """
    Initialize a blank lower-triangular conflict matrix CSV
    for all user activity rasters in a scenario.

    :param folder_project: Path to the root project directory
    :type folder_project: str
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :return: Path to the generated conflict matrix CSV
    :rtype: :class:`pathlib.Path`

    .. dropdown:: Extra notes
        :icon: bookmark-fill
        :open:

        This utility scans the scenario directory for raster files and creates a square
        symmetric-ready CSV. The lower triangle is initialized with ``1`` and the rest
        with ``0``, serving as a template for users to define conflict weights between activities.

    .. include:: includes/examples/conflict_setup_matrix.rst

    """
    _heading()
    _message(f"Setup Conflict Matrix at {scenario}")

    pvars = _get_project_vars(folder_project=folder_project)

    folder_inputs = pvars["folder_inputs"]
    folder_users = folder_inputs / f"users/{scenario}"

    ls_files = list(folder_users.glob("*.tif"))
    items = [Path(f).stem for f in ls_files]

    _message("Computing Matrix ...")
    n = len(items)

    # Create lower triangular matrix (excluding diagonal)
    matrix = np.tril(np.ones((n, n), dtype=int), k=-1)

    df = pd.DataFrame(matrix, index=items, columns=items)
    df.index.name = "users"
    _message("Saving ...")
    fo = folder_users / "conflict.csv"
    df.to_csv(fo, sep=";", index=True)

    _message_end()
    return fo


def _util_normalize_rasters(ls_rasters, suffix="fz", force_vmin=0):
    """
    Apply linear fuzzy membership to normalize raster values between 0 and 1 using their min/max statistics.

    .. note::

        The function calculates the minimum and maximum values of each input raster and uses
        them as boundaries for a linear membership function. If the minimum and maximum
        values are identical, the maximum is incremented by 1 to avoid division by zero.

    :param ls_rasters: List of paths to the raster files to be normalized
    :type ls_rasters: list
    :param suffix: String to append to the filename of the generated rasters. Default value = ``fz``
    :type suffix: str
    :param force_vmin: [optional] Manual lower bound for normalization; if ``None``, the raster minimum is used. Default value = 0
    :type force_vmin: int
    :return: List of paths to the newly created normalized raster files
    :rtype: list
    """
    ls_new_rasters = list()
    for r in ls_rasters:
        p = Path(r)
        file_output = p.parent / f"{p.stem}_{suffix}.tif"

        # get values
        dc_stats = _util_get_raster_stats(input_raster=str(p), full=True)
        if force_vmin is not None:
            vmin = force_vmin
        else:
            vmax = dc_stats["min"]

        vmax = dc_stats["max"]

        if vmin == vmax:
            vmax = vmax + 1

        dc_specs = {
            "INPUT": str(p),
            "BAND": 1,
            "FUZZYLOWBOUND": vmin,
            "FUZZYHIGHBOUND": vmax,
            "OUTPUT": str(file_output),
        }
        processing.run("native:fuzzifyrasterlinearmembership", dc_specs)
        ls_new_rasters.append(file_output)

    return ls_new_rasters


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


def _util_get_raster_extent(file_input):
    """
    Retrieves the spatial bounding coordinates of a raster file as a dictionary.

    :param file_input: The path to the input raster file.
    :type file_input: str
    :return: A dictionary containing the ``xmin``, ``xmax``, ``ymin``, and ``ymax`` coordinates.
    :rtype: dict
    """
    # Create a raster layer object
    raster_layer = QgsRasterLayer(str(file_input), "Raster Layer")
    layer_extent = raster_layer.extent()

    return {
        "xmin": layer_extent.xMinimum(),
        "xmax": layer_extent.xMaximum(),
        "ymin": layer_extent.yMinimum(),
        "ymax": layer_extent.yMaximum(),
    }


def _util_get_raster_resolution(file_input):
    # todo docstring
    # Create a raster layer object
    raster_layer = QgsRasterLayer(str(file_input), "Raster Layer")
    res_x = raster_layer.rasterUnitsPerPixelX()
    res_y = raster_layer.rasterUnitsPerPixelY()

    return {
        "xres": res_x,
        "yres": res_y,
    }


def _util_get_raster_stats(input_raster, band=1, full=False):
    """
    Calculates the statistics for a specified band of a given raster file.

    :param input_raster: Full path to the input raster file.
    :type input_raster: str
    :param band: The band number to calculate statistics for. Default value = ``1``
    :type band: int
    :return: A dictionary containing the raster band's mean, standard deviation, minimum, maximum, sum, and element count.
    :rtype: dict

    **Notes**

    The function uses QGIS classes internally to read the raster and compute statistics.
    The keys in the returned dictionary are ``mean``, ``sd``, ``min``, ``max``, ``sum``, and ``count``.

    """
    dc_stats = None
    if full:
        dc_raster = _util_read_raster(
            file_input=input_raster, n_band=band, metadata=None
        )
        data = dc_raster["data"]
        dc_stats = {
            "mean": float(np.nanmean(data)),
            "sd": float(np.nanstd(data)),
            "min": float(np.nanmin(data)),
            "max": float(np.nanmax(data)),
            "sum": float(np.nansum(data)),
            "count": float(np.count_nonzero(~np.isnan(data))),  # number of valid pixels
            "p01": float(np.nanpercentile(data, 1)),
            "p05": float(np.nanpercentile(data, 5)),
            "p25": float(np.nanpercentile(data, 25)),
            "p50": float(np.nanpercentile(data, 50)),  # median
            "p75": float(np.nanpercentile(data, 75)),
            "p95": float(np.nanpercentile(data, 95)),
            "p99": float(np.nanpercentile(data, 99)),
        }
    else:
        layer = QgsRasterLayer(input_raster, "raster")
        provider = layer.dataProvider()
        stats = provider.bandStatistics(band, QgsRasterBandStats.All, layer.extent(), 0)
        dc_stats = {
            "mean": stats.mean,
            "sd": stats.stdDev,
            "min": stats.minimumValue,
            "max": stats.maximumValue,
            "sum": stats.sum,
            "count": stats.elementCount,
        }
    return dc_stats


def _util_read_raster(file_input, n_band=1, metadata=True):
    """
    Read a raster (GeoTIFF) file

    :param file_input: path to raster file
    :type file_input: str
    :param n_band: number of the band to read
    :type n_band: int
    :param metadata: option to return
    :type metadata: bool
    :return: dictionary with "data" and (optional) "metadata"
    :rtype: dict
    """
    # -------------------------------------------------------------------------
    # LOAD
    # Open the raster file using gdal
    raster_input = gdal.Open(file_input)
    # Get the raster band
    band_input = raster_input.GetRasterBand(n_band)
    # Read the raster data as a numpy array
    grid_input = band_input.ReadAsArray()
    dc_output = {"data": grid_input}
    # -- Collect useful metadata
    if metadata:
        dc_metadata = {}
        dc_metadata["raster_x_size"] = raster_input.RasterXSize
        dc_metadata["raster_y_size"] = raster_input.RasterYSize
        dc_metadata["raster_projection"] = raster_input.GetProjection()
        dc_metadata["raster_geotransform"] = raster_input.GetGeoTransform()
        dc_metadata["cellsize"] = dc_metadata["raster_geotransform"][1]
        # append to output
        dc_output["metadata"] = dc_metadata
    # -- Close the raster
    raster_input = None

    return dc_output


def _util_write_raster(
    grid_output, dc_metadata, file_output, n_band=1, nodata_value=-99999
):
    """
    Write a numpy array to raster

    :param grid_output: 2D numpy array
    :type grid_output: :class:`numpy.ndarray`
    :param dc_metadata: dict with metadata
    :type dc_metadata: dict
    :param file_output: path to output raster file
    :type file_output: str
    :param n_band: number of the band to write
    :type n_band: int
    :param nodata_value: numeric value to represent NoData
    :type nodata_value: float or int
    :return: path to the written file
    :rtype: str
    """
    # Get the driver to create the new raster
    driver = gdal.GetDriverByName("GTiff")

    # get metadata
    raster_x_size = grid_output.shape[1]  # dc_metadata["raster_x_size"]
    raster_y_size = grid_output.shape[0]  # dc_metadata["raster_y_size"]
    raster_projection = dc_metadata["raster_projection"]
    raster_geotransform = dc_metadata["raster_geotransform"]

    # create the raster
    raster_output = driver.Create(
        file_output, raster_x_size, raster_y_size, 1, gdal.GDT_Float32
    )

    # Set the projection and geotransform of the new raster to match the original
    raster_output.SetProjection(raster_projection)
    raster_output.SetGeoTransform(raster_geotransform)

    # Get the band
    out_band = raster_output.GetRasterBand(n_band)

    # Assign the NoData value to the band
    if nodata_value is not None:
        out_band.SetNoDataValue(nodata_value)

    # Write the new data to the new raster
    out_band.WriteArray(grid_output)

    # Flush the cache to disk to prevent corrupted files
    out_band.FlushCache()

    # Close
    raster_output = None

    return file_output


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
