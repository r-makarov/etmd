import json
from pathlib import Path

import colorcet as cc
import numpy as np
from bokeh.embed import file_html
from bokeh.layouts import column, row
from bokeh.models import (ColumnDataSource, CustomJS, Div, HoverTool, LassoSelectTool, LinearColorMapper,
                          MultiLine, Range1d, Scatter, Segment, Select, Slope, Switch)
from bokeh.plotting import figure
from bokeh.resources import CDN
from tmd.Topology.vectorizations import persistence_image_data

ROOT = Path(__file__).resolve().parents[2]
CELL_NAMES = {
    'Hay_2011': 'L5 pyramidal (Hay et al., 2011)',
    'Park_2019': 'L2/3 pyramidal (Park et al., 2019)',
}
LABELS = {
    'path': 'path distance (µm)',
    'electrotonic': 'electrotonic distance X',
}
NEURITES = {'apic': 'apical', 'basal': 'basal'}
REPAIRED_COLOR = 'pink'
PAGE_WIDTH = 1280
FOREGROUND = 'black'
DENSITY_ALPHA = 0.5
MARGIN = 0.05

TEXT = f"""
<h2>Barcode explorer</h2>

<p style="margin-bottom: 10px">
GitHub repository: <a href="https://github.com/r-makarov/etmd" target="_blank">https://github.com/r-makarov/etmd</a>
</p>

<p style="margin-bottom: 10px">
Topological morphology descriptor (TMD) barcodes of dendritic trees (<a href="https://doi.org/10.1007/s12021-017-9341-1" target="_blank">Kanari et al., 2018</a>), 
computed on DendroTweaks section trees (<a href="https://doi.org/10.7554/eLife.103324" target="_blank">Makarov et al., 2025</a>) under two filtrations: 
<ol>
<li>
    Path distance from the soma, as in the <a href="https://tmd.readthedocs.io/en/latest/index.html" target="_blank">TMD package</a>,
</li>
<li>
    Electrotonic distance, which measures length in units of the local length constant of the passive cable
</li>
</ol>
</p>

<p style="margin-bottom: 10px">
Each bar is one branch of the tree, from its tip to the branch point where it merges into a branch that reaches further.
In the persistence diagram each bar is a point: its birth at the tip and its death at the branch point where it ends;
the further from the diagonal, the longer the bar. The shading is the Gaussian kernel density of the diagram,
as in the persistence images of the TMD. Tap or box-select bars, points or branches: the same bars are highlighted in all three views.
Bars in <span style="color: pink"><b>pink</b></span> end at a different branch point than under path distance:
the filtration changes which branch survives there.
<span style="color: steelblue"><b>Apical</b></span> and <span style="color: seagreen"><b>basal</b></span>
dendrites are shown in their own colours.
</p>
"""

REFERENCES = """
<h3>References</h3>
<p>
The barcodes are the topological morphology descriptor (TMD) of Kanari et al. [1, 2], computed with the elder rule
on DendroTweaks section trees [4]; for path distance they reproduce the <a href="https://tmd.readthedocs.io/en/latest/index.html" target="_blank">TMD package</a> [3].
The electrotonic distance replaces path length by length in units of the local length constant, using the passive
properties of the published models [5, 6].
</p>
<ol>
<li>
    Kanari L., Dłotko P., Scolamiero M., Levi R., Shillcock J., Hess K., Markram H. (2018).
    A topological representation of branching neuronal morphologies. <i>Neuroinformatics</i> 16:3–13.
    <a href="https://doi.org/10.1007/s12021-017-9341-1" target="_blank">doi:10.1007/s12021-017-9341-1</a>
</li>
<li>
    Kanari L., Garin A., Hess K. (2020). From trees to barcodes and back again: theoretical and statistical perspectives.
    <i>Algorithms</i> 13:335. <a href="https://doi.org/10.3390/a13120335" target="_blank">doi:10.3390/a13120335</a>
</li>
<li>
    TMD: the topological morphology descriptor, Python package.
    <a href="https://tmd.readthedocs.io/en/latest/index.html" target="_blank">tmd.readthedocs.io</a>
</li>
<li>
    Makarov R., Chavlis S., Poirazi P. (2024). DendroTweaks, an interactive approach for unraveling dendritic dynamics.
    <i>eLife</i> 13:RP103324. <a href="https://doi.org/10.7554/eLife.103324" target="_blank">doi:10.7554/eLife.103324</a>
</li>
<li>
    Hay E., Hill S., Schürmann F., Markram H., Segev I. (2011). Models of neocortical layer 5b pyramidal cells capturing
    a wide range of dendritic and perisomatic active properties. <i>PLoS Computational Biology</i> 7:e1002107.
    <a href="https://doi.org/10.1371/journal.pcbi.1002107" target="_blank">doi:10.1371/journal.pcbi.1002107</a>
</li>
<li>
    Park J., Papoutsi A., Ash R. T., Marin M. A., Poirazi P., Smirnakis S. M. (2019). Contribution of apical and basal
    dendrites to orientation encoding in mouse V1 L2/3 pyramidal neurons. <i>Nature Communications</i> 10:5372.
    <a href="https://doi.org/10.1038/s41467-019-13029-0" target="_blank">doi:10.1038/s41467-019-13029-0</a>
</li>
</ol>
"""


