"""Generate the model setup reference pages of the heatpumps documentation.

The heat pump model registry, the default parameter files and the topology
diagrams all live inside ``src/heatpumps``. This extension reads them at build
time and emits one reStructuredText page per topology into
``docs/documentation/models/``, plus an overview page.

The registry is read with :mod:`ast` rather than by importing ``heatpumps``.
``src/heatpumps/variables.py`` starts with a flat ``from models import (...)``
that only resolves when Streamlit puts the package directory on ``sys.path``,
and importing ``heatpumps.parameters`` instead would pull in all 44 model
modules (and with them TESPy and CoolProp) on every documentation build.
Parsing the module literally costs a few milliseconds and no imports at all.

Both the generated pages and the copied diagrams are gitignored.
"""

import ast
import json
import re
import shutil
from pathlib import Path

from sphinx.util import logging

logger = logging.getLogger(__name__)

LANGUAGE = 'ENG'

#: Where the topology diagrams are staged inside the documentation source,
#: relative to it. Deliberately not below ``_static``: Sphinx copies every
#: referenced image into ``_images`` anyway, so a staging directory that is
#: also a static path would ship all of them twice.
STAGING_DIR = '_topologies'

#: Connection sections are named after the labels in the topology diagrams,
#: e.g. ``A6``, ``B1``, ``C3``, ``D5``.
CONNECTION_PATTERN = re.compile(r'^([A-D])(\d+)$')

#: Letter prefix of a connection label -> which part of the plant it belongs to.
CONNECTION_GROUPS = {
    'A': 'Refrigerant cycle (low temperature cycle in cascaded models)',
    'B': 'Heat source',
    'C': 'Heat sink / consumer',
    'D': 'High temperature refrigerant cycle (cascaded models)',
}

GROUP_SETUP = 'Setup and fluids'
GROUP_COMPONENTS = 'Components'
GROUP_CONNECTIONS = 'Connections'
GROUP_SIMULATION = 'Diagram and offdesign'

GROUP_ORDER = (GROUP_SETUP, GROUP_COMPONENTS, GROUP_CONNECTIONS)  # , GROUP_SIMULATION)

#: JSON section -> (heading, group). Connection sections are handled separately.
SECTION_INFO = {
    'setup': ('Setup', GROUP_SETUP),
    'fluids': ('Fluids', GROUP_SETUP),
    'ambient': ('Ambient state', GROUP_SETUP),
    'cond': ('Condenser', GROUP_COMPONENTS),
    'trans': ('Transcritical heat exchanger', GROUP_COMPONENTS),
    'evap': ('Evaporator', GROUP_COMPONENTS),
    'inter': ('Intermediate heat exchanger', GROUP_COMPONENTS),
    'econ': ('Economizer', GROUP_COMPONENTS),
    'econ1': ('Economizer 1', GROUP_COMPONENTS),
    'econ2': ('Economizer 2', GROUP_COMPONENTS),
    'ihx': ('Internal heat exchanger', GROUP_COMPONENTS),
    'ihx1': ('Internal heat exchanger 1', GROUP_COMPONENTS),
    'ihx2': ('Internal heat exchanger 2', GROUP_COMPONENTS),
    'ihx3': ('Internal heat exchanger 3', GROUP_COMPONENTS),
    'ihx4': ('Internal heat exchanger 4', GROUP_COMPONENTS),
    'ic': ('Intercooler', GROUP_COMPONENTS),
    'ic1': ('Intercooler 1', GROUP_COMPONENTS),
    'ic2': ('Intercooler 2', GROUP_COMPONENTS),
    'comp': ('Compressor', GROUP_COMPONENTS),
    'comp1': ('Compressor 1', GROUP_COMPONENTS),
    'comp2': ('Compressor 2', GROUP_COMPONENTS),
    'LT_comp': ('Low temperature compressor', GROUP_COMPONENTS),
    'LT_comp1': ('Low temperature compressor 1', GROUP_COMPONENTS),
    'LT_comp2': ('Low temperature compressor 2', GROUP_COMPONENTS),
    'HT_comp': ('High temperature compressor', GROUP_COMPONENTS),
    'HT_comp1': ('High temperature compressor 1', GROUP_COMPONENTS),
    'HT_comp2': ('High temperature compressor 2', GROUP_COMPONENTS),
    'cons': ('Consumer', GROUP_COMPONENTS),
    'hs_pump': ('Heat source pump', GROUP_COMPONENTS),
    'cons_pump': ('Consumer pump', GROUP_COMPONENTS),
    'logph': ('State diagram limits', GROUP_SIMULATION),
    'offdesign': ('Offdesign simulation', GROUP_SIMULATION),
}

