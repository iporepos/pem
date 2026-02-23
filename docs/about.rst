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
**Marine Ecosystem Services Use Performance Index**,

.. note::

    In portuguese, this index is referred as *Índice de Desempenho do Uso de Serviços Ecossistêmicos do Mar*,
    or **IDUSE-Mar** for short.

This index, denoted as :math:`D`, synthesizes the three component
dimensions — benefit, risk, and conflict — into a single expression of marine use performance:

.. math::

    D = \frac{B}{R \times C} \quad \text{where } D \in [0, +\infty]

Where:

* :math:`D` is the **use performance index** :math:`\in [0, +\infty]`;
* :math:`B` is the **benefit index** :math:`\in [0, 1]`;
* :math:`R` is the **habitat risk index** :math:`\in [0, 1]`; and
* :math:`C` is the **conflict index** :math:`\in [0, 1]`.

The interpretation of :math:`D` is straight-forward:
it is as a correction for the economic benefit of using the ocean space
by taking consideration risk and conflict as well.

The value of :math:`D` must be maximized by ocean management policies,
since it indicates a more sustainable and efficient use of
the ocean space — high benefits with relatively low risk and conflict.
A policy that solely maximizes benefit will more likely
yield an inferior use performance than one that keeps risk and conflict low.

All component variables are spatially explicit, hence :math:`D` is a local
spatial variable too, being computed at every model cell.
The value of :math:`D` can then be upscaled by averaging for the scale of interest,
like the Management Units.

Performance Hyperspace
-------------------------------------------

Because all components of :math:`D` are normalized variables, *i.e.*, defined
between 0 and 1, the mathematical **hyperspace** of :math:`D` can be explored
a priori.

.. tab-set::

    .. tab-item:: English

        .. figure:: figs/plots.jpg
            :name: fig-plots
            :width: 100%
            :align: center

            Exploration of the Use Performance Index formula. (**a**) The performance
            mathematical hyperspace. (**b**) Mathematical bounds for the performance
            index.

    .. tab-item:: Português

        .. figure:: figs/plots_pt.jpg
            :name: fig-plots-pt
            :width: 100%
            :align: center

            Exploração da fórmula do Índice de Desempenho.
            (a) O hiperespaço matemático de desempenho.
            (b) Limites matemáticos para o índice de desempenho.



The upper value of :math:`D` is unbounded, it goes to infinity.
That means that values of :math:`D` can skyrocket if the product :math:`R \times C`
goes very low, close to zero.
To avoid technical issues with numerical overflow, one might
*truncate* the value of the product :math:`R \times C`
to 0.01, which will yield an upper bound of 100.

The lower value of :math:`D` is bounded to zero, and always
converges to the value of :math:`B`. When the product :math:`R \times C`
goes to maximum possible, that is 1,
The value of :math:`D` converges to :math:`B`. This means that
the correction for :math:`R` and :math:`C` are always
incremental, making :math:`D` larger than :math:`B`,
like an incentive to lower :math:`R` or :math:`C`.


Spatial Indexes
-------------------------------------------

To get :math:`D` one need to compute all three subjacent spatial
indexes: :math:`B`, :math:`R` and :math:`C`.

The PEM framework is designed to help in this process. Through a series of
converging analytical processes, the input data are transformed into this
spatial index components.


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



