
.. _guide-project:

Tutorial: Setting Up a PEM Project
############################################

.. _guide-project-overview:

Overview of a PEM Project
==========================

As introduced :ref:`earlier <usage-pem-project>`, a PEM Project must adhere to a
well-defined and standardized file system structure. The framework assumes a
deterministic file system organization so that scripts can systematically
discover, read, merge, and write datasets without manual intervention.

The typical project workflow is:

1. Create the file system exactly as specified :ref:`here <usage-pem-project-folders>`.
2. Populate the input directories with the required raster and vector layers for each scenario.
3. Compute the **Habitat Risk Index** for the defined scenarios.
4. Compute the **Conflict Index** for the defined scenarios.
5. Compute the **Benefit Index** for the defined scenarios.
6. Compute the **Performance Index**, integrating the previous indices.

Each stage can be executed using automated or semi-automated routines provided
by the PEM scripts, ensuring reproducibility, traceability, and consistency
across scenarios.

.. include:: includes/project_layout.rst

.. _guide-project-setup:

1. Run Script: Setup the File System
=======================================

The PEM directory structure can be generated programmatically using the
``setup_folders()`` function available in the ``project.py`` module, as
shown below.

This procedure ensures that the project complies exactly with the required
hierarchical layout expected by the framework.

To execute the setup, the user must provide:

- The absolute path to the ``project.py`` module;
- The absolute path to a base directory where the project folder will be created;
- The project name;
- An optional list of scenario names.

.. note::

    The ``baseline`` scenario is always generated, regardless of whether
    it is explicitly included in the scenarios list.

.. include:: includes/examples/project_setup_project.rst

.. _guide-project-bathymetry:

2. Manually Populate Bathymetry
=======================================

The file ``bathymetry.tif`` is the canonical raster of the PEM Project.
It defines the reference grid, resolution, extent, and projected CRS used
throughout all spatial computations.

The user must place the file at:

.. code-block:: text

    {project}/inputs/bathymetry.tif



.. _guide-project-roi:

3. Populate ROI
=======================================

The ROI (Region of Interest) is a polygon vector layer delimiting the
analysis domain.

.. _guide-project-roi-manul:

Manual Input
-------------------------------

The user must provide the ROI layer at:

.. code-block:: text

    {project}/inputs/vectors.gpkg|roi

It is recommended that the ROI uses the same projected CRS as
``bathymetry.tif``. If necessary, reprojection can be handled automatically
by the framework.

.. _guide-project-roi-setup:

Script: Setup ROI
-------------------------------

.. todo develop

.. include:: includes/ipsum.rst

.. include:: includes/examples/project_setup_roi.rst

.. _guide-project-habitats:

4. Populate Ocean Habitats
=======================================

Ocean benthic and pelagic habitat maps are required for the Habitat Risk Index
assessment and for the delineation of biophysically grounded Management Units.

During processing, habitat layers are rasterized onto the canonical grid and
encoded as a categorical (qualitative) raster, where each cell represents a
specific habitat group identifier.

.. _guide-project-habitats-manual:

Manual Input
-------------------------------

Habitats are polygon vector layers classified into:

.. code-block:: text

    {project}/inputs/vectors.gpkg|habitat_benthic
    {project}/inputs/vectors.gpkg|habitat_pelagic

These layers are later rasterized onto the canonical grid defined by
``bathymetry.tif``.

Technical recommendations:

- No overlapping polygons within the same layer.
- A unique identifier (ID or code) per habitat class.
- Prefer single-part geometries (avoid multipart features when possible).

Habitat thematic detail is user-defined. The PEM framework allows
aggregation into broader habitat groups at a later stage (e.g., grouping
multiple mud-related classes into a single “mud” category).

.. _guide-project-habitats-setup:

Script: Setup Habitats
-------------------------------

.. todo develop

.. include:: includes/ipsum.rst

.. include:: includes/examples/project_setup_habitats.rst

.. _guide-project-users:

5. Populate Ocean Users
=======================================

Ocean Users represent spatially explicit human activities within the marine
domain. Activities may overlap spatially both within the same economic sector
and across different sectors.

For each scenario, user layers are ultimately transformed into a continuous
intensity quantitative raster, representing the relative magnitude or footprint of
each activity across the ocean space.

.. _guide-project-users-over:

Ocean User Mapping Overview
-------------------------------

Multiple layers geometries and formats may spatially represent a Ocean User
economic sector across multiple scenarios.

Examples:

- Offshore wind: turbines (points) and cable corridors (lines).
- Fisheries: polygon zones and rasterized intensity maps.
- Oil extraction: distinct layers for baseline and future expansion scenarios.

Therefore, the user may populate these different data sources accordingly.

.. seealso::

   Learn how to setup layer groups in the scripts in
   :ref:`Tutorial: Defining Ocean Users Groups <usage-groups-users>`.



.. _guide-project-users-vector:

Manual Input: vector layers
-------------------------------

Vector users may be points, lines, or polygons. Layers may include
numeric attributes representing intensity, density, or effort
(e.g., ``intensity``, ``density``).

The user must populate in the ``vectors.gpkg`` database, like:

.. code-block:: text

    {project}/inputs/vectors.gpkg|ocean_user_a_baseline
    {project}/inputs/vectors.gpkg|ocean_user_a_utopia
    {project}/inputs/vectors.gpkg|ocean_user_b

Recommendations:

- Ensure the spatial extent is equal to or larger than the canonical raster.
- Avoid using hyphens, blank space or any non-ASCII characters in layer naming
- Maintain consistent attribute naming for quantitative fields.



.. _guide-project-users-raster:

Manual Input: Raster Layers
-------------------------------

Raster layers for ocean users may represent:

- Boolean footprint layers; or
- Continuous scalar fields (e.g., intensity, density, heat maps).

The user must place raster sources under:

.. code-block:: text

    {project}/inputs/_sources/ocean_user_c
    {project}/inputs/_sources/ocean_user_d

Recommendations:

- Ensure the spatial extent is equal to or larger than the canonical raster.
- Maintain consistent resolution when possible (resampling is handled during reprojection).



.. _guide-project-users-setup:

Script: Setup Ocean Users
-------------------------------

.. todo develop

.. include:: includes/ipsum.rst

.. include:: includes/examples/project_setup_users.rst
