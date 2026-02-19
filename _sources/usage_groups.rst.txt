
.. _usage-groups:

.. include:: ./includes/warning_dev.rst

Tutorial: Defining Model Layer Groups
############################################

.. _usage-groups-overview:

Overview to Layer Groups
========================

Defining *layer groups* is a core mechanism in the Python API of the PEM framework.
Layer groups are the standardized interface used to feed spatial layers into the framework
Python functions.

Most high-level functions operate by:

- Collecting layers from one or more groups
- Rasterizing vectors when necessary
- Normalizing raster values to a 0–1 range
- Applying global weight factors
- Merging layers into composite outputs

Layer Groups exist to streamline complex spatial workflows. A model may
combine:

- Multiple vector layers
- Multiple raster layers
- Only vectors
- Only rasters
- Or both

Additionally, layers often require:

- A **weight factor** (global multiplier)
- A **field attribute** for rasterization (when learning from vectors)

Instead of redefining input logic for every function, the group
structure centralizes these parameters. This ensures consistency,
modularity, and predictable behavior across the entire modeling
pipeline.

Because this structure is used throughout the system, correct group
definition is essential for stable and reproducible results.

.. _usage-groups-conceptual:

Conceptual Structure
====================

At the highest level, the inputs are defined as:

1. Individual layer definitions (vector or raster)
2. Layer groups (thematic collections)
3. A master ``groups`` Python Dictionary

The final dictionary structure looks like:

.. code-block:: python

    groups = {
        "group_name": group_definition,
        ...
    }

.. _usage-groups-definition:

1. Defining a Group
===================

Each group is a Python Dictionary with up to two keys:

- ``"vectors"`` → Python List of vector layer definitions
- ``"rasters"`` → Python List of raster layer definitions

Example:

.. code-block:: python

    group_fisheries = {
        "vectors": [...],
        "rasters": [...],
    }

The ``"vectors"`` and ``"rasters"`` keys are optional.
A group may contain only vectors or only rasters.

.. _usage-groups-vector:

2. Vector Layer Group
==========================

Each vector layer must be defined as a Dictionary inside the
``"vectors"`` List.

All layers are expected to be sourced from the ``vectors.gpkg`` file in the
PEM Project.

Mandatory Keys
--------------

``name`` (str)
    Name of the vector layer inside the geopackage.

Optional Keys
-------------

``field`` (str or None)
    Attribute field used for rasterization.

    - If ``None``, a constant value of ``1`` is burned.
    - If not defined, defaults to ``None``

``weight`` (float or None)
    Global weight multiplier for this layer.

    - If ``None``, defaults to ``1``.
    - If not defined, defaults to ``None``

Full Example
------------

.. code-block:: python

    {
        "name": "fisheries_01",
        "field": "intensity",
        "weight": 1,
    }

Minimal Example
---------------

.. code-block:: python

    {
        "name": "fisheries_02",
        "field": "intensity",
    }

If optional keys are omitted, the system assigns defaults automatically.

.. _usage-groups-raster:

3. Raster Layer Group
==========================

Raster layers are defined inside the ``"rasters"`` List.

They can represent:

- Boolean layers (presence/absence, footprints)
- Scalar layers (density, intensity, probability, etc.)

All raster values are normalized to the 0–1 range during merging.

All rasters are expected to be sourced from the ``_inputs`` folder under the
PEM Project. Subfolder may vary depending on the processing routine.

Mandatory Keys
--------------

``name`` (str)
    Filename of the raster.

Optional Keys
-------------

``weight`` (float or None)
    Global weight multiplier.

    - If ``None``, defaults to ``1``.
    - If not defined, defaults to ``None``

Example
-------

.. code-block:: python

    {
        "name": "fish_industry_footprints.tif",
        "weight": 3,
    }


.. _usage-groups-example:

4. Complete Example: Fisheries Group
=====================================

.. code-block:: python

    group_fisheries = {

        "vectors": [

            {
                "name": "fisheries_01",
                "weight": 2,
            },

            {
                "name": "fisheries_02",
                "field": "intensity",
            },

        ],

        "rasters": [

            {
                "name": "fish_industry_footprints.tif",
                "weight": 3,
            },

            {
                "name": "fish_industry_density.tif",
                "weight": 4,
            },

        ],
    }


.. _usage-groups-example2:

5. Another Example: Windfarms Group
====================================

Groups do not need both vectors and rasters.

.. code-block:: python

    group_windfarms = {
        "vectors": [
            {
                "name": "windfarms",
                "field": None,
                "weight": 3,
            },
        ],
    }

.. _usage-groups-registering:

6. Registering All Groups
==========================

After defining individual groups, register them in the master
``groups`` Dictionary.

.. code-block:: python

    groups = {
        "fisheries": group_fisheries,
        "windfarms": group_windfarms,
    }

The key (e.g., ``"fisheries"``) becomes the group identifier used
throughout the model.

.. _usage-groups-defaults:

7. Default Behavior Summary
============================

If a key is missing or set to ``None``:

+----------------+-------------------------------+
| Parameter      | Default Behavior              |
+================+===============================+
| ``field``      | Burns constant value = 1      |
+----------------+-------------------------------+
| ``weight``     | Assumes weight = 1            |
+----------------+-------------------------------+
| ``rasters``    | No raster layers processed    |
+----------------+-------------------------------+
| ``vectors``    | No vector layers processed    |
+----------------+-------------------------------+


.. warning::

    If both ``rasters`` or ``vectors`` are missing or empty, then
    an error is raised.


.. _usage-groups-recommend:

8. Recommended Best Practices
==============================

- Always define ``name`` explicitly.
- Use weights consistently across groups.
- Keep thematic logic separated by group.

.. _usage-groups-workflow:

9. Typical Workflow
===================

1. Define vector and raster layers.
2. Organize them into thematic groups.
3. Register groups in the master Dictionary.
4. Pass ``groups`` to the model parser.

