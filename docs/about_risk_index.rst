.. _about-risk-index:

.. include:: ./includes/warning_dev.rst

Habitat Risk Index
############################################

The **Habitat Risk Index**, denoted as :math:`R`, follows the conceptual structure of the
*InVEST Habitat Risk model*. It estimates the likelihood of impact for a given
habitat cell in the spatial model based on exposure to one or more stressors,
the consequence of this exposure, and the sensitivity of the habitat to each stressor.

The sensitivity, consequence, and exposure parameters are defined by a
**habitat–stressor table**, which specifies how each stressor
(e.g., ocean use, infrastructure, or activity) affects each habitat type.
The resulting risk values are calculated for every cell in the spatial grid,
producing a continuous risk surface.

.. seealso::

    Refer to the `InVEST Habitat Risk model <https://naturalcapitalproject.stanford.edu/invest/habitat-risk-assessment>`_
    documentation for theoretical and technical details regarding data inputs
    and methodological background.

Habitat and Stressors
==============================================

As illustrated in bellow, multiple stressors can
overlap spatially, compounding their individual impacts. The cumulative habitat
risk is therefore nonlinear, reflecting potential synergistic effects among
stressors.

.. tab-set::

    .. tab-item:: English

        .. figure:: figs/risk.jpg
            :name: fig-habitat-risk-concept2
            :width: 100%
            :align: center

            Conceptual representation of the Habitat Risk Index. (**a**) The spatial
            distribution of multiple habitat types and the footprint of a
            stressor, illustrating both direct and border impacts with distance-decay
            exposure. (**b**) The model aggregates overlapping stressors into a cumulative,
            nonlinear habitat risk surface.

    .. tab-item:: Português

        .. figure:: figs/risk_pt.jpg
            :name: fig-habitat-risk-concept2-pt
            :width: 100%
            :align: center

            Representação conceitual do Índice de Risco Ecológico. (**a**)
            A distribuição espacial de múltiplos tipos de habitat e a pegada de um estressor,
            ilustrando impactos diretos e de borda com exposição que decai com a distância.
            (**b**) O modelo agrega estressores sobrepostos em uma
            superfície cumulativa e não linear de risco ao habitat.



Benthic and Pelagic Habitats
==============================================

In the PEM framework, two sets of habitats are
considered: **benthic** and **pelagic**.

Each set is processed separately to produce
two distinct habitat risk maps under a given scenario of ocean use.

These maps are then combined and normalized to a range of 0–1 for comparison across
scenarios, as expressed by the equation below:

.. math::

    R = \frac{R_{b} + R_{p}}{\max(R_{b} + R_{p})}

where :math:`R_{b}` and :math:`R_{p}` are the respective risk
indices for benthic and pelagic habitats.


