import json
import os

import darkdetect
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import variables as var
from CoolProp.CoolProp import PropsSI as PSI
from simulation import run_design, run_partload
from streamlit import session_state as ss


def switch2design():
    """Switch to design simulation tab."""
    ss.select = 'Auslegung'


def switch2partload():
    """Switch to partload simulation tab."""
    ss.select = 'Teillast'


def reset2design():
    """Reset session state and switch to design simulation tab."""
    keys = list(ss.keys())
    for key in keys:
        ss.pop(key)
    ss.select = 'Auslegung'


def info_df(label, refrigs):
    """Create Dataframe with info of chosen refrigerant."""
    df_refrig = pd.DataFrame(
        columns=['Typ', 'T_NBP', 'T_krit', 'p_krit', 'SK', 'ODP', 'GWP']
        )
    df_refrig.loc[label, 'Typ'] = refrigs[label]['type']
    df_refrig.loc[label, 'T_NBP'] = str(refrigs[label]['T_NBP'])
    df_refrig.loc[label, 'T_krit'] = str(refrigs[label]['T_crit'])
    df_refrig.loc[label, 'p_krit'] = str(refrigs[label]['p_crit'])
    df_refrig.loc[label, 'SK'] = refrigs[label]['ASHRAE34']
    df_refrig.loc[label, 'ODP'] = str(refrigs[label]['ODP'])
    df_refrig.loc[label, 'GWP'] = str(refrigs[label]['GWP100'])

    return df_refrig


def calc_limits(wf, prop, padding_rel, scale='lin'):
    """
    Calculate states diagram limits of given property.

    Parameters
    ----------

    wf : str
        Working fluid for which to filter heat pump simulation results.
    
    prop : str
        Fluid property to calculate limits for.

    padding_rel : float
        Padding from minimum and maximum value to axes limit in relation to
        full range between minimum and maximum.

    scale : str
        Either 'lin' or 'log'. Scale on with padding is applied. Defaults to
        'lin'.
    """
    if scale not in ['lin', 'log']:
        raise ValueError(
            f"Parameter 'scale' has to be either 'lin' or 'log'. '{scale}' is "
            + "not allowed."
            )

    wfmask = ss.hp.nw.results['Connection'][wf] == 1.0

    min_val = ss.hp.nw.results['Connection'].loc[wfmask, prop].min()
    max_val = ss.hp.nw.results['Connection'].loc[wfmask, prop].max()
    if scale == 'lin':
        delta_val = max_val - min_val
        ax_min_val = min_val - padding_rel * delta_val
        ax_max_val = max_val + padding_rel * delta_val
    elif scale == 'log':
        delta_val = np.log10(max_val) - np.log10(min_val)
        ax_min_val = 10 ** (np.log10(min_val) - padding_rel * delta_val)
        ax_max_val = 10 ** (np.log10(max_val) + padding_rel * delta_val)

    return ax_min_val, ax_max_val


src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

# %% MARK: Initialisation
refrigpath = os.path.join(src_path, 'refrigerants.json')
with open(refrigpath, 'r', encoding='utf-8') as file:
    refrigerants = json.load(file)

st.set_page_config(
    layout='wide',
    page_title='Wärmepumpen Dashboard',
    page_icon=os.path.join(src_path, 'img', 'page_icon_ZNES.png')
    )

is_dark = darkdetect.isDark()