#: Presentation order of the non-connection sections.
SECTION_ORDER = tuple(SECTION_INFO)

DIMENSIONLESS = '–'

#: Parameter name -> (unit, description), valid in any section.
#:
#: The units follow the TESPy network defaults set in
#: ``HeatPumpBase.__init__`` (``temperature='degC'``, ``pressure='bar'``,
#: ``enthalpy='kJ / kg'``, ``mass_flow='kg / s'``).
PARAM_INFO = {
    'T': ('°C', 'Temperature'),
    'p': ('bar', 'Pressure'),
    'x': (DIMENSIONLESS, 'Vapour quality'),
    'eta_s': (DIMENSIONLESS, 'Isentropic efficiency'),
    'pr': (DIMENSIONLESS, 'Pressure ratio'),
    'pr1': (DIMENSIONLESS, 'Pressure ratio, hot side'),
    'pr2': (DIMENSIONLESS, 'Pressure ratio, cold side'),
    'ttd_u': ('K', 'Upper terminal temperature difference'),
    'ttd_l': ('K', 'Lower terminal temperature difference'),
    'dT_sh': ('K', 'Superheating and subcooling'),
    'dT_ic': ('K', 'Temperature difference of the intercooling'),
    'Q': ('W', 'Heat demand of the consumer (negative: rejected by the cycle)'),
}

#: (section, parameter) -> (unit, description), overriding :data:`PARAM_INFO`.
SECTION_PARAM_INFO = {
    ('setup', 'name'): (DIMENSIONLESS, 'Descriptive name of the configuration'),
    ('setup', 'type'): (DIMENSIONLESS, 'Identifier used for export file names'),
    ('setup', 'refrig'): (DIMENSIONLESS, 'Refrigerant'),
    ('setup', 'refrig1'): (DIMENSIONLESS, 'Refrigerant of the low temperature cycle'),
    ('setup', 'refrig2'): (DIMENSIONLESS, 'Refrigerant of the high temperature cycle'),
    ('fluids', 'wf'): (DIMENSIONLESS, 'Working fluid'),
    ('fluids', 'wf1'): (DIMENSIONLESS, 'Working fluid of the low temperature cycle'),
    ('fluids', 'wf2'): (DIMENSIONLESS, 'Working fluid of the high temperature cycle'),
    ('fluids', 'si'): (DIMENSIONLESS, 'Fluid of the heat sink'),
    ('fluids', 'so'): (DIMENSIONLESS, 'Fluid of the heat source'),
    ('logph', 'x_min'): ('kJ/kg', 'Lower limit of the enthalpy axis'),
    ('logph', 'x_max'): ('kJ/kg', 'Upper limit of the enthalpy axis'),
    ('logph', 'y_min'): ('bar', 'Lower limit of the pressure axis'),
    ('logph', 'y_max'): ('bar', 'Upper limit of the pressure axis'),
    ('offdesign', 'T_hs_ff_start'): ('°C', 'Heat source feed flow temperature, first step'),
    ('offdesign', 'T_hs_ff_end'): ('°C', 'Heat source feed flow temperature, last step'),
    ('offdesign', 'T_hs_ff_steps'): (DIMENSIONLESS, 'Number of heat source temperature steps'),
    ('offdesign', 'T_cons_ff_start'): ('°C', 'Consumer feed flow temperature, first step'),
    ('offdesign', 'T_cons_ff_end'): ('°C', 'Consumer feed flow temperature, last step'),
    ('offdesign', 'T_cons_ff_steps'): (DIMENSIONLESS, 'Number of consumer temperature steps'),
    ('offdesign', 'partload_min'): (DIMENSIONLESS, 'Lowest simulated part load fraction'),
    ('offdesign', 'partload_max'): (DIMENSIONLESS, 'Highest simulated part load fraction'),
    ('offdesign', 'partload_steps'): (DIMENSIONLESS, 'Number of part load steps'),
    ('offdesign', 'save_results'): (DIMENSIONLESS, 'Write the results into the user cache directory'),
}

