.. _about:

About
############################################

The **PEM Project** (*Planejamento Espacial Marinho do Brasil*, or *Marine Spatial Planning for Brazil*)
is a national initiative aimed at developing **spatially explicit guidelines** for the sustainable and
strategic use of the Brazilian marine environment.

This page provides a conceptual overview of the **general workflow**, which forms the core of
the **PEM methodology** and underpins all regional plans, such as the **PEM Sul**.

By following this structured and data-driven workflow, the PEM methodology ensures
**reproducibility**, **transparency**, and **scientific robustness** in the
assessment of marine spatial planning outcomes.

All analytical steps are implemented through **R and Python scripts**,
available in this repository, which can be adapted for different regions and data resolutions.

.. seealso::

   For implementation details see the :ref:`User Guide <usage>`


General Workflow
============================================

The **general workflow** represents the most abstract and reproducible component of the PEM method.
It begins at a **zero level of information**, where only spatial data are available, and transforms these datasets into **spatially explicit indicators** and **decision-support maps**.

Input Data
============================================

At the foundation level, the workflow integrates diverse spatial datasets, including:

* **Bathymetry** – ocean depth and seabed morphology.
* **Habitats** – distribution and characteristics of marine ecosystems.
* **Uses of the ocean** – spatial footprint of human activities across sectors such as fisheries, energy, transportation, and conservation.
* **Coastal hubs** – ports, cities, and infrastructure nodes that influence or depend on marine uses.

These datasets serve as the basis for constructing higher-level spatial information layers.

Management and Planning Units (UPG)
============================================

An important component of the PEM workflow is the creation of **Management and Planning Units (UPG)** —
spatial zones that organize and guide marine management actions.

These units are derived from **input data** such as bathymetry, habitats, and coastal uses,
combined with **expert-defined thresholds** for distance, depth, and sensitivity.
The process groups similar areas into **nested spatial units**, allowing analysis and planning at multiple scales.

UPGs are used to support **decision-making and scenario analysis**, ensuring that management strategies
reflect ecological patterns, human activities, and the connectivity between land and sea.

Spatial Indices
============================================

Through a series of converging analytical processes, the raw data are transformed into
**three key spatial indices**, each representing a different dimension of marine use performance:

1. **Benefit (B)** — quantifies the economic and social **benefit** derived from the use of each spatial unit of the ocean.
2. **Conflict (C)** — expresses the **intensity of overlap** or competition between different marine uses within the same area.
3. **Risk (R)** — captures the **environmental fragility** and **sensitivity** of marine habitats exposed to human activities.

Each of these indices is calculated as a **relative measure**, allowing
comparisons across spatial scales and scenarios of marine use.

Integrated Performance Index
============================================

The core integrative indicator of the PEM framework is the **Marine Use Performance Index**,
or **IDUSE-Mar** (*Índice de Desempenho do Uso de Serviços Ecossistêmicos do Mar*).
This index synthesizes the three dimensions—benefit, risk, and
conflict—into a single expression of marine use performance:

.. math::

    D = \frac{B}{R \times C} \quad \text{where } D \in [0, 1]

Where:

* :math:`D` is the **performance** of marine use;
* :math:`B` is the **benefit**;
* :math:`R` is the **risk**; and
* :math:`C` is the **conflict**.

A higher value of :math:`D` indicates a more sustainable and efficient use of
the marine space—high benefits with relatively low risk and conflict.

Benefit Index
---------------------------------------------

The **benefit index** is derived from the spatialized intensity and value of marine uses.
It aggregates sectoral information into a normalized economic density indicator:

.. math::

    B = \sum_{j = 1}^{N} \mathcal{B}(U_j) \quad U \in \mathbb{U}

Where :math:`U_j` represents each use sector :math:`j`.

For each municipality :math:`i` and time step :math:`t`, the benefit is
computed as a function of local value and activity:

.. math::

    B_{i, j, t} = f(V_{i, t}, U_{j, t}), \quad B \in [0, 1]

Each sectoral benefit :math:`B_j` is normalized such that:

.. math::

    \sum_{i = 1}^{N} B_i = 1


Risk Index
---------------------------------------------

**Risk (R)** — follows the conceptual structure of the *InVEST Habitat Risk* model,
estimating the likelihood of impact based on exposure, consequence, and habitat sensitivity.

Conflict Index
---------------------------------------------

**Conflict (C)** — measures spatial incompatibility or overlap between uses,
reflecting competition for marine space or interference between activities.

Scenario-Based Analyses
---------------------------------------------

All indices (:math:`B`, :math:`R`, and :math:`C`) are computed for specific **use scenarios**.
Scenarios may represent current conditions, projected developments, or management
alternatives, allowing the **IDUSE-Mar** to serve as a comparative tool
for evaluating policy or spatial planning options.