# %% MARK: Sidebar
with st.sidebar:
    if is_dark:
        logo = os.path.join(src_path, 'img', 'Logo_ZNES_mitUnisV2_dark.svg')
    else:
        logo = os.path.join(src_path, 'img', 'Logo_ZNES_mitUnisV2.svg')
    st.image(logo, use_column_width=True)

    mode = st.selectbox(
        'Auswahl Modus', ['Start', 'Auslegung', 'Teillast'],
        key='select', label_visibility='hidden'
        )

    st.markdown("""---""")

    # %% MARK: Design
    if mode == 'Auslegung':
        ss.rerun_req = True
        st.header('Auslegung der Wärmepumpe')

        with st.expander('Setup', expanded=True):
            base_topology = st.selectbox(
                'Grundtopologie',
                var.base_topologies,
                index=0, key='base_topology'
            )

            models = []
            for model, mdata in var.hp_models.items():
                if mdata['base_topology'] == base_topology:
                    if mdata['process_type'] != 'transcritical':
                        models.append(mdata['display_name'])

            model_name = st.selectbox(
                'Wärmepumpenmodell', models, index=0, key='model'
            )

            process_type = st.radio(
                'Prozessart', options=('subkritisch', 'transkritisch'),
                horizontal=True
            )

            if process_type == 'transkritisch':
                model_name = f'{model_name} | Transkritisch'

            for model, mdata in var.hp_models.items():
                correct_base = mdata['base_topology'] == base_topology
                correct_model_name = mdata['display_name'] == model_name
                if correct_base and correct_model_name:
                    hp_model = mdata
                    hp_model_name = model
                    if 'trans' in hp_model_name:
                        hp_model_name_topology = hp_model_name.replace('_trans', '')
                    else:
                        hp_model_name_topology = hp_model_name
                    break

            parampath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'models', 'input',
                f'params_hp_{hp_model_name}.json'
                ))
            with open(parampath, 'r', encoding='utf-8') as file:
                params = json.load(file)
        if hp_model['nr_ihx'] == 1:
            with st.expander('Interne Wärmerübertragung'):
                params['ihx']['dT_sh'] = st.slider(
                    'Überhitzung/Unterkühlung', value=5,
                    min_value=0, max_value=25, format='%d°C',
                    key='dT_sh')
        if hp_model['nr_ihx'] > 1:
            with st.expander('Interne Wärmerübertragung'):
                dT_ihx = {}
                for i in range(1, hp_model['nr_ihx']+1):
                     dT_ihx[i] = st.slider(
                        f'Nr. {i}: Überhitzung/Unterkühlung', value=5,
                        min_value=0, max_value=25, format='%d°C',
                        key=f'dT_ihx{i}'
                        )
                     params[f'ihx{i}']['dT_sh'] = dT_ihx[i]

        with st.expander('Kältemittel'):
            if hp_model['nr_refrigs'] == 1:
                refrig_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params['setup']['refrig']:
                        refrig_index = ridx
                        break
                    elif rdata['CP'] == params['setup']['refrig']:
                        refrig_index = ridx
                        break

                refrig_label = st.selectbox(
                    '', refrigerants.keys(), index=refrig_index,
                    key='refrigerant'
                    )
                params['setup']['refrig'] = refrigerants[refrig_label]['CP']
                params['fluids']['wf'] = refrigerants[refrig_label]['CP']
                df_refrig = info_df(refrig_label, refrigerants)

            elif hp_model['nr_refrigs'] == 2:
                refrig2_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params['setup']['refrig2']:
                        refrig2_index = ridx
                        break
                    elif rdata['CP'] == params['setup']['refrig2']:
                        refrig2_index = ridx
                        break

                refrig2_label = st.selectbox(
                    'Kältemittel (Hochtemperaturkreis)', refrigerants.keys(),
                    index=refrig2_index, key='refrigerant2'
                    )
                params['setup']['refrig2'] = refrigerants[refrig2_label]['CP']
                params['fluids']['wf2'] = refrigerants[refrig2_label]['CP']
                df_refrig2 = info_df(refrig2_label, refrigerants)

                refrig1_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params['setup']['refrig1']:
                        refrig1_index = ridx
                        break
                    elif rdata['CP'] == params['setup']['refrig1']:
                        refrig1_index = ridx
                        break

                refrig1_label = st.selectbox(
                    'Kältemittel (Niedertemperaturkreis)', refrigerants.keys(),
                    index=refrig1_index, key='refrigerant1'
                    )
                params['setup']['refrig1'] = refrigerants[refrig1_label]['CP']
                params['fluids']['wf1'] = refrigerants[refrig1_label]['CP']
                df_refrig1 = info_df(refrig1_label, refrigerants)


        if hp_model['nr_refrigs'] == 1:
            T_crit = int(np.floor(refrigerants[refrig_label]['T_crit']))
            p_crit = int(np.floor(refrigerants[refrig_label]['p_crit']))
        elif hp_model['nr_refrigs'] == 2:
            T_crit = int(np.floor(refrigerants[refrig2_label]['T_crit']))
            p_crit = int(np.floor(refrigerants[refrig2_label]['p_crit']))

        ss.T_crit = T_crit
        ss.p_crit = p_crit

        if 'trans' in hp_model_name:
            with st.expander('Traskritischer Druck'):
                params['A0']['p'] = st.slider('Wert in bar', min_value=ss.p_crit,
                                        value=params['A0']['p'], max_value=300,
                                        format='%d bar', key='p_trans_out')

        with st.expander('Thermische Nennleistung'):
            params['cons']['Q'] = st.number_input(
                'Wert in MW', value=abs(params['cons']['Q']/1e6),
                step=0.1, key='Q_N'
                )
            params['cons']['Q'] *= -1e6

        with st.expander('Wärmequelle'):
            params['B1']['T'] = st.slider(
                'Temperatur Vorlauf', min_value=0, max_value=T_crit,
                value=params['B1']['T'], format='%d°C', key='T_heatsource_ff'
                )
            params['B2']['T'] = st.slider(
                'Temperatur Rücklauf', min_value=0, max_value=T_crit,
                value=params['B2']['T'], format='%d°C', key='T_heatsource_bf'
                )

            invalid_temp_diff = params['B2']['T'] >= params['B1']['T']
            if invalid_temp_diff:
                st.error(
                    'Die Rücklauftemperatur muss niedriger sein, als die '
                    + 'Vorlauftemperatur.'
                    )

        # TODO: Aktuell wird T_mid im Modell als Mittelwert zwischen von Ver-
        #       dampfungs- und Kondensationstemperatur gebildet. An sich wäre
        #       es analytisch sicher interessant den Wert selbst festlegen zu
        #       können.
        # if hp_model['nr_refrigs'] == 2:
        #     with st.expander('Zwischenwärmeübertrager'):
        #         param['design']['T_mid'] = st.slider(
        #             'Mittlere Temperatur', min_value=0, max_value=T_crit,
        #             value=40, format='%d°C', key='T_mid'
        #             )

        with st.expander('Wärmesenke'):
            T_max_sink = T_crit
            if 'trans' in hp_model_name:
                T_max_sink = 200  # °C -- Ad hoc value, maybe find better one

            params['C3']['T'] = st.slider(
                'Temperatur Vorlauf', min_value=0, max_value=T_max_sink,
                value=params['C3']['T'], format='%d°C', key='T_consumer_ff'
            )
            params['C1']['T'] = st.slider(
                'Temperatur Rücklauf', min_value=0, max_value=T_max_sink,
                value=params['C1']['T'], format='%d°C', key='T_consumer_bf'
            )

            invalid_temp_diff = params['C1']['T'] >= params['C3']['T']
            if invalid_temp_diff:
                st.error(
                    'Die Rücklauftemperatur muss niedriger sein, als die '
                    + 'Vorlauftemperatur.'
                )
            invalid_temp_diff = params['C1']['T'] <= params['B1']['T']
            if invalid_temp_diff:
                st.error(
                    'Die Temperatur der Wärmesenke muss höher sein, als die '
                    + 'der Wärmequelle.'
                )

        with st.expander('Verdichter'):
            if hp_model['comp_var'] is None and hp_model['nr_refrigs'] == 1:
                params['comp']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_s$', min_value=0, max_value=100, step=1,
                    value=int(params['comp']['eta_s']*100), format='%d%%'
                    ) / 100
            elif hp_model['comp_var'] is not None and hp_model['nr_refrigs'] == 1:
                params['comp1']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,1}$', min_value=0, max_value=100, step=1,
                    value=int(params['comp1']['eta_s']*100), format='%d%%'
                    ) / 100
                params['comp2']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,2}$', min_value=0, max_value=100, step=1,
                    value=int(params['comp2']['eta_s']*100), format='%d%%'
                    ) / 100
            elif hp_model['comp_var'] is None and hp_model['nr_refrigs'] == 2:
                params['HT_comp']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,HTK}$', min_value=0, max_value=100, step=1,
                    value=int(params['HT_comp']['eta_s']*100), format='%d%%'
                    ) / 100
                params['LT_comp']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,NTK}$', min_value=0, max_value=100, step=1,
                    value=int(params['LT_comp']['eta_s']*100), format='%d%%'
                    ) / 100
            elif hp_model['comp_var'] is not None and hp_model['nr_refrigs'] == 2:
                params['HT_comp1']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,HTK,1}$', min_value=0, max_value=100, step=1,
                    value=int(params['HT_comp1']['eta_s']*100), format='%d%%'
                    ) / 100
                params['HT_comp2']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,HTK,2}$', min_value=0, max_value=100, step=1,
                    value=int(params['HT_comp2']['eta_s']*100), format='%d%%'
                    ) / 100
                params['LT_comp1']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,NTK,1}$', min_value=0, max_value=100, step=1,
                    value=int(params['LT_comp1']['eta_s']*100), format='%d%%'
                    ) / 100
                params['LT_comp2']['eta_s'] = st.slider(
                    'Wirkungsgrad $\eta_{s,NTK,2}$', min_value=0, max_value=100, step=1,
                    value=int(params['LT_comp2']['eta_s']*100), format='%d%%'
                    ) / 100

        with st.expander('Umgebungsbedingungen (Exergie)'):
            params['ambient']['T'] = st.slider(
                'Temperatur', min_value=1, max_value=45, step=1,
                value=params['ambient']['T'], format='%d°C', key='T_env'
                )
            params['ambient']['p'] = st.number_input(
                'Druck in bar', value=float(params['ambient']['p']), step=0.01,
                format='%.4f', key='p_env'
                )

        with st.expander('Parameter zur Kostenkalkulation'):
            costcalcparams = {}

            cepcipath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'models', 'input', 'CEPCI.json'
                ))
            with open(cepcipath, 'r', encoding='utf-8') as file:
                cepci = json.load(file)

            costcalcparams['current_year'] = st.selectbox(
                'Jahr der Kostenkalkulation',
                options=sorted(list(cepci.keys()), reverse=True),
                key='current_year'
            )

            costcalcparams['k_evap'] = st.slider(
                'Wärmedurchgangskoeffizient (Verdampfung)',
                min_value=0, max_value=5000, step=10,
                value=1500, format='%d W/m²K', key='k_evap'
                )

            costcalcparams['k_cond'] = st.slider(
                'Wärmedurchgangskoeffizient (Verflüssigung)',
                min_value=0, max_value=5000, step=10,
                value=3500, format='%d W/m²K', key='k_cond'
                )

            if 'trans' in hp_model_name:
                costcalcparams['k_trans'] = st.slider(
                    'Wärmedurchgangskoeffizient (transkritisch)',
                    min_value=0, max_value=1000, step=5,
                    value=60, format='%d W/m²K', key='k_trans'
                    )

            costcalcparams['k_misc'] = st.slider(
                'Wärmedurchgangskoeffizient (Sonstige)',
                min_value=0, max_value=1000, step=5,
                value=50, format='%d W/m²K', key='k_misc'
                )

            costcalcparams['residence_time'] = st.slider(
                'Verweildauer Flashtank',
                min_value=0, max_value=60, step=1,
                value=10, format='%d s', key='residence_time'
                )

        ss.hp_params = params

        run_sim = st.button('🧮 Auslegung ausführen')
        # run_sim = True
    # autorun = st.checkbox('AutoRun Simulation', value=True)

    # %% MARK: Offdesign
    if mode == 'Teillast' and 'hp' in ss:
        params = ss.hp_params
        st.header('Teillastsimulation der Wärmepumpe')

        with st.expander('Teillast'):
            (params['offdesign']['partload_min'],
             params['offdesign']['partload_max']) = st.slider(
                'Bezogen auf Nennmassenstrom',
                min_value=0, max_value=120, step=5,
                value=(30, 100), format='%d%%', key='pl_slider'
                )

            params['offdesign']['partload_min'] /= 100
            params['offdesign']['partload_max'] /= 100

            params['offdesign']['partload_steps'] = int(np.ceil(
                    (params['offdesign']['partload_max']
                     - params['offdesign']['partload_min'])
                    / 0.1
                    ) + 1)

        with st.expander('Wärmequelle'):
            type_hs = st.radio(
                '', ('Konstant', 'Variabel'), index=1, horizontal=True,
                key='temp_hs'
                )
            if type_hs == 'Konstant':
                params['offdesign']['T_hs_ff_start'] = (
                    ss.hp.params['B1']['T']
                    )
                params['offdesign']['T_hs_ff_end'] = (
                    params['offdesign']['T_hs_ff_start'] + 1
                    )
                params['offdesign']['T_hs_ff_steps'] = 1

                text = (
                    f'Temperatur <p style="color:{var.st_color_hex}">'
                    + f'{params["offdesign"]["T_hs_ff_start"]} °C'
                    + r'</p>'
                    )
                st.markdown(text, unsafe_allow_html=True)

            elif type_hs == 'Variabel':
                params['offdesign']['T_hs_ff_start'] = st.slider(
                    'Starttemperatur',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['B1']['T']
                        - 5
                        ),
                    format='%d°C', key='T_hs_ff_start_slider'
                    )
                params['offdesign']['T_hs_ff_end'] = st.slider(
                    'Endtemperatur',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['B1']['T']
                        + 5
                        ),
                    format='%d°C', key='T_hs_ff_end_slider'
                    )
                params['offdesign']['T_hs_ff_steps'] = int(np.ceil(
                    (params['offdesign']['T_hs_ff_end']
                     - params['offdesign']['T_hs_ff_start'])
                    / 3
                    ) + 1)

        with st.expander('Wärmesenke'):
            type_cons = st.radio(
                '', ('Konstant', 'Variabel'), index=1, horizontal=True,
                key='temp_cons'
                )
            if type_cons == 'Konstant':
                params['offdesign']['T_cons_ff_start'] = (
                    ss.hp.params['C3']['T']
                    )
                params['offdesign']['T_cons_ff_end'] = (
                    params['offdesign']['T_cons_ff_start'] + 1
                    )
                params['offdesign']['T_cons_ff_steps'] = 1

                text = (
                    f'Temperatur <p style="color:{var.st_color_hex}">'
                    + f'{params["offdesign"]["T_cons_ff_start"]} °C'
                    + r'</p>'
                    )
                st.markdown(text, unsafe_allow_html=True)

            elif type_cons == 'Variabel':
                params['offdesign']['T_cons_ff_start'] = st.slider(
                    'Starttemperatur',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['C3']['T']
                        - 10
                        ),
                    format='%d°C', key='T_cons_ff_start_slider'
                    )
                params['offdesign']['T_cons_ff_end'] = st.slider(
                    'Endtemperatur',
                    min_value=0, max_value=ss.T_crit, step=1,
                    value=int(
                        ss.hp.params['C3']['T']
                        + 10
                        ),
                    format='%d°C', key='T_cons_ff_end_slider'
                    )
                params['offdesign']['T_cons_ff_steps'] = int(np.ceil(
                    (params['offdesign']['T_cons_ff_end']
                     - params['offdesign']['T_cons_ff_start'])
                    / 1
                    ) + 1)

        ss.hp_params = params
        run_pl_sim = st.button('🧮 Teillast simulieren')

