# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
{Short module description (1-3 sentences)}
todo docstring

"""
import shutil

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
from pathlib import Path
import os, pprint

# ... {develop}

# External imports
# =======================================================================
import numpy as np
import geopandas as gpd
import fiona

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

# Project-level imports
# =======================================================================
# import {module}
# ... {develop}


# CONSTANTS
# ***********************************************************************
# define constants in uppercase

# CONSTANTS -- Project-level
# =======================================================================
# ... {develop}
CRS_OPS = {
    "5641": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=merc +lat_ts=-2 +lon_0=-43 +x_0=5000000 +y_0=10000000 +ellps=GRS80",
    # SIRGAS 2000 BRAZIL POLYCONIC
    "5880": "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad +step +proj=poly +lat_0=0 +lon_0=-54 +x_0=5000000 +y_0=10000000 +ellps=GRS80",
}

# CONSTANTS -- Module-level
# =======================================================================
# ... {develop}


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


def setup_project(name, folder_base, scenarios=None):
    """
    Initialize the directory structure for a PEM project.

    .. note::

       This function creates a standardized hierarchy of folders for inputs
       and outputs. It also handles the creation of scenario-specific subdirectories and
       intermediate folders within each output directory.

    :param name: The name of the project, used as the root folder name.
    :type name: str
    :param folder_base: The base directory where the project structure will be created.
    :type folder_base: str or :class:`pathlib.Path`
    :param scenarios: [optional] A list of scenario names to create specific subfolders for.
    :type scenarios: list
    :return: A list of all directory paths created during the setup process.
    :rtype: list

    .. dropdown:: Script example
        :icon: code-square

        .. code-block:: python

            # !WARNING: run this in QGIS Python Environment
            import importlib.util as iu

            # define the paths to the module
            # ----------------------------------------
            the_module = "path/to/project.py"  # change here

            # define the base folder
            # ----------------------------------------
            folder_base = "path/to/folder"  # change here

            # define project name
            # ----------------------------------------
            project_name = "narnia"  # change here

            # define scenario names
            # ----------------------------------------
            # change here
            scenarios = [
                "baseline",
                "utopia",
                "distopia",
            ]

            # call the function
            # ----------------------------------------
            spec = iu.spec_from_file_location("module", the_module)
            module = iu.module_from_spec(spec)
            spec.loader.exec_module(module)

            output_file = module.setup_folders(
                name=project_name,
                folder_base=folder_base,
                scenarios=scenarios,
            )

    """
    folder_base = Path(folder_base)

    print(80 * "=")
    print("Setting up PEM project\n")
    print(f"Project name: {name}")
    print(f"Project base folder: {folder_base}")

    d_output = folder_base / f"{name}/outputs"

    ls = [
        folder_base / name,
        folder_base / f"{name}/inputs",
        folder_base / f"{name}/inputs/_sources",
        folder_base / f"{name}/inputs/benefit",
        folder_base / f"{name}/inputs/habitats",
        folder_base / f"{name}/inputs/risk/baseline",
        folder_base / f"{name}/inputs/roi",
        folder_base / f"{name}/inputs/users/baseline",
        d_output / "baseline",
    ]

    if scenarios is not None:
        ls_scenarios_bases = [
            folder_base / f"{name}/inputs/users",
            folder_base / f"{name}/inputs/risk",
            folder_base / f"{name}/outputs",
        ]
        for sn in scenarios:
            for b in ls_scenarios_bases:
                new_folder = b / sn
                ls.append(new_folder)

    for d in ls:
        d.mkdir(parents=True, exist_ok=True)

    ls_out = os.listdir(d_output)
    for d in ls_out:
        dinter = d_output / f"{d}/intermediate"
        dinter.mkdir(parents=True, exist_ok=True)

    return ls


def setup_roi(folder_project):
    # todo docstring

    pvars = _get_project_vars(folder_project)

    folder_output = pvars["folder_inputs"] / "roi"

    input_db = pvars["vectors"]
    dst_crs = pvars["crs"]
    layer = "roi"

    # reproject to SHP
    # -----------------------------------

    src_file = "{}|layername={}".format(input_db, layer)
    dst_file = f"{folder_output}/{layer}.shp"

    dc_params = {
        "INPUT": src_file,
        "TARGET_CRS": QgsCoordinateReferenceSystem(f"EPSG:{dst_crs}"),
        "CONVERT_CURVED_GEOMETRIES": False,
        "OPERATION": CRS_OPS[dst_crs],
        "OUTPUT": dst_file,
    }
    processing.run("native:reprojectlayer", dc_params)

    # make blank
    # -----------------------------------
    raster_output = f"{folder_output}/roi.tif"
    util_raster_blank(output_raster=raster_output, input_raster=pvars["refraster"])

    # rasterize
    # -----------------------------------
    util_rasterize_layer(
        input_raster=raster_output,
        input_db=None,
        input_layer=dst_file,
        burn_value=1,
    )

    return [dst_file, raster_output]


def setup_habitats(folder_project, habitat_field="code", groups=None, to_byte=True):

    # todo docstring

    pvars = _get_project_vars(folder_project)

    folder_output = pvars["folder_inputs"] / "habitats"

    input_db = pvars["vectors"]
    dst_crs = pvars["crs"]
    layers = ["habitats_benthic", "habitats_pelagic"]

    # reproject layers
    # -----------------------------------
    output_db = util_reproject_vectors(
        input_db=input_db,
        layers=layers,
        folder_output=folder_output,
        dst_crs=dst_crs,
        name_out="habitats",
    )

    ls_outputs = list()

    for hab in layers:

        hab_type = hab.split("_")[-1]

        input_layer = f"{output_db}|layername={hab}"

        # group rows
        # -----------------------------------
        layer_grouped = hab + "_grouped"
        dst_out_a = "ogr:dbname='{}' table=".format(output_db)
        dst_out_b = '"{}" (geom)'.format(layer_grouped)
        dst_out = dst_out_a + dst_out_b

        # add a 'raster' field with unique number the dissolved layer
        dc_params = {
            "INPUT": input_layer,
            "FIELD_NAME": "raster",
            "FIELD_TYPE": 1,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 2,
            "FORMULA": "$id",
            "OUTPUT": dst_out,
        }
        processing.run("native:fieldcalculator", dc_params)

        # handle groups
        # -----------------------------------
        gdf = gpd.read_file(output_db, layer=layer_grouped)

        rules = groups[hab_type]
        if rules is not None:

            # --- 1. Build the lookup dictionaries ---
            name_mapping = {}
            id_mapping = {}
            current_id = 1

            for rule in rules:
                group_name = rule["name"]

                # Assign a new ID only if we haven't seen this group_name yet
                if group_name not in id_mapping:
                    id_mapping[group_name] = current_id
                    current_id += 1

                # Map each individual value to its target group_name
                for val in rule["values"]:
                    name_mapping[val] = group_name

            # Map the values to the new columns
            gdf["group_name"] = gdf[habitat_field].map(name_mapping).fillna("UNGROUPED")
            gdf["group_id"] = gdf["group_name"].map(id_mapping).fillna(0).astype(int)

            # Set raster as the group id
            gdf["raster"] = gdf["group_id"].values
        else:
            gdf["group_name"] = gdf[habitat_field]
            gdf["group_id"] = gdf["raster"]

        # Overwrite layer
        gdf.to_file(output_db, layer=layer_grouped, driver="GPKG")

        # Clean up
        with fiona.Env():
            fiona.remove(output_db, layer=hab, driver="GPKG")

        # get raster blank
        # -----------------------------------
        raster_output = f"{folder_output}/{hab}.tif"
        util_raster_blank(output_raster=raster_output, input_raster=pvars["refraster"])
        ls_outputs.append(raster_output)

        # rasterize field
        # -----------------------------------
        util_rasterize_layer(
            input_raster=raster_output,
            input_db=output_db,
            input_layer=layer_grouped,
            use_field="raster",
        )

    # align no-data standard and data type
    # -----------------------------------
    for r in ls_outputs:
        nm = Path(r).stem + "_aux.tif"
        file_out = Path(r).parent / nm
        dc_params = {
            "INPUT": str(r),
            "TARGET_CRS": None,
            "NODATA": -99999,
            "COPY_SUBDATASETS": False,
            "OPTIONS": None,
            "EXTRA": "",
            "DATA_TYPE": 6,
            "OUTPUT": str(file_out),
        }

        if to_byte:
            dc_params["NODATA"] = 255
            dc_params["DATA_TYPE"] = 1

        processing.run("gdal:translate", dc_params)

        # clear and remove
        os.remove(r)
        os.rename(src=file_out, dst=r)

    return ls_outputs


def setup_users(folder_project, groups, scenario="baseline"):
    """
    Configures the OceanUse analysis by processing vector and raster data into weighted thematic user groups.

    :param folder_project: The root directory path of the project.
    :type folder_project: str
    :param groups: The master Layer Group dictionary defining the hierarchical structure of raster and vector layers with their associated weights.
    :type groups: dict
    :param scenario: The name of the analysis scenario, used for organizing output subdirectories. Default value = ``baseline``
    :type scenario: str
    :return: [optional] No value is returned by this function.
    :rtype: None

    .. dropdown:: Extra notes
        :icon: bookmark-fill

        This function orchestrates a multi-step geospatial workflow:
        1. Validates the existence of project folders and core input files (bathymetry and vector databases).
        2. Extracts spatial metadata (CRS, Extent, Resolution) from the reference raster.
        3. Processes defined groups by clipping/rasterizing vectors and aligning external rasters.
        4. Applies normalization and weighted map algebra to layers within each group to produce a final thematic surface.

    .. dropdown:: Script example
        :icon: code-square

        .. code-block:: python

            # !WARNING: run this in QGIS Python Environment
            import importlib.util as iu

            # define the paths to the module
            the_module = "path/to/project.py" # change here

            # define the project folder
            folder_project = "path/to/folder" # change here

            # define the analysis scenario
            scenario = "baseline" # change here

            # define layer groups
            # change "name", "field" and "weight"

            group_fisheries = {
                "vectors": [
                    {"name": "fisheries_traps", "field": None, "weight": 2 },
                    {"name": "fisheries_seines", "field": "intensity", "weight": 3 },
                ],
                "rasters": [
                    {"name": "fisheries_gillnets.tif", "weight": 10 },
                    {"name": "fisheries_longlines.tif", "weight": 5 },
                ]
            }
            group_windfarms = {
                "vectors": [
                    {"name": "windfarms", "field": None, "weight": 5 },
                ],
            }

            # setup groups dictionary
            # define actual names for Ocean Users
            groups = {
                "fisheries": group_fisheries,
                "windfarms": group_windfarms,
            }

            # call the function
            # do not change here
            spec = iu.spec_from_file_location("module", the_module)
            module = iu.module_from_spec(spec)
            spec.loader.exec_module(module)

            output_file = module.setup_users(
                folder_project=folder_project,
                groups=groups,
                scenario=scenario
            )

    """

    def _list_weights(ls_layers):
        ls_weights = list()
        for layer_dc in ls_layers:
            w = layer_dc.get("weight", 1)
            if w is None:
                w = 1
            ls_weights.append(w)
        return ls_weights

    pvars = _get_project_vars(folder_project=folder_project)

    folder_project = pvars["folder_project"]
    folder_inputs = pvars["folder_inputs"]

    # get specific folders
    # ===============================================
    folder_output = folder_project / f"inputs/users/{scenario}"
    folder_outputs_interm = folder_project / f"outputs/{scenario}/intermediate"
    folder_sources = folder_inputs / "_sources"

    # get files
    # ===============================================
    input_db = pvars["vectors"]
    reference_raster = pvars["refraster"]

    # get extra parameters
    # ===============================================
    dst_crs = pvars["crs"]
    dst_ext = pvars["ext"]
    dst_res = pvars["res"]

    # master check up
    # ===============================================

    _folder_checker([folder_outputs_interm])
    _file_checker([input_db, reference_raster])

    for k in groups:
        if "vectors" not in groups[k].keys() and "rasters" not in groups[k].keys():
            raise KeyError(
                f"On '{k}' group >> neither 'vectors' or 'rasters' keys were found"
            )

    # enter main loop
    # ===============================================

    for g in groups:
        ls_rasters = list()
        ls_weights = list()
        # setup vectors
        # ===============================================
        if "vectors" in groups[g]:
            ls = _setup_users_vectors(
                input_db=input_db,
                groups=groups[g],
                dst_crs=dst_crs,
                dst_ext=dst_ext,
                folder_output=folder_outputs_interm,
                reference_raster=reference_raster,
            )
            ls_rasters = ls_rasters + ls[:]

            ls_w = _list_weights(ls_layers=groups[g]["vectors"])
            ls_weights = ls_weights + ls_w

        # setup rasters
        # ===============================================
        if "rasters" in groups[g]:
            ls = _setup_users_rasters(
                folder_sources=folder_sources,
                groups=groups[g],
                dst_crs=dst_crs,
                dst_ext=dst_ext,
                dst_res=dst_res,
                folder_output=folder_outputs_interm,
            )
            ls_rasters = ls_rasters + ls[:]

            ls_w = _list_weights(ls_layers=groups[g]["rasters"])
            ls_weights = ls_weights + ls_w

        # normalize
        # ===============================================
        ls_normalized = util_normalize_rasters(ls_rasters=ls_rasters)

        if len(ls_normalized) > 1:
            # map algebra
            # ===============================================
            file_output = folder_outputs_interm / f"{g}_wavg.tif"
            file_raster = _setup_users_algebra(
                ls_normalized, ls_weights, file_output, reference_raster
            )

            # normalize
            # ===============================================
            ls_normalized = util_normalize_rasters(ls_rasters=[file_raster])

        dc = {
            "INPUT": str(ls_normalized[0]),
            "BAND": 1,
            "FILL_VALUE": 0,
            "CREATE_OPTIONS": None,
            "OUTPUT": str(folder_output / f"{g}.tif"),
        }
        processing.run("native:fillnodata", dc)

    return None


def _setup_users_algebra(
    ls_rasters, ls_weights, file_output, reference_raster, in_nodata=-99999
):
    if len(ls_rasters) != len(ls_weights):
        raise ValueError("List of files and weights not the same size")

    weighted_sum = None
    total_weight = sum(ls_weights)
    out_metadata = None

    for i in range(len(ls_rasters)):
        w = float(ls_weights[i])
        # 1. Read the raster
        raster_dict = util_read_raster(ls_rasters[i])

        # 2. Extract data and convert to float32
        data = raster_dict["data"].astype(np.float32)

        # 3. Cast incoming NoData values to NaN so they don't skew the math
        data[data == in_nodata] = np.nan

        # 4. Initialize the accumulator array
        if weighted_sum is None:
            weighted_sum = np.zeros_like(data)
            out_metadata = raster_dict.get("metadata")

        # 5. Multiply the map by its weight and add it to the running total
        weighted_sum += data * w

    # 6. Calculate the final weighted average
    # Note: If a pixel has NaN in ANY of the input rasters,
    # the math here ensures it remains NaN in the weighted_avg.
    weighted_avg = weighted_sum / total_weight

    # 7. Convert NaNs back to the NoData value for the final TIF
    final_data = np.nan_to_num(weighted_avg, nan=in_nodata)

    # 8. Write to disk
    util_write_raster(
        grid_output=final_data,  # Pass the cleaned data, not the array with NaNs
        dc_metadata=out_metadata,
        file_output=str(file_output),
        nodata_value=in_nodata,
    )

    return file_output


def _setup_users_rasters(
    folder_sources, groups, dst_crs, dst_ext, dst_res, folder_output
):

    layers = [layer["name"] for layer in groups["rasters"]]

    if len(layers) == 0:
        raise ValueError("Raster layer list empty")

    ls_outputs = list()
    for layer_dc in groups["rasters"]:
        name = layer_dc["name"]
        file_output = f"{folder_output}/{name}"
        file_input_raster = folder_sources / name
        src_crs = util_get_raster_crs(file_input_raster, code_only=True)

        dst_extent = f'{dst_ext["xmin"]},{dst_ext["xmax"]},{dst_ext["ymin"]},{dst_ext["ymax"]} [EPSG:{dst_crs}]'

        dc_params = {
            "INPUT": str(file_input_raster),
            "SOURCE_CRS": QgsCoordinateReferenceSystem("EPSG:{}".format(src_crs)),
            "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:{}".format(dst_crs)),
            "RESAMPLING": 3,
            "NODATA": -99999,
            "TARGET_RESOLUTION": dst_res,
            "OPTIONS": None,
            "DATA_TYPE": 6,
            "TARGET_EXTENT": dst_extent,
            "TARGET_EXTENT_CRS": QgsCoordinateReferenceSystem(f"EPSG:{dst_crs}"),
            "MULTITHREADING": False,
            "EXTRA": "",
            "OUTPUT": file_output,
        }
        processing.run("gdal:warpreproject", dc_params)
        ls_outputs.append(Path(file_output))

    return ls_outputs


def _setup_users_vectors(
    input_db, groups, dst_crs, dst_ext, folder_output, reference_raster
):

    layers = [layer["name"] for layer in groups["vectors"]]

    if len(layers) == 0:
        raise ValueError("Vector layer list empty")

    # reproject
    # ===============================================
    reprojected = util_reproject_vectors(
        input_db=input_db,
        layers=layers,
        folder_output=folder_output,
        dst_crs=dst_crs,
        name_out="users_reprojected",
    )

    # clip/extract
    # ===============================================
    extracted = util_extractextent_vectors(
        input_db=reprojected,
        layers=layers,
        folder_output=folder_output,
        dst_crs=dst_crs,
        dst_ext=dst_ext,
        name_out="users_extracted",
    )

    # rasterize
    # ===============================================
    ls_outputs = list()
    for layer_dc in groups["vectors"]:
        name = layer_dc["name"]

        file_raster = util_raster_blank(
            output_raster=f"{folder_output}/{name}.tif", input_raster=reference_raster
        )

        use_field = False

        if "field" in layer_dc.keys():
            field = layer_dc["field"]
            if field is not None:
                use_field = True

        if use_field:
            # rasterize field
            ls_fields = util_get_vector_fields(extracted, layer_name=name)
            if field not in ls_fields:
                raise ValueError(f"Field '{field}' not found in database.")
            file_output = util_rasterize_layer(
                input_raster=file_raster,
                input_db=extracted,
                input_layer=name,
                use_field=field,
                extra="-add",
            )

        else:
            file_output = util_rasterize_layer(
                input_raster=file_raster,
                input_db=extracted,
                input_layer=name,
                burn_value=1,
                extra="-add",
            )
        ls_outputs.append(Path(file_raster))
    return ls_outputs


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


def util_rasterize_layer(
    input_raster,
    input_db=None,
    input_layer=None,
    burn_value=1,
    use_field=None,
    add=False,
    extra="",
):
    # todo docstring

    input_vector = str(input_layer)

    if input_db is not None:
        input_vector = "{}|layername={}".format(input_db, input_layer)

    dc_parameters = {
        "INPUT": input_vector,
        "INPUT_RASTER": str(input_raster),
        "ADD": add,
        "EXTRA": extra,
    }

    if use_field is not None:
        dc_parameters["FIELD"] = use_field
        processing.run("gdal:rasterize_over", dc_parameters)
    else:
        dc_parameters["BURN"] = burn_value
        processing.run("gdal:rasterize_over_fixed_value", dc_parameters)

    return input_raster


def util_extractextent_vectors(
    input_db, layers, folder_output, dst_ext, dst_crs="5880", name_out="extractextent"
):
    """
    Extracts specific vector layers based on a spatial extent and saves them to a GeoPackage.

    .. note::

        Iterates through a list of layers from an input database, clips each to the
        provided spatial bounds using the ``native:extractbyextent`` algorithm,
        and appends the result to a destination GeoPackage.

    :param input_db: Path to the source database or vector file.
    :type input_db: str
    :param layers: List of layer names to be extracted from the source.
    :type layers: list
    :param folder_output: Directory where the output file will be saved.
    :type folder_output: str
    :param dst_ext: Dictionary containing the spatial bounds with keys ``xmin``, ``xmax``, ``ymin``, and ``ymax``.
    :type dst_ext: dict
    :param dst_crs: Coordinate Reference System identifier for the extent. Default value = ``5880``
    :type dst_crs: str
    :param name_out: Filename for the output GeoPackage (without extension). Default value = ``extractextent``
    :type name_out: str
    :return: The file path to the generated GeoPackage.
    :rtype: str
    """
    dst_file = "{}/{}.gpkg".format(folder_output, name_out)
    dst_extent = f'{dst_ext["xmin"]},{dst_ext["xmax"]},{dst_ext["ymin"]},{dst_ext["ymax"]} [EPSG:{dst_crs}]'

    for layer in layers:
        src_file = "{}|layername={}".format(input_db, layer)

        # 1. Fix Geometries first using a temporary output
        fix_params = {
            "INPUT": src_file,
            "OUTPUT": "TEMPORARY_OUTPUT",  # This keeps the result in memory
        }
        fixed_layer = processing.run("native:fixgeometries", fix_params)["OUTPUT"]

        # 2. Define your destination
        dst_out = "ogr:dbname='{}' table=".format(dst_file) + '"{}" (geom)'.format(
            layer
        )

        # 3. Run the extraction using the 'fixed_layer' as input
        dc_params = {
            "INPUT": fixed_layer,  # Using the temporary layer here
            "EXTENT": dst_extent,
            "CLIP": True,
            "OUTPUT": dst_out,
        }
        processing.run("native:extractbyextent", dc_params)

    return dst_file


def util_reproject_vectors(
    input_db, layers, folder_output, dst_crs="5880", name_out="reprojected"
):
    """
    Reprojects a list of vector layers from a source database to a specified coordinate
    reference system and saves them into a new GeoPackage.

    :param input_db: Path to the source database containing the layers.
    :type input_db: str
    :param layers: List of layer names to be reprojected.
    :type layers: list
    :param folder_output: Directory path where the output GeoPackage will be stored.
    :type folder_output: str
    :param dst_crs: The EPSG code for the destination coordinate reference system. Default value = ``5880``
    :type dst_crs: str
    :return: The file path to the generated GeoPackage containing the reprojected layers.
    :rtype: str

    .. note::

         The function utilizes ``native:reprojectlayer`` and stores all processed layers within a single ``.gpkg`` file named ``reprojected.gpkg``.

    todo script example

    """

    dst_file = "{}/{}.gpkg".format(folder_output, name_out)

    for layer in layers:
        src_file = "{}|layername={}".format(input_db, layer)

        dst_out = "ogr:dbname='{}' table=".format(dst_file) + '"{}" (geom)'.format(
            layer
        )
        # dst_out = 'ogr:dbname=\'{}/{}\' table="{}" (geom)'.format(dst_file, layer)
        dc_params = {
            "INPUT": src_file,
            "TARGET_CRS": QgsCoordinateReferenceSystem(f"EPSG:{dst_crs}"),
            "CONVERT_CURVED_GEOMETRIES": False,
            "OPERATION": CRS_OPS[dst_crs],
            "OUTPUT": dst_out,
        }
        processing.run("native:reprojectlayer", dc_params)

    return dst_file


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


# FUNCTIONS -- Module-level
# =======================================================================
# ... {develop}


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


def util_get_raster_crs(file_input, code_only=True):
    """
    Extracts the Coordinate Reference System (CRS) from a raster file.

    :param file_input: The file path to the raster source.
    :type file_input: str
    :param code_only: Whether to return only the numerical ID (e.g., ``31983``) or the full authority ID (e.g., ``EPSG:31983``). Default value = ``True``
    :type code_only: bool
    :return: The CRS identifier as a string.
    :rtype: str

    todo script example

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

    # Create a raster layer object
    raster_layer = QgsRasterLayer(str(file_input), "Raster Layer")
    res_x = raster_layer.rasterUnitsPerPixelX()
    res_y = raster_layer.rasterUnitsPerPixelY()

    return {
        "xres": res_x,
        "yres": res_y,
    }


def util_get_vector_fields(file_input, layer_name):
    """
    Retrieves a list of all attribute field names from a specific layer within a vector file.

    :param file_input: The path to the source vector database or file.
    :type file_input: str
    :param layer_name: The name of the specific layer to access.
    :type layer_name: str
    :return: A list of strings representing the field names in the layer.
    :rtype: list
    """
    # Combine them for the URI
    uri = f"{file_input}|layername={layer_name}"
    # Create the layer object (Source, Display Name, Provider Key)
    vlayer = QgsVectorLayer(uri, "My Roads Layer", "ogr")

    # Assuming 'layer' is your loaded vector layer
    fields = vlayer.fields()

    # List all field names
    ls = []
    for field in fields:
        ls.append(field.name())
    return ls


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


# CLASSES
# ***********************************************************************

# CLASSES -- Project-level
# =======================================================================
# ... {develop}

# CLASSES -- Module-level
# =======================================================================
# ... {develop}


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
