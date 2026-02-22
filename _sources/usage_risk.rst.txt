.. _guide-risk:

Tutorial: Habitat Risk Index
############################################

.. seealso::

   Before proceeding, make sure your project structure is fully configured.
   See :ref:`Tutorial: Setting Up a PEM Project <guide-project>`.


Overview
=======================================

The Habitat Risk Index (R) quantifies cumulative ecological risk by
combining spatial habitat distributions with ocean user pressures.

The PEM framework integrates with the `Habitat Risk Assessment model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_ (HRA),
developed by the InVEST initiative.
PEM does **not** reimplement the HRA algorithm. Instead, it:

1. Automatically prepares all required configuration files.
2. Delegates ecological risk computation to InVEST.
3. Post-processes and normalizes the resulting rasters into a
   single, scenario-ready Habitat Risk Index.

The workflow therefore combines automated scripting with a manual
InVEST execution step to ensure methodological transparency.

Complete Workflow
=======================================

The Habitat Risk pipeline follows three stages:

1. run ``setup_hra_model()`` function from ``risk.py`` module

2. Run InVEST HRA (benthic and pelagic)

3. ``get_risk_index()`` function from ``risk.py`` module

Each stage is described below. Conceptually:

.. code-block:: text

    Habitats + Ocean Users
            ↓
    setup_hra_model()
            ↓
    InVEST HRA (benthic + pelagic)
            ↓
    get_risk_index()
            ↓
    Normalized Habitat Risk Index

This design ensures:

- Methodological robustness (InVEST ecological framework);
- Structural reproducibility (PEM file system standardization);
- Quantitative comparability across scenarios (normalization).


1. Script: Setup HRA Model
=======================================

The function ``setup_hra_model()`` initializes the full configuration
environment required by the InVEST Habitat Risk Assessment model.

Function signature:

.. code-block:: python

    setup_hra_model(folder_project, scenario)


Example:

.. include:: includes/examples/risk_setup_hra.rst

This function:

- Generates habitat–stressor interaction tables;
- Creates scoring tables;
- Prepares stressor lists derived from Ocean Users;
- Builds the JSON configuration file required by InVEST;
- Organizes all files under the scenario directory.

It does **not** execute the HRA model itself.

2. Manual Step: Edit Scores Table
==================================================

The user must edit the generated score files both for
benthic and pelagic habitat:

.. code-block:: text

   {project}/inputs/risk/{scenario}/benthic_scores.csv
   {project}/inputs/risk/{scenario}/pelagic_scores.csv

This includes, Rating, Data Quality and Weight values.
Details about these parameters are presented in the
`Habitat Risk Assessment model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_
documentation.

3. Manual Step: Run InVEST Habitat Risk Assessment
==================================================

After running ``setup_hra_model()`` and editing the score tables,
the user must manually execute the Habitat Risk Assessment
model within the InVEST Workbench. Two independent runs are required:

- One for **benthic habitats**
- One for **pelagic habitats**

For each run:

1. Open InVEST Workbench.
2. Load the generated JSON configuration file.
3. Verify workspace and file paths.
4. Execute the model.
5. Locate the resulting risk raster output.

At the end of this stage, you must obtain:

- A benthic HRA raster
- A pelagic HRA raster

These rasters will be merged and normalized in the next step.


4. Script: Generate the Normalized Habitat Risk Index
======================================================

The final Habitat Risk Index is computed using:

.. code-block:: python

    get_risk_index(
        folder_project,
        scenario,
        hra_benthic,
        hra_pelagic
    )

Example:

.. include:: includes/examples/risk_get_risk.rst

The function performs:

1. Reprojection and resampling of both rasters to the canonical grid
   defined by ``bathymetry.tif``.
2. Spatial alignment (extent and resolution harmonization).
3. Raster summation (benthic + pelagic).
4. Min–max normalization of the combined layer.
5. Export of the final normalized raster:

.. code-block:: text

   {project}/outputs/{scenario}/{scenario}_risk.tif