# %% MARK: Main Content
st.title('*heatpumps*')

if mode == 'Start':
    # %% MARK: Landing Page
    st.write(
        """
        Der Wärmepumpensimulator *heatpumps* ist eine leistungsfähige Simulationssoftware
        zur Analyse und Bewertung von Wärmepumpen.

        Mit diesem Dashboard lassen sich eine Vielzahl komplexer
        thermodynamischer Anlagenmodelle mithilfe numerischer Methoden über eine
        einfache Oberfläche steuern, ohne Fachkenntnisse über diese
        vorauszusetzen. Dies beinhaltet sowohl die Auslegung von Wärmepumpen,
        als auch die Simulation ihres stationären Teillastbetriebs. Dabei geben
        die Ergebnisse der Simulationen Aufschluss über das prinzipielle
        Verhalten, den COP, Zustandsgrößen und Kosten der einzelnen Komponenten
        sowie Gesamtinvestitionskosten der betrachteten Wärmepumpe. Damit
        wird Zugang zu komplexen Fragestellungen ermöglicht, die regelmäßig in
        der Konzeption und Planung von Wärmepumpen aufkommen.

        ### Key Features

        - Stationäre Auslegungs- und Teillastsimulation basierend auf [TESPy](https://github.com/oemof/tespy)
        - Parametrisierung and Ergebnisvisualisierung mithilfe eines [Streamlit](https://github.com/streamlit/streamlit) Dashboards
        - In der Industrie, Forschung und Entwicklung gängige Schaltungstopologien
        - Sub- und transkritische Prozesse
        - Große Auswahl an Arbeitsmedien aufgrund der Integration von [CoolProp](https://github.com/CoolProp/CoolProp)
        """
        )

    st.button('Auslegung starten', on_click=switch2design)

    st.markdown("""---""")

    with st.expander('Verwendete Software'):
        st.info(
            """
            #### Verwendete Software:

            Zur Modellerstellung und Berechnung der Simulationen wird die
            Open Source Software TESPy verwendet. Des Weiteren werden
            eine Reihe weiterer Pythonpakete zur Datenverarbeitung,
            -aufbereitung und -visualisierung genutzt.

            ---

            #### TESPy:

            TESPy (Thermal Engineering Systems in Python) ist ein
            leistungsfähiges Simulationswerkzeug für thermische
            Verfahrenstechnik, zum Beispiel für Kraftwerke,
            Fernwärmesysteme oder Wärmepumpen. Mit dem TESPy-Paket ist es
            möglich, Anlagen auszulegen und den stationären Betrieb zu
            simulieren. Danach kann das Teillastverhalten anhand der
            zugrundeliegenden Charakteristiken für jede Komponente der
            Anlage ermittelt werden. Die komponentenbasierte Struktur in
            Kombination mit der Lösungsmethode bieten eine sehr hohe
            Flexibilität hinsichtlich der Anlagentopologie und der
            Parametrisierung. Weitere Informationen zu TESPy sind in dessen
            [Onlinedokumentation](https://tespy.readthedocs.io) in
            englischer Sprache zu finden.

            #### Weitere Pakete:

            - [Streamlit](https://docs.streamlit.io) (Graphische Oberfläche)
            - [NumPy](https://numpy.org) (Datenverarbeitung)
            - [pandas](https://pandas.pydata.org) (Datenverarbeitung)
            - [SciPy](https://scipy.org/) (Interpolation)
            - [scikit-learn](https://scikit-learn.org) (Regression)
            - [Matplotlib](https://matplotlib.org) (Datenvisualisierung)
            - [FluProDia](https://fluprodia.readthedocs.io) (Datenvisualisierung)
            - [CoolProp](http://www.coolprop.org) (Stoffdaten)
            """
            )

    with st.expander('Disclaimer'):
        st.warning(
            """
            #### Simulationsergebnisse:

            Numerische Simulationen sind Berechnungen mittels geeigneter
            Iterationsverfahren in Bezug auf die vorgegebenen und gesetzten
            Randbedingungen und Parameter. Eine Berücksichtigung aller
            möglichen Einflüsse ist in Einzelfällen nicht möglich, so dass
            Abweichungen zu Erfahrungswerten aus Praxisanwendungen
            entstehen können und bei der Bewertung berücksichtigt werden
            müssen. Die Ergebnisse geben hinreichenden bis genauen
            Aufschluss über das prinzipielle Verhalten, den COP und
            Zustandsgrößen in den einzelnen Komponenten der Wärmepumpe.
            Dennoch sind alle Angaben und Ergebnisse ohne Gewähr.
            """
            )

    with st.expander('Copyright'):

        st.success(
            """
            #### Softwarelizenz
            MIT License

            Copyright © 2023 Jonas Freißmann and Malte Fritz

            Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:

            The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.

            THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.
            """
        )

