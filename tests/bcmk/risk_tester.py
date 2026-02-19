# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Testing routines for the pem.risk module

.. warning::

    Run this script in the QGIS python environment or via OSGeo4W


"""

# IMPORTS
# ***********************************************************************
# import modules from other libs

# Native imports
# =======================================================================
import sys, os, datetime
import argparse
import inspect
import shutil
from pathlib import Path
from pprint import pprint
import importlib.util as iu


# QGIS imports
# =======================================================================
# Define the path to QGIS plugins (adjust if your OSGeo4W root is different)
# For LTR, it's usually under apps\qgis-ltr\python\plugins
PLUGIN_PATH = r"C:\OSGeo4W\apps\qgis-ltr\python\plugins"

if PLUGIN_PATH not in sys.path:
    sys.path.append(PLUGIN_PATH)

from qgis.core import QgsApplication
from processing.core.Processing import Processing

# Initialize QGIS (Required for standalone scripts)
# 1. Setup Paths
# This must happen BEFORE initQgis
os.environ["QT_QPA_PLATFORM"] = (
    "offscreen"  # Prevents 'no display' errors on some systems
)
QgsApplication.setPrefixPath(r"C:\OSGeo4W\apps\qgis-ltr", True)
QGS = QgsApplication([], False)
QGS.initQgis()

# Initialize the Processing framework
Processing.initialize()

# CONSTANTS
# ***********************************************************************
# ... {develop}

HERE = Path(__file__).resolve()
FOLDER_ROOT = HERE.parent.parent.parent
DATA_DIR = FOLDER_ROOT / "tests/data/pemsul"
OUTPUT_DIR = FOLDER_ROOT / "tests/outputs"

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


def _get_timestamp():
    now = datetime.datetime.now()
    return str(now.strftime("%Y-%m-%dT%H%M%S"))


def _make_run_folder(folder_output, run_name):
    """
    Creates a unique, time-stamped run folder within a specified output directory.

    :param folder_output: The parent directory where the new run folder will be created.
    :type folder_output: str or :class:`pathlib.Path`
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
        folder_run = Path(folder_output) / f"{run_name}_{ts}"
        if os.path.exists(folder_run):
            time.sleep(1)
        else:
            os.mkdir(folder_run)
            break

    return os.path.abspath(folder_run)


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


def live_check():
    print("This is a live check.")


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Run OSGeo Shell tester",
        epilog="Usage example: python -m tests.bcmk.risk_tester --all",
    )

    parser.add_argument("--which", default=20, help="Which tests to run")

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Run all tests",
    )

    args = parser.parse_args()

    return args


def main():

    print("\nTESTING risk.py\n")

    args = get_arguments()

    f_which = int(args.which)

    is_all = args.all

    dc_test_dispatcher = {
        # utils
        0: test_util_raster_blank,
        2: test_util_raster_reproject,
        3: test_util_split_features,
        4: test_util_layer_rasterize,
        5: test_util_get_raster_stats,
        6: test_util_fuzzify_raster,
        # setups
        7: test_setup_stressors,
        8: test_setup_habitats,
        9: test_setup_hra_model,
        # computes
        10: test_compute_risk_index,
        20: live_check,
    }

    if is_all:
        for i in dc_test_dispatcher:
            dc_test_dispatcher[i]()
    else:
        if f_which in dc_test_dispatcher:
            dc_test_dispatcher[f_which]()

    return None


# SCRIPT
# ***********************************************************************
# ... {develop}
if __name__ == "__main__":

    main()
    QGS.exitQgis()
