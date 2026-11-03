#!/usr/bin/env python3
"""
This is the complete API reference for the ``build_scenarios`` python module of the ``pem`` system.

This module builds the ``a0`` to ``a3`` scenarios from the published baseline
``results.gpkg`` into a sidecar GeoPackage, with the layer system expected by
:mod:`pem.post_process`. Benefit, risk, and conflict at each grid cell are
computed as follows:

.. list-table::
    :header-rows: 1
    :widths: 15 20 65

    * - Scenario
      - Layer suffix
      - Values
    * - ``a0``
      - ``_cenario0``
      - baseline
    * - ``a1``
      - ``_cenario1``
      - baseline × intensification factors
    * - ``a2``
      - ``_cenario2``
      - baseline × expansion factors of the unit holding the cell
    * - ``a3``
      - ``_cenario3``
      - baseline × intensification factors × expansion factors

.. important::

    All scenarios are multiplied by the same scale and capped at 1. A baseline
    that spans 0 to 1 yields an ``a0`` that spans 0 to the scale, and the factors
    remain comparable across scenarios. Values beyond the cap saturate, so ``a3``
    reaches 1 only if the combined factors are large enough.

Performance metrics are computed after the scaling, and unit layers are the mean
of the scenario grid by unit. All other columns are copied without changes.

This module does not depend on the QGIS Python environment.

.. dropdown:: Script example
    :icon: code-square
    :open:

    .. code-block:: bash

        python -m pem.build_scenarios --config path/to/config.json

.. dropdown:: Config file
    :icon: gear

    .. code-block:: json

        {
            "input_gpkg": "path/to/results.gpkg",
            "output_gpkg": "path/to/result_scenarios.gpkg",
            "scale": 0.6,
            "a1_factors": {"benefit": 1.5, "risk": 1.5, "conflict": 1.0},
            "expansion_layer": "units_macro",
            "expansion": [
                {"upg_id": 1, "benefit_factor": 1.2, "conflict_factor": 1.3, "risk_factor": 1.4},
                {"upg_id": 3, "benefit_factor": 1.4, "conflict_factor": 1.1, "risk_factor": 1.4}
            ],
            "grid_layer": "grid",
            "units_layers": {"units_micro": "id_micro", "units_macro": "id_macro"},
            "scenario_titles": {"a0": "Cenário A0", "a1": "Cenário A1"},
            "variable_titles": {"ned": "Desempenho", "risk": "Risco"},
            "scale_bar_km": 300,
            "map_background": "#D6EAF8",
            "decorators": [
                {"source": "path/to/vectors.gpkg|layername=land", "facecolor": "#E5E5E5"},
                {
                    "source": "path/to/vectors.gpkg|layername=states",
                    "edgecolor": "#444444",
                    "linewidth": 0.4,
                    "label": "nome",
                    "label_offset": [0, 0.3],
                    "label_offsets": {"Rio Grande do Sul": [0, 0.95]},
                    "above_data": true
                }
            ]
        }

    .. list-table::
        :header-rows: 1
        :widths: 25 75

        * - Key
          - Description
        * - ``input_gpkg``
          - Path to the baseline GeoPackage published by :mod:`pem.publish`.
        * - ``output_gpkg``
          - [optional] Path to the output GeoPackage. An existing file is replaced.
            Default value is ``result_scenarios.gpkg`` next to the input.
        * - ``scale``
          - Scale applied to all scenarios.
        * - ``a1_factors``
          - Intensification factors by variable, used in ``a1`` and ``a3``. A missing
            variable has a factor of 1, and any other key is ignored.
        * - ``expansion_layer``
          - Name of the unit layer that ``upg_id`` refers to. Used to select the
            grid cells, so the grid must have a column with this name.
        * - ``expansion``
          - List of units to expand, used in ``a2`` and ``a3``. Each entry has the
            ``upg_id`` and the three factors. Other cells have a factor of 1.
        * - ``grid_layer``
          - Name of the grid layer in the input.
        * - ``units_layers``
          - Mapping of unit layer name to the name of its id column.
        * - ``plots_dir``
          - [optional] Path to the folder of output plots. Default value is the
            ``plots`` folder next to the output GeoPackage.
        * - ``scenario_titles``
          - [optional] Title of the maps by scenario. A missing scenario is titled
            with its name (e.g., ``a0``).
        * - ``variable_titles``
          - [optional] Name of the variables, used in the map titles and color bars, by
            ``ned``, ``ned-rel``, ``risk``, ``benefit``, and ``conflict``.
        * - ``scale_bar_km``
          - [optional] Length of the scale bar in km. By default, it is set from the
            width of the map.
        * - ``map_background``
          - [optional] Background color of the maps. Default value is ``white``.
        * - ``decorators``
          - [optional] List of layers to add to the maps, plotted in the order of the
            list. Each entry has a ``source``, as ``path|layername=name``, and the
            optional ``facecolor``, ``edgecolor``, ``linewidth``, ``label`` (name of
            the column with the labels), ``label_offset`` (``[x, y]`` shift of the labels,
            in map units), ``label_offsets`` (shift by label, which replaces
            ``label_offset``), and ``above_data`` (to plot it above the data
            layer, rather than below it). Labels are placed out of the data layer, and
            polygons with little area visible in the map are not labeled.

.. dropdown:: Output layers
    :icon: database

    Each input layer yields one output layer by scenario:

    * ``{grid_layer}_cenario0`` to ``{grid_layer}_cenario3``
    * ``{unit_layer}_cenario0`` to ``{unit_layer}_cenario3``

    Each output layer holds the updated ``benefit``, ``risk``, ``conflict``,
    ``performance_d``, ``performance_aed``, and ``performance_ned`` columns, and a
    new ``performance`` column with the ``performance_ned`` values.

.. dropdown:: Output plots
    :icon: image

    One figure is saved by spatial scale and variable, named
    ``result_scenario_<grid, micro, macro>_<ned, ned-rel, risk, benefit, conflict>.png``.
    Each figure is 16 cm wide, for an A4 report, and has one choropleth map by
    scenario, with a vertical color bar and a histogram below it. In a geographic CRS,
    the scale bar is measured at the center of the map.

    The color scale of each variable is the range of the ``a3`` grid, for all
    scenarios and spatial scales. The exceptions are ``ned``, from 0 to 1, and
    ``ned-rel``, from the range of the grid across all scenarios, rounded outwards to
    a multiple of 0.05. A message is printed if any value is out of the color scale.
    These values have the color of the end of the scale, and are counted in the last
    bar of the histogram.

"""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.ticker import FuncFormatter, MaxNLocator
from pyproj import Geod
from shapely.geometry import box