PROCESS_LABELS = {
    'subcritical': 'Subcritical',
    'transcritical': 'Transcritical',
}

TRANS_SUFFIX = '_trans'


class ModelDocsError(RuntimeError):
    """Raised when the model registry and its assets are inconsistent."""


# %% Reading the registry


def _assignments(module_path):
    """Map every top level assignment of a module to its value node."""
    tree = ast.parse(module_path.read_text(encoding='utf-8'))
    nodes = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                nodes[target.id] = node.value
    return nodes


def load_registry(repo_root):
    """Read ``hp_models``, ``base_topologies`` and the model class names.

    ``hp_model_classes`` maps to the classes themselves, so it cannot be
    evaluated literally. All of its values are plain names though, which is
    all that is needed here.
    """
    nodes = _assignments(repo_root / 'src' / 'heatpumps' / 'variables.py')
    missing = {'hp_models', 'base_topologies', 'hp_model_classes'} - set(nodes)
    if missing:
        raise ModelDocsError(
            f'variables.py does not define {", ".join(sorted(missing))}'
            )

    hp_models = ast.literal_eval(nodes['hp_models'])
    base_topologies = ast.literal_eval(nodes['base_topologies'])

    classes_node = nodes['hp_model_classes']
    if not isinstance(classes_node, ast.Dict):
        raise ModelDocsError('hp_model_classes is not a dictionary literal')
    model_classes = {}
    for key, value in zip(classes_node.keys, classes_node.values):
        if not isinstance(value, ast.Name):
            raise ModelDocsError(
                f'hp_model_classes[{ast.literal_eval(key)!r}] is not a plain '
                'class name'
                )
        model_classes[ast.literal_eval(key)] = value.id

    return hp_models, base_topologies, model_classes


def load_translations(repo_root):
    """Return a lookup of translation key to its English text."""
    tlpath = repo_root / 'src' / 'heatpumps' / 'static' / 'translations.json'
    translations = json.loads(tlpath.read_text(encoding='utf-8'))

    def txt(key):
        try:
            return translations[key][LANGUAGE]
        except KeyError:
            raise ModelDocsError(
                f'translations.json has no {LANGUAGE} entry for {key!r}'
                ) from None

    return txt


def build_pages(hp_models):
    """Pair every subcritical model with its transcritical counterpart.

    All 72 models come in such pairs, and both members share one topology
    diagram, so each pair becomes a single page.
    """
    pages = []
    for model_key, metadata in hp_models.items():
        if model_key.endswith(TRANS_SUFFIX):
            continue
        trans_key = f'{model_key}{TRANS_SUFFIX}'
        if trans_key not in hp_models:
            raise ModelDocsError(
                f'model {model_key!r} has no transcritical counterpart'
                )
        pages.append({
            'name': model_key,
            'metadata': metadata,
            'topology': model_key,
            'variants': [
                ('subcritical', model_key),
                ('transcritical', trans_key),
            ],
        })
    return pages


# %% Formatting helpers


def indent(lines, level=1):
    """Indent a block of reStructuredText by ``level`` steps of four spaces."""
    prefix = '    ' * level
    return [f'{prefix}{line}' if line else '' for line in lines]


def format_value(value):
    """Render a JSON value the way it reads in the parameter file.

    The result ends up inside an inline literal, which must neither start nor
    end with whitespace. A few of the shipped parameter files have a stray
    space in ``setup.name``, so strip it here.
    """
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, float):
        return f'{value:g}'
    return str(value).strip() or DIMENSIONLESS


