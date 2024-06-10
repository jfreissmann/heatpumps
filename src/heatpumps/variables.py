from models import (HeatPumpCascade, HeatPumpCascadeTrans, HeatPumpCascade2IHX,
                    HeatPumpCascade2IHXTrans, HeatPumpEcon, HeatPumpEconTrans,
                    HeatPumpEconIHX, HeatPumpEconIHXTrans, HeatPumpFlash, HeatPumpFlashTrans,
                    HeatPumpIC, HeatPumpICTrans, HeatPumpIHX, HeatPumpIHXTrans,
                    HeatPumpIHXEcon, HeatPumpIHXEconTrans, HeatPumpPC, HeatPumpPCTrans,
                    HeatPumpIHXPC, HeatPumpIHXPCTrans, HeatPumpPCIHX, HeatPumpPCIHXTrans,
                    HeatPumpIHXPCIHX, HeatPumpIHXPCIHXTrans, HeatPumpSimple, HeatPumpSimpleTrans)

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
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Allgemein | Transkritisch',
        'nr_ihx': 0,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        },
    'cascade_2ihx': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Doppelte interne WÜT',
        'nr_ihx': 2,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'subcritical'
        },
    'cascade_2ihx_trans': {
        'base_topology': 'Kaskadierter Kreis',
        'display_name': 'Doppelte interne WÜT | Transkritisch',
        'nr_ihx': 2,
        'econ_type': None,
        'comp_var': 'series',
        'nr_refrigs': 2,
        'process_type': 'transcritical'
        }
    }

hp_model_classes = {
    'simple': HeatPumpSimple.HeatPumpSimple,
    'simple_trans': HeatPumpSimpleTrans.HeatPumpSimpleTrans,
    'ihx': HeatPumpIHX.HeatPumpIHX,
    'ihx_trans': HeatPumpIHXTrans.HeatPumpIHXTrans,
    'ic': HeatPumpIC.HeatPumpIC,
    'ic_trans': HeatPumpICTrans.HeatPumpICTrans,
    'econ_closed': HeatPumpEcon.HeatPumpEcon,
    'econ_closed_trans': HeatPumpEconTrans.HeatPumpEconTrans,
    'econ_closed_ihx': HeatPumpEconIHX.HeatPumpEconIHX,
    'econ_closed_ihx_trans': HeatPumpEconIHXTrans.HeatPumpEconIHXTrans,
    'ihx_econ_closed': HeatPumpIHXEcon.HeatPumpIHXEcon,
    'ihx_econ_closed_trans': HeatPumpIHXEconTrans.HeatPumpIHXEconTrans,
    'econ_open': HeatPumpEcon.HeatPumpEcon,
    'econ_open_trans': HeatPumpEconTrans.HeatPumpEconTrans,
    'econ_open_ihx': HeatPumpEconIHX.HeatPumpEconIHX,
    'econ_open_ihx_trans': HeatPumpEconIHXTrans.HeatPumpEconIHXTrans,
    'ihx_econ_open': HeatPumpIHXEcon.HeatPumpIHXEcon,
    'ihx_econ_open_trans': HeatPumpIHXEconTrans.HeatPumpIHXEconTrans,
    'pc_econ_closed': HeatPumpPC.HeatPumpPC,
    'pc_econ_closed_trans': HeatPumpPCTrans.HeatPumpPCTrans,
    'ihx_pc_econ_closed': HeatPumpIHXPC.HeatPumpIHXPC,
    'ihx_pc_econ_closed_trans': HeatPumpIHXPCTrans.HeatPumpIHXPCTrans,
    'pc_econ_closed_ihx': HeatPumpPCIHX.HeatPumpPCIHX,
    'pc_econ_closed_ihx_trans': HeatPumpPCIHXTrans.HeatPumpPCIHXTrans,
    'ihx_pc_econ_closed_ihx': HeatPumpIHXPCIHX.HeatPumpIHXPCIHX,
    'ihx_pc_econ_closed_ihx_trans': HeatPumpIHXPCIHXTrans.HeatPumpIHXPCIHXTrans,
    'pc_econ_open': HeatPumpPC.HeatPumpPC,
    'pc_econ_open_trans': HeatPumpPCTrans.HeatPumpPCTrans,
    'ihx_pc_econ_open': HeatPumpIHXPC.HeatPumpIHXPC,
    'ihx_pc_econ_open_trans': HeatPumpIHXPCTrans.HeatPumpIHXPCTrans,
    'pc_econ_open_ihx': HeatPumpPCIHX.HeatPumpPCIHX,
    'pc_econ_open_ihx_trans': HeatPumpPCIHXTrans.HeatPumpPCIHXTrans,
    'ihx_pc_econ_open_ihx': HeatPumpIHXPCIHX.HeatPumpIHXPCIHX,
    'ihx_pc_econ_open_ihx_trans': HeatPumpIHXPCIHXTrans.HeatPumpIHXPCIHXTrans,
    'flash': HeatPumpFlash.HeatPumpFlash,
    'flash_trans': HeatPumpFlashTrans.HeatPumpFlashTrans,
    'cascade': HeatPumpCascade.HeatPumpCascade,
    'cascade_trans': HeatPumpCascadeTrans.HeatPumpCascadeTrans,
    'cascade_2ihx': HeatPumpCascade2IHX.HeatPumpCascade2IHX,
    'cascade_2ihx_trans': HeatPumpCascade2IHXTrans.HeatPumpCascade2IHXTrans
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