# ======================================================================
# CALLBACKS
# ======================================================================

DATA_CALLBACK = """
const c = cell.value, f = filtration.value
source.data = bars[c][f]
source.selected.indices = []
density.data = densities[c][f]
const [low, high] = limits[c][f]
for (const range of [diagram.x_range, diagram.y_range]) {
    range.start = low
    range.end = high
}
barcode.below[0].axis_label = labels[f]
diagram.below[0].axis_label = 'birth (tip), ' + labels[f]
diagram.left[0].axis_label = 'death (branch point), ' + labels[f]
bar.options = options[c][f][neurite.value]
bar.value = ''
"""

# Show only the bars of one neurite type in the bar selector
FILTER_CALLBACK = """
bar.options = options[cell.value][filtration.value][neurite.value]
if (!bar.options.some(option => option[0] === bar.value)) {
    bar.value = ''
}
"""

# A bar chosen in the selector is selected in the figures
BAR_CALLBACK = """
if (bar.value !== '') {
    source.selected.indices = [Number(bar.value)]
} else if (source.selected.indices.length === 1) {
    source.selected.indices = []
}
"""

# A single bar selected in the figures is shown in the selector (several bars show 'none')
SELECTION_CALLBACK = """
const indices = source.selected.indices
const value = indices.length === 1 ? String(indices[0]) : ''
if (value !== '' && !bar.options.some(option => option[0] === value)) {
    neurite.value = 'all'
    bar.options = options[cell.value][filtration.value]['all']
}
bar.value = value
"""


# ======================================================================
# DERIVED DATA
# ======================================================================

def with_display_color(columns):
    """Add the colour shown on the page: the domain colour, or pink for re-paired bars."""
    colors = [REPAIRED_COLOR if repaired else color
              for color, repaired in zip(columns['color'], columns['repaired'])]
    return {**columns, 'display_color': colors}


def bar_options(columns):
    """Options of the bar selector per neurite filter ('all', 'apical', 'basal'), longest bar first."""
    rows = sorted(range(len(columns['y'])), key=lambda i: columns['y'][i], reverse=True)
    ranked = [(rank, i, NEURITES[columns['domain'][i]]) for rank, i in enumerate(rows, start=1)]
    return {
        neurite: [('', 'none')] + [(str(i), f"{rank} {kind} tip {columns['tip'][i]}")
                                   for rank, i, kind in ranked if neurite in ('all', kind)]
        for neurite in ['all', 'apical', 'basal']
    }


def diagram_limits(columns, margin=MARGIN):
    """Square axis limits from 0 to the largest birth, widened by margin of it on both sides."""
    largest = max(columns['birth'])
    return -margin * largest, (1 + margin) * largest


def density_image(columns, limits, resolution=100):
    """Gaussian kernel density of the persistence diagram on the axis limits, as a Bokeh image.

    Computed with tmd as for persistence images.
    """
    # Images must be NumPy arrays, BokehJS needs their shape.
    low, high = limits
    ph = np.column_stack([columns['birth'], columns['death']])
    z = persistence_image_data(ph, xlim=[low, high], ylim=[low, high], resolution=resolution)
    return {'image': [np.ascontiguousarray(z.T, dtype=np.float32)],
            'x': [low], 'y': [low], 'dw': [high - low], 'dh': [high - low]}


