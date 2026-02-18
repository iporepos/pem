.. _usage:

.. include:: ./includes/warning_dev.rst

User Guide
############################################

This guide describes how to install, configure, and use the **PEM framework**
from source. The framework is organized as a collection of standalone Python
modules, each targeting a specific analytical component.

.. seealso::

   If you intend to extend or modify the framework, refer to
   :ref:`Development <development>`.


.. _installation:

Installation
============================================

The PEM framework is distributed as source code. Each script is designed to
run as an independent process within the broader workflow.

Clone the official repository using ``git``:

.. code-block:: bash

    git clone https://github.com/iporepos/pem.git
    cd pem

Alternatively, download the latest release directly from GitHub:

https://github.com/iporepos/pem

.. note::

   Ensure that ``git`` is properly installed and available in your system
   environment variables before attempting to clone the repository.


.. _install-qgis:

Install PyQGIS
--------------------------------------------

All Python scripts are designed to run within the **QGIS Python environment**
(PyQGIS). Therefore, installing QGIS is a mandatory prerequisite.

1. Download QGIS from the official website:
   https://qgis.org/download

2. During installation, ensure that the bundled Python environment is included.

.. seealso::

   For PyQGIS scripting details, consult the
   `PyQGIS Developer Cookbook <https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/index.html>`_.


.. _install-invest:

Install InVEST Workbench
--------------------------------------------

The :ref:`Habitat Risk Index page <about-risk-index>` — a core component of
the PEM framework — is derived from the
`Habitat Risk Assessment model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_,
part of the
`InVEST suite <https://naturalcapitalalliance.stanford.edu/software/invest>`_.

To ensure compatibility with the risk modeling workflow:

1. Download and install the
   `InVEST Workbench <https://naturalcapitalalliance.stanford.edu/software/invest/invest-downloads-data>`_.
2. Install on a supported operating system (Windows or macOS).
3. Verify that the Habitat Risk Assessment model executes successfully.

.. important::

   The Habitat Risk Index implemented in PEM assumes conceptual and
   methodological alignment with the InVEST Habitat Risk Assessment model.


.. _run-scripts:

Source Code
============================================

The repository follows a standard ``src`` layout:

.. code-block:: text

    pem/                             # repository root
    ├── src/                         # source directory
    │   └── pem/                     # package root
    │       ├── risk.py              # Habitat Risk Index module
    │       ├── conflict.py          # User Conflict Index module
    │       ├── benefit.py           # Benefit Index module
    │       ├── iduse.py             # Use Performance Index module
    │       └── data/                # runtime data resources
    └── docs/                        # documentation (if applicable)

Each module encapsulates a logically distinct index within the PEM framework.


.. _run-scripts-python:

Running Python via PyQGIS
--------------------------------------------

All python modules defines functions that are documented in
the :ref:`API page <api>`.

Because the framework is distributed as source code (not as an installed package),
the functions in the modules should be dynamically loaded using :mod:`importlib`.

This approach ensures:

- Execution inside the correct PyQGIS runtime.
- Full access to QGIS core libraries.
- No need for system-wide package installation.

.. important::

   Always execute the scripts from the **QGIS Python Console** or from a
   Python interpreter explicitly bound to the QGIS environment.


