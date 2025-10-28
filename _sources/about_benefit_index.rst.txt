.. _about-benefit-index:

.. include:: ./includes/warning_dev.rst

Benefit Index
############################################

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


