from models import (HeatPumpCascade, HeatPumpCascade2IHX,
                    HeatPumpCascade2IHXTrans, HeatPumpCascadeTrans,
                    HeatPumpEcon, HeatPumpEconIHX, HeatPumpEconIHXTrans,
                    HeatPumpEconTrans, HeatPumpFlash, HeatPumpFlashTrans,
                    HeatPumpIC, HeatPumpICTrans, HeatPumpIHX, HeatPumpIHXEcon,
                    HeatPumpIHXEconTrans, HeatPumpIHXPC, HeatPumpIHXPCIHX,
                    HeatPumpIHXPCIHXTrans, HeatPumpIHXPCTrans,
                    HeatPumpIHXTrans, HeatPumpPC, HeatPumpPCIHX,
                    HeatPumpPCIHXTrans, HeatPumpPCTrans, HeatPumpSimple,
                    HeatPumpSimpleTrans, HeatPumpCascadeEcon, HeatPumpCascadeEconIHX,
                    HeatPumpCascadeEconIHXTrans, HeatPumpCascadeEconTrans,
                    HeatPumpCascadeFlash, HeatPumpCascadeFlashTrans,
                    HeatPumpCascadeIC, HeatPumpCascadeICTrans, HeatPumpCascadeIHXEcon,
                    HeatPumpCascadeIHXEconTrans, HeatPumpCascadeIHXPC,
                    HeatPumpCascadeIHXPCIHX, HeatPumpCascadeIHXPCIHXTrans,
                    HeatPumpCascadeIHXPCTrans, HeatPumpCascadePC,
                    HeatPumpCascadePCIHX, HeatPumpCascadePCIHXTrans,
                    HeatPumpCascadePCTrans)

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
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ihx': {
        'base_topology': 'Einfacher Kreis',
        'display_name': 'Interne WÜT',
        'nr_ihx': 1,
        'econ_type': None,
        'comp_var': None,
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'simple_trans': {
        'base_topology': 'Einfacher Kreis',
        'display_name': 'Allgemein | Transkritisch',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': None,
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ihx_trans': {
        'base_topology': 'Einfacher Kreis',
        'display_name': 'Interne WÜT | Transkritisch',
        'nr_ihx': 1,
        'econ_type': None,
        'comp_var': None,
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ic': {
        'base_topology': 'Zwischenkühlung',
        'display_name': 'Allgemein',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ic_trans': {
        'base_topology': 'Zwischenkühlung',
        'display_name': 'Allgemein | Transkritisch',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'econ_closed': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'econ_closed_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ihx_econ_closed': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante A)',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ihx_econ_closed_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'econ_closed_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante B)',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'econ_closed_ihx_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'econ_open': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'econ_open_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ihx_econ_open': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante A)',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ihx_econ_open_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'econ_open_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante B)',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'econ_open_ihx_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'pc_econ_closed': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_closed_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ihx_pc_econ_closed': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante A)',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ihx_pc_econ_closed_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'pc_econ_closed_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante B)',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_closed_ihx_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ihx_pc_econ_closed_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | doppelte interne WÜT',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ihx_pc_econ_closed_ihx_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Geschlossen | Parallelschaltung | doppelte interne WÜT | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'pc_econ_open': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_open_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ihx_pc_econ_open': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante A)',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ihx_pc_econ_open_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'pc_econ_open_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante B)',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'pc_econ_open_ihx_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 1,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'ihx_pc_econ_open_ihx': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | doppelte interne WÜT',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'ihx_pc_econ_open_ihx_trans': {
        'base_topology': 'Economizer',
        'display_name': 'Offen | Parallelschaltung | doppelte interne WÜT | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'flash': {
        'base_topology': 'Flashtank',
        'display_name': 'Allgemein',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'subcritical'
        },
    'flash_trans': {
        'base_topology': 'Flashtank',
        'display_name': 'Allgemein | Transkritisch',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 1,
        'process_type': 'transcritical'
        },
    'cascade': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Allgemein',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': None,
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Allgemein | Transkritisch',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': None,
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_2ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Doppelte interne WÜT',
        'nr_ihx': 2,
        'econ_type': None,
        'comp_var': None,
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_2ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Doppelte interne WÜT | Transkritisch',
        'nr_ihx': 2,
        'econ_type': None,
        'comp_var': None,
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_ic': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Zwischenkühlung',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_ic_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Zwischenkühlung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_econ_closed': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Reihenschaltung',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_econ_closed_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Reihenschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_ihx_econ_closed': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante A)',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_ihx_econ_closed_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_econ_closed_ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante B)',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_econ_closed_ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Reihenschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_econ_open': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Reihenschaltung',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_econ_open_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Reihenschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_ihx_econ_open': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante A)',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_ihx_econ_open_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_econ_open_ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante B)',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_econ_open_ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Reihenschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_pc_econ_closed': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_pc_econ_closed_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_ihx_pc_econ_closed': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante A)',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_ihx_pc_econ_closed_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_pc_econ_closed_ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante B)',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_pc_econ_closed_ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_ihx_pc_econ_closed_ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung | doppelte interne WÜT',
        'nr_ihx': 4,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_ihx_pc_econ_closed_ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Geschlossen | Parallelschaltung | doppelte interne WÜT | Transkritisch',
        'nr_ihx': 4,
        'econ_type': 'closed',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_pc_econ_open': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_pc_econ_open_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung | Transkritisch',
        'nr_ihx': 0,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_ihx_pc_econ_open': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante A)',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_ihx_pc_econ_open_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante A) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_pc_econ_open_ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante B)',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_pc_econ_open_ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung | interne WÜT (Variante B) | Transkritisch',
        'nr_ihx': 2,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_ihx_pc_econ_open_ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung | doppelte interne WÜT',
        'nr_ihx': 4,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_ihx_pc_econ_open_ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Offen | Parallelschaltung | doppelte interne WÜT | Transkritisch',
        'nr_ihx': 4,
        'econ_type': 'open',
        'comp_var': 'parallel',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_flash': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Flashtank',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_flash_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Flashtank | Transkritisch',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    }