VARIABLES = ["benefit", "risk", "conflict"]
METRICS = ["performance_d", "performance_aed", "performance_ned", "performance"]
N_SCENARIOS = 4
N_BINS = 20
NODATA_COLOR = "#d9d9d9"
# layout of the figures, as fractions of the figure size
LAYOUT = {
    "map_left": 0.04,
    "map_step": 0.2425,
    "map_bottom": 0.40,
    "map_width": 0.19,
    "map_height": 0.51,
    "colorbar_bottom": 0.33,
    "colorbar_height": 0.018,
    "colorbar_width": 0.55,  # as a fraction of the map width
    "hist_bottom": 0.10,
    "hist_width": 0.117,
    "hist_height": 0.18,
}
# name in the output files: (column, label, colormap, range of the color scale)
# the range is fixed, or RANGE_A3 or RANGE_SCENARIOS to get it from the data
RANGE_A3 = "a3"
RANGE_SCENARIOS = "scenarios"
RANGE_ROUNDING = 0.05
PLOTS = {
    "ned": ("performance_ned", "NED", "RdYlGn", (0.0, 1.0)),
    "ned-rel": ("performance_ned", "Relative NED", "RdYlGn", RANGE_SCENARIOS),
    "risk": ("risk", "Risk", "YlOrRd", RANGE_A3),
    "benefit": ("benefit", "Benefit", "YlOrRd", RANGE_A3),
    "conflict": ("conflict", "Conflict", "YlOrRd", RANGE_A3),
}
# figure for an A4 report, 16 cm wide
FIGURE_WIDTH = 16 / 2.54
FIGURE_HEIGHT = 3.19
FIGURE_DPI = 600
HIST_BACKGROUND = "#EAEAF2"
FONT_SIZE = 5
SMALL_FONT_SIZE = 4.5
LABEL_WRAP = 10  # characters by line
LABEL_MIN_AREA = 0.02  # as a fraction of the area of the map
# room around the values in the histogram, as a fraction of the range of the values
HIST_MARGIN_BOTTOM = 0.15
HIST_MARGIN_TOP = 0.15
# layout of the figures, in inches
LAYOUT = {
    "map_left": 0.03,
    "map_step": 1.58,
    "map_bottom": 1.22,
    "map_width": 1.5,
    "map_height": 1.80,
    "colorbar_left": 0.21,  # from the left side of the map frame
    "colorbar_width": 0.07,
    "hist_left": 0.34,  # from the left side of the map frame
    "hist_bottom": 0.19,
    "hist_height": 1.0,
}


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_expansion_factors(grid, unit_ids, expansion, expansion_layer):
    """Burn the expansion setup into the grid, as one factor column per variable.

    Grid rows are assigned to units by the column that ``publish_results``
    stores on the grid, which holds the unit containing each cell's centroid.
    Cells outside of the listed units get a factor of 1.

    :param grid: baseline grid, carrying the ``expansion_layer`` column
    :type grid: geopandas.GeoDataFrame
    :param unit_ids: ids of the unit layer
    :type unit_ids: pandas.Series
    :param expansion: list of dicts with ``upg_id`` and one ``<variable>_factor``
        key per variable
    :type expansion: list
    :param expansion_layer: name of the unit layer the setup refers to
    :type expansion_layer: str
    :return: factors by variable, aligned with ``grid``
    :rtype: pandas.DataFrame
    """
    ls_ids = [item["upg_id"] for item in expansion]

    duplicates = sorted({i for i in ls_ids if ls_ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"Duplicated upg_id in expansion: {duplicates}")

    unknown = sorted(set(ls_ids) - set(unit_ids))
    if unknown:
        raise ValueError(f"upg_id not found in '{expansion_layer}': {unknown}")

    factors = pd.DataFrame(index=grid.index)
    for var in VARIABLES:
        dc = {item["upg_id"]: item[f"{var}_factor"] for item in expansion}
        factors[var] = grid[expansion_layer].map(dc).fillna(1.0)
    return factors


def compute_scenario_values(grid, scenario, a1_factors, expansion_factors, scale):
    """Compute the scaled benefit, risk and conflict of a scenario.

    :param grid: baseline grid, carrying the ``benefit``, ``risk`` and
        ``conflict`` columns
    :type grid: geopandas.GeoDataFrame
    :param scenario: scenario number, from 0 to 3
    :type scenario: int
    :param a1_factors: intensification factors by variable, which default to 1
    :type a1_factors: dict
    :param expansion_factors: expansion factors by variable, aligned with ``grid``
    :type expansion_factors: pandas.DataFrame
    :param scale: scale applied to all scenarios
    :type scale: float
    :return: scaled values by variable, aligned with ``grid``
    :rtype: pandas.DataFrame
    """
    values = pd.DataFrame(index=grid.index)
    for var in VARIABLES:
        data = grid[var].astype(float)
        if scenario in (1, 3):
            data = data * a1_factors.get(var, 1.0)
        if scenario in (2, 3):
            data = data * expansion_factors[var]
        # NaN (no data) is kept as NaN
        values[var] = np.minimum(data * scale, 1.0)
    return values


def compute_performance_metrics(values):
    """Compute the performance metrics, as in ``publish._compute_performance_metrics``.

    The ``performance`` column is the Normalized Euclidean Distance, under the
    name expected by post_process.py.

    :param values: scaled values, with ``benefit``, ``risk`` and ``conflict`` columns
    :type values: pandas.DataFrame
    :return: metrics aligned with ``values``
    :rtype: pandas.DataFrame
    """
    b = values["benefit"].values
    r = values["risk"].values
    c = values["conflict"].values

    aed = np.sqrt((b - 1.0) ** 2 + r**2 + c**2)
    ned = 1.0 - aed / np.sqrt(3.0)

    return pd.DataFrame(
        {
            "performance_d": b / np.clip(r * c, 0.01, 1.0),
            "performance_aed": aed,
            "performance_ned": ned,
            "performance": ned,
        },
        index=values.index,
    )


def aggregate_to_unit(grid_scenario, unit, unit_layer, unit_id, stat_cols):
    """Replace the stat columns of a unit layer by the mean of the grid by unit.

    :param grid_scenario: scenario grid, carrying the ``unit_layer`` column
    :type grid_scenario: geopandas.GeoDataFrame
    :param unit: baseline unit layer
    :type unit: geopandas.GeoDataFrame
    :param unit_layer: name of the unit layer
    :type unit_layer: str
    :param unit_id: name of the id column of the unit layer
    :type unit_id: str
    :param stat_cols: names of the columns to aggregate
    :type stat_cols: list
    :return: copy of the unit layer with the aggregated columns
    :rtype: geopandas.GeoDataFrame
    """
    means = grid_scenario.groupby(unit_layer)[stat_cols].mean()
    unit_scenario = unit.copy()
    for col in stat_cols:
        unit_scenario[col] = unit_scenario[unit_id].map(means[col])
    return unit_scenario


def print_summary(scenario, values):
    ls = []
    for var in VARIABLES:
        n_capped = int((values[var] >= 1.0).sum())
        ls.append(f"{var} max={values[var].max():.4f} at_1={n_capped}")
    print(f"  cenario{scenario}: " + " | ".join(ls))


def get_km_per_map_unit(layer):
    """Get the length in km of one unit of the x axis of a map.

    In a geographic CRS the length of a degree of longitude changes with the
    latitude, so it is measured at the center of the layer.

    :param layer: layer to plot
    :type layer: geopandas.GeoDataFrame
    :return: length in km of one unit of the x axis
    :rtype: float
    """
    if not layer.crs.is_geographic:
        return layer.crs.axis_info[0].unit_conversion_factor / 1000

    xmin, ymin, xmax, ymax = layer.total_bounds
    lon = (xmin + xmax) / 2
    lat = (ymin + ymax) / 2
    _, _, meters = Geod(ellps="WGS84").inv(lon - 0.5, lat, lon + 0.5, lat)
    return meters / 1000


def format_map_frame(ax, is_geographic):
    """Set a frame with sparse coordinates on a map.

    :param ax: map axes
    :type ax: matplotlib.axes.Axes
    :param is_geographic: whether the coordinates are longitude and latitude
    :type is_geographic: bool
    :return: Always returns ``None``
    :rtype: None
    """
    ax.xaxis.set_major_locator(MaxNLocator(nbins=3, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=3, steps=[1, 2, 5, 10]))
    ax.tick_params(direction="in", length=2, labelsize=SMALL_FONT_SIZE)
    ax.tick_params(axis="x", pad=-(FONT_SIZE + 2))
    ax.tick_params(axis="y", pad=-3)
    if is_geographic:
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _: f"{abs(v):g}°{'W' if v < 0 else 'E'}")
        )
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _: f"{abs(v):g}°{'S' if v < 0 else 'N'}")
        )
    for tick in ax.yaxis.get_major_ticks():
        tick.label1.set_horizontalalignment("left")


