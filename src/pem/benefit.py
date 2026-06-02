# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
This is the complete API reference for the ``benefit`` python module of the ``pem`` system.

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
import matplotlib.pyplot as plt

# qgis stuff
import processing
from osgeo import gdal
from qgis.core import (
    QgsRasterLayer,
    QgsRasterBandStats,
)


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
    print(f" >>> pem @ benefit: {msg}")


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


def _get_benefit_weight(df, scenario, user, attribute):
    df = df.query(f"scenario == '{scenario}'").copy()
    df = df.query(f"user =='{user}'").copy()
    w = df[attribute].sum()
    return w


def get_benefit_index(folder_project, scenario, attribute):
    """
    Calculate and map the spatial Benefit Index for a given scenario and socio-economic metric.

    This function executes the core downscaling pipeline of the PEM framework's benefit
    component. It maps aggregate socio-economic value (e.g., employment, revenue) back
    to the marine space based on relative ocean use intensity.

    **Mathematical Pipeline**

    For each ocean user :math:`i`, the function reads its spatial intensity surface :math:`U_{i, j}`
    across all grid cells :math:`j` and scales it linearly against the total onshore economic
    benefit :math:`B_i` aggregated from coastal hubs:

    .. math::

        c_i = \\frac{B_i}{\sum_{j} U_{i, j}}

    .. math::

        B_{i, j} = c_i \cdot U_{i, j}

    Individual scaled layers are summed into a cumulative absolute benefit surface, which
    is then linearly fuzzified to a standard :math:`[0, 1]` range to represent relative
    benefit hotspots.

    :param folder_project: Path to the root project directory containing 'inputs' and 'outputs'.
    :type folder_project: str or pathlib.Path
    :param scenario: Name of the simulation scenario (matches folder name under ``inputs/users/``).
    :type scenario: str
    :param attribute: The targeted column header name in the benefit CSV file (e.g., ``'jobs_number'``).
    :type attribute: str
    :return: A list of file paths pointing to the individual, un-normalized spatial benefit rasters generated for each active user.
    :rtype: list[pathlib.Path]

    :raises FileNotFoundError: If the project directory structure, mandatory reference
        rasters/vectors, or the core data file ``inputs/benefit/benefit_users.csv`` are missing.
    :raises KeyError: If the provided ``attribute`` string does not exist as a column header
        in the benefit database.

    **File Inputs and Prerequisites**

    The function dynamically infers and requires the following files:

    * ``{folder_project}/inputs/benefit/benefit_users.csv``: Semicolon-separated database containing columns ``[scenario, user, hub, <attribute>]``.
    * ``{folder_project}/inputs/users/{scenario}/*.tif``: User intensity surfaces. *Note: Files containing underscores ("_") are ignored as internal/intermediate layers.*
    * ``{folder_project}/inputs/bathymetry.tif``: Reference raster utilized to determine spatial resolution, extent, and coordinate reference system (CRS).

    **Side Effects & File Outputs**

    Running this function populates the project directories with the following outputs:

    * ``outputs/{scenario}/{scenario}_benefit.tif``: The final, cumulative, normalized (0 to 1) Benefit Index spatial raster.
    * ``outputs/{scenario}/{scenario}_benefit_users.csv``: A clean summary table detailing the absolute total benefit weight (:math:`B_i`) allocated per evaluated sector.
    * ``outputs/{scenario}/intermediate/benefit/benefit_{user}.tif``: Sector-specific absolute benefit density maps.
    * ``outputs/{scenario}/intermediate/benefit/benefit_wsum.tif``: The un-normalized cumulative sum map of all downscaled benefits.

    **Example**

    .. code-block:: python

        >>> from pem import benefit
        >>> generated_rasters = benefit.get_benefit_index(
        ...     folder_project="/workspaces/pem_project",
        ...     scenario="baseline",
        ...     attribute="jobs_number"
        ... )
        >>> print([p.name for p in generated_rasters])
        ['benefit_cargo.tif', 'benefit_oil.tif', 'benefit_tourism.tif']

    """
    _heading()
    _message(f"Get Benefit Index at {scenario}")

    pvars = _get_project_vars(folder_project=folder_project)

    folder_project = pvars["folder_project"]
    folder_inputs = pvars["folder_inputs"]
    folder_output = pvars["folder_outputs"] / f"{scenario}"
    folder_output_sub = folder_output / "intermediate/benefit"
    folder_output_sub.mkdir(exist_ok=True)

    file_df = folder_inputs / "benefit/benefit_users.csv"
    df_benefit = pd.read_csv(file_df, sep=";", encoding="utf-8")

    folder_users = folder_inputs / f"users/{scenario}"
    ls_files = _get_users_maps(folder_users)

    ls_output_files = []

    ls_users = []
    ls_benefit = []

    weighted_sum = None

    # loop over users (i)
    for user_file in ls_files[:]:

        _message(f"processing {user_file.name}")
        ls_users.append(user_file.name)
        # load the user intensity fuzzy map U_ij

        raster_dict = _util_read_raster(user_file, n_band=1, metadata=True)
        u_map = raster_dict["data"][:].astype(np.float32)
        # calculate the total intensity U_i = np.sum(U_ij)
        U = np.sum(u_map)
        _message(f"U sum: {U}")

        # assess the global benefit for the user B_i
        B = _get_benefit_weight(df_benefit, scenario, user_file.stem, attribute)
        ls_benefit.append(B)
        _message(f"B: {B}")

        # calculate the scaling constant for each user
        # c = B_i / U_i
        c = B / U
        _message(f"c: {c}")

        # map the spatial benefit:
        # B_ij = c * U_ij
        b_map = c * u_map
        b_map_sum = np.sum(b_map)
        _message(f"b_map sum: {b_map_sum}")

        if weighted_sum is None:
            weighted_sum = np.zeros_like(b_map)
            out_metadata = raster_dict.get("metadata")

        # Multiply the map by its weight and add it to the running total
        weighted_sum += b_map

        # export B_ij to
        nm = "benefit_" + user_file.name
        fo = folder_output_sub / nm

        _message("writing benefit raster")
        _util_write_raster(
            grid_output=b_map,
            dc_metadata=raster_dict["metadata"],
            file_output=fo,
        )
        ls_output_files.append(fo)

    _message(f"Saving sum ...")
    file_output = folder_output_sub / "benefit_wsum.tif"
    _util_write_raster(
        grid_output=weighted_sum,  # Pass the cleaned data, not the array with NaNs
        dc_metadata=out_metadata,
        file_output=str(file_output),
    )

    _message(f"Normalizing sum ...")
    ls = _util_normalize_rasters([str(file_output)])

    fo = folder_output / f"{scenario}_benefit.tif"
    shutil.copy(src=ls[0], dst=fo)

    df = pd.DataFrame(
        {
            "user": ls_users,
            "benefit": ls_benefit,
        }
    )
    df["scenario"] = scenario

    fo = folder_output / f"{scenario}_benefit_users.csv"
    df.to_csv(fo, sep=",", index=False)

    return ls_output_files


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

    # Write the new data to the new raster
    out_band.WriteArray(grid_output)

    # Assign the NoData value to the band
    if nodata_value is not None:
        out_band.SetNoDataValue(nodata_value)

    # Flush the cache to disk to prevent corrupted files
    out_band.FlushCache()
    raster_output.FlushCache()  # <-- Add this line

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