# ======================================================================
# VIEW
# ======================================================================

class View:
    """View of the data in the browser."""

    def __init__(self, data, cell_names):
        """Data as written by prepare_data.py"""
        self.cell_names = cell_names
        self.cell = next(iter(cell_names))
        self.filtration = 'path'
        self.bars = {cell: {name: with_display_color(columns) for name, columns in by_filtration.items()}
                     for cell, by_filtration in data.items()}
        self.limits = {cell: {name: diagram_limits(columns) for name, columns in by_filtration.items()}
                       for cell, by_filtration in data.items()}
        self.densities = {cell: {name: density_image(columns, self.limits[cell][name])
                                 for name, columns in by_filtration.items()}
                          for cell, by_filtration in data.items()}
        self.options = {cell: {name: bar_options(columns) for name, columns in by_filtration.items()}
                        for cell, by_filtration in data.items()}
        self.figures = {}
        self.sources = {}
        self.renderers = {}
        self.widgets = {}

    # Data
    def _create_sources(self):
        """One source with a row per bar, shared by the three figures, and one for the density."""
        self.sources['bars'] = ColumnDataSource(data=self.bars[self.cell][self.filtration], name='bars')
        self.sources['density'] = ColumnDataSource(data=self.densities[self.cell][self.filtration])

    # Figures
    @staticmethod
    def _hide_axes(fig):
        fig.axis.visible = False
        fig.grid.visible = False

    def _create_morphology_figure(self):
        """Each bar's path multi_line of bar_xs / bar_ys."""
        fig = figure(title='Branches', width=420, height=520, match_aspect=True,
                     tools='tap,box_select,pan,wheel_zoom,reset,save', toolbar_location='above')
        self._hide_axes(fig)
        fields = dict(xs='bar_xs', ys='bar_ys', line_color='display_color', line_width=1.5)
        renderer = fig.add_glyph(self.sources['bars'], MultiLine(line_alpha=0.8, **fields))
        renderer.selection_glyph = MultiLine(line_alpha=1, **fields)
        renderer.nonselection_glyph = MultiLine(line_alpha=0.15, **fields)
        self.figures['morphology'] = fig

    def _create_barcode_figure(self):
        """Bars from death to birth at height y."""
        fig = figure(title='Barcode', width=380, height=520,
                     tools='tap,box_select,xwheel_zoom,reset,save', toolbar_location='above',
                     x_axis_label=LABELS[self.filtration])
        fig.yaxis.visible = False
        fig.ygrid.visible = False
        fields = dict(x0='death', x1='birth', y0='y', y1='y', line_color='display_color', line_width=2)
        renderer = fig.add_glyph(self.sources['bars'], Segment(line_alpha=0.9, **fields))
        renderer.selection_glyph = Segment(line_alpha=1, **fields)
        renderer.nonselection_glyph = Segment(line_alpha=0.15, **fields)
        self._add_hover(fig, renderer)
        self.figures['barcode'] = fig

    def _create_diagram_figure(self):
        """Persistence diagram with overlaid persistence image (Gaussian kernel density)."""
        low, high = self.limits[self.cell][self.filtration]
        fig = figure(title='Persistence diagram', width=480, height=520,
                     x_range=Range1d(low, high), y_range=Range1d(low, high),
                     tools='lasso_select,tap,box_select,pan,wheel_zoom,reset,save', toolbar_location='above',
                     x_axis_label='birth (tip), ' + LABELS[self.filtration],
                     y_axis_label='death (branch point), ' + LABELS[self.filtration])
        fig.toolbar.active_drag = fig.select_one(LassoSelectTool)
        self.renderers['density'] = self._add_density(fig, self.sources['density'])
        fig.add_layout(Slope(gradient=1, y_intercept=0, line_color=FOREGROUND, line_alpha=0.6, line_width=1))
        fields = dict(x='birth', y='death', size=8, fill_color='display_color', line_color='white')
        renderer = fig.add_glyph(self.sources['bars'], Scatter(fill_alpha=0.85, **fields))
        renderer.selection_glyph = Scatter(fill_alpha=1, **fields)
        renderer.nonselection_glyph = Scatter(fill_alpha=0.12, line_alpha=0.12, **fields)
        self._add_hover(fig, renderer)
        self.figures['diagram'] = fig

    @staticmethod
    def _add_density(fig, source):
        """Gaussian kernel density of the diagram, behind the points."""
        mapper = LinearColorMapper(palette=cc.rainbow4, low=0, high=1)
        return fig.image(image='image', x='x', y='y', dw='dw', dh='dh', source=source,
                         color_mapper=mapper, alpha=DENSITY_ALPHA)

    @staticmethod
    def _add_hover(fig, renderer):
        """Tooltip (tip, domain, birth, death and re-paired)"""
        fig.add_tools(HoverTool(renderers=[renderer], tooltips=[
            ('tip section', '@tip'), ('domain', '@domain'),
            ('birth', '@birth{0.00}'), ('death', '@death{0.00}'), ('re-paired', '@repaired'),
        ]))

    # Widgets
    def _create_widgets(self):
        """Create widgets and set their callbacks."""

        self.widgets['cell'] = Select(title='Cell', value=self.cell, name='cell',
                                      options=list(self.cell_names.items()))
        self.widgets['filtration'] = Select(title='Filtration', value=self.filtration, name='filtration',
                                            options=list(LABELS.items()))
        self.widgets['neurite'] = Select(title='Neurite', value='all', name='neurite', width=100,
                                         options=['all', 'apical', 'basal'])
        self.widgets['bar'] = Select(title='Bar (longest first)', value='', name='bar', width=220,
                                     options=self.options[self.cell][self.filtration]['all'])
        selectors = dict(cell=self.widgets['cell'], filtration=self.widgets['filtration'],
                         neurite=self.widgets['neurite'], bar=self.widgets['bar'])
        source = self.sources['bars']

        update = CustomJS(
            args=dict(source=source, density=self.sources['density'],
                      bars=self.bars, densities=self.densities, limits=self.limits,
                      options=self.options, labels=LABELS, **selectors,
                      barcode=self.figures['barcode'], diagram=self.figures['diagram']),
            code=DATA_CALLBACK,
        )
        self.widgets['cell'].js_on_change('value', update)
        self.widgets['filtration'].js_on_change('value', update)
        self.widgets['neurite'].js_on_change('value', CustomJS(
            args=dict(options=self.options, **selectors), code=FILTER_CALLBACK))
        self.widgets['bar'].js_on_change('value', CustomJS(
            args=dict(source=source, bar=self.widgets['bar']), code=BAR_CALLBACK))
        source.selected.js_on_change('indices', CustomJS(
            args=dict(source=source, options=self.options, **selectors), code=SELECTION_CALLBACK))

    def _create_density_switch(self, name, renderer):
        """A switch that shows or hides the density behind a persistence diagram."""
        self.widgets[name] = Switch(active=True, name=name)
        self.widgets[name].js_on_change('active', CustomJS(
            args=dict(renderer=renderer, toggle=self.widgets[name]),
            code='renderer.visible = toggle.active',
        ))
        return column(Div(text='Density'), self.widgets[name])

    # Page layout
    def create_layout(self):
        """Create the sources, figures and widgets, and return the layout."""
        self._create_sources()
        self._create_morphology_figure()
        self._create_barcode_figure()
        self._create_diagram_figure()
        self._create_widgets()
        controls = row(self.widgets['cell'], self.widgets['filtration'],
                       self.widgets['neurite'], self.widgets['bar'],
                       self._create_density_switch('density', self.renderers['density']))
        return column(
            Div(text=TEXT, width=PAGE_WIDTH),
            controls,
            row(self.figures['morphology'], self.figures['barcode'], self.figures['diagram']),
            Div(text=REFERENCES, width=PAGE_WIDTH),
            styles={'margin': '0 auto'},
        )


def main():
    data = {cell: json.loads((ROOT / 'data' / cell / 'barcodes.json').read_text()) for cell in CELL_NAMES}
    layout = View(data, CELL_NAMES).create_layout()
    output = ROOT / 'docs' / 'index.html'
    output.parent.mkdir(exist_ok=True)
    output.write_text(file_html(layout, CDN, 'Electrotonic barcodes'))


if __name__ == '__main__':
    main()
