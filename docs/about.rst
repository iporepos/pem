.. _about:

About
############################################

.. toctree::
   :maxdepth: 1

   Home <self>
   about_upg
   about_benefit_index
   about_risk_index
   about_conflict_index
   about_performance_index


The **PEM Project** (*Planejamento Espacial Marinho do Brasil*, or *Marine Spatial Planning for Brazil*)
is a national initiative aimed at developing **spatially explicit guidelines** for the sustainable and
strategic use of the Brazilian marine environment.

This page provides a conceptual overview of the **general workflow**, which forms the core of
the PEM methodology and underpins all regional plans.

By following this structured and data-driven workflow, the PEM framework ensures
**reproducibility**, **transparency**, and **scientific robustness** in the
assessment of marine spatial planning outcomes.

All analytical steps are implemented through **R and Python scripts**,
available in this repository, which can be adapted for different regions and data resolutions.

.. seealso::

   For implementation details see the :ref:`User Guide <usage>`

.. _about_workflow:

PEM framework
============================================

The **PEM framework** represents the most abstract and reproducible component of the PEM method.

It begins at a **zero level of information**, where only spatial data are available, and
transforms these datasets into **spatially explicit indicators** and **decision-support maps**.

.. _about_input_data:

Input Data
============================================

At the foundation level, the workflow integrates diverse spatial datasets, including:

* **Bathymetry** – ocean depth and seabed morphology.
* **Habitats** – distribution and characteristics of marine environments that provide ecosystem services.
* **Users** – spatial footprint or intensity of human activities in the ocean across sectors such as fisheries, energy and transportation.
* **Land Hubs** – ports, cities, and infrastructure nodes in land that receives direct economic benefits from activities in the ocean.
* **Coastal features** - other important geographical features of the coastline that influence the definition of management units.

These datasets serve as the basis for constructing higher-level spatial information layers.

.. _about_model:

The Spatial Model
============================================

PEM framework use a spatial model that allows comprehensive decision-making.

This model represents the ocean space and adjacent land as a two-dimensional
surface divided into model cells. Each model cell describes the spatial
unit of analysis, allowing the integration of land,
coastline, and marine environments within the same planning structure.

.. tab-set::

    .. tab-item:: English

        .. figure:: figs/model.jpg
            :name: fig-spatial-model
            :width: 100%
            :align: center

            Conceptual representation of the spatial model in the PEM framework.
            The ocean and land areas are divided into a spatial grid, where land hubs,
            habitats, and users interact to generate benefit, risk, and conflict metrics
            that support integrated performance assessment and scenario simulation.

    .. tab-item:: Português

        .. figure:: figs/model_pt.jpg
            :name: fig-spatial-model-pt
            :width: 100%
            :align: center

            Representação conceitual do modelo espacial no arcabouço PEM.
            As áreas oceânicas e terrestres são divididas em uma grade espacial,
            onde os Hubs costeiros, Habitats e usuários interagem para gerar métricas
            de benefício, risco e conflito que apoiam avaliação integrada
            de desempenho e simulação de cenários.


Within this space, several spatial features are represented: **Land Hubs** such
as ports and coastal cities; **Habitats**, which are sources of ecosystem
services and may be sensitive to disturbance; and ocean **Users**, representing the
various economic sectors that occupy and use ecosystem services.

These elements coexist and interact across the ocean space grid, forming the physical and
functional components of the system.

The dynamic interaction among these components gives rise to three key
dimensions of spatial performance: **Benefit**, **Risk**, and **Conflict**.

Benefits flow from users through the use of ecosystem services and connect back
to land hubs. Risks emerge where users overlap with sensitive habitats, and
conflicts arise where different users compete for the same space.

Together, these dimensions define the integrative structure of the PEM framework, which
supports both diagnostic evaluation and scenario-based simulation of marine use
performance.

Scenario-Based Analyses
============================================

All spatial indexes (:math:`B`, :math:`R`, and :math:`C`) are computed for specific
use **Scenarios** of the ocean space.

Scenarios may represent current conditions, projected developments, or management
alternatives, allowing :math:`D` to serve as a comparative tool
for evaluating policy or spatial planning options.

Examples of a typical scenario setting in the PEM framework:

1. ``baseline`` scenario, representing the observed conditions until the present moment.
2. ``business-as-usual`` scenario, representing the projected future if no extra management or planning if taken.
3. ``eco-development`` scenario, representing a simulated future where biodiversity conservation heavily is enforced.


.. _about_upg:

Management Units
============================================

An important component of the PEM framework is the definition of
**Management Units**, denoted as UPG — spatial zones that organize
and guide marine management actions.

.. seealso::

   Check out more information about the definition of :ref:`Management Units <about-upg>`

.. _about_indexes:


Use Performance Index
============================================

The core integrative indicator of the PEM framework is the
**Marine Ecosystem Services Use Performance Index** (IDUSE-Mar),
which synthesizes the three component dimensions —
**Benefit** (:math:`B`), **Habitat Risk** (:math:`R`), and **Conflict** (:math:`C`) —
into a single spatial expression of marine use performance.

All component variables are normalized to :math:`[0, 1]` and spatially explicit,
so the performance index is computed at every model cell and can be upscaled by
averaging to the scale of interest, such as the Management Units.

The PEM framework supports multiple **benchmark performance metrics** to
quantify how far or close a given spatial configuration is from the
theoretical ideal of maximum benefit and minimum impacts
:math:`(B=1,\; R=0,\; C=0)`.
Available options include the original **Ratio Index**
(:math:`D = B / (R \times C)`),
the **Absolute Euclidean Distance** (AED), and the
**Normalized Euclidean Distance** (NED).

.. seealso::

    Full description of all metric options, their formulas, ranges, and
    guidance on which to use in the
    :ref:`Use Performance Index page <about-performance-index>`.


Spatial Indexes
-------------------------------------------

To compute any performance metric, the three component spatial
indexes — :math:`B`, :math:`R`, and :math:`C` — must first be obtained.

The PEM framework provides structured workflows for each component.


.. seealso::

    The **Benefit Index** quantifies the economic and social **benefit** derived
    from the use of every model cell in the ocean space.

    Check out more about the in the :ref:`Benefit Index page <about-benefit-index>`


.. seealso::

    The **Habitat Risk Index** captures the **sensitivity** of
    marine habitats exposed to human activities, considered here as ecosystem **stressors**.

    Check out more about in the :ref:`Habitat Risk Index page <about-risk-index>`


.. seealso::

    The **Conflict Index** expresses the **intensity of overlap** or
    competition between different marine uses within the model cell.

    Check out more about in the :ref:`Conflict Index page <about-conflict-index>`



