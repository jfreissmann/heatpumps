"""Tests for ``HeatPumpBase.generate_sankey_diagram`` on exerpy's
``SankeyBuilder``.

The node and link topology comes from exerpy, while heatpumps applies its
own colors and labels, and prunes nodes without links. These tests pin that
contract down, as well as the exergy balance that the diagram is drawn from.

Usage
-----
    pytest tests/test_sankey.py -q
"""
import logging
import math

import plotly.graph_objects as go
import pytest

from heatpumps.models import HeatPumpCascade, HeatPumpSimple
from heatpumps.models.HeatPumpBase import SANKEY_COLORS
from heatpumps.parameters import get_params

logging.disable(logging.CRITICAL)

LABELS = {
    'fuel_label': 'Fuel',
    'product_label': 'Product',
    'destruction_label': 'Destruction',
    'loss_label': 'Loss',
    'net_suffix': '(netto)',
}

CASES = [
    (HeatPumpSimple, None),
    # Gaseous source: the recirculation device is a fan.
    (HeatPumpSimple, 'Air'),
    # The intermediate heat exchanger is a TESPy ``Condenser`` as well.
    (HeatPumpCascade, None),
]
CASE_IDS = [
    cls.__name__ if source is None else f'{cls.__name__}-{source}'
    for cls, source in CASES
]


@pytest.fixture(scope='module', params=CASES, ids=CASE_IDS)
def hp(request):
    cls, source = request.param
    params = get_params(cls.__name__)
    if source is not None:
        params['fluids']['so'] = source

    hp = cls(params=params)
    hp.run_model(iterinfo=False)

    assert hp.nw.status == 0, (
        f'{cls.__name__} did not converge (status={hp.nw.status})'
    )
    return hp


@pytest.fixture(scope='module')
def sankey(hp):
    fig = hp.generate_sankey_diagram(
        label_map={'Condenser': 'Kondensator'}, **LABELS
        )
    return fig.data[0]


def component_destructions(ean):
    """Return the finite exergy destruction of each component."""
    destructions = {}
    for label, comp in ean.components.items():
        E_D = getattr(comp, 'E_D', None)
        if E_D is not None and not math.isnan(E_D):
            destructions[label] = E_D
    return destructions


def test_condensers_are_productive_heat_exchangers(hp):
    """TESPy ``Condenser`` must be analysed as productive heat exchanger.

    exerpy maps it to ``HeatExchanger`` since v0.0.11, which heatpumps used
    to patch in itself. Analysed as dissipative, it has no exergy product.
    """
    condensers = [
        c.label for c in hp.nw.comps['object']
        if c.__class__.__name__ == 'Condenser'
    ]
    assert condensers

    for label in condensers:
        comp = hp.ean.components[label]
        assert comp.__class__.__name__ == 'HeatExchanger'
        assert math.isfinite(comp.E_P), f'{label} has no exergy product'


def test_exergy_balance_closes(hp):
    # The consumer lies outside of the product boundary, so its small
    # destruction (about 0.05 %) is part of the components' sum only.
    assert sum(component_destructions(hp.ean).values()) == pytest.approx(
        hp.ean.E_D, rel=1e-2
        )


def test_single_sankey_trace(hp):
    fig = hp.generate_sankey_diagram()

    assert len(fig.data) == 1
    assert isinstance(fig.data[0], go.Sankey)


def test_every_node_is_linked(sankey):
    linked = set(sankey.link.source) | set(sankey.link.target)

    assert linked == set(range(len(sankey.node.label)))


def test_link_values_are_positive(sankey):
    assert len(sankey.link.value) > 0
    assert all(value > 0 for value in sankey.link.value)


def test_node_labels(sankey):
    labels = list(sankey.node.label)

    assert LABELS['fuel_label'] in labels
    assert LABELS['product_label'] in labels
    assert LABELS['destruction_label'] in labels
    # Heat pumps have no exergy loss, so its node is pruned.
    assert LABELS['loss_label'] not in labels
    # The product boundary has inputs and outputs, so exerpy inserts a net
    # node in front of the product node.
    assert f"{LABELS['product_label']} {LABELS['net_suffix']}" in labels
    assert 'Kondensator' in labels
    assert 'Condenser' not in labels
    assert not any(label.startswith('__') for label in labels)


def test_destruction_links_match_components(hp, sankey):
    target = list(sankey.node.label).index(LABELS['destruction_label'])
    destruction = sum(
        value for value, tgt in zip(sankey.link.value, sankey.link.target)
        if tgt == target
        )
    expected = sum(
        E_D for E_D in component_destructions(hp.ean).values() if E_D > 0
        )

    assert destruction == pytest.approx(expected, rel=1e-9)


@pytest.mark.parametrize('kind,category', [
    ('material', 'two-phase-fluid'),
    ('power', 'work'),
])
def test_reversed_link_is_pale(hp, kind, category):
    conn_id = next(
        label for label, conn in hp.ean.connections.items()
        if conn.get('kind') == kind
        )
    nodes = [{'id': 'Upstream'}, {'id': 'Downstream'}]
    link = {'source': 0, 'target': 1, 'label': f'{conn_id} [E]: 1.0 kW'}
    reversed_link = {**link, 'label': f"{link['label']} (reversed)"}

    color = hp._sankey_link_color(link, nodes, SANKEY_COLORS)
    reversed_color = hp._sankey_link_color(
        reversed_link, nodes, SANKEY_COLORS
        )

    assert color == SANKEY_COLORS[category]
    assert reversed_color.startswith('rgba(')
    assert reversed_color.endswith(',0.25)')