def param_info(section, parameter, model_key):
    """Look up unit and description, warning about unknown parameters."""
    if (section, parameter) in SECTION_PARAM_INFO:
        return SECTION_PARAM_INFO[(section, parameter)]
    if parameter in PARAM_INFO:
        return PARAM_INFO[parameter]
    logger.warning(
        f'no unit and description known for {section}.{parameter} '
        f'(params_hp_{model_key}.json); add it to PARAM_INFO or '
        'SECTION_PARAM_INFO in docs/_ext/hpmodels.py',
        type='hpmodels', subtype='unknown_parameter'
        )
    return (DIMENSIONLESS, '')


def sort_sections(sections):
    """Order the sections of a parameter file for presentation."""
    def key(section):
        match = CONNECTION_PATTERN.match(section)
        if match:
            return (1, match.group(1), int(match.group(2)), '')
        try:
            return (0, '', SECTION_ORDER.index(section), '')
        except ValueError:
            raise ModelDocsError(
                f'unknown parameter section {section!r}; add it to '
                'SECTION_INFO in docs/_ext/hpmodels.py'
                ) from None
    return sorted(sections, key=key)


def section_heading(section):
    """Human readable heading for a parameter section."""
    match = CONNECTION_PATTERN.match(section)
    if match:
        return f'Connection ``{section}``'
    return f'{SECTION_INFO[section][0]} (``{section}``)'


def section_group(section):
    if CONNECTION_PATTERN.match(section):
        return GROUP_CONNECTIONS
    return SECTION_INFO[section][1]


def parameter_table(model_key, section, body):
    """Render one parameter section as a ``list-table``."""
    lines = [
        f'.. list-table:: {section_heading(section)}',
        '    :header-rows: 1',
        '    :width: 100%',
        '    :widths: 25 20 12 43',
        '',
        '    * - Parameter',
        '      - Value',
        '      - Unit',
        '      - Description',
    ]
    for parameter, value in body.items():
        unit, description = param_info(section, parameter, model_key)
        lines.extend([
            f'    * - ``{parameter}``',
            f'      - ``{format_value(value)}``',
            f'      - {unit}',
            f'      - {description or DIMENSIONLESS}',
        ])
    lines.append('')
    return lines


def raw_json_block(model_key, text):
    """Collapsible verbatim copy of the parameter file."""
    lines = [
        f'.. dropdown:: Full parameter file (``params_hp_{model_key}.json``)',
        '',
        '    .. code-block:: json',
        '',
    ]
    lines.extend(indent(text.rstrip().splitlines(), 2))
    lines.append('')
    return lines


def variant_body(model_key, params, raw_text):
    """Render the parameter tables of one model, grouped by topic."""
    sections = sort_sections(params)
    lines = []
    for group in GROUP_ORDER:
        in_group = [s for s in sections if section_group(s) == group]
        if not in_group:
            continue
        lines.extend([f'.. rubric:: {group}', ''])
        if group == GROUP_CONNECTIONS:
            letters = sorted({CONNECTION_PATTERN.match(s).group(1) for s in in_group})
            lines.append(
                'The connection labels match the annotated topology diagram '
                'above:'
                )
            lines.append('')
            for letter in letters:
                lines.append(f'* ``{letter}`` — {CONNECTION_GROUPS[letter]}')
            lines.append('')
        for section in in_group:
            lines.extend(parameter_table(model_key, section, params[section]))
    lines.extend(raw_json_block(model_key, raw_text))
    return lines


# %% Page rendering


def figure_pair(topology, alt, caption):
    """Light and dark variant of one topology diagram."""
    lines = []
    for suffix, figclass in (('', 'only-light'), ('_dark', 'only-dark')):
        lines.extend([
            f'.. figure:: /{STAGING_DIR}/hp_{topology}{suffix}.svg',
            '    :align: center',
            f'    :alt: {alt}',
            f'    :figclass: {figclass}',
            '',
            f'    {caption}',
            '',
        ])
    return lines