def add_scale_bar(ax, km_per_unit, km=None):
    """Add a scale bar to the upper right side of a map.

    :param ax: map axes
    :type ax: matplotlib.axes.Axes
    :param km_per_unit: length in km of one unit of the x axis
    :type km_per_unit: float
    :param km: [optional] length of the scale bar in km. By default, the largest of
        1, 2 or 5 times a power of 10 that fits in a quarter of the width of the map.
    :type km: float
    :return: Always returns ``None``
    :rtype: None
    """
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    if km is None:
        target = (xmax - xmin) * km_per_unit / 4
        power = 10 ** np.floor(np.log10(target))
        km = max(i * power for i in (1, 2, 5) if i * power <= target)

    x1 = xmax - (xmax - xmin) * 0.05
    x0 = x1 - km / km_per_unit
    y = ymax - (ymax - ymin) * 0.09
    ax.plot([x0, x1], [y, y], color="black", linewidth=1, solid_capstyle="butt")
    ax.annotate(
        f"{km:g} km",
        xy=((x0 + x1) / 2, y),
        xytext=(0, 1),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=SMALL_FONT_SIZE,
    )
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def get_map_extent(layer, margin=0.05):
    """Get the extent of a map, so it does not depend on the decorators.

    :param layer: layer to plot
    :type layer: geopandas.GeoDataFrame
    :param margin: margin as a fraction of the size of the layer. Default value = ``0.05``
    :type margin: float
    :return: ``xmin``, ``ymin``, ``xmax`` and ``ymax`` of the map
    :rtype: tuple
    """
    xmin, ymin, xmax, ymax = layer.total_bounds
    dx = (xmax - xmin) * margin
    dy = (ymax - ymin) * margin
    return xmin - dx, ymin - dy, xmax + dx, ymax + dy


