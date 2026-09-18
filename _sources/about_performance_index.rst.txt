.. _about-performance-index:

.. include:: ./includes/warning_dev.rst

Use Performance Index
############################################

The **Use Performance Index** is the core integrative indicator of the PEM framework.
It synthesizes the three component dimensions — **Benefit** (:math:`B`),
**Habitat Risk** (:math:`R`), and **Conflict** (:math:`C`) — into a single spatial
expression of marine use performance.

.. note::

    In portuguese, this index is referred as *Índice de Desempenho do Uso de Serviços Ecossistêmicos do Mar*,
    or **IDUSE-Mar** for short.

All three component dimensions are spatially explicit and normalized to :math:`[0, 1]`,
meaning the performance index is computed at every model cell and can be upscaled by
averaging to the scale of interest (e.g., Management Units).

.. seealso::

    Learn how the component indexes are computed:
    :ref:`Benefit Index <about-benefit-index>`,
    :ref:`Habitat Risk Index <about-risk-index>`,
    :ref:`Conflict Index <about-conflict-index>`.


The Ideal Point
==============================================

All benchmark performance metrics in the PEM framework share a common reference:
the **ideal point**, which represents the theoretical configuration of
maximum benefit and minimum negative impacts:

.. math::

    (B^*, R^*, C^*) = (1,\; 0,\; 0)

This ideal represents the best possible state of marine use — full benefit capture,
zero habitat risk, and zero inter-user conflict.
No real scenario is expected to reach this point exactly; it serves as a
fixed reference for measuring how far or close a given spatial configuration
is from the optimum.

Because all dimensions are normalized, the ideal point is a well-defined corner
of the unit cube :math:`[0, 1]^3`.


Performance Metric Options
==============================================

The PEM framework provides multiple formulations to quantify performance relative
to the ideal point. These options are not mutually exclusive — analysts may choose
the metric that best suits the theoretical requirements and communication needs
of their application.


Option 1: Ratio Index
----------------------------------------------

The **Ratio Index** is the original formulation of the performance index in the PEM
framework. It expresses performance as a benefit-to-impact ratio:

.. math::

    D = \frac{B}{R \times C} \quad \text{where } D \in [0,\; +\infty]

The interpretation of :math:`D` is intuitive: it is the economic benefit of using
the ocean space, corrected downward by risk and conflict. A higher value of
:math:`D` indicates a more sustainable and efficient use — high benefit with
relatively low risk and conflict.

.. admonition:: Theoretical limitation

    The Ratio Index is undefined when :math:`R = 0` or :math:`C = 0` (division by zero).
    It is also unbounded above, which can cause numerical overflow when the denominator
    :math:`R \times C` is very close to zero. These limitations motivated the development
    of the distance-based alternatives below.

The upper value of :math:`D` is unbounded — values can grow very large if the product
:math:`R \times C` is close to zero. A common workaround is to *truncate* the product
to a minimum of 0.01, yielding an effective upper bound of 100.

The lower value converges to :math:`B` when :math:`R \times C = 1`, meaning the
correction for risk and conflict is always incremental — :math:`D` is never smaller
than :math:`B`.


Option 2: Absolute Euclidean Distance (AED)
----------------------------------------------

The **Absolute Euclidean Distance** metric quantifies performance as the geometric
distance between a solution :math:`(B, R, C)` and the ideal point :math:`(1, 0, 0)`
in the three-dimensional performance space:

.. math::

    \text{AED} = \sqrt{(B - 1)^2 + R^2 + C^2}

* When :math:`\text{AED} = 0`, the solution coincides with the ideal point — maximum performance.
* The worst possible solution :math:`(B=0,\; R=1,\; C=1)` yields
  :math:`\text{AED} = \sqrt{3} \approx 1.732`.

.. math::

    \text{AED} \in \bigl[0,\; \sqrt{3}\bigr]

The AED metric is **lower-is-better**: a value close to zero indicates high performance,
while a value near :math:`\sqrt{3}` indicates poor performance.

Unlike the Ratio Index, AED is well-defined for all combinations of
:math:`(B, R, C)` in :math:`[0, 1]^3`, including cases where :math:`R = 0` or :math:`C = 0`.


Option 3: Normalized Euclidean Distance (NED)
----------------------------------------------

The **Normalized Euclidean Distance** rescales the AED to a standard :math:`[0, 1]`
interval and inverts the direction so that higher values indicate better performance:

.. math::

    \text{NED} = 1 - \frac{\text{AED}}{\sqrt{3}}

* :math:`\text{NED} = 1` corresponds to the ideal point :math:`(B=1, R=0, C=0)` — best performance.
* :math:`\text{NED} = 0` corresponds to :math:`(B=0, R=1, C=1)` — worst performance.

.. math::

    \text{NED} \in [0,\; 1]

The NED metric is **higher-is-better** and directly comparable across scenarios and
spatial units, making it especially suited for mapping, ranking, and communication
purposes.


Summary
==============================================

.. list-table::
   :header-rows: 1
   :widths: 18 32 18 16 16

   * - Metric
     - Formula
     - Range
     - Better direction
     - Defined when :math:`R=0` or :math:`C=0`?
   * - Ratio Index (:math:`D`)
     - :math:`B\;/\;(R \times C)`
     - :math:`[0,\;+\infty]`
     - Higher
     - No
   * - AED
     - :math:`\sqrt{(B-1)^2 + R^2 + C^2}`
     - :math:`[0,\;\sqrt{3}]`
     - Lower
     - Yes
   * - NED
     - :math:`1 - \text{AED}\;/\;\sqrt{3}`
     - :math:`[0,\;1]`
     - Higher
     - Yes

For new applications, the **NED** is the recommended default metric: it is
well-defined across the entire variable space, bounded between 0 and 1, and
follows the intuitive convention that higher values indicate better performance.
