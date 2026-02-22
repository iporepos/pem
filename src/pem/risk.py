# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
This is the complete API reference for the ``risk`` python module of the ``pem`` system.

.. seealso::

   Learn how to derive the Habitat Risk Index in
   :ref:`Tutorial: Habitat Risk Index <guide-risk>`.

"""
import os
import shutil

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
from pathlib import Path

# External imports
# =======================================================================
import numpy as np
import pandas as pd


# qgis stuff
import processing
from osgeo import gdal
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsRasterLayer,
    QgsRasterBandStats,
    QgsVectorLayer,
)

# ... {develop}


INVEST_JSON = """
{
    "args": {
        "aoi_vector_path": "[aoi]",
        "criteria_table_path": "[criteria]",
        "decay_eq": "linear",
        "info_table_path": "[info]",
        "max_rating": "3",
        "n_overlapping_stressors": "10",
        "resolution": "[res]",
        "results_suffix": "[suffix]",
        "risk_eq": "euclidean",
        "visualize_outputs": false,
        "workspace_dir": "[workspace]"
    },
    "invest_version": "3.16.0",
    "model_id": "habitat_risk_assessment"
}
"""

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}

# FUNCTIONS
# ***********************************************************************


def _message(msg):
    print(f" >>> pem @ risk: {msg}")


def _message_end():
    _message("DONE")


def _heading():
    print(80 * "=")


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
    pvars["crs"] = util_get_raster_crs(pvars["refraster"], code_only=True)
    pvars["ext"] = util_get_raster_extent(pvars["refraster"])
    res_dc = util_get_raster_resolution(pvars["refraster"])
    pvars["res"] = res_dc["xres"]

    return pvars


# FUNCTIONS -- Project-level
# =======================================================================


def get_risk_index(folder_project, scenario, hra_benthic, hra_pelagic):
    """
    Calculate and normalize the total risk index by combining
    benthic and pelagic Habitat Risk Assessment (HRA) results.

    :param folder_project: Path to the root project directory
    :type folder_project: str
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :param hra_benthic: Path to the benthic HRA raster file
    :type hra_benthic: str
    :param hra_pelagic: Path to the pelagic HRA raster file
    :type hra_pelagic: str
    :return: Path to the generated normalized risk raster
    :rtype: :class:`pathlib.Path`

    .. dropdown:: Extra notes
        :icon: bookmark-fill
        :open:

        The function reprojects and resamples input HRA rasters to a common grid, sums the
        overlapping layers using raster calculation, and applies a normalization process
        to produce a final risk map.

    .. include:: includes/examples/risk_get_risk.rst

    """

    _heading()
    _message("Get Risk Index")
    _message(f"Scenario: {scenario}")

    # Setup
    # ---------------------------------------------------------
    pvars = _get_project_vars(folder_project)

    folder_project = pvars["folder_project"]
    folder_inputs = pvars["folder_inputs"]
    folder_outputs = pvars["folder_outputs"]
    folder_output = folder_outputs / f"{scenario}"
    folder_output_sub = folder_outputs / f"{scenario}/intermediate"

    dst_ext = pvars["ext"]
    dst_crs = pvars["crs"]
    dst_extent = f'{dst_ext["xmin"]},{dst_ext["xmax"]},{dst_ext["ymin"]},{dst_ext["ymax"]} [EPSG:{dst_crs}]'

    fo = folder_output / f"{scenario}_risk.tif"

    dc = {"benthic": hra_benthic, "pelagic": hra_pelagic}

    # Loop
    # ---------------------------------------------------------
    for hab in dc:
        _message(f"Processing HRA - {hab} ...")
        fi = Path(dc[hab])

        fo_sub = folder_output_sub / f"{scenario}_hra_{hab}.tif"

        dc_params = {
            "INPUT": str(fi),
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "RESAMPLING": 3,
            "NODATA": -99999,
            "TARGET_RESOLUTION": 5000,
            "OPTIONS": None,
            "DATA_TYPE": 6,
            "TARGET_EXTENT": dst_ext,
            "TARGET_EXTENT_CRS": None,
            "MULTITHREADING": False,
            "EXTRA": "",
            "OUTPUT": str(fo_sub),
        }
        processing.run("gdal:warpreproject", dc_params)

    # add hra
    # -----------------------------------
    _message(f"Adding HRA ...")
    name_benthic = Path(hra_benthic).stem
    name_pelagic = Path(hra_pelagic).stem

    fo_sub = folder_output_sub / f"{scenario}_hra_sum.tif"

    dc_parameters = {
        "LAYERS": [str(hra_benthic), str(hra_pelagic)],
        "EXPRESSION": '"{}@1" + "{}@1"'.format(name_benthic, name_pelagic),
        "EXTENT": None,
        "CELL_SIZE": None,
        "CRS": None,
        "OUTPUT": str(fo_sub),
    }
    processing.run("native:rastercalc", dc_parameters)

    _message("Normalizing HRA ...")
    ls = util_normalize_rasters(ls_rasters=[str(fo_sub)])
    fo_sub2 = ls[0]
    shutil.copy(src=fo_sub2, dst=fo)

    return fo


def setup_hra_model(folder_project, scenario):
    """
    Execute the full configuration suite required to initialize an InVEST HRA model.

    :param folder_project: Path to the root project directory
    :type folder_project: str
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :return: Always returns ``None``
    :rtype: None

    .. include:: includes/examples/risk_setup_hra.rst

    """

    heading()
    _message("Setup HRA Model")
    _message(f"Scenario: {scenario}")

    setup_hra_info(folder_project, scenario)
    setup_hra_scores(folder_project, scenario)
    setup_hra_json(folder_project, scenario)

    return None


def setup_hra_scores(folder_project, scenario):
    """
    Generate the CSV scoring matrices for habitats and stressors based on project info tables.

    :param folder_project: Path to the root project directory
    :type folder_project: str
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :return: List of paths to the generated score CSV files
    :rtype: list
    """

    _heading()
    _message("Setup HRA info table")
    _message(f"Scenario: {scenario}")

    # Setup
    # ---------------------------------------------------------
    pvars = _get_project_vars(folder_project)

    folder_project = pvars["folder_project"]
    folder_inputs = pvars["folder_inputs"]
    folder_habitats = folder_inputs / "habitats"
    folder_users = folder_inputs / f"users/{scenario}"
    folder_risk = folder_inputs / f"risk/{scenario}"

    ls_outputs = list()

    ls = ["benthic", "pelagic"]

    for hab in ls:

        prefix = f"{scenario} -- {hab}"
        _message(prefix)

        fi = folder_risk / f"{hab}_info.csv"
        df = pd.read_csv(fi, sep=",")

        df_habitats = df.query("TYPE == 'HABITAT'").copy()
        df_stressors = df.query("TYPE == 'STRESSOR'").copy()

        fo = folder_risk / f"{hab}_scores.csv"
        _message(f"{prefix} -- saving table ...")
        util_generate_hra_scores(
            habitats=list(df_habitats["NAME"]),
            stressors=list(df_stressors["NAME"]),
            output_path=fo,
        )
        ls_outputs.append(fo)

    _message_end()
    return ls_outputs


def setup_hra_info(folder_project, scenario, buffers=10000):
    """
    Create the HRA information tables linking habitat
    and stressor names to their respective file paths.

    :param folder_project: Path to the root project directory
    :type folder_project: str
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :param buffers: The buffer distance for stressors in meters. Default value = 10000
    :type buffers: int
    :return: List of paths to the generated info CSV files
    :rtype: list
    """

    _heading()
    _message("Setup HRA info table")
    _message(f"Scenario: {scenario}")

    # Setup
    # ---------------------------------------------------------
    pvars = _get_project_vars(folder_project)

    folder_project = pvars["folder_project"]
    folder_inputs = pvars["folder_inputs"]
    folder_habitats = folder_inputs / "habitats"
    folder_users = folder_inputs / f"users/{scenario}"
    folder_risk = folder_inputs / f"risk/{scenario}"

    ls_outputs = list()

    # handle stressors
    # ---------------------------------------------------------
    prefix = f"{scenario} -- Handling stressors info ..."
    ls_users = list(folder_users.glob("*.tif"))
    ls_users_names = [Path(s).stem.upper() for s in ls_users]
    ls_users_paths = [str(Path(s)) for s in ls_users]
    ls_users_types = ["STRESSOR" for s in ls_users]
    ls_users_buffs = [buffers for s in ls_users]
    dc_users = {
        "NAME": ls_users_names,
        "PATH": ls_users_paths,
        "TYPE": ls_users_types,
        "STRESSOR BUFFER (meters)": ls_users_buffs,
    }
    df_users = pd.DataFrame(dc_users)

    # handle habitats
    # ---------------------------------------------------------
    prefix = f"{scenario} -- Handling habitats info ..."
    _message(prefix)
    ls = ["benthic", "pelagic"]

    # habitat loop
    # ---------------------------------------------------------
    for hab in ls:
        prefix = f"{scenario} -- {hab}"
        _message(prefix)
        habitats_csv = folder_habitats / f"habitats_{hab}.csv"
        df = pd.read_csv(habitats_csv, sep=";")

        # Iterate over rows as dictionaries
        ls_names = list()
        ls_paths = list()
        ls_types = list()
        ls_buffers = list()
        for row_dict in df.to_dict(orient="records"):

            nm = row_dict["group_name"]

            _message(f"{prefix} -- {nm}")

            fi = str(folder_habitats / f"{hab}/{nm}.tif")

            ls_names.append(nm.upper())
            ls_paths.append(fi)
            ls_types.append("HABITAT")
            ls_buffers.append("")

        dc_out = {
            "NAME": ls_names,
            "PATH": ls_paths,
            "TYPE": ls_types,
            "STRESSOR BUFFER (meters)": ls_buffers,
        }
        df_hab = pd.DataFrame(dc_out)

        # concat
        df_out = pd.concat([df_hab.copy(), df_users])

        # save
        # ---------------------------------------------------------
        _message(f"{prefix} -- saving table ...")
        fo = folder_risk / f"{hab}_info.csv"
        df_out.to_csv(fo, sep=",", encoding="utf-8", index=False)
        ls_outputs.append(fo)

    _message_end()
    return ls_outputs


def setup_hra_json(folder_project, scenario):
    """
    Configure and save InVEST model parameter files in JSON format for the specified scenario.

    :param folder_project: Path to the root project directory
    :type folder_project: str
    :param scenario: Name of the simulation scenario
    :type scenario: str
    :return: List of paths to the created JSON configuration files
    :rtype: list
    """

    _heading()
    _message("Setup HRA JSON file")
    _message(f"Scenario: {scenario}")

    # Setup
    # ---------------------------------------------------------
    pvars = _get_project_vars(folder_project)

    folder_project = pvars["folder_project"]
    folder_output = pvars["folder_outputs"] / f"{scenario}/intermediate/hra"
    folder_output.mkdir(exist_ok=True)
    folder_inputs = pvars["folder_inputs"]
    folder_habitats = folder_inputs / "habitats"
    folder_users = folder_inputs / f"users/{scenario}"
    folder_risk = folder_inputs / f"risk/{scenario}"
    folder_roi = folder_inputs / "roi"

    aoi_file = str(folder_roi / "roi.shp")
    resolution = pvars["res"]

    ls_outputs = list()
    ls = ["benthic", "pelagic"]
    for hab in ls:

        _message(f"{hab} -- setting up JSON file ... ")

        info_file = str(folder_risk / f"{hab}_info.csv")
        criteria_file = str(folder_risk / f"{hab}_scores.csv")
        suffix = folder_project.stem + "-" + hab

        # Handle model file for InVEST
        # -----------------------------------
        json_string = INVEST_JSON[:]
        json_string = json_string.replace("[aoi]", aoi_file)
        json_string = json_string.replace("[info]", info_file)
        json_string = json_string.replace("[res]", str(resolution))
        json_string = json_string.replace("[suffix]", suffix)
        json_string = json_string.replace("[criteria]", criteria_file)
        json_string = json_string.replace("[workspace]", str(folder_output))
        json_string = json_string.replace("\\", "/")

        _message(f"{hab} -- Saving ... ")
        fo = folder_risk / f"{hab}_model.json"
        with open(fo, "w") as file:
            file.write(json_string)
            file.close()
        ls_outputs.append(fo)
    _message_end()

    return ls_outputs


def util_generate_hra_scores(habitats, stressors, output_path):
    """
    Create a standardized HRA criteria template CSV with default
    ratings for resilience and overlap attributes.

    :param habitats: List of habitat names to include as columns
    :type habitats: list
    :param stressors: List of stressor names to include as row groups
    :type stressors: list
    :param output_path: Destination path for the generated CSV
    :type output_path: str
    :return: The path where the CSV was saved
    :rtype: str

    .. dropdown:: Extra notes
        :icon: bookmark-fill
        :open:

        This utility builds a complex multi-column table where each habitat receives columns for
        ``RATING``, ``DQ`` (Data Quality), and ``WEIGHT``. It includes predefined rows for
        recruitment, mortality, connectivity, and various stressor-overlap properties.

    """
    habitats = list(habitats)
    stressors = list(stressors)

    per_hab_cols = 3  # RATING, DQ, WEIGHT

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    def get_score_columns():
        cols = []
        for h in habitats:
            cols.extend(["RATING", "DQ", "WEIGHT"])
        return cols + ["E/C", "Rating Instruction"]

    def get_habitat_names():
        cols = []
        for h in habitats:
            cols.extend([h, "", ""])
        return cols + ["CRITERIA TYPE", ""]

    def score_values():
        cols = []
        for h in habitats:
            cols.extend([0, 1, 1])
        return cols

    score_columns = get_score_columns()

    # Master column structure
    columns = ["HABITAT NAME"] + get_habitat_names()

    rows = []

    # ------------------------------------------------------------
    # HABITAT RESILIENCE SECTION
    # ------------------------------------------------------------
    row_1 = ["HABITAT RESILIENCE ATTRIBUTES"] + score_columns
    rows.append(row_1)

    resilience_criteria = [
        (
            "recruitment rate",
            "C",
            "<enter (3) every 2+ yrs, (2) every 1-2 yrs, (1) every <1 yrs, or (0) no score>",
        ),
        (
            "natural mortality rate",
            "C",
            "<enter (3) 0-20%, (2) 20-50%, (1) >80% mortality, or (0) no score>",
        ),
        (
            "connectivity rate",
            "C",
            "<enter (3) <10km, (2) 10-100km, (1) >100km, or (0) no score>",
        ),
        (
            "recovery time",
            "C",
            "<enter (3) >10 yrs, (2) 1-10 yrs, (1) <1 yr, or (0) no score>",
        ),
    ]

    for name, ec, instruction in resilience_criteria:
        rows.append([name] + score_values() + [ec, instruction])

    rows.append([""] * len(columns))

    # ------------------------------------------------------------
    # STRESSOR SECTIONS
    # ------------------------------------------------------------

    rows.append(["HABITAT STRESSOR OVERLAP PROPERTIES"] + [""] * (len(columns) - 1))

    stressor_criteria = [
        (
            "frequency of disturbance",
            "C",
            "<enter (3) Annually or less often, (2) Several times per year, (1) Weekly or more often, (0) no score>",
        ),
        (
            "change in area rating",
            "C",
            "<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>",
        ),
        (
            "change in structure rating",
            "C",
            "<enter (3) 50-100% loss, (2) 20-50% loss, (1) 0-20% loss, (0) no score>",
        ),
        (
            "temporal overlap rating",
            "E",
            "<enter (3) co-occur 8-12 mo/year, (2) 4-8 mo/yr, (1) 0-4 mo/yr, (0) no score>",
        ),
        (
            "management effectiveness",
            "E",
            "<enter (3) not effective, (2) somewhat effective, (1) very effective, (0) no score>",
        ),
        (
            "intensity rating",
            "E",
            "<enter (3) high, (2) medium, (1) low, (0) no score>",
        ),
    ]

    for stressor in stressors:

        # Stressor header row
        rows.append([stressor] + score_columns)

        for name, ec, instruction in stressor_criteria:
            rows.append([name] + score_values() + [ec, instruction])

        rows.append([""] * len(columns))

    # ------------------------------------------------------------
    # Create DataFrame and export
    # ------------------------------------------------------------

    df = pd.DataFrame(rows[:-1], columns=columns)

    df.to_csv(output_path, index=False)

    return output_path


def util_read_raster(file_input, n_band=1, metadata=True):
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


def util_write_raster(
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

    # Close
    raster_output = None

    return file_output


def util_get_raster_crs(file_input, code_only=True):
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


def util_get_raster_extent(file_input):
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


def util_get_raster_resolution(file_input):
    # todo docstring
    # Create a raster layer object
    raster_layer = QgsRasterLayer(str(file_input), "Raster Layer")
    res_x = raster_layer.rasterUnitsPerPixelX()
    res_y = raster_layer.rasterUnitsPerPixelY()

    return {
        "xres": res_x,
        "yres": res_y,
    }


def util_normalize_rasters(ls_rasters, suffix="fz", force_vmin=0):
    # todo docstring
    ls_new_rasters = list()
    for r in ls_rasters:
        p = Path(r)
        file_output = p.parent / f"{p.stem}_{suffix}.tif"

        # get values
        dc_stats = util_get_raster_stats(input_raster=str(p), full=True)
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


def util_get_raster_stats(input_raster, band=1, full=False):
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
        dc_raster = util_read_raster(
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