def get_label_points(gdf, column, free_area, min_area):
    """Get the position of the labels of a decorator, out of the data layer.

    Each label stays at the largest part of its polygon that is visible in the map
    and not covered by the data layer. Polygons with a small part are not labeled.

    :param gdf: decorator layer
    :type gdf: geopandas.GeoDataFrame
    :param column: name of the column with the labels
    :type column: str
    :param free_area: area of the map that is not covered by the data layer
    :type free_area: shapely.Geometry
    :param min_area: minimum area of the part that holds a label
    :type min_area: float
    :return: list of ``x``, ``y`` and label text
    :rtype: list
    """
    ls_labels = []
    visible = gdf.geometry.make_valid().intersection(free_area)
    for geometry, text in zip(visible, gdf[column]):
        if geometry.is_empty:
            continue
        part = max(getattr(geometry, "geoms", [geometry]), key=lambda g: g.area)
        if part.area >= min_area:
            point = part.representative_point()
            ls_labels.append((point.x, point.y, str(text)))
    return ls_labels


def load_decorators(ls_specs, data_layer, extent):
    """Load the decorator layers that reach the extent of the map.

    :param ls_specs: decorators, as set in the config
    :type ls_specs: list
    :param data_layer: layer with the geometries of the map
    :type data_layer: geopandas.GeoDataFrame
    :param extent: ``xmin``, ``ymin``, ``xmax`` and ``ymax`` of the map
    :type extent: tuple
    :return: copy of the decorators, each with its layer in the ``gdf`` key and its
        label positions in the ``labels`` key
    :rtype: list
    """
    xmin, ymin, xmax, ymax = extent
    map_area = box(*extent)
    free_area = map_area.difference(data_layer.geometry.union_all())
    ls_decorators = []
    for spec in ls_specs:
        path, layer = spec["source"].split("|layername=")
        gdf = gpd.read_file(path, layer=layer).to_crs(data_layer.crs)
        gdf = gdf.cx[xmin:xmax, ymin:ymax]
        ls_labels = []
        if "label" in spec:
            ls_labels = get_label_points(
                gdf, spec["label"], free_area, LABEL_MIN_AREA * map_area.area
            )
        ls_decorators.append({**spec, "gdf": gdf, "labels": ls_labels})
    return ls_decorators


