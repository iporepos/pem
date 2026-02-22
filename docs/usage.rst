.. _usage:

User Guide
############################################

This guide describes how to install, configure, and use the **PEM framework**
from source. The framework is organized as a collection of standalone Python
modules, each targeting a specific analytical component.

.. toctree::
   :maxdepth: 1

   Home <self>
   usage_project
   usage_groups_habitats
   usage_groups_users
   usage_risk
   usage_conflict

.. seealso::

   If you intend to extend or modify the framework, refer to
   :ref:`Development <development>`.

.. _usage-installation:

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


.. _usage-install-qgis:

Install PyQGIS
--------------------------------------------

All Python scripts are designed to run within the **QGIS Python environment**
(PyQGIS). Therefore, installing QGIS is a mandatory prerequisite.

1. Download QGIS from the official website:
   https://qgis.org/download

2. During installation, ensure that the bundled Python environment is included.

3. During installation, ensure ``numpy``, ``pandas`` and ``geopandas`` Python packages are included.

.. warning::

    The ``geopandas`` Python package is not included as default for most QGIS versions.

.. tip::

    For Windows users, installing QGIS via the OSGeo4W system is recommended. This allows the user
    to select all Python packages needed.


.. _usage-install-invest:

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


.. _usage-run-scripts:

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


.. _usage-run-scripts-python:

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

.. seealso::

   For PyQGIS scripting details, consult the
   `PyQGIS Developer Cookbook <https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/index.html>`_.


.. dropdown:: Example: loading functions from the modules
    :icon: code-square
    :open:

    The following template demonstrates how to dynamically load the module ``project.py``
    and execute one of its functions

    .. include:: includes/examples/project_setup_roi.rst

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


.. _usage-pem-project:

PEM Project
============================================

The PEM framework may be deployed by the user under the concept
of a **PEM Project**.

.. _usage-pem-project-folders:

File System Structure
--------------------------------------------

A file-based PEM Project can follow a standardized file system schema to ensure
reproducibility, scenario management, and compatibility with all framework
modules.

The structure below represents the recommended layout for a complete project.

.. include:: includes/project_layout.rst

.. important::

   Adherence to this directory structure is not mandatory but is strongly recommended.
   The rationale of the PEM framework relies on this layout.

.. _usage-pem-project-design:

Design Principles
--------------------------------------------

The PEM Project presented above has some core design principles.

**1. Scenario Isolation**

Each scenario (e.g., ``baseline``, ``ssp1``) maintains:

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

.. _usage-spatial:

Spatial Reference
============================================

The PEM framework is architected around a **canonical/reference raster**:
the **bathymetry** layer:

.. code-block:: text

    {project}/inputs/bathymetry.tif

This reference raster defines the spatial standard for the entire project and is a template for:

- Coordinate Reference System (CRS)
- Projection
- Spatial resolution
- Grid alignment
- Spatial extent (bounding box)

.. important::

   The bathymetry raster **must be projected**, not geodetic (i.e., not
   latitude/longitude).

   This is because equal-area computations are invalid in geographic (degree-based) CRS.
   Also, the InVEST Habitat Risk Assessment model requires projected inputs.

.. tip::

   For the Brazilian ocean space, the projected Coordinate Reference System (CRS)
   we strongly recommend is `SIRGAS 2000 / Brazil Polyconic [EPSG 5880] <https://epsg.io/5880>`_.


.. _usage-tutorials:

Tutorials
============================================

This section provides step-by-step guides for configuring and operating the PEM workflow,
from initial project setup to advanced model structuring and automation tasks.

.. seealso::

   Learn how to setup a PEM Project in
   :ref:`Tutorial: Setting Up a PEM Project <guide-project>`.

.. seealso::

   Learn how to setup habitat groups in the scripts in
   :ref:`Tutorial: Defining Ocean Habitat Groups <usage-groups-habitats>`.

.. seealso::

   Learn how to user groups in the scripts in
   :ref:`Tutorial: Defining Ocean Users Groups <usage-groups-users>`.

.. seealso::

   Learn how to derive the Habitat Risk Index in
   :ref:`Tutorial: Habitat Risk Index <guide-risk>`.

.. seealso::

   Learn how to derive the Conflict Index in
   :ref:`Tutorial: Conflict Index <guide-conflict>`.

.. add more as needed