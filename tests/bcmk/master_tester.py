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
import glob

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
import pprint
import importlib.util as iu


import geopandas as gpd

# QGIS imports
# =======================================================================
# Define the path to QGIS plugins (adjust if your OSGeo4W root is different)
# For LTR, it's usually under apps\qgis-ltr\python\plugins
PLUGIN_PATH = r"C:\OSGeo4W\apps\qgis-ltr\python\plugins"

if PLUGIN_PATH not in sys.path:
    sys.path.append(PLUGIN_PATH)

from qgis.core import QgsApplication, QgsProject
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
MODULE_PROJECT = FOLDER_ROOT / "src/pem/project.py"
MODULE_RISK = FOLDER_ROOT / "src/pem/risk.py"
MODULE_CONFLICT = FOLDER_ROOT / "src/pem/conflict.py"


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
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    # define input raster
    # ----------------------------------------
    file_input = DATA_DIR / "inputs/bathymetry.tif"

    # call the function
    # ----------------------------------------
    crs_code = module.util_get_raster_crs(file_input=file_input, code_only=True)

    try:
        assert crs_code == "5880", f"Expected 5880, got: {crs_code}"
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_get_raster_resolution():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    # define input raster
    # ----------------------------------------
    file_input = DATA_DIR / "inputs/bathymetry.tif"

    # call the function
    # ----------------------------------------
    dc_res = module.util_get_raster_resolution(
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
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    # define input database
    # ----------------------------------------
    file_input = DATA_DIR / "inputs/vectors.gpkg"

    # define input database
    # ----------------------------------------
    layer_name = "fisheries_traps"

    ls = module.util_get_vector_fields(file_input=file_input, layer_name=layer_name)
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
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    # define the path to output folder
    # ----------------------------------------
    output_dir = _make_run_folder(folder_output=OUTPUT_DIR, run_name=func_name)

    # define reference raster
    # ----------------------------------------
    reference_raster = DATA_DIR / "inputs/bathymetry.tif"

    # call the function
    # ----------------------------------------
    output_file = module.util_raster_blank(
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


def test_util_rasterize_layer():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

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
    output_file1 = module.util_rasterize_layer(
        input_raster=input_raster1,
        input_db=input_db,
        input_layer="fisheries_seines",
        burn_value=666,
        extra="",
    )

    output_file2 = module.util_rasterize_layer(
        input_raster=input_raster2,
        input_db=input_db,
        input_layer="fisheries_traps",
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
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    # define the input database
    # ----------------------------------------
    input_db = DATA_DIR / "inputs/vectors.gpkg"

    # define the layers list
    # ----------------------------------------
    layers = ["fisheries_traps", "fisheries_seines"]

    folder_output = _make_run_folder(OUTPUT_DIR, "reproject-vectors")

    # call the function
    # ----------------------------------------
    f = module.util_reproject_vectors(
        input_db=input_db, layers=layers, folder_output=folder_output
    )

    try:
        assert Path(f).is_file()
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_util_generate_hra_scores():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_RISK)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    out = module.util_generate_hra_scores(
        habitats=["habitat2", "HEY", "THISS", "OKGO"],
        stressors=["TEST", "TES666", "OKOKOKO"],
        output_path=OUTPUT_DIR / "test_scores.csv",
    )

    try:
        assert out.is_file()
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()


def test_setup_project():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    ls_output = module.setup_project(
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


def test_setup_roi():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    # ----------------------------------------
    file = MODULE_PROJECT

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", file)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    ls_output = module.setup_roi(folder_project)

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_output)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_habitats():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define habitat code/id field
    # ----------------------------------------
    habitat_field = "code"

    # define habitats grouping scheme
    # ----------------------------------------
    group_benthic = [
        {"name": "benthic_a", "values": ["MB3", "MC3"]},
        {"name": "benthic_b", "values": ["MB4", "MB5", "MB6"]},
        {"name": "benthic_b", "values": ["MC4", "MC5", "MC6"]},
        {"name": "benthic_c", "values": ["MD3"]},
        {"name": "benthic_d", "values": ["MD4", "MD5", "MD6"]},
        {"name": "benthic_e", "values": ["ME1"]},
        {"name": "benthic_f", "values": ["ME4", "MF4", "MF5"]},
        {"name": "benthic_f", "values": ["MG4", "MG6"]},
    ]

    group_pelagic = None  # if None, habitats are not grouped.

    # call the function
    # ----------------------------------------
    ls_output = module.setup_habitats(
        folder_project=folder_project,
        habitat_field="code",
        groups={"benthic": group_benthic, "pelagic": group_pelagic},
    )

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_output)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_users():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)
    IU_SPEC = iu.spec_from_file_location("module", MODULE_PROJECT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define scenario
    # ----------------------------------------
    scenario = "baseline"

    # define layer groups
    # ----------------------------------------

    group_fisheries = {
        "vectors": [
            {"name": "fisheries_traps", "field": None, "weight": 1},
            {"name": "fisheries_seines", "field": "intensity", "weight": 1},
        ],
        "rasters": [
            {"name": "fisheries_gillnets.tif", "weight": 5},
            {"name": "pesca_drifting_longlines.tif", "weight": 2},
            {"name": "pesca_gillnets.tif", "weight": 2},
            {"name": "pesca_pole_and_line.tif", "weight": 2},
            {"name": "pesca_pots_and_traps.tif", "weight": 2},
            {"name": "pesca_purse_seines.tif", "weight": 2},
            {"name": "pesca_trawlers.tif", "weight": 2},
            {"name": "pesca_set_longlines.tif", "weight": 2},
        ],
    }

    group_offshorewind = {
        "vectors": [
            {"name": "windfarms", "field": None, "weight": 1},
            {"name": "eolico_linhas_transmissao", "field": None, "weight": 3},
            {"name": "eolico_torres", "field": None, "weight": 5},
        ],
    }

    group_minerals = {
        "vectors": [
            {"name": "petroleo_blocos_concessao", "field": None, "weight": 2},
            {"name": "mineracao_processos", "field": None, "weight": 3},
        ],
        "rasters": [
            {"name": "petroleo_densidade_navios.tif", "weight": 5},
        ],
    }

    group_cargo = {
        "vectors": [
            {"name": "navegacao_portos", "field": None, "weight": 3},
            {"name": "navegacao_estaleiros", "field": None, "weight": 2},
            {"name": "pdz_area_porto", "field": None, "weight": 2},
            {"name": "pdz_bacias_evolucao", "field": None, "weight": 2},
            {"name": "pdz_fundeadouros", "field": None, "weight": 2},
        ],
        "rasters": [
            {"name": "navegacao_densidade.tif", "weight": 1},
        ],
    }

    group_tourism = {
        "vectors": [
            {"name": "turismo_esportes_nauticos", "field": None, "weight": 1},
            {"name": "turismo_infra_sul", "field": None, "weight": 2},
            {"name": "turismo_mergulho_autonomo", "field": None, "weight": 1},
        ],
    }

    # setup groups dictionary
    # ----------------------------------------
    groups = {
        "fisheries": group_fisheries,
        "offshorewind": group_offshorewind,
        "minerals": group_minerals,
        "cargo": group_cargo,
        "tourism": group_tourism,
    }

    module.setup_users(folder_project=folder_project, groups=groups, scenario=scenario)

    _print_passed_msg()

    return None


def test_get_risk_index():

    pass


def test_setup_hra_scores():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    file = MODULE_RISK
    # ----------------------------------------

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define user scenario
    # ----------------------------------------
    scenario = "baseline"

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_RISK)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    ls_output = module.setup_hra_info(folder_project=folder_project, scenario=scenario)

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_output)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_hra_info():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    file = MODULE_RISK
    # ----------------------------------------

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define user scenario
    # ----------------------------------------
    scenario = "baseline"

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_RISK)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    ls_output = module.setup_hra_info(folder_project=folder_project, scenario=scenario)

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_output)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_hra_scores():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    file = MODULE_RISK
    # ----------------------------------------

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define user scenario
    # ----------------------------------------
    scenario = "baseline"

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_RISK)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    ls_output = module.setup_hra_scores(
        folder_project=folder_project, scenario=scenario
    )

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_output)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_hra_json():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    file = MODULE_RISK
    # ----------------------------------------

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define user scenario
    # ----------------------------------------
    scenario = "baseline"

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_RISK)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    ls_output = module.setup_hra_json(folder_project=folder_project, scenario=scenario)

    # Assertions
    # ----------------------------------------
    try:
        assert_files(ls_output)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_get_risk_index():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    file = MODULE_RISK
    # ----------------------------------------

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define user scenario
    # ----------------------------------------
    scenario = "baseline"

    # define HRA benthic output
    # ----------------------------------------
    hra_dir = folder_project / f"outputs/{scenario}/intermediate/hra/outputs"
    hra_benthic = glob.glob(f"{hra_dir}/TOTAL*_Ecosystem_*benthic.tif")[0]
    hra_pelagic = glob.glob(f"{hra_dir}/TOTAL*_Ecosystem_*pelagic.tif")[0]

    print(hra_benthic)
    print(hra_pelagic)

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_RISK)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    output = module.get_risk_index(
        folder_project=folder_project,
        scenario=scenario,
        hra_benthic=hra_benthic,
        hra_pelagic=hra_pelagic,
    )

    # Assertions
    # ----------------------------------------
    try:
        assert_files([output])
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_get_conflict_index():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    file = MODULE_RISK
    # ----------------------------------------

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define user scenario
    # ----------------------------------------
    scenario = "baseline"

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_CONFLICT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    output = module.get_conflict_index(folder_project=folder_project, scenario=scenario)

    # Assertions
    # ----------------------------------------
    try:
        assert_files(output)
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def test_setup_conflict_matrix():
    func_name = inspect.currentframe().f_code.co_name
    _print_func_name(func_name)

    # define module file
    file = MODULE_RISK
    # ----------------------------------------

    # define folder project
    # ----------------------------------------
    folder_project = DATA_DIR

    # define user scenario
    # ----------------------------------------
    scenario = "baseline"

    # call the function
    # ----------------------------------------
    IU_SPEC = iu.spec_from_file_location("module", MODULE_CONFLICT)
    module = iu.module_from_spec(IU_SPEC)
    IU_SPEC.loader.exec_module(module)

    output = module.setup_conflict_matrix(
        folder_project=folder_project, scenario=scenario
    )

    # Assertions
    # ----------------------------------------
    try:
        assert_files([output])
        _print_passed_msg()
    except AssertionError:
        _print_failed_msg()

    return None