def page_title(txt, metadata):
    """Globally unique title, combining base topology and variant name."""
    return f'{txt(metadata["base_topology"])} — {txt(metadata["display_name"])}'


def render_page(page, txt, model_classes, input_dir):
    """Render one complete topology page."""
    metadata = page['metadata']
    topology = page['topology']
    title = page_title(txt, metadata)

    lines = [
        f'.. _hpmodel-{page["name"]}:',
        '',
        '~' * len(title),
        title,
        '~' * len(title),
        '',
    ]

    caption = f'Topology of the {txt(metadata["display_name"])} model'
    # lines.extend(figure_pair(topology, title, caption))

    # lines.extend([
    #     '.. dropdown:: Diagram with component and connection labels',
    #     '',
    # ])
    # lines.extend(indent(figure_pair(
    lines.extend(figure_pair(
        f'{topology}_label', f'{title}, with labels',
        f'{caption}, annotated with connection labels'
        ))
        # )))

    econ_type = metadata['econ_type'] or 'none'
    comp_var = metadata['comp_var'] or 'single stage'
    lines.extend([
        f':Base topology: {txt(metadata["base_topology"])}',
        f':Variant: {txt(metadata["display_name"])}',
        f':Economizer: {econ_type}',
        f':Compression: {comp_var}',
        f':Internal heat exchangers: {metadata["nr_ihx"]}',
        f':Refrigerant cycles: {metadata["nr_refrigs"]}',
    ])
    for process, model_key in page['variants']:
        lines.append(
            f':{PROCESS_LABELS[process]}: model key ``{model_key}``, class '
            f'``{model_classes[model_key]}``'
            )
    lines.extend([
        '',
        'The tables below list the default parameters, i.e. the values that '
        '``get_params()`` returns before you change anything.',
        '',
        '.. tab-set::',
        '',
    ])

    for process, model_key in page['variants']:
        parampath = input_dir / f'params_hp_{model_key}.json'
        if not parampath.is_file():
            raise ModelDocsError(f'missing parameter file {parampath}')
        raw_text = parampath.read_text(encoding='utf-8')
        params = json.loads(raw_text)
        body = variant_body(model_key, params, raw_text)
        lines.extend(indent([f'.. tab-item:: {PROCESS_LABELS[process]}', '']))
        lines.extend(indent(body, 2))

    return '\n'.join(lines).rstrip() + '\n'


def render_index(pages, txt, base_topologies, model_classes):
    """Render the overview page with a card grid per base topology."""
    title = 'Model setups'
    by_topology = {topology: [] for topology in base_topologies}
    for page in pages:
        by_topology[page['metadata']['base_topology']].append(page)

    lines = [
        '.. _model_setups_label:',
        '',
        '~' * len(title),
        title,
        '~' * len(title),
        '',
        'heatpumps ships {0} heat pump model configurations, grouped into the '
        '{1} base topologies below. Every configuration exists as a '
        'subcritical and a transcritical process; the two share a topology '
        'and differ only in their parametrization, so they are documented '
        'together on one page.'.format(
            len(pages) * 2, len(base_topologies)
            ),
        '',
        'Each page shows the topology diagram and the default parameters that '
        '``get_params()`` returns for that model. Use them as the starting '
        'point described in :ref:`model_classes_label`.',
        '',
        '.. note::',
        '',
        '    Units follow the TESPy network defaults used by all models: '
        'temperatures in °C, pressures in bar, specific enthalpies in kJ/kg '
        'and mass flows in kg/s. The consumer heat demand ``cons.Q`` is the '
        'one exception and is given in W, with a negative sign because the '
        'heat is rejected by the cycle.',
        '',
    ]

    for topology in base_topologies:
        heading = txt(topology)
        lines.extend([heading, '=' * len(heading), '', '.. grid:: 1 2 2 3', '    :gutter: 3', ''])
        for page in by_topology[topology]:
            card = [
                f'.. grid-item-card:: {txt(page["metadata"]["display_name"])}',
                f'    :link: {page["name"]}',
                '    :link-type: doc',
                '',
            ]
            for process, model_key in page['variants']:
                card.append(f'    | ``{model_key}``')
            card.append('')
            lines.extend(indent(card))
        lines.append('')

    lines.extend([
        '.. dropdown:: All model keys and their classes',
        '',
        '    .. list-table::',
        '        :header-rows: 1',
        '        :width: 100%',
        '        :widths: 30 30 20 20',
        '',
        '        * - Model key',
        '          - Class',
        '          - Process',
        '          - Economizer',
    ])
    for page in pages:
        for process, model_key in page['variants']:
            econ_type = page['metadata']['econ_type'] or DIMENSIONLESS
            lines.extend([
                f'        * - ``{model_key}``',
                f'          - ``{model_classes[model_key]}``',
                f'          - {PROCESS_LABELS[process]}',
                f'          - {econ_type}',
            ])
    lines.extend([
        '',
        '..  toctree::',
        '    :maxdepth: 1',
        '    :hidden:',
        '',
    ])
    for topology in base_topologies:
        for page in by_topology[topology]:
            lines.append(f'    {page["name"]}')

    return '\n'.join(lines).rstrip() + '\n'