.. dropdown:: Example: loading functions from the modules
    :icon: code-square

    The following template demonstrates how to dynamically load the module ``risk.py``
    (Habitat Risk Index utility) and execute one of its functions.

    .. code-block:: python

        # WARNING: run this in QGIS Python Environment

        import importlib.util as iu

        # ------------------------------------------------------------------
        # 1. Define the path to the target module (e.g., risk.py)
        # ------------------------------------------------------------------
        the_module = "path/to/risk.py"

        spec = iu.spec_from_file_location("module", the_module)
        module = iu.module_from_spec(spec)
        spec.loader.exec_module(module)

        # ------------------------------------------------------------------
        # 2. Define input and output directories
        # ------------------------------------------------------------------
        input_dir = "path/to/input_dir"
        output_dir = "path/to/output_dir"

        # Path to the GeoPackage database
        input_db = f"{input_dir}/pem.gpkg"

        # ------------------------------------------------------------------
        # 3. Define analytical parameters
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # 4. Execute the target function
        # ------------------------------------------------------------------
        output_file = module.setup_habitats(
            input_db=input_db,
            folder_output=output_dir,
            input_layer="habitats_bentonicos_sul_v2",
            groups=groups,
            field_name="code",
            reference_raster=f"{input_dir}/raster.tif",
            resolution=1000
        )

    The workflow follows four conceptual stages:

    1. **Dynamic module binding** via ``importlib``.
    2. **Path configuration** for input/output resources.
    3. **Parameter definition** (e.g., habitat grouping rules).
    4. **Function execution**, returning the generated output artifact.

    This pattern is applicable to all PEM python modules
    Simply change the file path, parameters and target function accordingly.

    .. tip::

       For reproducibility, store your execution script alongside your
       project data and document all parameter choices explicitly.
       This ensures traceability of spatial preprocessing decisions.


.. _project:

PEM Project
============================================

The PEM framework may be deployed by the user under the concept
of a **PEM Project**.

.. _project-folders:

Folder Structure
--------------------------------------------

A file-based PEM Project can follow a standardized directory schema to ensure
reproducibility, scenario management, and compatibility with all framework
modules.

The structure below represents the recommended layout for a complete project.

.. important::

   Adherence to this directory structure is not mandatory but is strongly recommended.
   The rationale of the PEM framework relies on this layout.

.. code-block:: text

    pem-project/                          # Project root
    │
    ├── inputs/                           # All model inputs
    │   │
    │   ├── bathymetry.tif                 # Reference raster (resolution, extent, CRS)
    │   │
    │   ├── layers.gpkg                    # Core vector data container
    │   ├── layers.gpkg|roi                # Region of Interest (polygon layer)
    │   ├── layers.gpkg|hubs               # Land hubs (point layer)
    │   ├── layers.gpkg|...                # Additional optional layers
    │   │
    │   ├── habitats/                      # Habitat rasters
    │   │   ├── benthic.tif                # Benthic habitat map
    │   │   └── pelagic.tif                # Pelagic habitat map
    │   │
    │   ├── oceanuse/                      # Ocean use configuration
    │   │   ├── oceanuse.csv               # Table of ocean users
    │   │   ├── conflict.csv               # Spatial conflict matrix
    │   │   │
    │   │   ├── baseline/                  # Baseline scenario
    │   │   │   ├── oil-and-gas.tif        # user raster footprint
    │   │   │   ├── fish-industrial.tif    # (suggested users)
    │   │   │   ├── windfarms.tif
    │   │   │   ├── {username}.tif
    │   │   │   └── ...
    │   │   │
    │   │   └── {scenario}/                # Alternative scenarios
    │   │
    │   ├── risk/                          # Habitat Risk model parameters
    │   │   ├── baseline/
    │   │   │   ├── roi.shp                # ROI shapefile (required by InVEST-HRA)
    │   │   │   ├── stressors_benthic.csv  # Stressor table (required by InVEST-HRA)
    │   │   │   ├── scores_benthic.csv     # Criteria scores (required by InVEST-HRA)
    │   │   │   ├── stressors_pelagic.csv
    │   │   │   └── scores_pelagic.csv
    │   │   │
    │   │   └── {scenario}/                # Alternative scenarios
    │   │
    │   └── benefit/                       # Benefit Index parameters and data
    │
    └── outputs/                           # Model outputs
        │
        ├── baseline/
        │   ├── baseline_iduse.tif         # Use Performance Index
        │   ├── baseline_benefit.tif       # Benefit Index
        │   ├── baseline_conflict.tif      # Conflict Index
        │   ├── baseline_risk.tif          # Habitat Risk Index
        │   │
        │   └── intermediate/              # Intermediate artifacts
        │       ├── baseline_hra_benthic.tif      # InVEST output
        │       ├── baseline_hra_benthic_fz.tif   # fuzzy transform
        │       ├── baseline_hra_pelagic.tif
        │       └── baseline_hra_pelagic_fz.tif
        │
        └── {scenario}/                    # Alternative scenario outputs