def live_check():
    print("This is a live check.")


def reset():

    d1 = DATA_DIR / "inputs/users/baseline"
    shutil.rmtree(d1)
    d1.mkdir(exist_ok=True)

    d1 = DATA_DIR / "inputs/users/utopia"
    shutil.rmtree(d1)
    d1.mkdir(exist_ok=True)

    d1 = DATA_DIR / "inputs/roi"
    shutil.rmtree(d1)
    d1.mkdir(exist_ok=True)

    d1 = DATA_DIR / "inputs/habitats"
    shutil.rmtree(d1)
    d1.mkdir(exist_ok=True)

    d1 = DATA_DIR / "outputs/baseline"
    shutil.rmtree(d1)
    d1.mkdir(exist_ok=True)
    d2 = d1 / "intermediate"
    d2.mkdir(exist_ok=True)

    d1 = DATA_DIR / "outputs/utopia"
    shutil.rmtree(d1)
    d1.mkdir(exist_ok=True)
    d2 = d1 / "intermediate"
    d2.mkdir(exist_ok=True)

    print("--- purged")


def get_arguments():

    parser = argparse.ArgumentParser(
        description="Run OSGeo Shell tester",
        epilog="Usage example: python -m tests.bcmk.risk_tester --all",
    )

    parser.add_argument("--which", default=0, help="Which tests to run")

    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Run all tests",
    )

    args = parser.parse_args()

    return args


def main():

    print("\nTESTING\n")

    args = get_arguments()

    f_which = int(args.which)

    is_all = args.all

    dc_test_dispatcher = {
        0: reset,
        1: test_setup_project,
        2: test_setup_roi,
        3: test_setup_habitats,
        4: test_setup_users,
        5: test_setup_hra_info,
        6: test_setup_hra_scores,
        7: test_setup_hra_json,
        8: test_get_risk_index,
        9: test_setup_conflict_matrix,
        10: test_get_conflict_index,
        101: test_util_reproject_vectors,
        102: test_util_get_vector_fields,
        103: test_util_raster_blank,
        104: test_util_rasterize_layer,
        105: test_get_raster_resolution,
        106: test_util_get_raster_crs,
        107: test_util_generate_hra_scores,
        1000: live_check,
    }

    if is_all:
        for i in dc_test_dispatcher:
            dc_test_dispatcher[i]()
    else:
        if f_which in dc_test_dispatcher:
            dc_test_dispatcher[f_which]()

    return None


if __name__ == "__main__":

    main()

    QGS.exitQgis()