def plot_decorators(ax, ls_decorators, above_data):
    """Plot the decorators of one side of the data layer, in the order of the list.

    :param ax: map axes
    :type ax: matplotlib.axes.Axes
    :param ls_decorators: decorators, as returned by ``load_decorators``
    :type ls_decorators: list
    :param above_data: whether to plot the decorators set above the data layer
    :type above_data: bool
    :return: Always returns ``None``
    :rtype: None
    """
    for decorator in ls_decorators:
        if decorator.get("above_data", False) != above_data:
            continue
        decorator["gdf"].plot(
            ax=ax,
            facecolor=decorator.get("facecolor", "none"),
            edgecolor=decorator.get("edgecolor", "none"),
            linewidth=decorator.get("linewidth", 0.4),
        )
        offset = decorator.get("label_offset", (0, 0))
        offsets = decorator.get("label_offsets", {})
        for x, y, text in decorator["labels"]:
            dx, dy = offsets.get(text, offset)
            ax.text(
                x + dx,
                y + dy,
                textwrap.fill(text, LABEL_WRAP),
                fontsize=FONT_SIZE - 1,
                linespacing=0.9,
                color=decorator.get("edgecolor", "black"),
                ha="center",
                va="center",
                clip_on=True,
            )


def get_figure_rect(left, bottom, width, height):
    """Convert a rectangle in inches to fractions of the figure size.

    :param left: left side, in inches
    :type left: float
    :param bottom: bottom side, in inches
    :type bottom: float
    :param width: width, in inches
    :type width: float
    :param height: height, in inches
    :type height: float
    :return: rectangle as expected by ``Figure.add_axes``
    :rtype: list
    """
    return [
        left / FIGURE_WIDTH,
        bottom / FIGURE_HEIGHT,
        width / FIGURE_WIDTH,
        height / FIGURE_HEIGHT,
    ]


