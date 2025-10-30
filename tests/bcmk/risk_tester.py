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

# FUNCTIONS -- internal module utils
# =======================================================================


def _print_func_name(func_name):
    src_func_name = func_name.replace("test_", "")
    print(f"\n\ntest: risk.{func_name}()")
    return None


def _print_passed_msg():
    print("\n >>> test passed.")
    return None


def _print_failed_msg():
    print("\n >>> test failed.")
    return None


# FUNCTIONS -- assertions
# =======================================================================


def assert_files_by_names(ls_names, file_extension, folder_output):
    ls_files = list()
    for name in ls_names:
        ls_files.append(Path(folder_output) / f"{name}.{file_extension}")
    assert_files(ls_files)
    return None


def assert_files_by_file_names(ls_names, folder_output):
    ls_files = list()
    for name in ls_names:
        ls_files.append(Path(folder_output) / name)
    assert_files(ls_files)
    return None


def assert_files(ls_files):
    for f in ls_files:
        assert Path(f).is_file()
    return None


# FUNCTIONS -- test public utils
# =======================================================================


def test_util_get_raster_stats():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = f"{DATA_DIR}/outputs"

    # define the path to input raster
    # ----------------------------------------
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

    # call the function
    # ----------------------------------------
    output_dc_1 = MODULE.util_get_raster_stats(
        input_raster=reference_raster, band=1, full=False
    )
    pprint(output_dc_1)

    output_dc_2 = MODULE.util_get_raster_stats(
        input_raster=reference_raster, band=1, full=True
    )
    pprint(output_dc_2)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output_dc_1, dict)
        assert isinstance(output_dc_2, dict)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_fuzzify_raster():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = f"{DATA_DIR}/outputs"

    # define the path to input raster
    # ----------------------------------------
    reference_raster = f"{DATA_DIR}/gebco_topobathymetry.tif"

    # call the function
    # ----------------------------------------

    output_file_1 = MODULE.util_fuzzify_raster(
        input_raster=reference_raster,
        output_raster=f"{output_dir}/fuzzy_raster_nobounds.tif",
        lo=None,
        hi=None,
    )

    output_file_2 = MODULE.util_fuzzify_raster(
        input_raster=reference_raster,
        output_raster=f"{output_dir}/fuzzy_raster_bounds.tif",
        lo=-5000,
        hi=500,
    )

    output_file_3 = MODULE.util_fuzzify_raster(
        input_raster=reference_raster,
        output_raster=f"{output_dir}/fuzzy_raster_partialbounds.tif",
        lo=None,
        hi=0,
    )

    output_file_4 = MODULE.util_fuzzify_raster(
        input_raster=reference_raster,
        output_raster=f"{output_dir}/fuzzy_raster_percentiles.tif",
        lo=None,
        hi=0,
        use_percentiles=True,
    )

    # Assertions
    # ----------------------------------------
    try:
        ls_files = [
            output_file_1,
            output_file_2,
            output_file_3,
            output_file_4,
        ]
        assert_files(ls_files=ls_files)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_split_features():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

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
        folder_output=output_dir,
        input_layer="habitats_bentonicos_sul_v2",
        groups=groups,
        field_name="code",  # field of habitat name
    )

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_files=[output_file])
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_raster_blank():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = MODULE._make_run_folder(
        folder_output=f"{DATA_DIR}/outputs", run_name=func_name
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
        assert_files(ls_files=[output_file])
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_raster_reproject():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = MODULE._make_run_folder(
        folder_output=f"{DATA_DIR}/outputs", run_name=func_name
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
        assert_files(ls_files=[output_file])
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_layer_rasterize():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = MODULE._make_run_folder(
        folder_output=f"{DATA_DIR}/outputs", run_name=func_name
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
        assert_files(ls_files=[output_file])
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


# FUNCTIONS -- test procedures
# =======================================================================


def test_setup_habitats():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

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
    folder_output = MODULE.setup_habitats(
        input_db=input_db,
        folder_output=output_dir,
        input_layer="habitats_bentonicos_sul_v2",
        groups=groups,
        field_name="code",
        reference_raster=reference_raster,
        resolution=1000,
    )

    # Assertions
    # ----------------------------------------
    try:
        ls_names = list(groups.keys())
        assert_files_by_names(
            ls_names=ls_names, file_extension="tif", folder_output=folder_output
        )
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_stressors():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

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
    folder_output = MODULE.setup_stressors(
        input_db=input_db,
        folder_output=output_dir,
        groups=groups,
        reference_raster=reference_raster,
        is_blank=False,
        resolution=1000,  # in meters
    )

    # Assertions
    # ----------------------------------------
    try:
        ls_names = list(groups.keys())
        assert_files_by_names(
            ls_names=ls_names, file_extension="tif", folder_output=folder_output
        )
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_hra_model():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

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
    folder_output = MODULE.setup_hra_model(
        folder_output=output_dir,
        file_criteria=criteria_table,
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
    try:
        # habitats
        ls_names = list(habitat_groups.keys())
        assert_files_by_names(
            ls_names=ls_names,
            file_extension="tif",
            folder_output=f"{folder_output}/habitats",
        )

        # stressors
        ls_names = list(stressor_groups.keys())
        assert_files_by_names(
            ls_names=ls_names,
            file_extension="tif",
            folder_output=f"{folder_output}/stressors",
        )

        # other files
        ls_file_names = [
            "criteria.csv",
            "info.csv",
            "model.json",
            "reference_raster_blank.tif",
        ]
        assert_files_by_file_names(ls_names=ls_file_names, folder_output=folder_output)

        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_compute_risk_index():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = f"{DATA_DIR}/outputs"

    # define the path to rasters
    # ----------------------------------------
    raster_hra_benthic = f"{DATA_DIR}/hra_bsl_ben.tif"
    raster_hra_pelagic = f"{DATA_DIR}/hra_bsl_pel.tif"

    # call the function
    # ----------------------------------------
    folder_output = MODULE.compute_risk_index(
        folder_output=output_dir,
        raster_hra_benthic=raster_hra_benthic,
        raster_hra_pelagic=raster_hra_pelagic,
    )

    # Assertions
    # ----------------------------------------
    try:
        # habitats
        ls_names = [
            "risk_b",
            "risk_p",
            "hra_sum",
            "risk",
        ]
        assert_files_by_names(
            ls_names=ls_names, file_extension="tif", folder_output=folder_output
        )
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()
    return None


def main():
    print("\nTESTING risk.py\n")

    # utils
    test_util_raster_blank()
    test_util_raster_reproject()
    test_util_split_features()
    test_util_layer_rasterize()
    test_util_get_raster_stats()
    test_util_fuzzify_raster()

    # setups
    test_setup_stressors()
    test_setup_habitats()
    test_setup_hra_model()

    # computes
    test_compute_risk_index()

    return None


# SCRIPT
# ***********************************************************************
# ... {develop}

main()
