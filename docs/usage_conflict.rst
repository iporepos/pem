.. _guide-conflict:

Tutorial: Conflict Index
############################################

.. important::

   Before proceeding, make sure your project structure is fully configured.
   See :ref:`Tutorial: Setting Up a PEM Project <guide-project>`.

Overview
=======================================

The Conflict Index quantifies the spatial probability of interaction
conflicts between ocean users within a given scenario.

Unlike the Habitat Risk Index, which integrates ecological exposure,
the Conflict Index focuses exclusively on **user–user spatial overlap**.

Ocean Users may be represented as:

- Boolean footprint rasters (0/1 presence); or
- Continuous fuzzy rasters (values between 0 and 1).

The Conflict Index is computed as:

1. Pairwise raster multiplication between all user combinations;
2. Weighting of each overlap using a conflict matrix;
3. Aggregation of weighted overlaps;
4. Final normalization to a 0–1 scale.

The result is a normalized spatial indicator representing the
relative likelihood of conflict within the scenario.

.. seealso::

    Learn more on the Conflict Index in :ref:`About: Conflict Index <about-conflict-index>`

.. seealso::

   Ensure that Ocean Users have been properly configured before computing
   the Conflict Index. See
   :ref:`Tutorial: Setting Up a PEM Project <guide-project>`
   and :ref:`Populate Ocean Users <guide-project-users>`.

Complete Workflow
=======================================

1. setup_conflict_matrix()

2. (Optional but recommended) Adjust conflict weights

3. get_conflict_index()

Each stage is detailed below.


1. Script: Initialize the Conflict Matrix
==========================================

Before computing spatial conflicts, a conflict weight matrix must be defined.

Run:

.. code-block:: python

    setup_conflict_matrix(folder_project, scenario)

Example:

.. include:: includes/examples/conflict_setup_matrix.rst

What the function does:

- Scans all user rasters under:

  .. code-block:: text

      {project}/inputs/users/{scenario}

- Identifies all user layer names;
- Creates a square CSV matrix;
- Initializes the **lower triangle with value 1**;
- Sets diagonal and upper triangle to 0.

The generated file:

.. code-block:: text

    {project}/inputs/users/{scenario}/conflict.csv

This CSV defines pairwise conflict weights between users.


2. Manual Step: Adjust Conflict Weights
=======================================

By default, all user pairs are assigned weight = 1.

However, in realistic marine spatial planning contexts,
conflict intensity is not uniform across activities.

Examples:

- Offshore wind vs tourism → potentially high conflict
- Fisheries vs conservation zones → context-dependent
- Submarine cables vs shipping lanes → possibly low conflict
- Compatible activities → zero conflict

The user should manually edit ``conflict.csv`` to reflect
domain knowledge, policy priorities, or stakeholder input.

Important notes:

- Only the **lower triangle** is used.
- Diagonal values are ignored.
- Weights typically range from 0 (no conflict)
  to 1 (maximum conflict), but any non-negative
  numeric value is allowed.
- Symmetry is assumed.

Although optional, adjusting weights is **strongly recommended**
to ensure realistic conflict representation.

.. include:: includes/examples/conflict_matrix.rst


3. Script: Generate the Conflict Index
=======================================

Once the matrix is finalized, compute the Conflict Index:

.. code-block:: python

    get_conflict_index(folder_project, scenario)

Example:

.. include:: includes/examples/conflict_get_conflict.rst

Computation Steps
-------------------------------

The function performs:

1. Identification of all unique user raster pairs.
2. Pairwise raster multiplication:
3. Normalization of each pairwise overlap.
4. Weighting using the conflict matrix:
5. Summation of all weighted overlaps.
6. Final normalization of the aggregated map.

Output:

.. code-block:: text

    {project}/outputs/{scenario}/{scenario}_conflict.tif

The output raster:

- Is continuous;
- Is normalized between 0 and 1;
- Represents relative spatial conflict probability;
- Is comparable between scenarios.


Conceptual Interpretation
=======================================

The Conflict Index measures spatial coincidence of activities,
weighted by their incompatibility.

Conceptually:

.. code-block:: text

    User A × User B
    User A × User C
    User B × User C
            ↓
      Apply conflict weights
            ↓
      Sum weighted overlaps
            ↓
        Normalize (0–1)

Important clarification:

The index magnitude is normalized per scenario.
Therefore:

- Absolute values may not be directly comparable across different
  spatial extents or user compositions.
- Spatial patterns and relative intensities are the primary
  interpretation targets.

The Conflict Index can now be integrated into the
multi-criteria Performance Index framework.