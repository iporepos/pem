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
from os.path import isdir
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
DATA_DIR = FOLDER_ROOT / "tests/data/narnia"
OUTPUT_DIR = FOLDER_ROOT / "tests/outputs"

# define the paths to this module
# ----------------------------------------
FILE_MODULE = FOLDER_ROOT / "src/pem/project.py"

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
    Path(folder_output).mkdir(parents=True, exist_ok=True)
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


def assert_files(ls_files):
    for f in ls_files:
        assert Path(f).is_file()
    return None


# FUNCTIONS -- test public
# =======================================================================
def test_util_get_raster_crs():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define input raster
    # ----------------------------------------
    file_input = DATA_DIR / "inputs/bathymetry.tif"

    # call the function
    # ----------------------------------------
    crs_code = MODULE.util_get_raster_crs(file_input=file_input, code_only=True)

    try:
        assert crs_code == "5880", f"Expected 5880, got: {crs_code}"
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_get_raster_resolution():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define input raster
    # ----------------------------------------
    file_input = DATA_DIR / "inputs/bathymetry.tif"

    # call the function
    # ----------------------------------------
    dc_res = MODULE.util_get_raster_resolution(
        file_input=file_input,
    )

    print(dc_res)

    try:
        assert dc_res["xres"] == 5000, f"Expected 50000, got: {dc_res['xres']}"
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_get_vector_fields():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define input database
    # ----------------------------------------
    file_input = DATA_DIR / "inputs/vectors.gpkg"

    # define input database
    # ----------------------------------------
    layer_name = "fisheries_02"

    ls = MODULE.util_get_vector_fields(file_input=file_input, layer_name=layer_name)
    print(ls)

    try:
        assert len(ls) >= 2
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_raster_blank():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = _make_run_folder(folder_output=OUTPUT_DIR, run_name=func_name)

    # define reference raster
    # ----------------------------------------
    reference_raster = DATA_DIR / "inputs/bathymetry.tif"

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


def test_util_layer_rasterize():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the path to output folder
    # ----------------------------------------
    output_dir = _make_run_folder(folder_output=OUTPUT_DIR, run_name=func_name)

    # define the path to input database
    # ----------------------------------------
    input_db = DATA_DIR / "inputs/vectors.gpkg"

    # define reference raster
    # ----------------------------------------
    reference_raster = DATA_DIR / "inputs/bathymetry.tif"

    input_raster1 = f"{output_dir}/rasterized_constant.tif"
    shutil.copy(src=reference_raster, dst=input_raster1)

    input_raster2 = f"{output_dir}/rasterized_field.tif"
    shutil.copy(src=reference_raster, dst=input_raster2)

    # call the function
    # ----------------------------------------
    output_file1 = MODULE.util_layer_rasterize(
        input_raster=input_raster1,
        input_db=input_db,
        input_layer="fisheries_01",
        burn_value=666,
        extra="",
    )

    output_file2 = MODULE.util_layer_rasterize(
        input_raster=input_raster2,
        input_db=input_db,
        input_layer="fisheries_02",
        use_field="intensity",
        extra="",
    )

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_files=[output_file1, output_file2])
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_reproject_vectors():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define the input database
    # ----------------------------------------
    input_db = DATA_DIR / "inputs/vectors.gpkg"

    # define the layers list
    # ----------------------------------------
    layers = ["fisheries_01", "fisheries_02"]

    folder_output = _make_run_folder(OUTPUT_DIR, "reproject-vectors")

    # call the function
    # ----------------------------------------
    f = MODULE.util_reproject_vectors(
        input_db=input_db, layers=layers, folder_output=folder_output
    )

    try:
        assert Path(f).is_file()
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_oceanuse():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define scenario
    # ----------------------------------------
    scenario = "baseline"

    # define layer groups
    # ----------------------------------------
    group_fisheries = {
        # (required) List all vector layers that compounds to the use
        "vectors": [
            # first vector layer
            {
                # mandatory entry
                "name": "fisheries_01",
                # optional keys (assumed None if missing)
                "source": None,  # geopackage path. If None, then assumes from ./{project}/inputs/vectors.gpkg
                "field": None,  # If None, burns constant 1 to raster
                # global weight of the layer
                "weight": None,  # If None, assumes 1
            },
            # second vector layer
            {
                "name": "fisheries_02",
                "field": "intensity",
            },
            # ... add more layers if applicable
        ],
        # (optional) List all rasters layers
        #   Raster layers can be either boolean or scalar variables
        #   The merging process normalizes all values to the 0-1 range
        "rasters": [
            # first raster layer (this is boolean/footprint)
            {
                "name": "fisheries_03.tif",
                "weight": 5,  # If None, assumes 1
            },
            # second raster layer (this is scalar)
            {
                "name": "fisheries_04.tif",
                "weight": 2,  # If None, assumes 1
            },
        ],
        # "raster": []
    }

    # Other group
    group_windfarms = {
        "vectors": [
            {
                "name": "windfarms",
                "source": None,
                "field": None,
                "weight": None,
            },
        ],
    }

    # setup groups dictionary
    # ----------------------------------------
    groups = {
        "fisheries": group_fisheries,
        "windfarms": group_windfarms,
    }

    MODULE.setup_oceanuse(
        folder_project=folder_project, groups=groups, scenario=scenario
    )

    _print_passed_msg()
    return None


def test_setup_folders():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # call the function
    # ----------------------------------------
    ls_output = MODULE.setup_folders(
        name="narnia",
        folder_base=DATA_DIR.parent,
        scenarios=["baseline", "bau", "utopia"],
    )

    # Assertions
    # ----------------------------------------
    try:
        for d in ls_output:
            assert d.is_dir(), f"Expected a directory, got: {d}"
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

    print("\nTESTING project.py\n")

    args = get_arguments()

    f_which = int(args.which)

    is_all = args.all

    dc_test_dispatcher = {
        0: test_setup_folders,
        1: test_util_get_raster_crs,
        2: test_setup_oceanuse,
        3: test_util_reproject_vectors,
        4: test_util_get_vector_fields,
        5: test_util_raster_blank,
        6: test_util_layer_rasterize,
        7: test_get_raster_resolution,
        20: live_check,
    }

    if is_all:
        for i in dc_test_dispatcher:
            dc_test_dispatcher[i]()
    else:
        if f_which in dc_test_dispatcher:
            dc_test_dispatcher[f_which]()

    return None


if __name__ == "__main__":

    print(" >>> purging outputs ...")
    # shutil.rmtree(OUTPUT_DIR)

    print(" >>> resetting outputs ...")
    # os.mkdir(OUTPUT_DIR)

    print(" >>> running main ...")
    main()

    QGS.exitQgis()