hp_model_classes = {
    'simple': HeatPumpSimple,
    'simple_trans': HeatPumpSimpleTrans,
    'ihx': HeatPumpIHX,
    'ihx_trans': HeatPumpIHXTrans,
    'ic': HeatPumpIC,
    'ic_trans': HeatPumpICTrans,
    'econ_closed': HeatPumpEcon,
    'econ_closed_trans': HeatPumpEconTrans,
    'econ_closed_ihx': HeatPumpEconIHX,
    'econ_closed_ihx_trans': HeatPumpEconIHXTrans,
    'ihx_econ_closed': HeatPumpIHXEcon,
    'ihx_econ_closed_trans': HeatPumpIHXEconTrans,
    'econ_open': HeatPumpEcon,
    'econ_open_trans': HeatPumpEconTrans,
    'econ_open_ihx': HeatPumpEconIHX,
    'econ_open_ihx_trans': HeatPumpEconIHXTrans,
    'ihx_econ_open': HeatPumpIHXEcon,
    'ihx_econ_open_trans': HeatPumpIHXEconTrans,
    'pc_econ_closed': HeatPumpPC,
    'pc_econ_closed_trans': HeatPumpPCTrans,
    'ihx_pc_econ_closed': HeatPumpIHXPC,
    'ihx_pc_econ_closed_trans': HeatPumpIHXPCTrans,
    'pc_econ_closed_ihx': HeatPumpPCIHX,
    'pc_econ_closed_ihx_trans': HeatPumpPCIHXTrans,
    'ihx_pc_econ_closed_ihx': HeatPumpIHXPCIHX,
    'ihx_pc_econ_closed_ihx_trans': HeatPumpIHXPCIHXTrans,
    'pc_econ_open': HeatPumpPC,
    'pc_econ_open_trans': HeatPumpPCTrans,
    'ihx_pc_econ_open': HeatPumpIHXPC,
    'ihx_pc_econ_open_trans': HeatPumpIHXPCTrans,
    'pc_econ_open_ihx': HeatPumpPCIHX,
    'pc_econ_open_ihx_trans': HeatPumpPCIHXTrans,
    'ihx_pc_econ_open_ihx': HeatPumpIHXPCIHX,
    'ihx_pc_econ_open_ihx_trans': HeatPumpIHXPCIHXTrans,
    'flash': HeatPumpFlash,
    'flash_trans': HeatPumpFlashTrans,
    'cascade': HeatPumpCascade,
    'cascade_trans': HeatPumpCascadeTrans,
    'cascade_2ihx': HeatPumpCascade2IHX,
    'cascade_2ihx_trans': HeatPumpCascade2IHXTrans,
    'cascade_ic': HeatPumpCascadeIC,
    'cascade_ic_trans': HeatPumpCascadeICTrans,
    'cascade_econ_closed': HeatPumpCascadeEcon,
    'cascade_econ_closed_trans': HeatPumpCascadeEconTrans,
    'cascade_ihx_econ_closed': HeatPumpCascadeIHXEcon,
    'cascade_ihx_econ_closed_trans': HeatPumpCascadeIHXEconTrans,
    'cascade_econ_closed_ihx': HeatPumpCascadeEconIHX,
    'cascade_econ_closed_ihx_trans': HeatPumpCascadeEconIHXTrans,
    'cascade_econ_open': HeatPumpCascadeEcon,
    'cascade_econ_open_trans': HeatPumpCascadeEconTrans,
    'cascade_ihx_econ_open': HeatPumpCascadeIHXEcon,
    'cascade_ihx_econ_open_trans': HeatPumpCascadeIHXEconTrans,
    'cascade_econ_open_ihx': HeatPumpCascadeEconIHX,
    'cascade_econ_open_ihx_trans': HeatPumpCascadeEconIHXTrans,
    'cascade_pc_econ_closed': HeatPumpCascadePC,
    'cascade_pc_econ_closed_trans': HeatPumpCascadePCTrans,
    'cascade_ihx_pc_econ_closed': HeatPumpCascadeIHXPC,
    'cascade_ihx_pc_econ_closed_trans': HeatPumpCascadeIHXPCTrans,
    'cascade_pc_econ_closed_ihx': HeatPumpCascadePCIHX,
    'cascade_pc_econ_closed_ihx_trans': HeatPumpCascadePCIHXTrans,
    'cascade_ihx_pc_econ_closed_ihx': HeatPumpCascadeIHXPCIHX,
    'cascade_ihx_pc_econ_closed_ihx_trans': HeatPumpCascadeIHXPCIHXTrans,
    'cascade_pc_econ_open': HeatPumpCascadePC,
    'cascade_pc_econ_open_trans': HeatPumpCascadePCTrans,
    'cascade_ihx_pc_econ_open': HeatPumpCascadeIHXPC,
    'cascade_ihx_pc_econ_open_trans': HeatPumpCascadeIHXPCTrans,
    'cascade_pc_econ_open_ihx': HeatPumpCascadePCIHX,
    'cascade_pc_econ_open_ihx_trans': HeatPumpCascadePCIHXTrans,
    'cascade_ihx_pc_econ_open_ihx': HeatPumpCascadeIHXPCIHX,
    'cascade_ihx_pc_econ_open_ihx_trans': HeatPumpCascadeIHXPCIHXTrans,
    'cascade_flash': HeatPumpCascadeFlash,
    'cascade_flash_trans': HeatPumpCascadeFlashTrans
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