if mode == 'Auslegung':
    # %% MARK: Design Simulation
    if not run_sim:
        # %% Topology & Refrigerant
        col_left, col_right = st.columns([1, 4])

        with col_left:
            st.subheader('Topologie')

            if is_dark:
                try:
                    top_file = os.path.join(
                        src_path, 'img', 'topologies',
                        f'hp_{hp_model_name_topology}_dark.svg'
                        )
                    st.image(top_file)
                except:
                    top_file = os.path.join(
                        src_path, 'img', 'topologies', f'hp_{hp_model_name_topology}.svg'
                        )
                    st.image(top_file)

            else:
                top_file = os.path.join(
                    src_path, 'img', 'topologies', f'hp_{hp_model_name_topology}.svg'
                    )
                st.image(top_file)

        with col_right:
            st.subheader('Kältemittel')

            if hp_model['nr_refrigs'] == 1:
                st.dataframe(df_refrig, use_container_width=True)
            elif hp_model['nr_refrigs'] == 2:
                st.markdown('#### Hochtemperaturkreis')
                st.dataframe(df_refrig2, use_container_width=True)
                st.markdown('#### Niedertemperaturkreis')
                st.dataframe(df_refrig1, use_container_width=True)

            st.write(
                """
                Alle Stoffdaten und Klassifikationen aus
                [CoolProp](http://www.coolprop.org) oder
                [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                """
                )

        with st.expander('Anleitung'):
            st.info(
                """
                #### Anleitung

                Sie befinden sich auf der Oberfläche zur Auslegungssimulation
                Ihrer Wärmepumpe. Dazu sind links in der Sidebar neben der
                Dimensionierung und der Wahl des zu verwendenden Kältemittels
                verschiedene zentrale Parameter des Kreisprozesse vorzugeben.

                Dies sind zum Beispiel die Temperaturen der Wärmequelle und -senke,
                aber auch die dazugehörigen Netzdrücke. Darüber hinaus kann
                optional ein interner Wärmeübertrager hinzugefügt werden. Dazu ist
                weiterhin die resultierende Überhitzung des verdampften
                Kältemittels vorzugeben.

                Ist die Auslegungssimulation erfolgreich abgeschlossen, werden die
                generierten Ergebnisse graphisch in Zustandsdiagrammen
                aufgearbeitet und quantifiziert. Die zentralen Größen wie die
                Leistungszahl (COP) sowie die relevanten Wärmeströme und Leistung
                werden aufgeführt. Darüber hinaus werden die thermodynamischen
                Zustandsgrößen in allen Prozessschritten tabellarisch aufgelistet.

                Im Anschluss an die Auslegungsimulation erscheint ein Knopf zum
                Wechseln in die Teillastoberfläche. Dies kann ebenfalls über das
                Dropdownmenü in der Sidebar erfolgen. Informationen zur
                Durchführung der Teillastsimulationen befindet sich auf der
                Startseite dieser Oberfläche.
                """
                )

    if run_sim:
        # %% Run Design Simulation
        with st.spinner('Simulation wird durchgeführt...'):
            try:
                ss.hp = run_design(hp_model_name, params)
                sim_succeded = True
                st.success(
                    'Die Simulation der Wärmepumpenauslegung war erfolgreich.'
                    )
            except ValueError as e:
                sim_succeded = False
                print(f'ValueError: {e}')
                st.error(
                    'Bei der Simulation der Wärmepumpe ist der nachfolgende '
                    + 'Fehler aufgetreten. Bitte korrigieren Sie die '
                    + f'Eingangsparameter und versuchen es erneut.\n\n"{e}"'
                    )

        # %% MARK: Results
        if sim_succeded:
            with st.spinner('Ergebnisse werden visualisiert...'):

                stateconfigpath = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), 'models', 'input',
                    'state_diagram_config.json'
                    ))
                with open(stateconfigpath, 'r', encoding='utf-8') as file:
                    config = json.load(file)
                if hp_model['nr_refrigs'] == 1:
                    if ss.hp.params['setup']['refrig'] in config:
                        state_props = config[
                            ss.hp.params['setup']['refrig']
                            ]
                    else:
                        state_props = config['MISC']
                if hp_model['nr_refrigs'] == 2:
                    if ss.hp.params['setup']['refrig1'] in config:
                        state_props1 = config[
                            ss.hp.params['setup']['refrig1']
                            ]
                    else:
                        state_props1 = config['MISC']
                    if ss.hp.params['setup']['refrig2'] in config:
                        state_props2 = config[
                            ss.hp.params['setup']['refrig2']
                            ]
                    else:
                        state_props2 = config['MISC']

                st.header('Ergebnisse der Auslegung')

                col1, col2, col3, col4 = st.columns(4)
                col1.metric('COP', round(ss.hp.cop, 2))
                Q_dot_ab = abs(
                    ss.hp.buses['heat output'].P.val / 1e6
                    )
                col2.metric('Q_dot_ab', f"{Q_dot_ab:.2f} MW")
                col3.metric(
                    'P_zu',
                    f"{ss.hp.buses['power input'].P.val/1e6:.2f} MW"
                    )
                Q_dot_zu = abs(
                    ss.hp.comps['evap'].Q.val/1e6
                    )
                col4.metric('Q_dot_zu', f'{Q_dot_zu:.2f} MW')

                with st.expander('Topologie & Kältemittel'):
                    # %% Topology & Refrigerant
                    col_left, col_right = st.columns([1, 4])

                    with col_left:
                        st.subheader('Topologie')

                        top_file = os.path.join(
                            src_path, 'img', 'topologies',
                            f'hp_{hp_model_name_topology}_label.svg'
                            )
                        if is_dark:
                            top_file_dark = os.path.join(
                                src_path, 'img', 'topologies',
                                f'hp_{hp_model_name_topology}_label_dark.svg'
                                )
                            if os.path.exists(top_file_dark):
                                top_file = top_file_dark

                        st.image(top_file)

                    with col_right:
                        st.subheader('Kältemittel')

                        if hp_model['nr_refrigs'] == 1:
                            st.dataframe(df_refrig, use_container_width=True)
                        elif hp_model['nr_refrigs'] == 2:
                            st.markdown('#### Hochtemperaturkreis')
                            st.dataframe(df_refrig2, use_container_width=True)
                            st.markdown('#### Niedertemperaturkreis')
                            st.dataframe(df_refrig1, use_container_width=True)

                        st.write(
                            """
                            Alle Stoffdaten und Klassifikationen aus
                            [CoolProp](http://www.coolprop.org) oder
                            [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                            """
                            )

                with st.expander('Zustandsdiagramme'):
                    # %% State Diagrams
                    col_left, _, col_right = st.columns([0.495, 0.01, 0.495])
                    _, slider_left, _, slider_right, _ = (
                        st.columns([0.5, 8, 1, 8, 0.5])
                        )

                    if is_dark:
                        state_diagram_style = 'dark'
                    else:
                        state_diagram_style = 'light'

                    with col_left:
                        # %% Log(p)-h-Diagram
                        st.subheader('Log(p)-h-Diagramm')
                        if hp_model['nr_refrigs'] == 1:
                            xmin, xmax = calc_limits(
                                wf=ss.hp.wf, prop='h', padding_rel=0.35
                                )
                            ymin, ymax = calc_limits(
                                wf=ss.hp.wf, prop='p', padding_rel=0.25,
                                scale='log'
                                )

                            diagram = ss.hp.generate_state_diagram(
                                diagram_type='logph',
                                figsize=(12, 7.5),
                                xlims=(xmin, xmax), ylims=(ymin, ymax),
                                style=state_diagram_style,
                                return_diagram=True, display_info=False,
                                open_file=False, savefig=False
                                )
                            st.pyplot(diagram.fig)

                        elif hp_model['nr_refrigs'] == 2:
                            xmin1, xmax1 = calc_limits(
                                wf=ss.hp.wf1, prop='h', padding_rel=0.35
                                )
                            ymin1, ymax1 = calc_limits(
                                wf=ss.hp.wf1, prop='p', padding_rel=0.25,
                                scale='log'
                                )

                            xmin2, xmax2 = calc_limits(
                                wf=ss.hp.wf2, prop='h', padding_rel=0.35
                                )
                            ymin2, ymax2 = calc_limits(
                                wf=ss.hp.wf2, prop='p', padding_rel=0.25,
                                scale='log'
                                )

                            diagram1, diagram2 = ss.hp.generate_state_diagram(
                                diagram_type='logph',
                                figsize=(12, 7.5),
                                xlims=((xmin1, xmax1), (xmin2, xmax2)),
                                ylims=((ymin1, ymax1), (ymin2, ymax2)),
                                style=state_diagram_style,
                                return_diagram=True, display_info=False,
                                savefig=False, open_file=False
                                )
                            st.pyplot(diagram1.fig)
                            st.pyplot(diagram2.fig)

                    with col_right:
                        # %% T-s-Diagram
                        st.subheader('T-s-Diagramm')
                        if hp_model['nr_refrigs'] == 1:
                            xmin, xmax = calc_limits(
                                wf=ss.hp.wf, prop='s', padding_rel=0.35
                                )
                            ymin, ymax = calc_limits(
                                wf=ss.hp.wf, prop='T', padding_rel=0.25
                                )

                            diagram = ss.hp.generate_state_diagram(
                                diagram_type='Ts',
                                figsize=(12, 7.5),
                                xlims=(xmin, xmax), ylims=(ymin, ymax),
                                style=state_diagram_style,
                                return_diagram=True, display_info=False,
                                open_file=False, savefig=False
                                )
                            st.pyplot(diagram.fig)

                        elif hp_model['nr_refrigs'] == 2:
                            xmin1, xmax1 = calc_limits(
                                wf=ss.hp.wf1, prop='s', padding_rel=0.35
                                )
                            ymin1, ymax1 = calc_limits(
                                wf=ss.hp.wf1, prop='T', padding_rel=0.25
                                )

                            xmin2, xmax2 = calc_limits(
                                wf=ss.hp.wf2, prop='s', padding_rel=0.35
                                )
                            ymin2, ymax2 = calc_limits(
                                wf=ss.hp.wf2, prop='T', padding_rel=0.25
                                )

                            diagram1, diagram2 = ss.hp.generate_state_diagram(
                                diagram_type='Ts',
                                figsize=(12, 7.5),
                                xlims=((xmin1, xmax1), (xmin2, xmax2)),
                                ylims=((ymin1, ymax1), (ymin2, ymax2)),
                                style=state_diagram_style,
                                return_diagram=True, display_info=False,
                                savefig=False, open_file=False
                                )
                            st.pyplot(diagram1.fig)
                            st.pyplot(diagram2.fig)

                with st.expander('Zustandsgrößen'):
                    # %% State Quantities
                    state_quantities = (
                        ss.hp.nw.results['Connection'].copy()
                        )
                    state_quantities = state_quantities.loc[:, ~state_quantities.columns.str.contains('_unit', case=False, regex=False)]
                    try:
                        state_quantities['water'] = (
                            state_quantities['water'] == 1.0
                            )
                    except KeyError:
                        state_quantities['H2O'] = (
                            state_quantities['H2O'] == 1.0
                            )
                    if hp_model['nr_refrigs'] == 1:
                        refrig = ss.hp.params['setup']['refrig']
                        state_quantities[refrig] = (
                            state_quantities[refrig] == 1.0
                            )
                    elif hp_model['nr_refrigs'] == 2:
                        refrig1 = ss.hp.params['setup']['refrig1']
                        state_quantities[refrig1] = (
                            state_quantities[refrig1] == 1.0
                            )
                        refrig2 = ss.hp.params['setup']['refrig2']
                        state_quantities[refrig2] = (
                            state_quantities[refrig2] == 1.0
                            )
                    if 'Td_bp' in state_quantities.columns:
                        del state_quantities['Td_bp']
                    for col in state_quantities.columns:
                        if state_quantities[col].dtype == np.float64:
                            state_quantities[col] = state_quantities[col].apply(
                                lambda x: f'{x:.5}'
                                )
                    state_quantities['x'] = state_quantities['x'].apply(
                        lambda x: '-' if float(x) < 0 else x
                        )
                    state_quantities.rename(
                        columns={
                            'm': 'm in kg/s',
                            'p': 'p in bar',
                            'h': 'h in kJ/kg',
                            'T': 'T in °C',
                            'v': 'v in m³/kg',
                            'vol': 'vol in m³/s',
                            's': 's in kJ/(kgK)'
                            },
                        inplace=True)
                    st.dataframe(
                        data=state_quantities, use_container_width=True
                        )

                with st.expander('Ökonomische Bewertung'):
                    # %% Eco Results
                    ss.hp.calc_cost(
                        ref_year='2013', **costcalcparams
                        )

                    col1, col2 = st.columns(2)
                    invest_total = ss.hp.cost_total
                    col1.metric(
                        'Gesamtinvestitionskosten',
                        f'{invest_total:,.0f} €'
                        )
                    inv_sepc = (
                        invest_total
                        / abs(ss.hp.params["cons"]["Q"]/1e6)
                        )
                    col2.metric(
                        'Spez. Investitionskosten',
                        f'{inv_sepc:,.0f} €/MW'
                        )
                    costdata = pd.DataFrame({
                        k: [round(v, 2)]
                        for k, v in ss.hp.cost.items()
                        })
                    st.dataframe(
                        costdata, use_container_width=True, hide_index=True
                        )

                    st.write(
                        """
                        Methodik zur Berechnung der Kosten analog zu
                        [Kosmadakis et al. (2020)](https://doi.org/10.1016/j.enconman.2020.113488),
                        basierend auf [Bejan et al. (1995)](https://www.wiley.com/en-us/Thermal+Design+and+Optimization-p-9780471584674).
                        """
                        )


                with st.expander('Exergiebewertung'):
                    # %% Exergy Analysis
                    st.header('Ergebnisse der Exergieanalyse')

                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric(
                        'Epsilon',
                        f'{ss.hp.ean.network_data.epsilon*1e2:.2f} %'
                        )
                    col2.metric(
                        'E_F',
                        f'{(ss.hp.ean.network_data.E_F)/1e6:.2f} MW'
                        )
                    col3.metric(
                        'E_P',
                        f'{(ss.hp.ean.network_data.E_P)/1e6:.2f} MW'
                        )
                    col4.metric(
                        'E_D',
                        f'{(ss.hp.ean.network_data.E_D)/1e6:.2f} MW'
                        )
                    col5.metric(
                        'E_L',
                        f'{(ss.hp.ean.network_data.E_L)/1e3:.2f} KW'
                        )

                    st.subheader('Ergebnisse nach Komponente')
                    exergy_component_result = (
                        ss.hp.ean.component_data.copy()
                        )
                    exergy_component_result = exergy_component_result.drop(
                        'group', axis=1
                        )
                    exergy_component_result.dropna(subset=['E_F'], inplace=True)
                    for col in ['E_F', 'E_P', 'E_D']:
                        exergy_component_result[col] = (
                            exergy_component_result[col].round(2)
                            )
                    for col in ['epsilon', 'y_Dk', 'y*_Dk']:
                        exergy_component_result[col] = (
                            exergy_component_result[col].round(4)
                            )
                    exergy_component_result.rename(
                        columns={
                            'E_F': 'E_F in W',
                            'E_P': 'E_P in W',
                            'E_D': 'E_D in W',
                        },
                        inplace=True)
                    st.dataframe(
                        data=exergy_component_result, use_container_width=True
                        )

                    col6, _, col7 = st.columns([0.495, 0.01, 0.495])
                    with col6:
                        st.subheader('Grassmann Diagramm')
                        diagram_placeholder_sankey = st.empty()

                        diagram_sankey = ss.hp.generate_sankey_diagram()
                        diagram_placeholder_sankey.plotly_chart(
                            diagram_sankey, use_container_width=True
                            )

                    with col7:
                        st.subheader('Wasserfall Diagramm')
                        diagram_placeholder_waterfall = st.empty()

                        diagram_waterfall = ss.hp.generate_waterfall_diagram()
                        diagram_placeholder_waterfall.pyplot(
                            diagram_waterfall, use_container_width=True
                            )

                    st.write(
                        """
                        Definitionen und Methodik der Exergieanalyse basierend auf
                        [Morosuk und Tsatsaronis (2019)](https://doi.org/10.1016/j.energy.2018.10.090),
                        dessen Implementation in TESPy beschrieben in [Witte und Hofmann et al. (2022)](https://doi.org/10.3390/en15114087)
                        und didaktisch aufbereitet in [Witte, Freißmann und Fritz (2023)](https://fwitte.github.io/TESPy_teaching_exergy/).
                        """
                        )

                st.info(
                    'Um die Teillast zu berechnen, drücke auf "Teillast '
                    + 'simulieren".'
                    )

                st.button('Teillast simulieren', on_click=switch2partload)