.. _project-design:

Design Principles
--------------------------------------------

The PEM Project presented above has some core design principles.

**1. Scenario Isolation**

Each scenario (e.g., ``baseline``, ``future-ssp1``) maintains:

- Dedicated ocean-use rasters.
- Independent risk parameterization.
- Separate output folders.

This guarantees clean scenario comparison and prevents cross-contamination
of intermediate artifacts.

**2. Bathymetry is the Single Source of Spatial Truth**

The ``bathymetry.tif`` file defines:

- Spatial resolution
- Projection (CRS)
- Raster extent

All derived rasters must conform strictly to this reference grid.

**3. Modular Input Domains**

Inputs are grouped by analytical domain:

- ``habitats/`` → ecological state
- ``oceanuse/`` → human pressures and interactions
- ``risk/`` → Habitat Risk parameterization
- ``benefit/`` → Benefit Index parameters

This separation aligns with the internal architecture of the PEM modules.

**4. Deterministic Outputs**

All primary indices are written to:

.. code-block:: text

    outputs/{scenario}/

Intermediate model artifacts are explicitly separated under:

.. code-block:: text

    outputs/{scenario}/intermediate/

This ensures traceability of derived layers such as InVEST-HRA results and
their fuzzy-transformed counterparts.

.. _project-technical:

Technical Recommendations
============================================

The PEM framework is architected around a **single spatial reference raster**:
the bathymetry layer. This raster defines the spatial standard for the entire
project and governs:

- Coordinate Reference System (CRS)
- Projection
- Spatial resolution
- Grid alignment
- Spatial extent (bounding box)

Strict spatial consistency is mandatory for deterministic and valid results.

Bathymetry as Spatial Reference
--------------------------------------------

The file:

.. code-block:: text

    inputs/bathymetry.tif

acts as the **authoritative spatial template** for the project.

All raster outputs and intermediate layers are expected to:

- Match its CRS exactly
- Match its resolution exactly
- Align to its pixel grid
- Remain within its bounding box

.. important::

   The bathymetry raster **must be projected**, not geodetic (i.e., not
   latitude/longitude).

Rationale:

1. PEM indices rely on **area-consistent spatial calculations**.
2. Equal-area computations are invalid in geographic (degree-based) CRS.
3. The InVEST Habitat Risk Assessment model requires projected inputs.
4. Distance-based and raster-based operations assume metric units.

Recommended practice:

- Use an equal-area projection appropriate for your study region.
- Ensure linear units are in meters.
- Avoid on-the-fly reprojection during analysis.

ROI (Region of Interest) Requirements
--------------------------------------------

The ROI layer (e.g., ``layers.gpkg|roi`` or ``roi.shp`` under risk inputs)
must comply strictly with the bathymetry raster.

Requirements:

1. Identical CRS and projection.
2. Spatial extent fully contained within the bathymetry raster.
3. No geometry outside the raster bounding box.
4. Valid polygon geometry (no self-intersections).

Non-compliance may result in:

- Cropping inconsistencies
- Misaligned rasterization
- InVEST execution errors
- Distorted area calculations

Alignment Verification Checklist
--------------------------------------------

Before running any PEM module, verify:

- ``bathymetry.tif`` is projected (not EPSG:4326 or similar).
- All habitat rasters match its resolution and grid alignment.
- ROI polygon overlays perfectly without reprojection warnings.
- All scenario rasters share identical dimensions and geotransform.

.. tip::

   In QGIS, confirm alignment by checking:

   - Layer CRS properties
   - Raster resolution (pixel size)
   - Extent coordinates
   - On-the-fly reprojection disabled for validation

Failure to enforce spatial coherence at the project initialization stage
is the most common source of downstream analytical errors.