# %% Assets and output


def copy_topology_svgs(pages, source_dir, target_dir):
    """Copy the diagrams into the source tree so Sphinx can resolve them.

    Sphinx only resolves image targets below the documentation source
    directory, so referencing ``src/heatpumps/static`` directly is not an
    option.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for page in pages:
        for suffix in ('', '_dark', '_label', '_label_dark'):
            name = f'hp_{page["topology"]}{suffix}.svg'
            source = source_dir / name
            if not source.is_file():
                raise ModelDocsError(f'missing topology diagram {source}')
            target = target_dir / name
            if target.is_file():
                stat_source, stat_target = source.stat(), target.stat()
                if (stat_source.st_size == stat_target.st_size
                        and stat_source.st_mtime <= stat_target.st_mtime):
                    continue
            shutil.copy2(source, target)
            copied += 1
    return copied


def write_if_changed(path, content):
    """Only touch a file when its content actually changed.

    Rewriting all pages on every run would make Sphinx reread them all.
    """
    if path.is_file() and path.read_text(encoding='utf-8') == content:
        return False
    path.write_text(content, encoding='utf-8')
    return True


def generate(app):
    """Entry point, connected to Sphinx' ``builder-inited`` event."""
    srcdir = Path(app.srcdir)
    repo_root = srcdir.parent
    package_dir = repo_root / 'src' / 'heatpumps'

    hp_models, base_topologies, model_classes = load_registry(repo_root)
    txt = load_translations(repo_root)
    pages = build_pages(hp_models)

    titles = {}
    for page in pages:
        title = page_title(txt, page['metadata'])
        if title in titles:
            raise ModelDocsError(
                f'models {titles[title]!r} and {page["name"]!r} share the '
                f'page title {title!r}'
                )
        titles[title] = page['name']

    copied = copy_topology_svgs(
        pages,
        package_dir / 'static' / 'img' / 'topologies',
        srcdir / STAGING_DIR
        )

    outdir = srcdir / 'documentation' / 'models'
    outdir.mkdir(parents=True, exist_ok=True)
    input_dir = package_dir / 'models' / 'input'

    written = 0
    generated = {'index.rst'}
    for page in pages:
        content = render_page(page, txt, model_classes, input_dir)
        generated.add(f'{page["name"]}.rst')
        written += write_if_changed(outdir / f'{page["name"]}.rst', content)

    written += write_if_changed(
        outdir / 'index.rst',
        render_index(pages, txt, base_topologies, model_classes)
        )

    for stale in outdir.glob('*.rst'):
        if stale.name not in generated:
            stale.unlink()

    logger.info(
        f'[hpmodels] {len(pages)} model pages ({written} updated), '
        f'{copied} diagrams copied'
        )


def setup(app):
    app.connect('builder-inited', generate)
    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