if mode == 'Teillast':
    # %% MARK: Offdesign Simulation
    st.header('Betriebscharakteristik')

    if 'hp' not in ss:
        st.warning(
            '''
            Um eine Teillastsimulation durchzuführen, muss zunächst eine 
            Wärmepumpe ausgelegt werden. Wechseln Sie bitte zunächst in den 
            Modus "Auslegung".
            '''
        )
    else:
        if not run_pl_sim and 'partload_char' not in ss:
            # %% Landing Page
            st.write(
                '''
                Parametrisierung der Teillastberechnung:
                + Prozentualer Anteil Teillast
                + Bereich der Quelltemperatur
                + Bereich der Senkentemperatur
                '''
                )

        if run_pl_sim:
            # %% Run Offdesign Simulation
            with st.spinner(
                    'Teillastsimulation wird durchgeführt... Dies kann eine '
                    + 'Weile dauern.'
                    ):
                ss.hp, ss.partload_char = (
                    run_partload(ss.hp)
                    )
                # ss.partload_char = pd.read_csv(
                #     'partload_char.csv', index_col=[0, 1, 2], sep=';'
                #     )
                st.success(
                    'Die Simulation der Wärmepumpencharakteristika war '
                    + 'erfolgreich.'
                    )

        if run_pl_sim or 'partload_char' in ss:
            # %% Results
            with st.spinner('Ergebnisse werden visualisiert...'):

                with st.expander('Diagramme', expanded=True):
                    col_left, col_right = st.columns(2)

                    with col_left:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char, cmap_type='COP',
                            cmap='plasma', return_fig_ax=True
                            )
                        pl_cop_placeholder = st.empty()

                        if type_hs == 'Konstant':
                            T_select_cop = (
                                ss.hp.params['offdesign']['T_hs_ff_start']
                                )
                        elif type_hs == 'Variabel':
                            T_hs_min = ss.hp.params['offdesign']['T_hs_ff_start']
                            T_hs_max = ss.hp.params['offdesign']['T_hs_ff_end']
                            T_select_cop = st.slider(
                                'Quellentemperatur',
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max+T_hs_min)/2),
                                format='%d °C',
                                key='pl_cop_slider'
                                )

                        pl_cop_placeholder.pyplot(figs[T_select_cop])

                    with col_right:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char, cmap_type='T_cons_ff',
                            cmap='plasma', return_fig_ax=True
                            )
                        pl_T_cons_ff_placeholder = st.empty()

                        if type_hs == 'Konstant':
                            T_select_T_cons_ff = (
                                ss.hp.params['offdesign']['T_hs_ff_start']
                                )
                        elif type_hs == 'Variabel':
                            T_select_T_cons_ff = st.slider(
                                'Quellentemperatur',
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max+T_hs_min)/2),
                                format='%d °C',
                                key='pl_T_cons_ff_slider'
                                )
                        pl_T_cons_ff_placeholder.pyplot(figs[T_select_T_cons_ff])

                with st.expander('Exergieanalyse Teillast', expanded=True):

                    col_left_1, col_right_1 = st.columns(2)

                    with col_left_1:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char, cmap_type='epsilon',
                            cmap='plasma', return_fig_ax=True
                        )
                        pl_epsilon_placeholder = st.empty()

                        if type_hs == 'Konstant':
                            T_select_epsilon = (
                                ss.hp.params['offdesign']['T_hs_ff_start']
                            )
                        elif type_hs == 'Variabel':
                            T_hs_min = ss.hp.params['offdesign']['T_hs_ff_start']
                            T_hs_max = ss.hp.params['offdesign']['T_hs_ff_end']
                            T_select_epsilon = st.slider(
                                'Quellentemperatur',
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max + T_hs_min) / 2),
                                format='%d °C',
                                key='pl_epsilon_slider'
                            )

                        pl_epsilon_placeholder.pyplot(figs[T_select_epsilon])

                st.button('Neue Wärmepumpe auslegen', on_click=reset2design)
