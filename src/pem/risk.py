# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Module for pre- and post-processing routines supporting the Habitat Risk Index workflow.

This module provides a collection of helper functions for organizing, rasterizing, and
reprojecting spatial data layers used in the InVEST Habitat Risk model. It is intended
to be executed within the **QGIS Python environment** and relies on its processing framework
(`processing` algorithms, CRS handling, rasterization utilities, etc.).

.. seealso::

    Refer to the `InVEST Habitat Risk model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_
    documentation for theoretical and technical details regarding input data
    preparation for the Habitat Risk Index.

**Requirements**

The following libraries and environment are required:

* QGIS 3 (Python environment)
* ``numpy``
* ``pandas``
* ``geopandas``

**Overview**

This module includes routines for:

* Preparing and rasterizing stressor and habitat layers.
* Reprojecting rasters and generating blank templates.
* Splitting vector datasets into grouped layers.
* Creating structured, time-stamped output directories for reproducible runs.

Each function performs a self-contained processing step designed to integrate
smoothly with other spatial workflows in QGIS.

**Examples**

Scripted usage examples are provided in the docstrings of each function.
No global examples are included at module level.


"""
# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import datetime, os, time
import shutil
from pathlib import Path

# ... {develop}

# External imports
# =======================================================================
import geopandas as gpd
import pandas as pd
import processing
from qgis.core import QgsCoordinateReferenceSystem

# ... {develop}

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

CRS_OPS = {
    "5641": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=merc +lat_ts=-2 +lon_0=-43 +x_0=5000000 +y_0=10000000 +ellps=GRS80"
}

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

# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def setup_hra_model(
    output_folder,
    criteria_table,
    input_db,
    reference_raster,
    resolution,
    aoi_layer,
    habitat_layer,
    habitat_field,
    habitat_groups,
    stressor_groups,
    dst_crs="5641",
    suffix="",
):
    """
    Sets up all necessary input layers and data structures for the HRA (Habitat Risk Assessment) model run.

    .. note::

        This script is a utility for running the `InVEST Habitat Risk model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_.

    :param output_folder: Path to the main output directory where all generated files will be stored.
    :type output_folder: str
    :param criteria_table: Path to criteria table for habitat sensitivity
    :type criteria_table: str
    :param input_db: Path to the GeoPackage file containing the input vector layers.
    :type input_db: str
    :param reference_raster: Path to the raster used as a spatial template for model rasters.
    :type reference_raster: str
    :param resolution: The target spatial resolution (pixel size) for the model outputs.
    :type resolution: float
    :param aoi_layer: The name of the vector layer in ``input_db`` defining the Area of Interest (AOI).
    :type aoi_layer: str
    :param habitat_layer: The name of the vector layer in ``input_db`` containing the habitat features.
    :type habitat_layer: str
    :param habitat_field: The name of the field in ``habitat_layer`` used to classify habitats into groups.
    :type habitat_field: str
    :param habitat_groups: A dictionary defining how habitats are grouped and processed.
    :type habitat_groups: dict
    :param stressor_groups: A dictionary defining the stressor layers and their properties.
    :type stressor_groups: dict
    :param dst_crs: The EPSG code for the destination Coordinate Reference System (CRS). Default value = ``5641``
    :type dst_crs: str
    :param suffix: String suffix for model runs
    :type suffix: str
    :return: The path to the newly created main output folder for the model run.
    :rtype: str

    **Notes**

    This function prepares the environment by creating output folders,
    reprojecting the AOI, creating a blank reference raster,
    and running ``setup_habitats`` and ``setup_stressors`` to
    prepare those inputs. It also generates a combined ``info.csv`` table.


    .. warning::

        The following script is expected to be executed under the QGIS Python
        Environment with ``numpy``, ``pandas`` and ``geopandas`` installed.


    .. code-block:: python

        # WARNING: run this in QGIS Python Environment

        import importlib.util as iu

        # define the paths to this module
        # ----------------------------------------
        the_module = "path/to/risk.py"

        spec = iu.spec_from_file_location("module", the_module)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        # define the paths to input and output folders
        # ----------------------------------------
        input_dir = "path/to/dir"
        output_dir = "path/to/dir"

        # define the path to input database
        # ----------------------------------------
        input_db = f"{input_dir}/pem.gpkg"

        # define criteria table
        criteria_table = f"{input_dir}/criteria_ben_pem.csv"

        # define reference raster
        reference_raster = f"{input_dir}/gebco_topobathymetry.tif"

        # organize habitat groups
        habitat_groups = {
            # Habitat group
            "MB3_MC3": ["MB3", "MC3"],  # list of habitats names
            "MB4_MB5_MB6": ["MB4", "MB5", "MB6"],
            "MC4_MC5_MC6": ["MC4", "MC5", "MC6"],
            "MD3": ["MD3"],
            "MD4_MD5_MD6": ["MD4", "MD5", "MD6"],
            "ME1": ["ME1"],
            "ME4_MF4_MF5": ["ME4", "MF4", "MF5"],
            "MG4_MG6": ["MG4", "MG6"],
        }

        # organize stressors groups
        stressor_groups = {
            # stressor name
            "MINERACAO": {
                # list of layers in input database
                "layers": ["mineracao_processos", "mineracao_areas_potenciais"],
                "buffer": 10000, # in meters
            },
            "TURISMO": {
                "layers": ["turismo_atividades_esportivas_sul"],
                "buffer": 10000,
            },
            "EOLICAS": {
                "layers": ["eolico_parques"],
                "buffer": 10000,
            },
        }

        # call the function
        # ----------------------------------------
        output_folder = module.setup_hra_model(
            output_folder=output_dir,
            criteria_table=criteria_table,
            input_db=input_db,
            reference_raster=reference_raster,
            resolution=1000, # in meters
            aoi_layer="sul",
            habitat_layer="habitats_bentonicos_sul_v2",
            habitat_field="code",
            habitat_groups=habitat_groups,
            stressor_groups=stressor_groups,
        )

    """
    # Startup
    # -------------------------------------------------------------------
    func_name = setup_hra_model.__name__
    print(f"running: {func_name}")

    # Setup output variables
    # -------------------------------------------------------------------

    # folders
    # -----------------------------------
    os.makedirs(output_folder, exist_ok=True)
    output_folder = _make_run_folder(run_name=func_name, output_folder=output_folder)

    # files
    # -----------------------------------
    model_reference_raster = f"{output_folder}/blank.tif"

    # Run processes
    # -------------------------------------------------------------------

    # handle aoi layer
    # -----------------------------------
    aoi_file = f"{output_folder}/aoi.shp"
    dc_params = {
        "INPUT": f"{input_db}|layername={aoi_layer}",
        "TARGET_CRS": QgsCoordinateReferenceSystem(f"EPSG:{dst_crs}"),
        "CONVERT_CURVED_GEOMETRIES": False,
        "OPERATION": CRS_OPS[dst_crs],
        "OUTPUT": aoi_file,
    }
    processing.run("native:reprojectlayer", dc_params)

    # handle blank
    # -----------------------------------
    model_reference_raster = util_raster_blank(
        output_raster=model_reference_raster, input_raster=reference_raster
    )

    # Habitats
    # -----------------------------------
    habitat_folder = setup_habitats(
        output_folder=f"{output_folder}/habitats",
        input_db=input_db,
        input_layer=habitat_layer,
        groups=habitat_groups,
        field_name=habitat_field,
        reference_raster=model_reference_raster,
        is_blank=True,
        resolution=resolution,
        subfolder=False,
    )

    # Stressors
    # -----------------------------------
    stressor_folder = setup_stressors(
        output_folder=f"{output_folder}/stressors",
        input_db=input_db,
        groups=stressor_groups,
        reference_raster=model_reference_raster,
        is_blank=True,
        resolution=resolution,
        subfolder=False,
    )

    # Criteria table
    # -----------------------------------
    criteria_file = f"{output_folder}/criteria.csv"
    shutil.copy(src=criteria_table, dst=criteria_file)

    # Info table
    # -----------------------------------
    info_file = f"{output_folder}/info.csv"
    table_h = f"{habitat_folder}/info_habitats.csv"
    table_s = f"{stressor_folder}/info_stressors.csv"

    df_h = pd.read_csv(table_h, sep=",")
    df_s = pd.read_csv(table_s, sep=",")
    df_info = pd.concat([df_h, df_s])
    df_info.to_csv(info_file, sep=",", index=False)

    # Handle model file
    # -----------------------------------
    json_string = INVEST_JSON[:]
    json_string = json_string.replace("[aoi]", aoi_file)
    json_string = json_string.replace("[info]", info_file)
    json_string = json_string.replace("[res]", str(resolution))
    json_string = json_string.replace("[suffix]", suffix)
    json_string = json_string.replace("[criteria]", criteria_file)
    json_string = json_string.replace("[workspace]", output_folder)

    json_string = json_string.replace("\\", "/")

    with open(f"{output_folder}/model.json", "w") as file:
        file.write(json_string)
        file.close()

    print(f"run successfull. see for outputs:\n{output_folder}")

    return output_folder

    return None


# test developed
def setup_stressors(
    output_folder,
    input_db,
    groups,
    reference_raster,
    is_blank=False,
    resolution=400,
    subfolder=True,
):
    """
    Sets up stressor layers by rasterizing multiple vector layers from a
    database into single stressor rasters and reprojecting them to a specified resolution.

    .. note::

        This script is a utility for running the `InVEST Habitat Risk model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_.


    :param output_folder: The base directory where a new run-specific folder for all outputs will be created.
    :type output_folder: str
    :param input_db: The path to the source vector database (e.g., GeoPackage) containing the stressor layers.
    :type input_db: str
    :param groups: A dictionary defining the stressor groups. Keys are the desired output stressor names (e.g., ``Coastal_Pollution``), and values are dictionaries containing two keys: ``layers`` (a list of vector layer names to be combined) and ``buffer`` (the required buffer distance in meters for subsequent analysis).
    :type groups: dict
    :param reference_raster: The path to a raster file whose extent, CRS, and other properties will be used as a template for the output stressor rasters.
    :type reference_raster: str
    :param is_blank: [optional] If ``True``, the ``reference_raster`` is assumed to be a blank (zero-valued) template already, skipping the internal blanking step. Default value = False
    :type is_blank: bool
    :param resolution: The desired resolution (cell size) for the final output stressor rasters. Default value = 400
    :type resolution: float
    :return: The path to the newly created run-specific output folder containing the stressor rasters and metadata.
    :rtype: str

    **Notes**

    This function combines features from multiple vector layers into a single output stressor raster for each defined group.

    #. **Template Raster:** If ``is_blank`` is ``False``, a blank raster is generated from the ``reference_raster`` to serve as the template.
    #. **Rasterization Loop:** For each group, the template raster is copied, and all vector layers listed under the group's ``layers`` key are sequentially rasterized onto the copy using a burn value of 1 (features are present).
    #. **Reprojection:** The resulting raster is reprojected to the desired ``resolution`` (and default CRS of 5641).
    #. **Metadata:** An ``info_stressors.csv`` file is created, detailing the name, file path, and required **STRESSOR BUFFER (meters)** for each generated stressor raster.

    Intermediate rasters are cleaned up at the end.


    **Script example**

    .. warning::

        The following script is expected to be executed under the QGIS Python
        Environment with ``numpy``, ``pandas`` and ``geopandas`` installed.


    .. code-block:: python

        # WARNING: run this in QGIS Python Environment

        import importlib.util as iu

        # define the paths to this module
        # ----------------------------------------
        the_module = "path/to/risk.py"

        spec = iu.spec_from_file_location("module", the_module)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        # define the paths to input and output folders
        # ----------------------------------------
        input_dir = "path/to/dir"
        output_dir = "path/to/dir"

        # define the path to input database
        # ----------------------------------------
        input_db = f"{input_dir}/pem.gpkg"

        # organize stressors groups
        groups = {
            "MINERACAO": {
                "layers": ["mineracao_processos", "mineracao_areas_potenciais"],
                "buffer": 10000,
                "raster": None
            },
            "TURISMO": {
                "layers": ["turismo_atividades_esportivas_sul"],
                "buffer": 10000,
                "raster": None
            },
            "EOLICAS": {
                "layers": ["eolico_parques"],
                "buffer": 10000,
                "raster": None
            },
        }

        # call the function
        # ----------------------------------------
        output_file = module.setup_stressors(
            input_db=input_db,
            output_folder=output_dir,
            groups=groups,
            reference_raster=f"{input_dir}/raster.tif",
            is_blank=False,
            resolution=1000
        )


    """

    # Startup
    # -------------------------------------------------------------------
    func_name = setup_stressors.__name__
    print(f"running: {func_name}")

    # Setup output variables
    # -------------------------------------------------------------------

    # folders
    # -----------------------------------
    os.makedirs(output_folder, exist_ok=True)
    if subfolder:
        output_folder = _make_run_folder(
            run_name=func_name, output_folder=output_folder
        )

    # files
    # -----------------------------------

    # Run processes
    # -------------------------------------------------------------------

    # todo develop: a nice thing would be to save only the stressors to a database

    # handle reference raster
    # -----------------------------------
    if is_blank:
        pass
    else:
        reference_raster = util_raster_blank(
            output_raster=f"{output_folder}/blank.tif",
            input_raster=reference_raster,
        )

    # loop over for rasterizing
    # -----------------------------------
    ls_names = []
    ls_paths = []
    ls_buffers = []
    for g in groups:

        group_raster_src = Path(f"{output_folder}/{g}_src.tif")
        group_raster_warped = Path(f"{output_folder}/{g}.tif")

        # copy reference
        shutil.copy(src=reference_raster, dst=group_raster_src)

        # loop for handling multiple layers
        for layer in groups[g]["layers"]:
            # rasterize
            util_layer_rasterize(
                input_raster=str(group_raster_src),
                input_db=input_db,
                input_layer=layer,
                burn_value=1,
            )

        # reproject
        util_raster_reproject(
            output_raster=group_raster_warped,
            input_raster=group_raster_src,
            dst_resolution=resolution,
            dst_crs="5641",
            src_crs="4326",
            dtype=6,
            resampling=0,
        )

        ls_names.append(g)
        ls_paths.append(str(group_raster_warped))
        ls_buffers.append(groups[g]["buffer"])

        os.remove(group_raster_src)

    # save CSV info
    # -----------------------------------
    dc = {
        "NAME": ls_names,
        "PATH": ls_paths,
    }
    df = pd.DataFrame(dc)
    df["TYPE"] = "STRESSOR"
    df["STRESSOR BUFFER (meters)"] = ls_buffers
    df.to_csv(f"{output_folder}/info_stressors.csv", sep=",", index=False)

    # removals
    # -----------------------------------

    # handle blank
    if is_blank is None:
        os.remove(reference_raster)

    print(f"run successfull. see for outputs:\n{output_folder}")

    return output_folder


# test developed
def setup_habitats(
    output_folder,
    input_db,
    input_layer,
    groups,
    field_name,
    reference_raster,
    is_blank=False,
    resolution=400,
    subfolder=True,
):
    """
    Sets up habitat layers by splitting a vector layer, rasterizing each resulting
    habitat group, and reprojecting the rasters to a specified resolution.

    .. note::

        This script is a utility for running the `InVEST Habitat Risk model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_.

    :param output_folder: The base directory where a new run-specific folder for all outputs will be created.
    :type output_folder: str
    :param input_db: The path to the source vector database (e.g., GeoPackage) containing the habitat features.
    :type input_db: str
    :param input_layer: The name of the layer or table within the ``input_db`` to read the features from.
    :type input_layer: str
    :param groups: A dictionary defining the habitat groups: keys are the desired output habitat names (layer names), and values are lists of string values from ``field_name`` to include in that habitat layer.
    :type groups: dict
    :param field_name: The name of the attribute field in the input data used for grouping and querying the habitat features.
    :type field_name: str
    :param reference_raster: The path to a raster file whose extent, CRS, and other properties will be used as a template for the output habitat rasters.
    :type reference_raster: str
    :param is_blank: [optional] If ``True``, the ``reference_raster`` is assumed to be a blank (zero-valued) template already, skipping the internal blanking step. Default value = False
    :type is_blank: bool
    :param resolution: The desired resolution (cell size) for the final output habitat rasters. Default value = 400
    :type resolution: float
    :return: The path to the newly created run-specific output folder containing the habitat rasters and metadata.
    :rtype: str

    **Notes**

    This function orchestrates a multi-step process:

    #. **Vector Split:** Calls ``split_features`` to create a temporary GeoPackage where each habitat group is saved as a separate layer.
    #. **Template Raster:** If ``is_blank`` is ``False``, a blank raster is generated from the ``reference_raster`` to serve as the template for rasterization.
    #. **Rasterization Loop:** Each habitat layer is individually rasterized onto a copy of the template raster, setting the habitat cells to a burn value of 1.
    #. **Reprojection:** The resulting raster is reprojected to the desired ``resolution`` (and default CRS of 5641).
    #. **Metadata:** An ``info_habitats.csv`` file is created, detailing the name and file path for each generated habitat raster.

    Temporary files (split GeoPackage and intermediate rasters) are cleaned up at the end.

    **Script example**

    .. warning::

        The following script is expected to be executed under the QGIS Python
        Environment with ``numpy``, ``pandas`` and ``geopandas`` installed.

    .. code-block:: python

        # WARNING: run this in QGIS Python Environment

        import importlib.util as iu

        # define the paths to this module
        # ----------------------------------------
        the_module = "path/to/risk.py"

        spec = iu.spec_from_file_location("module", the_module)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        # define the paths to input and output folders
        # ----------------------------------------
        input_dir = "path/to/dir"
        output_dir = "path/to/dir"

        # define the path to input database
        # ----------------------------------------
        input_db = f"{input_dir}/pem.gpkg"

        # organize habitat groups
        groups = {
            "MB3_MC3": ["MB3", "MC3"],
            "MB4_MB5_MB6": ["MB4", "MB5", "MB6"],
            "MC4_MC5_MC6": ["MC4", "MC5", "MC6"],
            "MD3": ["MD3"],
            "MD4_MD5_MD6": ["MD4", "MD5", "MD6"],
            "ME1": ["ME1"],
            "ME4_MF4_MF5": ["ME4", "MF4", "MF5"],
            "MG4_MG6": ["MG4", "MG6"],
        }

        # call the function
        # ----------------------------------------
        output_file = module.setup_habitats(
            input_db=input_db,
            output_folder=output_dir,
            input_layer="habitats_bentonicos_sul_v2",
            groups=groups,
            field_name="code",
            reference_raster=f"{input_dir}/raster.tif",
            resolution=1000
        )

    """

    # Startup
    # -------------------------------------------------------------------
    func_name = setup_habitats.__name__
    print(f"running: {func_name}")

    # Setup output variables
    # -------------------------------------------------------------------

    # folders
    # -----------------------------------
    os.makedirs(output_folder, exist_ok=True)
    if subfolder:
        output_folder = _make_run_folder(
            run_name=func_name, output_folder=output_folder
        )

    # files
    # -----------------------------------

    # Run processes
    # -------------------------------------------------------------------

    # split vector features
    # -----------------------------------
    output_db = util_split_features(
        output_folder=output_folder,
        input_db=input_db,
        input_layer=input_layer,
        groups=groups,
        field_name=field_name,
    )

    # handle reference raster
    # -----------------------------------
    if is_blank:
        pass
    else:
        reference_raster = util_raster_blank(
            output_raster=f"{output_folder}/blank.tif",
            input_raster=reference_raster,
        )

    # loop over for rasterizing
    # -----------------------------------
    ls_names = []
    ls_paths = []
    for g in groups:

        group_raster_src = Path(f"{output_folder}/{g}_src.tif")

        group_raster_warped = Path(f"{output_folder}/{g}.tif")

        # copy reference
        shutil.copy(src=reference_raster, dst=group_raster_src)

        # rasterize
        util_layer_rasterize(
            input_raster=str(group_raster_src),
            input_db=output_db,
            input_layer=g,
            burn_value=1,
        )

        # reproject
        util_raster_reproject(
            output_raster=group_raster_warped,
            input_raster=group_raster_src,
            dst_resolution=resolution,
        )

        ls_names.append(g)
        ls_paths.append(str(group_raster_warped))

        os.remove(group_raster_src)

    # save CSV info
    # -----------------------------------
    dc = {
        "NAME": ls_names,
        "PATH": ls_paths,
    }
    df = pd.DataFrame(dc)
    df["TYPE"] = "HABITAT"
    df["STRESSOR BUFFER (meters)"] = ""
    df.to_csv(f"{output_folder}/info_habitats.csv", sep=",", index=False)

    # removals
    # -----------------------------------

    # handle blank
    if is_blank:
        pass
    else:
        os.remove(reference_raster)

    # handle geopackage
    shutil.copy(src=output_db, dst=f"{output_folder}/habitats.gpkg")
    shutil.rmtree(Path(output_db).parent)

    print(f"run successfull. see for outputs:\n{output_folder}")

    return output_folder


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


# test developed
def util_split_features(output_folder, input_db, input_layer, groups, field_name):
    """
    Splits features from a source GeoDataFrame into separate
    layers within a single GeoPackage file based on predefined groups of field values.

    :param output_folder: The base directory where a new run-specific folder for the outputs will be created.
    :type output_folder: str
    :param input_db: The path to the source vector database (e.g., a GeoPackage file).
    :type input_db: str
    :param input_layer: The name of the layer or table within the ``input_db`` to read the features from.
    :type input_layer: str
    :param groups: A dictionary where keys are the desired output layer names (groups) and values are lists of string values from ``field_name`` to include in that layer.
    :type groups: dict
    :param field_name: The name of the attribute field in the input data used for grouping and querying the features.
    :type field_name: str
    :return: The path to the output GeoPackage file containing the newly created layers.
    :rtype: :class:`pathlib.Path`

    **Notes**

    The function first reads the entire layer into a single GeoDataFrame.
    It then iterates through the ``groups`` dictionary, querying the GeoDataFrame
    for features where the value in ``field_name`` matches any of the values in
    the group's list. All resulting group GeoDataFrames are concatenated and
    saved as separate layers (named after the group keys) into a new GeoPackage
    file called ``split.gpkg`` within a run-specific subfolder in ``output_folder``.

    """

    # Startup
    # -------------------------------------------------------------------
    func_name = util_split_features.__name__
    print(f"running: {func_name}")

    # Setup output variables
    # -------------------------------------------------------------------

    # folders
    # -----------------------------------
    os.makedirs(output_folder, exist_ok=True)
    output_folder = _make_run_folder(run_name=func_name, output_folder=output_folder)

    # files
    # -----------------------------------
    output_file = Path(f"{output_folder}/split.gpkg")

    # Run processes
    # -------------------------------------------------------------------

    # load data
    # -----------------------------------
    gdf = gpd.read_file(input_db, layer=input_layer)

    # split loop
    # -----------------------------------
    dc_files = {}
    for g in groups:
        ls_gdf = []
        for name in groups[g]:
            s = f"{field_name} == '{name}'"
            gdf_q = gdf.query(s).copy()
            ls_gdf.append(gdf_q)
        gdf_group = pd.concat(ls_gdf).reset_index(drop=True)
        dc_files[g] = gdf_group.copy()

    # Export
    # -------------------------------------------------------------------
    for g in dc_files:
        dc_files[g].to_file(output_file, layer=g, driver="GPKG")

    # save
    # -----------------------------------
    print(f"run successfull. see for outputs:\n{output_folder}")

    return output_file


# test developed
def util_raster_blank(output_raster, input_raster):
    """
    Creates a blank (zero-valued) raster based on the extent,
    resolution, and CRS of an existing input raster.

    :param output_raster: name for the resulting blank raster file (without extension).
    :type output_raster: str
    :param input_raster: The path to the source raster file whose properties (extent, resolution, CRS) will be used.
    :type input_raster: str
    :return: The full path to the newly created blank raster file.
    :rtype: str

    **Notes**

    This function uses the QGIS processing algorithm ``native:rastercalc``
    (Raster calculator). It works by multiplying every cell in the input
    raster by zero, effectively preserving the metadata (extent, resolution, CRS)
    while setting all data values to zero. The output raster is a new
    file and does not modify the input raster.

    """
    filename = os.path.basename(input_raster).replace(".tif", "")
    dc_parameters = {
        "LAYERS": [str(input_raster)],
        "EXPRESSION": '"{}@1" * 0'.format(filename),
        "EXTENT": None,
        "CELL_SIZE": None,
        "CRS": None,
        "OUTPUT": output_raster,
    }
    processing.run("native:rastercalc", dc_parameters)
    return output_raster


def util_raster_reproject(
    output_raster,
    input_raster,
    dst_resolution,
    dst_crs="5641",
    src_crs="4326",
    dtype=6,
    resampling=0,
):
    """
    Reprojects and optionally resamples an input raster to a new Coordinate Reference System (CRS) and resolution.

    :param output_raster: The full path and filename for the resulting reprojected raster file.
    :type output_raster: str
    :param input_raster: The path to the source raster file to be reprojected.
    :type input_raster: str
    :param dst_resolution: The desired resolution (cell size) for the output raster, usually in the units of the target CRS.
    :type dst_resolution: float
    :param dst_crs: The EPSG code (as a string) for the target CRS. Default value = ``5641``
    :type dst_crs: str
    :param src_crs: The EPSG code (as a string) for the source CRS. Default value = ``4326``
    :type src_crs: str
    :param dtype: The desired data type for the output raster bands (GDAL data type code). Default value = 6 (Float32)
    :type dtype: int
    :param resampling: The resampling method to use (GDAL resampling code). Default value = 0 (Nearest Neighbour)
    :type resampling: int
    :return: The full path to the newly created output raster file.
    :rtype: str

    **Notes**

    This function uses the QGIS processing algorithm ``gdal:warpreproject``.
    The default NoData value is set to ``-99999``.
    Common values for ``dtype`` include 1 (Byte), 4 (Int32), 6 (Float32).
    Common values for ``resampling`` include 0 (Nearest Neighbour), 1 (Bilinear), 2 (Cubic).
    The output path is constructed using the ``output_raster`` parameter.
    """

    dc_parameters = {
        "INPUT": str(input_raster),
        "SOURCE_CRS": QgsCoordinateReferenceSystem(f"EPSG:{src_crs}"),
        "TARGET_CRS": QgsCoordinateReferenceSystem(f"EPSG:{dst_crs}"),
        "RESAMPLING": resampling,
        "NODATA": -99999,
        "TARGET_RESOLUTION": dst_resolution,
        "OPTIONS": "",
        "DATA_TYPE": dtype,
        "TARGET_EXTENT": None,
        "TARGET_EXTENT_CRS": None,
        "MULTITHREADING": False,
        "EXTRA": "",
        "OUTPUT": str(output_raster),
    }
    processing.run("gdal:warpreproject", dc_parameters)
    return output_raster


# test developed
def util_layer_rasterize(
    input_raster, input_db, input_layer, input_table=None, burn_value=1, extra=""
):
    """
    Rasterizes a vector layer from a database into an existing raster file, assigning a fixed burn value.

    :param input_raster: The path to the existing raster file to be modified (must be writable).
    :type input_raster: str
    :param input_db: The path or connection string to the vector database (e.g., GeoPackage, PostGIS connection).
    :type input_db: str
    :param input_layer: The name of the vector layer or table to rasterize.
    :type input_layer: str
    :param input_table: [optional] The schema or parent table name if the ``input_layer`` is a sub-table or view (e.g., for PostGIS).
    :type input_table: str or None
    :param burn_value: The fixed value to burn into the raster cells covered by the vector features. Default value = 1
    :type burn_value: int or float
    :param extra: Additional command-line options passed directly to the underlying GDAL tool. Default value = ``''``
    :type extra: str
    :return: The path to the modified input raster file.
    :rtype: str

    **Notes**

    This function uses the QGIS processing algorithm ``gdal:rasterize_over_fixed_value``, which modifies the ``input_raster`` in place. If ``input_table`` is not provided, it assumes a standard layer format (e.g., GeoPackage layer). If ``input_table`` is provided, it constructs a PostgreSQL-like table reference.
    """

    # infer input
    if input_table is None:
        input_vector = "{}|layername={}".format(input_db, input_layer)
    else:
        input_vector = r'{} table="{}"."{}" (geom)'.format(
            input_db, input_table, input_layer
        )

    dc_parameters = {
        "INPUT": input_vector,
        "INPUT_RASTER": input_raster,
        "BURN": burn_value,
        "ADD": False,
        "EXTRA": extra,
    }
    processing.run("gdal:rasterize_over_fixed_value", dc_parameters)
    return input_raster


# FUNCTIONS -- Utils
# =======================================================================


def _get_timestamp():
    now = datetime.datetime.now()
    return str(now.strftime("%Y-%m-%dT%H%M%S"))


def _make_run_folder(output_folder, run_name):
    """
    Creates a unique, time-stamped run folder within a specified output directory.

    :param output_folder: The parent directory where the new run folder will be created.
    :type output_folder: str or :class:`pathlib.Path`
    :param run_name: The base name for the new folder. A timestamp will be appended to it.
    :type run_name: str
    :return: The absolute path to the newly created run folder.
    :rtype: str

    **Notes**

    It appends a unique timestamp to the run name and ensures the
    folder doesn't already exist before creating it.

    """
    while True:
        ts = _get_timestamp()
        folder_run = Path(output_folder) / f"{run_name}_{ts}"
        if os.path.exists(folder_run):
            time.sleep(1)
        else:
            os.mkdir(folder_run)
            break

    return os.path.abspath(folder_run)


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script
if __name__ == "__main__":

    # Script section
    # ===================================================================
    print("Hello world!")
    # ... {develop}

    # Script subsection
    # -------------------------------------------------------------------
    # ... {develop}
