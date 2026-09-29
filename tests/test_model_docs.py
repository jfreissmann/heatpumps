"""Consistency checks for the generated model setup documentation.

``docs/_ext/hpmodels.py`` turns the model registry, the default parameter
files and the topology diagrams into one documentation page per topology. It
can only do so while those three stay in sync, and while every parameter it
encounters has a known unit and description.

Adding a model or a parameter without updating its counterparts would
otherwise only surface as a broken or silently incomplete documentation build,
so assert the invariants here instead.

These tests import neither ``heatpumps`` nor TESPy and run in well under a
second.

Usage
-----
    pytest tests/test_model_docs.py -q
"""
import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = REPO_ROOT / 'src' / 'heatpumps'
INPUT_DIR = PACKAGE_DIR / 'models' / 'input'
TOPOLOGY_DIR = PACKAGE_DIR / 'static' / 'img' / 'topologies'

SVG_VARIANTS = ('', '_dark', '_label', '_label_dark')


def _load_extension():
    """Import the Sphinx extension straight from ``docs/_ext``."""
    path = REPO_ROOT / 'docs' / '_ext' / 'hpmodels.py'
    spec = importlib.util.spec_from_file_location('hpmodels', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hpmodels = _load_extension()


@pytest.fixture(scope='module')
def registry():
    hp_models, base_topologies, model_classes = hpmodels.load_registry(REPO_ROOT)
    return hp_models, base_topologies, model_classes


@pytest.fixture(scope='module')
def txt():
    return hpmodels.load_translations(REPO_ROOT)


@pytest.fixture(scope='module')
def pages(registry):
    return hpmodels.build_pages(registry[0])


def test_every_model_has_a_parameter_file(registry):
    hp_models = registry[0]
    missing = [
        key for key in hp_models
        if not (INPUT_DIR / f'params_hp_{key}.json').is_file()
        ]
    assert not missing, f'no parameter file for {missing}'


def test_every_model_has_all_topology_diagrams(pages):
    missing = [
        f'hp_{page["topology"]}{variant}.svg'
        for page in pages for variant in SVG_VARIANTS
        if not (TOPOLOGY_DIR / f'hp_{page["topology"]}{variant}.svg').is_file()
        ]
    assert not missing, f'missing topology diagrams: {missing}'


def test_no_orphaned_parameter_files(registry):
    hp_models = registry[0]
    shipped = {
        path.stem[len('params_hp_'):]
        for path in INPUT_DIR.glob('params_hp_*.json')
        }
    assert shipped == set(hp_models)


def test_display_names_are_translated(registry, txt):
    hp_models, base_topologies, _ = registry
    for topology in base_topologies:
        assert txt(topology)
    for key, metadata in hp_models.items():
        assert txt(metadata['display_name']), key


def test_models_pair_up_by_process_type(registry, pages):
    hp_models = registry[0]
    assert len(pages) * 2 == len(hp_models)
    for page in pages:
        processes = {
            hp_models[key]['process_type'] for _, key in page['variants']
            }
        assert processes == {'subcritical', 'transcritical'}, page['name']


def test_page_titles_are_unique(pages, txt):
    titles = {}
    for page in pages:
        title = hpmodels.page_title(txt, page['metadata'])
        assert title not in titles, (
            f'{page["name"]} and {titles.get(title)} share the title {title!r}'
            )
        titles[title] = page['name']


def test_model_classes_cover_every_model(registry):
    hp_models, _, model_classes = registry
    assert set(model_classes) == set(hp_models)


def test_every_parameter_section_is_classified(registry):
    """Every section must map to a group, whether or not it is rendered.

    ``GROUP_ORDER`` selects which groups end up on the page and is meant to be
    edited, so check the classification itself rather than the render list.
    """
    known_groups = {group for _, group in hpmodels.SECTION_INFO.values()}
    known_groups.add(hpmodels.GROUP_CONNECTIONS)
    hp_models = registry[0]
    for key in hp_models:
        params = json.loads(
            (INPUT_DIR / f'params_hp_{key}.json').read_text(encoding='utf-8')
            )
        # Raises ModelDocsError on an unknown section.
        for section in hpmodels.sort_sections(params):
            assert hpmodels.section_group(section) in known_groups


def test_rendered_groups_are_known_groups():
    """Catch a typo in ``GROUP_ORDER``, which would silently render nothing."""
    known_groups = {group for _, group in hpmodels.SECTION_INFO.values()}
    known_groups.add(hpmodels.GROUP_CONNECTIONS)
    assert set(hpmodels.GROUP_ORDER) <= known_groups
    assert hpmodels.GROUP_ORDER, 'at least one group must be rendered'


def test_every_parameter_has_a_unit_and_description(registry):
    hp_models = registry[0]
    unknown = set()
    for key in hp_models:
        params = json.loads(
            (INPUT_DIR / f'params_hp_{key}.json').read_text(encoding='utf-8')
            )
        for section, body in params.items():
            for parameter in body:
                known = (
                    (section, parameter) in hpmodels.SECTION_PARAM_INFO
                    or parameter in hpmodels.PARAM_INFO
                    )
                if not known:
                    unknown.add(f'{section}.{parameter}')
    assert not unknown, (
        f'add {sorted(unknown)} to PARAM_INFO or SECTION_PARAM_INFO in '
        'docs/_ext/hpmodels.py'
        )


def test_rendered_values_are_valid_inline_literals(registry):
    """Inline literals must neither start nor end with whitespace."""
    hp_models = registry[0]
    for key in hp_models:
        params = json.loads(
            (INPUT_DIR / f'params_hp_{key}.json').read_text(encoding='utf-8')
            )
        for section, body in params.items():
            for parameter, value in body.items():
                rendered = hpmodels.format_value(value)
                assert rendered == rendered.strip() and rendered, (
                    f'{key}: {section}.{parameter}'
                    )
