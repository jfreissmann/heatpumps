# %% Important variables for the heat pump dashboard

# %% Model parameters
base_topologies = (
    'Einfacher Kreis',
    'Zwischenkühlung',
    'Economizer',
    'Flashtank',
    'Kaskadierter Kreis'
    )

hp_models = {
    'simple': {
        'base_topology': 'Einfacher Kreis',
        'display_name': 'Allgemein',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': None,
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'ihx': {
        'base_topology': 'Einfacher Kreis',
        'display_name': 'Interne WÜT',
        'nr_ihx': 1,
        'econ_type': None,
        'comp_var': None,
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'ic': {
        'base_topology': 'Zwischenkühlung',
        'display_name': 'Allgemein',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'econ_closed': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'econ_closed_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante A)',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'ihx_econ_closed': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante B)',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'econ_open': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'econ_open_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante A)',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'ihx_econ_open': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante B)',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_closed': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_closed_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_closed_2ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | doppelte interne WÜT',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_open': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_open_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | interne WÜT',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_open_2ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | doppelte interne WÜT',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_cycles': 1,
        'process_type': 'subcritical'
        },
    'flash': {
        'base_topology': 'Flashtank',
        'display_name': 'Allgemein',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_cycles': 2,
        'process_type': 'subcritical'
        },
    'cascade': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Allgemein',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_cycles': 2,
        'process_type': 'subcritical'
        },
    'cascade_2ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Doppelte interne WÜT',
        'nr_ihx': 2,
        'econ_type': None,
        'comp_var': 'series',
        'nr_cycles': 2,
        'process_type': 'subcritical'
        }
    }

# %% Misc
econ_translate = {
    'offen': 'open',
    'geschlossen': 'closed'
}
comp_translate = {
    'Reihenschaltung': 'series',
    'Parallelschaltung': 'parallel'
}

# %% Styling
st_color_hex = '#ff4b4b'
