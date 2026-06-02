.. _guide-benefit:

Tutorial: Benefit Index
############################################

.. important::

   Before proceeding, make sure your project structure is fully configured.
   See :ref:`Tutorial: Setting Up a PEM Project <guide-project>`.

Overview
=======================================

This tutorial walks you through calculating and mapping the **Benefit Index** using the
PEM automated engine. The Python ``benefit`` module bridges offshore marine activities
with onshore economic impacts. It loops over your active ocean spatial footprint, scales
relative user intensities using socio-economic totals retrieved from coastal hubs, and exports
both sector-specific and normalized cumulative benefit surfaces.

.. seealso::

    For a deep dive into the theoretical framework, see :ref:`About: Benefit Index <about-benefit-index>`.

.. seealso::

   Ensure that Ocean Users have been properly configured before computing
   the Benefit Index. See :ref:`Tutorial: Setting Up a PEM Project <guide-project>`
   and :ref:`Populate Ocean Users <guide-project-users>`.

Complete Workflow
=======================================

Calculating the Benefit Index consists of two primary phases:

1. **Manual Entry:** Populating the semicolon-separated ``benefit_users.csv`` database.
2. **Execution:** Running the Python script via ``get_benefit_index()``.

Each stage is detailed below.

1. Manual Step: Populate the Benefit Database
=========================================================

The Benefit Engine requires a structured CSV file located exactly at
``/inputs/benefit/benefit_users.csv``. This file associates total economic value
to specific coastal hubs (e.g., ports, processing centers, or municipalities)
per scenario and sector.

.. warning::
   **Delimiter Requirement:** The underlying parser reads this database using a
   **semicolon (`;`)** separator and ``utf-8`` encoding. Ensure your export configuration
   reflects this.

The database must include the following structural columns:

* ``scenario``: The exact case-sensitive scenario identifier (e.g., ``baseline``).
* ``user``: The sector's unique code. This **must match exactly** the root filename of the corresponding spatial raster map.
* ``hub``: The unique name or ID of the onshore destination node.

All additional columns represent the explicit economic metrics you wish to analyze.
Ensure these attributes use standard alphanumeric ASCII characters without spaces.

Example layout:

.. code-block:: text

    scenario;user;hub;jobs_number
    baseline;cargo;city_A;1000
    baseline;cargo;city_B;1200
    baseline;cargo;city_C;5000
    baseline;oil;city_A;500
    baseline;oil;city_B;200
    baseline;tourism;city_D;56000

2. Script: Generate the Benefit Index
=========================================================

Once your database is formatted and placed within the inputs folder, you can run the
spatial scaling pipeline using the following Python interface:

.. code-block:: python

    from pem import benefit

    benefit.get_benefit_index(
        folder_project="/path/to/project",
        scenario="baseline",
        attribute="jobs_number"
    )

Example:

.. include:: includes/examples/benefit_get_benefit.rst

Computation Steps
-------------------------------

When executing ``get_benefit_index()``, the engine runs through the following automated pipeline:

1. **Environment and Variable Check:**
   The function queries the core project directory to locate reference infrastructure,
   including ``inputs/vectors.gpkg`` and ``inputs/bathymetry.tif``. It extracts matching CRS and resolution limits.
2. **Spatial File Selection:**
   The engine scans ``inputs/users/{scenario}/*.tif`` to read user maps.

   .. important::
      **Naming Rule:** Files containing an underscore (``_``) in their name are explicitly skipped by the data loader. Only pure user root rasters (e.g., ``cargo.tif``) are compiled.

3. **Pixel Summation & Querying:**
   For each valid user raster, pixels are loaded into memory as a Float32 NumPy array. The total global intensity is summed:

   .. math::
       U = \sum U_{i,j}

   Simultaneously, the script executes a internal Pandas query against your database to fetch the total attribute value for that sector:

   .. code-block:: python

       df.query("scenario == 'baseline'").query("user == 'cargo'")['jobs_number'].sum()

4. **Linear Scaling:**
   The engine evaluates the scaling constant :math:`c = B / U`, translates the spatial grid cell array into localized benefit densities (:math:`b\_map = c \cdot u\_map`), and outputs individual rasters containing a ``-99999`` NoData fallback value.
5. **Summation & Fuzzification:**
   Individual sector surfaces are added to a cumulative matrix. The engine then utilizes QGIS native algorithm mapping components (``native:fuzzifyrasterlinearmembership``) to scale the cumulative results to a clean, final 0 to 1 range.

Generated Project Outputs
=======================================

Running the routine populates your scenario output directories with both
intermediate matrix calculations and final report products:

.. code-block:: text

    outputs/{scenario}/
    ├── {scenario}_benefit.tif            <-- The final, normalized (0-1) cumulative Benefit Index map.
    ├── {scenario}_benefit_users.csv       <-- Summary log containing compiled total benefits per sector.
    └── intermediate/benefit/
        ├── benefit_cargo.tif              <-- Raw absolute scaled benefit density for the cargo sector.
        ├── benefit_oil.tif                <-- Raw absolute scaled benefit density for the oil sector.
        └── benefit_wsum.tif               <-- Un-normalized cumulative absolute total benefit array.

Conceptual Interpretation
=======================================

When validating your generated output maps, notice these
design constraints built into the code:

* **Spatial Dominance:** The framework treats the spatial users map as the absolute source of truth. If a sector has entries inside the ``benefit_users.csv`` file but missing or invalid spatial rasters inside the user directory, it will be skipped from final index compilation.
* **Pixel Meaning:** While the raw intermediate maps match your specific metrics exactly (e.g., representing the localized portion of physical jobs or revenue attributed to that cell), the final top-level raster layer represents a relative scale.
* **Hotspots:** Pixels approaching ``1.0`` indicate spatial engines—focal geographic points in the ocean where either a single hyper-productive industry exists or where multiple distinct sectors overlap to create significant cumulative wealth for coastal hubs.