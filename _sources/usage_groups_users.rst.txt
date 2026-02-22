.. _usage-groups-users:

Tutorial: Defining Ocean User Groups
####################################

Ocean User groups define how human-use layers are provided to the PEM model.

This grouping system applies **only to Ocean Users**.
Ocean Habitats use a different grouping structure.

Each group represents one thematic activity (e.g., fisheries, windfarms)
and may contain vector and/or raster layers.

.. seealso::

   Learn how to setup habitat groups in the scripts in
   :ref:`Tutorial: Defining Ocean Habitat Groups <usage-groups-habitats>`.

Concept
=======

Ocean User inputs are structured in three levels:

1. Individual layer definitions
2. Thematic groups
3. A master ``groups`` dictionary

Final structure:

.. code-block:: python

    groups = {
        "group_name": group_definition,
        # ... other groups
    }



Group Structure
===============

Each group is a Python dictionary with up to two optional keys:

- ``"vectors"`` → list of vector layer definitions
- ``"rasters"`` → list of raster layer definitions

Example:

.. code-block:: python

    group_fisheries = {
        "vectors": [...],
        "rasters": [...],
    }

A group may contain only vectors or only rasters.
If both are missing or empty, an error is raised.

Vector Layer Definition
=======================

Vector layers must exist inside ``vectors.gpkg``.
Each vector is defined as:

.. code-block:: python

    {
        "name": "layer_name",      # required
        "field": "attribute",      # optional
        "weight": 1.0,             # optional
    }

Parameters
----------

``name`` (str)
    Layer name inside ``vectors.gpkg``. (required)

``field`` (str or None)
    Attribute used for rasterization.
    - If ``None`` or omitted → constant value ``1`` is burned.

``weight`` (float or None)
    Global multiplier applied after normalization.
    - If ``None`` or omitted → defaults to ``1``.

Example:

.. code-block:: python

    {
        "name": "fisheries_02",
        "field": "intensity",
        "weight": 2
    }


Raster Layer Definition
=======================

Raster files must be located in the project ``inputs/_sources`` directory.
Each raster is defined as:

.. code-block:: python

    {
        "name": "filename.tif",    # required
        "weight": 1.0,             # optional
    }

Parameters
----------

``name`` (str)
    Raster filename. (required)

``weight`` (float or None)
    Global multiplier.
    - If ``None`` or omitted → defaults to ``1``.

All rasters are normalized to the 0–1 range before merging.


Complete Example
================

.. code-block:: python

    group_fisheries = {

        "vectors": [
            {"name": "fisheries_01", "weight": 2},
            {"name": "fisheries_02", "field": "intensity"},
        ],

        "rasters": [
            {"name": "fish_industry_footprints.tif", "weight": 3},
            {"name": "fish_industry_density.tif", "weight": 4},
        ],
    }

    group_windfarms = {

        "vectors": [
            {"name": "lines", "field": None, "weight": 2},
            {"name": "turbines", "field": "intensity", "weight": 1},
        ],

    }

Registering groups:

.. code-block:: python

    groups = {
        "fisheries": group_fisheries,
        "windfarms": group_windfarms,
    }

The dictionary key (e.g., ``"fisheries"``) is the group identifier used by the model.

Workflow Summary
================

1. Define vector and raster layers.
2. Organize them into thematic Ocean User groups.
3. Register groups in ``groups`` dictionary.
4. Pass ``groups`` to the model parser.