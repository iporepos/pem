.. _about-conflict-index:

Conflict Index
############################################

The **Conflict Index**, denoted as :math:`C`, quantifies the spatial
incompatibility among Ocean Users within a given scenario.

While the :ref:`Habitat Risk Index <about-risk-index>` evaluates ecological
risk derived from habitat–stressor interactions, the Conflict Index is strictly
**user–user based**.

It measures the spatial coincidence of activities and
weights their overlap according to a predefined *conflict matrix*.

.. include:: includes/examples/conflict_matrix.rst

Conceptual Definition
==============================================

Let :math:`U_i` and :math:`U_j` represent two spatial user layers
(rasterized on a common grid). Each layer may be defined as:

- A Boolean footprint (:math:`0/1` presence–absence); or
- A fuzzy intensity surface (:math:`0 \leq u \leq 1`).

For every unique pair :math:`(i, j)`:

.. math::

    {O}_{ij} = U_i \times U_j

where :math:`O_{ij}` represents spatial overlap intensity.

Each pairwise overlap is multiplied by a weight
:math:`w_{ij}` extracted from a lower-triangular
**conflict matrix**:

.. math::

    C^* = \sum_{i<j} {w}_{ij} \cdot \hat{O}_{ij}

where :math:`\hat{O}_{ij}` is the normalized overlap surface.

The final Conflict Index is obtained by normalizing
the aggregated weighted sum:

.. math::

    C = \frac{C^*}{\max(C^*)}

Thus:

- :math:`C = 0` → no weighted spatial conflict
- :math:`C = 1` → maximum relative conflict within the scenario

Properties
==============================================

**1. Pairwise-only interactions**

The model evaluates all unique user combinations
(:math:`n(n-1)/2` pairs). Self-conflicts (diagonal terms)
are excluded.

**2. Symmetry assumption**

The conflict matrix is symmetric by construction.
Only the lower triangle is used operationally.

**3. Scenario-relative normalization**

The index is normalized per scenario. Therefore:

- Absolute magnitudes are scenario-dependent;
- Comparisons should focus on spatial patterns or
  relative differences between scenarios.

**4. No ecological mediation**

Unlike the Habitat Risk Index:

- No habitat layers are used;
- No exposure decay functions are applied;
- No nonlinear ecological aggregation occurs.

The Conflict Index is therefore a
**purely spatial compatibility indicator**.

Interpretation in Marine Spatial Planning
==============================================

The Conflict Index supports:

- Identification of hotspots of spatial competition;
- Evaluation of alternative user configurations;
- Screening of planning scenarios prior to ecological modeling;
- Integration into composite multi-criteria performance metrics.

Typical high-conflict examples include:

- Offshore wind farms vs tourism corridors;
- Industrial fisheries vs conservation zones;
- Aquaculture vs navigation routes.

Conversely, compatible or synergistic uses
may receive low or zero weights in the conflict matrix.

Relationship to the PEM Framework
==============================================

Within the PEM workflow:

1. Ocean Users are rasterized per scenario.
2. A conflict matrix defines pairwise incompatibility weights.
3. The Conflict Index is computed from weighted overlaps.
4. The resulting raster is normalized (0–1).
5. The index can be combined with other indicators
   (e.g., Habitat Risk Index, economic layers)
   in higher-level performance assessments.

The Conflict Index therefore complements
ecological risk modeling by providing
a structural measure of human-use competition
independent of habitat vulnerability.






