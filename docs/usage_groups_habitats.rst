.. _usage-groups-habitats:

Tutorial: Defining Ocean Habitat Groups
#######################################

Ocean Habitat grouping defines how benthic and pelagic habitat polygons
are aggregated into broader thematic habitat classes.

This grouping system applies **only to Ocean Habitats**.
Ocean Users use a different grouping structure.

Habitat grouping is optional.
If no grouping is defined, each habitat category is processed individually.

.. seealso::

   Learn how to user groups in the scripts in
   :ref:`Tutorial: Defining Ocean Users Groups <usage-groups-users>`.

Concept
=======

Habitat inputs are polygon layers stored in ``vectors.gpkg``:

- ``habitats_benthic``
- ``habitats_pelagic``

Each polygon contains a categorical field (e.g., habitat code).

Grouping allows users to:

- Merge multiple habitat codes into broader ecological classes
- Reduce model complexity
- Align categories with assessment needs

Grouping Structure
==================

Habitat grouping is defined by:

1. The categorical field name
2. A list of grouping definitions (per habitat type)
3. A master ``groups`` dictionary

Example structure:

.. code-block:: python

    field = "code"

    group_benthic = [
        {"name": "sandy_bottoms", "values": ["MB3", "MC3"]},
        {"name": "muddy_bottoms", "values": ["MB4", "MB5", "MB6"]},
        {"name": "mixed_sediments", "values": ["MC4", "MC5", "MC6"]},
        {"name": "deep_mud", "values": ["MD3"]},
        {"name": "consolidated_mud", "values": ["MD4", "MD5", "MD6"]},
        {"name": "biogenic_reef", "values": ["ME1"]},
        {"name": "rocky_reef", "values": ["ME4", "MF4", "MF5"]},
        {"name": "hard_substrate", "values": ["MG4", "MG6"]},
    ]

    group_pelagic = None  # no grouping applied

    groups = {
        "benthic": group_benthic,
        "pelagic": group_pelagic,
    }

Group Definition
================

Each group entry is a dictionary with two required keys:

``name`` (str)
    Name of the aggregated habitat class.

``values`` (list[str])
    List of categorical values from the habitat field that
    will be merged into this group.

Example:

.. code-block:: python

    {"name": "sandy_bottoms", "values": ["MB3", "MC3"]}

No Grouping
===========

If a habitat type is set to ``None``:

.. code-block:: python

    group_pelagic = None

Then:

- No aggregation is performed
- Each unique category in the habitat field is treated as an independent class

Important Rules
===============

- ``habitats_benthic`` and ``habitats_pelagic`` must exist in ``vectors.gpkg``.
- The specified ``field`` must exist in both layers.
- Each categorical value should appear in only one group.
- If a value is not included in any group, it remains ungrouped.

Workflow Summary
================

1. Ensure ``habitats_benthic`` and/or ``habitats_pelagic`` exist.
2. Define the categorical habitat field.
3. Create grouping lists (or set to ``None``).
4. Register them in the ``groups`` dictionary.
5. Run ``setup_habitats``.

When to Group
=============

Grouping is recommended when:

- Habitat codes are highly detailed.
- Ecological interpretation requires broader classes.
- Model simplification improves interpretability.

If detailed habitat resolution is required, grouping can be omitted.