def plot_scenarios(
    ls_layers,
    column,
    label,
    cmap,
    vrange,
    scenario_titles,
    extent,
    map_background,
    ls_decorators,
    scale_bar_km,
    file_output,
):
    """Plot one map, color bar and histogram by scenario, side by side.

    The color bar is aligned with the values of the histogram, so it holds the
    labels of both. Each scenario repeats its coordinates, color bar and histogram
    axes, so it can be cropped from the figure. Red lines highlight the minimum and
    maximum of each scenario in the histogram.

    :param ls_layers: layers to plot, one by scenario
    :type ls_layers: list
    :param column: name of the column to plot
    :type column: str
    :param label: name of the variable, used in the color bar and the map titles
    :type label: str
    :param cmap: name of the colormap
    :type cmap: str
    :param vrange: minimum and maximum of the color scale
    :type vrange: tuple
    :param scenario_titles: title by scenario name (e.g., ``a0``), which default to
        the scenario name
    :type scenario_titles: dict
    :param extent: ``xmin``, ``ymin``, ``xmax`` and ``ymax`` of the maps
    :type extent: tuple
    :param map_background: background color of the maps
    :type map_background: str
    :param ls_decorators: decorators, as returned by ``load_decorators``
    :type ls_decorators: list
    :param scale_bar_km: length of the scale bar in km, or ``None`` to set it from the
        width of the map
    :type scale_bar_km: float
    :param file_output: path to the output image
    :type file_output: pathlib.Path
    :return: Always returns ``None``
    :rtype: None
    """
    vmin, vmax = vrange
    norm = Normalize(vmin=vmin, vmax=vmax)
    colormap = plt.get_cmap(cmap)
    edges = np.linspace(vmin, vmax, N_BINS + 1)
    centers = (edges[:-1] + edges[1:]) / 2
    hist_range = 1 + HIST_MARGIN_BOTTOM + HIST_MARGIN_TOP
    hist_ymin = vmin - HIST_MARGIN_BOTTOM * (vmax - vmin)
    hist_ymax = vmax + HIST_MARGIN_TOP * (vmax - vmin)
    ticks = MaxNLocator(nbins=4, steps=[1, 2, 5, 10]).tick_values(vmin, vmax)
    ticks = ticks[(ticks >= vmin) & (ticks <= vmax)]

    km_per_unit = get_km_per_map_unit(ls_layers[0])
    is_geographic = ls_layers[0].crs.is_geographic
    # same aspect as geopandas, but independent of the extent of the decorators
    aspect = 1.0
    if is_geographic:
        aspect = 1 / np.cos(np.radians((extent[1] + extent[3]) / 2))

    fig = plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT))

    ls_hist = []
    for scenario, layer in enumerate(ls_layers):
        ax_map = fig.add_axes(
            get_figure_rect(
                LAYOUT["map_left"] + scenario * LAYOUT["map_step"],
                LAYOUT["map_bottom"],
                LAYOUT["map_width"],
                LAYOUT["map_height"],
            )
        )

        ax_map.set_facecolor(map_background)
        plot_decorators(ax_map, ls_decorators, False)
        layer.plot(
            column=column,
            ax=ax_map,
            cmap=colormap,
            norm=norm,
            linewidth=0,
            edgecolor="none",
            antialiased=False,
            missing_kwds={"color": NODATA_COLOR},
        )
        plot_decorators(ax_map, ls_decorators, True)
        ax_map.set_xlim(extent[0], extent[2])
        ax_map.set_ylim(extent[1], extent[3])
        ax_map.set_aspect(aspect)
        name = f"a{scenario}"
        ax_map.set_title(f"{label} | {scenario_titles.get(name, name)}", pad=3)
        format_map_frame(ax_map, is_geographic)
        add_scale_bar(ax_map, km_per_unit, scale_bar_km)

        # the frame of the map is only known after the aspect ratio is applied
        ax_map.apply_aspect()
        frame = ax_map.get_position()
        frame_left = frame.x0 * FIGURE_WIDTH
        frame_right = frame.x1 * FIGURE_WIDTH

        # the color bar skips the margin of the histogram, so their values match
        cax = fig.add_axes(
            get_figure_rect(
                frame_left + LAYOUT["colorbar_left"],
                LAYOUT["hist_bottom"]
                + HIST_MARGIN_BOTTOM / hist_range * LAYOUT["hist_height"],
                LAYOUT["colorbar_width"],
                LAYOUT["hist_height"] / hist_range,
            )
        )
        colorbar = fig.colorbar(ScalarMappable(norm=norm, cmap=colormap), cax=cax)
        colorbar.set_ticks(ticks)
        cax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        colorbar.set_label(label, labelpad=1)
        cax.yaxis.set_ticks_position("left")
        cax.yaxis.set_label_position("left")

        hist_left = frame_left + LAYOUT["hist_left"]
        ax_hist = fig.add_axes(
            get_figure_rect(
                hist_left,
                LAYOUT["hist_bottom"],
                frame_right - hist_left,
                LAYOUT["hist_height"],
            ),
            facecolor=HIST_BACKGROUND,
        )
        ls_hist.append(ax_hist)

        values = layer[column].dropna().values
        counts, _ = np.histogram(np.clip(values, vmin, vmax), bins=edges)
        ax_hist.barh(
            centers,
            100 * counts / len(values),
            height=(edges[1] - edges[0]) * 0.9,
            color=colormap(norm(centers)),
        )
        for value, text, va in [
            (values.min(), "min", "top"),
            (values.max(), "max", "bottom"),
        ]:
            ax_hist.axhline(value, color="red", linewidth=0.7)
            # a value out of the plot has no line, but its label stays at the frame
            y = value
            if value > hist_ymax:
                y, va = hist_ymax, "top"
            elif value < hist_ymin:
                y, va = hist_ymin, "bottom"
            ax_hist.text(
                0.98,
                y,
                f"{text} {value:.2f}",
                transform=ax_hist.get_yaxis_transform(),
                ha="right",
                va=va,
                fontsize=SMALL_FONT_SIZE,
            )
        ax_hist.set_ylim(hist_ymin, hist_ymax)
        ax_hist.set_yticks(ticks)
        ax_hist.tick_params(axis="y", labelleft=False, length=2)
        ax_hist.tick_params(axis="x", length=2)
        ax_hist.xaxis.set_major_locator(MaxNLocator(nbins=4, steps=[1, 2, 5, 10]))
        ax_hist.grid(color="white", linewidth=0.6)
        ax_hist.set_axisbelow(True)
        ax_hist.set_xlabel("(%)", labelpad=1)

    for ax_hist in ls_hist[1:]:
        ax_hist.sharex(ls_hist[0])

    fig.savefig(file_output, dpi=FIGURE_DPI)
    plt.close(fig)


