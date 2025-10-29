# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Testing routines for the pem.risk module

.. warning::

    Run this script in the QGIS python environment


"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import inspect
import shutil
from pathlib import Path
from pprint import pprint
import importlib.util as iu

# CONSTANTS
# ***********************************************************************
# ... {develop}

here = Path(__file__).resolve()
FOLDER_ROOT = here.parent.parent.parent
DATA_DIR = FOLDER_ROOT / "tests/data/pemsul"

# define the paths to this module
# ----------------------------------------
FILE_MODULE = FOLDER_ROOT / "src/pem/risk.py"

# setup module with importlib
# ----------------------------------------
IU_SPEC = iu.spec_from_file_location("module", FILE_MODULE)
MODULE = iu.module_from_spec(IU_SPEC)
IU_SPEC.loader.exec_module(MODULE)


# FUNCTIONS
# ***********************************************************************
# ... {develop}


def util_print_func_name(func_name):
    src_func_name = func_name.replace("test_", "")
    print(f"\n\ntest: risk.{func_name}()")
    return None


def test_util_split_features():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = f"{DATA_DIR}/outputs"

    # define the path to input database
    # ----------------------------------------
    input_db = f"{DATA_DIR}/pem.gpkg"

    # setup data
    # ----------------------------------------

    # organize habitat groups
    groups = {
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

    # call the function
    # ----------------------------------------
    output_file = MODULE.util_split_features(
        input_db=input_db,
        output_folder=output_dir,
        input_layer="habitats_bentonicos_sul_v2",
        groups=groups,
        field_name="code",  # field of habitat name
    )

    # Assertions
    # ----------------------------------------
    try:
        assert Path(output_file).is_file()
        print("\ntest passed")
    except AssertionError:
        print("\ntest failed")

    return None


def test_util_raster_blank():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = MODULE._make_run_folder(
        output_folder=f"{DATA_DIR}/outputs", run_name=func_name
    )

    # define reference raster
    # ----------------------------------------
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

    # call the function
    # ----------------------------------------
    output_file = MODULE.util_raster_blank(
        output_raster=f"{output_dir}/blank.tif", input_raster=reference_raster
    )

    # Assertions
    # ----------------------------------------
    try:
        assert Path(output_file).is_file()
        print("\ntest passed")
    except AssertionError:
        print("\ntest failed")

    return None


def test_util_raster_reproject():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = MODULE._make_run_folder(
        output_folder=f"{DATA_DIR}/outputs", run_name=func_name
    )

    # define reference raster
    # ----------------------------------------
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

    # call the function
    # ----------------------------------------
    output_file = MODULE.util_raster_reproject(
        output_raster=f"{output_dir}/warped.tif",
        input_raster=reference_raster,
        dst_resolution=1000,
        dst_crs="5641",
        src_crs="4326",
        dtype=6,
        resampling=0,
    )

    # Assertions
    # ----------------------------------------
    try:
        assert Path(output_file).is_file()
        print("\ntest passed")
    except AssertionError:
        print("\ntest failed")

    return None


def test_util_layer_rasterize():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = MODULE._make_run_folder(
        output_folder=f"{DATA_DIR}/outputs", run_name=func_name
    )

    # define the path to input database
    # ----------------------------------------
    input_db = f"{DATA_DIR}/pem.gpkg"

    # define reference raster
    # ----------------------------------------
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

    input_raster = f"{output_dir}/rasterize.tif"
    shutil.copy(src=reference_raster, dst=input_raster)

    # call the function
    # ----------------------------------------
    output_file = MODULE.util_layer_rasterize(
        input_raster=reference_raster,
        input_db=input_db,
        input_layer="eolico_parques",
        input_table=None,
        burn_value=100,
        extra="",
    )

    # Assertions
    # ----------------------------------------
    try:
        assert Path(output_file).is_file()
        print("\ntest passed")
    except AssertionError:
        print("\ntest failed")

    return None


def test_setup_habitats():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = f"{DATA_DIR}/outputs"

    # define the path to input database
    # ----------------------------------------
    input_db = f"{DATA_DIR}/pem.gpkg"

    # setup data
    # ----------------------------------------

    # define reference raster
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

    # organize habitat groups
    groups = {
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

    # call the function
    # ----------------------------------------
    output_folder = MODULE.setup_habitats(
        input_db=input_db,
        output_folder=output_dir,
        input_layer="habitats_bentonicos_sul_v2",
        groups=groups,
        field_name="code",
        reference_raster=reference_raster,
        resolution=1000,
    )

    # Assertions
    # ----------------------------------------
    try:
        for k in groups.keys():
            output_file = Path(output_folder) / f"{k}.tif"
            assert Path(output_file).is_file()
        print("\ntest passed")
    except AssertionError:
        print("\ntest failed")

    return None


def test_setup_stressors():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = f"{DATA_DIR}/outputs"

    # define the path to input database
    # ----------------------------------------
    input_db = f"{DATA_DIR}/pem.gpkg"

    # setup data
    # ----------------------------------------

    # define reference raster
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

    # organize stressors groups
    groups = {
        # stressor name
        "MINERACAO": {
            # list of layers in input database
            "layers": ["mineracao_processos", "mineracao_areas_potenciais"],
            "buffer": 10000,  # in meters
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
    output_folder = MODULE.setup_stressors(
        input_db=input_db,
        output_folder=output_dir,
        groups=groups,
        reference_raster=reference_raster,
        is_blank=False,
        resolution=1000,  # in meters
    )

    # Assertions
    # ----------------------------------------
    try:
        for k in groups.keys():
            output_file = Path(output_folder) / f"{k}.tif"
            assert Path(output_file).is_file()
        print("\ntest passed")
    except AssertionError:
        print("\ntest failed")

    return None


def test_setup_hra_model():
    func_name = inspect.currentframe().f_code.co_name
    util_print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = f"{DATA_DIR}/outputs"

    # define the path to input database
    # ----------------------------------------
    input_db = f"{DATA_DIR}/pem.gpkg"

    # setup data
    # ----------------------------------------

    # define criteria table
    criteria_table = f"{DATA_DIR}/criteria_ben_pem.csv"

    # define reference raster
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

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
            "buffer": 10000,  # in meters
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
    output_folder = MODULE.setup_hra_model(
        output_folder=output_dir,
        criteria_table=criteria_table,
        input_db=input_db,
        reference_raster=reference_raster,
        resolution=1000,  # in meters
        aoi_layer="sul",
        habitat_layer="habitats_bentonicos_sul_v2",
        habitat_field="code",
        habitat_groups=habitat_groups,
        stressor_groups=stressor_groups,
    )

    # Assertions
    # ----------------------------------------
    """  
    try:
        for k in groups.keys():
            output_file = Path(output_folder) / f"{k}.tif"
            assert Path(output_file).is_file()
        print("\ntest passed")
    except AssertionError:
        print("\ntest failed")

    """
    return None


def main():
    print("\nTESTING risk.py\n")

    test_util_raster_blank()
    test_util_raster_reproject()
    test_util_split_features()
    test_util_layer_rasterize()

    test_setup_stressors()
    test_setup_habitats()
    test_setup_hra_model()

    return None


# SCRIPT
# ***********************************************************************
# ... {develop}

test_setup_hra_model()
