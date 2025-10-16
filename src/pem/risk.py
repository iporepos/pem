# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

Features
--------
todo docstring

* {feature 1}
* {feature 2}
* {feature 3}
* {etc}

Overview
--------
todo docstring
{Overview description}

Examples
--------
todo docstring
{Examples in rST}

Print a message

.. code-block:: python

    # print message
    print("Hello world!")
    # [Output] >> 'Hello world!'


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


# FUNCTIONS
# ***********************************************************************

# FUNCTIONS -- Project-level
# =======================================================================


def setup_stressors(
    output_folder, input_db, groups, reference_raster, is_blank=False, resolution=400
):
    """
    Sets up stressor layers by rasterizing multiple vector layers from a
     database into single stressor rasters and reprojecting them to a specified resolution.

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
    1. **Template Raster:** If ``is_blank`` is ``False``, a blank raster is generated from the ``reference_raster`` to serve as the template.
    2. **Rasterization Loop:** For each group, the template raster is copied, and all vector layers listed under the group's ``layers`` key are sequentially rasterized onto the copy using a burn value of 1 (features are present).
    3. **Reprojection:** The resulting raster is reprojected to the desired ``resolution`` (and default CRS of 5641).
    4. **Metadata:** An ``info_stressors.csv`` file is created, detailing the name, file path, and required **STRESSOR BUFFER (meters)** for each generated stressor raster.
    Intermediate rasters are cleaned up at the end.


    **Script example**

    .. code-block:: python

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
    output_folder = make_run_folder(run_name=func_name, output_folder=output_folder)

    # files
    # -----------------------------------

    # Run processes
    # -------------------------------------------------------------------

    # handle reference raster
    # -----------------------------------
    if is_blank:
        pass
    else:
        output_blank = Path(f"{output_folder}/blank.tif")
        reference_raster = raster_blank(
            output_folder=output_folder,
            output_raster=output_blank,
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
            layer_rasterize(
                input_raster=str(group_raster_src),
                input_db=input_db,
                input_layer=layer,
                burn_value=1,
            )

        # reproject
        raster_reproject(
            output_folder=output_folder,
            output_raster=group_raster_warped,
            input_raster=group_raster_src,
            dst_resolution=resolution,
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
        os.remove(output_blank)

    print(f"run successfull. see for outputs:\n{output_folder}")

    return output_folder


def setup_habitats(
    output_folder,
    input_db,
    input_layer,
    groups,
    field_name,
    reference_raster,
    is_blank=False,
    resolution=400,
):
    """
    Sets up habitat layers by splitting a vector layer, rasterizing each resulting
    habitat group, and reprojecting the rasters to a specified resolution.

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
    1. **Vector Split:** Calls ``split_features`` to create a temporary GeoPackage where each habitat group is saved as a separate layer.
    2. **Template Raster:** If ``is_blank`` is ``False``, a blank raster is generated from the ``reference_raster`` to serve as the template for rasterization.
    3. **Rasterization Loop:** Each habitat layer is individually rasterized onto a copy of the template raster, setting the habitat cells to a burn value of 1.
    4. **Reprojection:** The resulting raster is reprojected to the desired ``resolution`` (and default CRS of 5641).
    5. **Metadata:** An ``info_habitats.csv`` file is created, detailing the name and file path for each generated habitat raster.
    Temporary files (split GeoPackage and intermediate rasters) are cleaned up at the end.

    **Script example**

    .. code-block:: python

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
    output_folder = make_run_folder(run_name=func_name, output_folder=output_folder)

    # files
    # -----------------------------------

    # Run processes
    # -------------------------------------------------------------------

    # split vector features
    # -----------------------------------
    output_db = split_features(
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
        output_blank = Path(f"{output_folder}/blank.tif")
        reference_raster = raster_blank(
            output_folder=output_folder,
            output_raster=output_blank,
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
        layer_rasterize(
            input_raster=str(group_raster_src),
            input_db=output_db,
            input_layer=g,
            burn_value=1,
        )

        # reproject
        raster_reproject(
            output_folder=output_folder,
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


def split_features(output_folder, input_db, input_layer, groups, field_name):
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
    func_name = split_features.__name__
    print(f"running: {func_name}")

    # Setup output variables
    # -------------------------------------------------------------------

    # folders
    # -----------------------------------
    os.makedirs(output_folder, exist_ok=True)
    output_folder = make_run_folder(run_name=func_name, output_folder=output_folder)

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


# ... {develop}

# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


def raster_blank(output_folder, output_raster, input_raster):
    """
    Creates a blank (zero-valued) raster based on the extent,
    resolution, and CRS of an existing input raster.

    :param output_folder: The directory where the blank raster will be saved (used for organization, though the full path is given by ``output_raster``).
    :type output_folder: str
    :param output_raster: The full path and filename for the resulting blank raster file.
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
        "OUTPUT": str(output_raster),
    }
    processing.run("native:rastercalc", dc_parameters)
    return output_raster


def raster_reproject(
    output_folder,
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

    :param output_folder: The directory where the reprojected raster will be saved (though not directly used in the current implementation, it implies the output location).
    :type output_folder: str
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


def layer_rasterize(
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


def get_timestamp():
    now = datetime.datetime.now()
    return str(now.strftime("%Y-%m-%dT%H%M%S"))


def make_run_folder(output_folder, run_name):
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
        ts = get_timestamp()
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