def get_color_range(ls_grids, column, color_range):
    """Get the range of the color scale of a variable.

    The grid sets the range for all spatial scales, since the unit layers are means
    of its cells.

    :param ls_grids: grid layers, one by scenario
    :type ls_grids: list
    :param column: name of the column to plot
    :type column: str
    :param color_range: fixed range, ``RANGE_A3`` for the range of the ``a3`` grid, or
        ``RANGE_SCENARIOS`` for the range across all scenarios, rounded outwards to a
        multiple of ``RANGE_ROUNDING``
    :type color_range: tuple or str
    :return: minimum and maximum of the color scale
    :rtype: tuple
    """
    if color_range == RANGE_A3:
        values = ls_grids[-1][column]
        return float(values.min()), float(values.max())
    if color_range == RANGE_SCENARIOS:
        values = pd.concat([grid[column] for grid in ls_grids])
        vmin = np.floor(values.min() / RANGE_ROUNDING) * RANGE_ROUNDING
        vmax = np.ceil(values.max() / RANGE_ROUNDING) * RANGE_ROUNDING
        return round(float(vmin), 10), round(float(vmax), 10)
    return color_range


def plot_all(
    dc_layers,
    grid_layer,
    plots_dir,
    scenario_titles,
    variable_titles,
    map_background,
    decorators,
    scale_bar_km,
):
    """Plot all variables at all spatial scales.

    The color scale of each variable is set by ``get_color_range``, and it is the same
    across scenarios and spatial scales, so all maps are comparable.

    :param dc_layers: layers by name, each with a list of layers by scenario
    :type dc_layers: dict
    :param grid_layer: name of the grid layer
    :type grid_layer: str
    :param plots_dir: path to the output folder
    :type plots_dir: pathlib.Path
    :param scenario_titles: title by scenario name (e.g., ``a0``)
    :type scenario_titles: dict
    :param variable_titles: name by variable (e.g., ``ned``), which default to the
        labels in ``PLOTS``
    :type variable_titles: dict
    :param map_background: background color of the maps
    :type map_background: str
    :param decorators: decorators, as set in the config
    :type decorators: list
    :param scale_bar_km: length of the scale bar in km, or ``None`` to set it from the
        width of the map
    :type scale_bar_km: float
    :return: Always returns ``None``
    :rtype: None
    """
    reference_layer = dc_layers[grid_layer][0]
    extent = get_map_extent(reference_layer)
    ls_decorators = load_decorators(decorators, reference_layer, extent)

    plots_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": FONT_SIZE,
            "axes.titlesize": FONT_SIZE + 1,
            "axes.linewidth": 0.5,
            "xtick.major.width": 0.4,
            "ytick.major.width": 0.4,
            "xtick.major.pad": 1.5,
            "ytick.major.pad": 1.5,
            "xtick.major.size": 2,
            "ytick.major.size": 2,
        }
    )

    for nm, (column, label, cmap, color_range) in PLOTS.items():
        vrange = get_color_range(dc_layers[grid_layer], column, color_range)

        for layer_name, ls_layers in dc_layers.items():
            for scenario, layer in enumerate(ls_layers):
                vmin, vmax = layer[column].min(), layer[column].max()
                if vmin < vrange[0] or vmax > vrange[1]:
                    print(
                        f"  warning: {layer_name} a{scenario} {column} "
                        f"[{vmin:.3f}, {vmax:.3f}] is outside of the range "
                        f"[{vrange[0]:.3f}, {vrange[1]:.3f}]"
                    )

            scale = layer_name.split("_")[-1]
            file_output = plots_dir / f"result_scenario_{scale}_{nm}.png"
            plot_scenarios(
                ls_layers,
                column,
                variable_titles.get(nm, label),
                cmap,
                vrange,
                scenario_titles,
                extent,
                map_background,
                ls_decorators,
                scale_bar_km,
                file_output,
            )
            print(f"  plot saved: {file_output.name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build PEM scenarios from the baseline results.gpkg"
    )
    parser.add_argument(
        "--config", required=True, type=Path, help="Path to config.json"
    )
    args = parser.parse_args()

    cfg = load_config(args.config)

    input_gpkg = Path(cfg["input_gpkg"])
    if not input_gpkg.exists():
        raise FileNotFoundError(f"Input GeoPackage not found: {input_gpkg}")

    output_gpkg = Path(
        cfg.get("output_gpkg", input_gpkg.parent / "result_scenarios.gpkg")
    )
    if output_gpkg.resolve() == input_gpkg.resolve():
        raise ValueError("output_gpkg must not be the input GeoPackage.")

    grid_layer = cfg["grid_layer"]
    units_layers = cfg["units_layers"]
    expansion_layer = cfg["expansion_layer"]

    grid = gpd.read_file(input_gpkg, layer=grid_layer)
    units = {nm: gpd.read_file(input_gpkg, layer=nm) for nm in units_layers}

    expansion_factors = get_expansion_factors(
        grid=grid,
        unit_ids=units[expansion_layer][units_layers[expansion_layer]],
        expansion=cfg["expansion"],
        expansion_layer=expansion_layer,
    )
    n_burned = int(
        grid[expansion_layer].isin(i["upg_id"] for i in cfg["expansion"]).sum()
    )
    print(f"Expansion: {len(cfg['expansion'])} units, {n_burned} grid cells")

    output_gpkg.parent.mkdir(parents=True, exist_ok=True)
    if output_gpkg.exists():
        output_gpkg.unlink()

    stat_cols = VARIABLES + METRICS
    dc_layers = {nm: [] for nm in [grid_layer, *units_layers]}

    for scenario in range(4):
        values = compute_scenario_values(
            grid=grid,
            scenario=scenario,
            a1_factors=cfg["a1_factors"],
            expansion_factors=expansion_factors,
            scale=cfg["scale"],
        )
        print_summary(scenario, values)
        metrics = compute_performance_metrics(values)

        grid_scenario = grid.copy()
        grid_scenario[VARIABLES] = values[VARIABLES]
        grid_scenario[METRICS] = metrics[METRICS]
        dc_layers[grid_layer].append(grid_scenario)
        grid_scenario.to_file(
            output_gpkg, layer=f"{grid_layer}_cenario{scenario}", driver="GPKG"
        )

        for unit_layer, unit_id in units_layers.items():
            unit_scenario = aggregate_to_unit(
                grid_scenario=grid_scenario,
                unit=units[unit_layer],
                unit_layer=unit_layer,
                unit_id=unit_id,
                stat_cols=stat_cols,
            )
            dc_layers[unit_layer].append(unit_scenario)
            unit_scenario.to_file(
                output_gpkg, layer=f"{unit_layer}_cenario{scenario}", driver="GPKG"
            )

    print(f"Saved: {output_gpkg}")

    plot_all(
        dc_layers=dc_layers,
        grid_layer=grid_layer,
        plots_dir=Path(cfg.get("plots_dir", output_gpkg.parent / "plots")),
        scenario_titles=cfg.get("scenario_titles", {}),
        variable_titles=cfg.get("variable_titles", {}),
        map_background=cfg.get("map_background", "white"),
        decorators=cfg.get("decorators", []),
        scale_bar_km=cfg.get("scale_bar_km"),
    )


if __name__ == "__main__":
    main()
