# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 09:54:24 2022

@author: Jonas Freißmann
"""

import streamlit as st
import json
import numpy as np
import pandas as pd
from simulation import run_design, run_partload


def switch2design():
    """Switch to design simulation tab."""
    st.session_state.select = 'Auslegung'


def switch2partload():
    """Switch to partload simulation tab."""
    st.session_state.select = 'Teillast'


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


st_color_hex = '#ff4b4b'

# %% Initialisation
with open('src\\refrigerants.json', 'r') as file:
    refrigerants = json.load(file)

st.set_page_config(
    layout='wide',
    page_title='Wärmepumpen Dashboard',
    page_icon='src\\img\\page_icon_ZNES.png'
    )

param = {'design': dict(), 'offdesign': dict()}

# TODO
param['design']['heatex_type_sink'] = 'Condenser'

# %% Sidebar
with st.sidebar:
    st.image('src\\img\\Logo_ZNES.png')

    mode = st.selectbox('', ['Auslegung', 'Teillast'], key='select')

    st.markdown("""---""")

    # %% Design
    if mode == 'Auslegung':
        st.header('Auslegung der Wärmepumpe')

        with st.expander('Thermische Nennleistung'):
            param['design']['Q_N'] = st.number_input(
                'Wert in MW', value=5.0, step=0.1, key='Q_N'
                )
            param['design']['Q_N'] *= -1e6

        with st.expander('Anzahl Kreisläufe'):
            nr_cycles = st.selectbox(
                '', [1, 2], key='nr_cycles'
                )
            if nr_cycles == 2:
                param['design']['int_heatex1'] = False
                param['design']['int_heatex2'] = False

        with st.expander('Kältemittel'):
            if nr_cycles == 1:
                refrig_label = st.selectbox(
                    '', refrigerants.keys(), index=len(refrigerants.keys())-1,
                    key='refrigerant'
                    )
                param['design']['refrigerant'] = refrigerants[
                    refrig_label]['CP']
                df_refrig = info_df(refrig_label, refrigerants)
            elif nr_cycles == 2:
                refrig_label1 = st.selectbox(
                    '1. Kältemittel', refrigerants.keys(),
                    index=len(refrigerants.keys())-1,
                    key='refrigerant1'
                    )
                param['design']['refrigerant1'] = refrigerants[
                    refrig_label1]['CP']
                refrig_label2 = st.selectbox(
                    '2. Kältemittel', refrigerants.keys(),
                    index=len(refrigerants.keys())-2,
                    key='refrigerant2'
                    )
                param['design']['refrigerant2'] = refrigerants[
                    refrig_label2]['CP']

        if nr_cycles == 1:
            T_crit = int(np.floor(refrigerants[refrig_label]['T_crit']))
        elif nr_cycles == 2:
            T_crit = int(np.floor(refrigerants[refrig_label2]['T_crit']))

        st.session_state.T_crit = T_crit

        with st.expander('Wärmequelle'):
            param['design']['T_heatsource_ff'] = st.slider(
                'Temperatur Vorlauf', min_value=0, max_value=T_crit, value=20,
                format='%d°C', key='T_heatsource_ff'
                )
            param['design']['T_heatsource_bf'] = st.slider(
                'Temperatur Rücklauf', min_value=0, max_value=T_crit, value=10,
                format='%d°C', key='T_heatsource_bf'
                )
            invalid_temp_diff = (
                param['design']['T_heatsource_bf']
                >= param['design']['T_heatsource_ff']
                )
            if invalid_temp_diff:
                st.error(
                    'Die Rücklauftemperatur muss niedriger sein, als die '
                    + 'Vorlauftemperatur.'
                    )
            param['design']['p_heatsource_ff'] = st.slider(
                'Druck', min_value=1.0, max_value=20.0, value=1.0,
                step=0.1, format='%f bar', key='p_heatsource_ff'
                )

        if nr_cycles == 2:
            with st.expander('Zwischenwärmeübertrager'):
                param['design']['T_mid'] = st.slider(
                    'Mittlere Temperatur', min_value=0, max_value=T_crit,
                    value=40, format='%d°C', key='T_mid'
                    )

        with st.expander('Wärmesenke'):
            param['design']['T_consumer_ff'] = st.slider(
                'Temperatur Vorlauf', min_value=0, max_value=T_crit, value=70,
                format='%d°C', key='T_consumer_ff'
                )
            param['design']['T_consumer_bf'] = st.slider(
                'Temperatur Rücklauf', min_value=0, max_value=T_crit, value=50,
                format='%d°C', key='T_consumer_bf'
                )
            invalid_temp_diff = (
                param['design']['T_consumer_bf']
                >= param['design']['T_consumer_ff']
                )
            if invalid_temp_diff:
                st.error(
                    'Die Rücklauftemperatur muss niedriger sein, als die '
                    + 'Vorlauftemperatur.'
                    )
            invalid_temp_diff = (
                param['design']['T_consumer_bf']
                <= param['design']['T_heatsource_ff']
                )
            if invalid_temp_diff:
                st.error(
                    'Die Temperatur der Wärmesenke muss höher sein, als die '
                    + 'der Wärmequelle.'
                    )
            param['design']['p_consumer_ff'] = st.slider(
                'Druck', min_value=1.0, max_value=20.0, value=10.0,
                step=0.1, format='%f bar', key='p_consumer_ff'
                )

        with st.expander('Interner Wärmeübertrager'):
            param['design']['int_heatex'] = st.checkbox('verwenden')
            if param['design']['int_heatex']:
                param['design']['deltaT_int_heatex'] = st.slider(
                    'Überhitzung/Unterkühlung', value=5, min_value=0,
                    max_value=25, format='%d°C', key='deltaT_int_heatex'
                    )

        st.session_state.hp_param = param

        run_sim = st.button('🧮 Auslegung ausführen')
        # run_sim = True
    # autorun = st.checkbox('AutoRun Simulation', value=True)

    # %% Offdesign
    if mode == 'Teillast':
        param = st.session_state.hp_param
        st.header('Teillastsimulation der Wärmepumpe')

        with st.expander('Teillast'):
            (param['offdesign']['partload_min'],
             param['offdesign']['partload_max']) = st.slider(
                'Bezogen auf Nennmassenstrom',
                min_value=0, max_value=120, step=5,
                value=(30, 100), format='%d%%', key='pl_slider'
                )

            param['offdesign']['partload_min'] /= 100
            param['offdesign']['partload_max'] /= 100

            param['offdesign']['partload_steps'] = int(np.ceil(
                    (param['offdesign']['partload_max']
                     - param['offdesign']['partload_min'])
                    / 0.1
                    ) + 1)

        with st.expander('Wärmequelle'):
            type_hs = st.radio(
                '', ('Konstant', 'Variabel'), index=1, horizontal=True,
                key='temp_hs'
                )
            if type_hs == 'Konstant':
                param['offdesign']['T_hs_ff_start'] = (
                    st.session_state.hp.param['design']['T_heatsource_ff']
                    )
                param['offdesign']['T_hs_ff_end'] = (
                    param['offdesign']['T_hs_ff_start'] + 1
                    )
                param['offdesign']['T_hs_ff_steps'] = 1

                text = (
                    f'Temperatur <p style="color:{st_color_hex}">'
                    + f'{param["offdesign"]["T_hs_ff_start"]} °C'
                    + r'</p>'
                    )
                st.markdown(text, unsafe_allow_html=True)

            elif type_hs == 'Variabel':
                param['offdesign']['T_hs_ff_start'] = st.slider(
                    'Starttemperatur',
                    min_value=0, max_value=st.session_state.T_crit, step=1,
                    value=int(
                        st.session_state.hp.param['design']['T_heatsource_ff']
                        - 5
                        ),
                    format='%d°C', key='T_hs_ff_start_slider'
                    )
                param['offdesign']['T_hs_ff_end'] = st.slider(
                    'Endtemperatur',
                    min_value=0, max_value=st.session_state.T_crit, step=1,
                    value=int(
                        st.session_state.hp.param['design']['T_heatsource_ff']
                        + 5
                        ),
                    format='%d°C', key='T_hs_ff_end_slider'
                    )
                param['offdesign']['T_hs_ff_steps'] = int(np.ceil(
                    (param['offdesign']['T_hs_ff_end']
                     - param['offdesign']['T_hs_ff_start'])
                    / 3
                    ) + 1)

        with st.expander('Wärmesenke'):
            type_cons = st.radio(
                '', ('Konstant', 'Variabel'), index=1, horizontal=True,
                key='temp_cons'
                )
            if type_cons == 'Konstant':
                param['offdesign']['T_cons_ff_start'] = (
                    st.session_state.hp.param['design']['T_consumer_ff']
                    )
                param['offdesign']['T_cons_ff_end'] = (
                    param['offdesign']['T_cons_ff_start'] + 1
                    )
                param['offdesign']['T_cons_ff_steps'] = 1

                text = (
                    f'Temperatur <p style="color:{st_color_hex}">'
                    + f'{param["offdesign"]["T_cons_ff_start"]} °C'
                    + r'</p>'
                    )
                st.markdown(text, unsafe_allow_html=True)

            elif type_cons == 'Variabel':
                param['offdesign']['T_cons_ff_start'] = st.slider(
                    'Starttemperatur',
                    min_value=0, max_value=st.session_state.T_crit, step=1,
                    value=int(
                        st.session_state.hp.param['design']['T_consumer_ff']
                        - 10
                        ),
                    format='%d°C', key='T_cons_ff_start_slider'
                    )
                param['offdesign']['T_cons_ff_end'] = st.slider(
                    'Endtemperatur',
                    min_value=0, max_value=st.session_state.T_crit, step=1,
                    value=int(
                        st.session_state.hp.param['design']['T_consumer_ff']
                        + 10
                        ),
                    format='%d°C', key='T_cons_ff_end_slider'
                    )
                param['offdesign']['T_cons_ff_steps'] = int(np.ceil(
                    (param['offdesign']['T_cons_ff_end']
                     - param['offdesign']['T_cons_ff_start'])
                    / 3
                    ) + 1)

        st.session_state.hp_param = param
        run_pl_sim = st.button('🧮 Teillast simulieren')

# %% Main Content
st.title('Wärmepumpensimulator 3k Pro™')

if mode == 'Auslegung':
    # %% Design Simulation
    if not run_sim and 'hp' not in st.session_state:
        # %% Landing Page
        st.write(
            """
            Der Wärmepumpensimulator 3k Pro™ ist eine leistungsfähige
            Simulationssoftware zur Auslegung und Teillastbetrachtung von
            Wärmepumpen.
            """
            )

        st.write(
            """
            Sie befinden sich auf der Oberfläche zur Auslegungssimulation
            Ihrer Wärmepumpe. Dazu sind links in der Sidebar neben der
            Dimensionierung und der Wahl des zu verwendenden Kältemittels
            verschiedene zentrale Parameter des Kreisprozesse vorzugeben.
            """
            )

        st.write(
            """
            Dies sind zum Beispiel die Temperaturen der Wärmequelle und -senke,
            aber auch die dazugehörigen Netzdrücke. Darüber hinaus kann
            optional ein interner Wärmeübertrager hinzugefügt werden. Dazu ist
            weiterhin die resultierende Überhitzung des verdampften
            Kältemittels vorzugeben.
            """
            )

        st.write(
            """
            Ist die Auslegungssimulation erfolgreich abgeschlossen, werden die
            generierten Ergebnisse graphisch in Zustandsdiagrammen
            aufgearbeitet und quantifiziert. Die zentralen Größen wie die
            Leistungszahl (COP) sowie die relevanten Wärmeströme und Leistung
            werden aufgeführt. Darüber hinaus werden die thermodynamischen
            Zustandsgrößen in allen Prozessschritten tabellarisch aufgelistet.
            """
            )

        st.write(
            """
            Im Anschluss an die Auslegungsimulation erscheint ein Knopf zum
            Wechseln in die Teillastoberfläche. Dies kann ebenfalls über das
            Dropdownmenü in der Sidebar erfolgen. Informationen zur
            Durchführung der Teillastsimulationen befindet sich auf der
            Startseite dieser Oberfläche.
            """
            )

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

    if run_sim:
        # %% Run Design Simulation
        with st.spinner('Simulation wird durchgeführt...'):
            st.session_state.hp = run_design(param, nr_cycles)

            st.success(
                'Die Simulation der Wärmepumpenauslegung war erfolgreich.'
                )

    if run_sim or 'hp' in st.session_state:
        # %% Results
        with st.spinner('Ergebnisse werden visualisiert...'):

            with open('state_diagram_config.json', 'r') as file:
                config = json.load(file)
            if st.session_state.hp.param['design']['refrigerant'] in config:
                state_props = config[
                    st.session_state.hp.param['design']['refrigerant']
                    ]
            else:
                state_props = config['MISC']

            st.header('Ergebnisse der Auslegung')

            col1, col2, col3, col4 = st.columns(4)
            col1.metric('COP', round(st.session_state.hp.cop, 2))
            col2.metric(
                'Q_dot_ab',
                f'{st.session_state.hp.busses["heat"].P.val*-1e-6:.2f} MW'
                )
            col3.metric(
                'P_zu',
                f'{st.session_state.hp.busses["power"].P.val/1e6:.2f} MW'
                )
            Q_dot_zu = abs(
                st.session_state.hp.components["Evaporator 1"].Q.val/1e6
                )
            col4.metric('Q_dot_zu', f'{Q_dot_zu:.2f} MW')

            with st.expander('Zustandsdiagramme', expanded=True):
                # %% State Diagrams
                col_left, _, col_right = st.columns([0.495, 0.01, 0.495])
                _, slider_left, _, slider_right, _ = (
                    st.columns([0.5, 8, 1, 8, 0.5])
                    )

                with col_left:
                    # %% Log(p)-h-Diagram
                    st.subheader('Log(p)-h-Diagramm')
                    diagram_placeholder = st.empty()

                with slider_left:
                    if nr_cycles == 1:
                        xmin, xmax = st.slider(
                            'X-Achsen Begrenzung',
                            min_value=0, max_value=3000, step=100,
                            value=(
                                state_props['h']['min'],
                                state_props['h']['max']
                                ),
                            format='%d kJ/kg',
                            key='ph_xslider'
                            )
                        ymin, ymax = st.slider(
                            'Y-Achsen Begrenzung',
                            min_value=-3, max_value=3,
                            value=(0, 2), format='10^%d bar', key='ph_yslider'
                            )
                        ymin, ymax = 10**ymin, 10**ymax
                    elif nr_cycles == 2:
                        xmin1, xmax1 = st.slider(
                            'X-Achsen Begrenzung (Kreislauf 1)',
                            min_value=0, max_value=3000, step=100,
                            value=(100, 2200), format='%d kJ/kg', key='1'
                            )
                        ymin1, ymax1 = st.slider(
                            'Y-Achsen Begrenzung (Kreislauf 1)',
                            min_value=-3, max_value=3,
                            value=(0, 2), format='10^%d bar', key='1'
                            )
                        ymin1, ymax1 = 10**ymin1, 10**ymax1
                        xmin2, xmax2 = st.slider(
                            'X-Achsen Begrenzung (Kreislauf 2)',
                            min_value=0, max_value=3000, step=100,
                            value=(100, 2200), format='%d kJ/kg', key='1'
                            )
                        ymin2, ymax2 = st.slider(
                            'Y-Achsen Begrenzung (Kreislauf 2)',
                            min_value=-3, max_value=3,
                            value=(0, 2), format='10^%d bar', key='1'
                            )
                        ymin2, ymax2 = 10**ymin2, 10**ymax2

                with col_left:
                    if nr_cycles == 1:
                        diagram = st.session_state.hp.generate_state_diagram(
                            diagram_type='logph',
                            xlims=(xmin, xmax), ylims=(ymin, ymax),
                            return_diagram=True, display_info=False,
                            save_file=False
                            )
                        diagram_placeholder.pyplot(diagram.fig)
                    elif nr_cycles == 2:
                        diagram1 = st.session_state.hp.generate_logph(
                            1, xlims=(xmin1, xmax1), ylims=(ymin1, ymax1),
                            return_diagram=True, display_info=False,
                            save_file=False
                            )
                        diagram_placeholder.pyplot(diagram1.fig)
                        diagram2 = st.session_state.hp.generate_logph(
                            2, xlims=(xmin2, xmax2), ylims=(ymin2, ymax2),
                            return_diagram=True, display_info=False,
                            save_file=False
                            )
                        diagram_placeholder.pyplot(diagram2.fig)

                with col_right:
                    # %% T-s-Diagram
                    st.subheader('T-s-Diagramm')
                    diagram_placeholder = st.empty()

                with slider_right:
                    if nr_cycles == 1:
                        xmin, xmax = st.slider(
                            'X-Achsen Begrenzung',
                            min_value=0, max_value=10000, step=100,
                            value=(
                                state_props['s']['min'],
                                state_props['s']['max']
                                ),
                            format='%d kJ/(kgK)',
                            key='ts_xslider'
                            )
                        ymin, ymax = st.slider(
                            'Y-Achsen Begrenzung',
                            min_value=-150, max_value=500,
                            value=(
                                state_props['T']['min'],
                                state_props['T']['max']
                                ),
                            format='%d °C', key='ts_yslider'
                            )
                    elif nr_cycles == 2:
                        xmin1, xmax1 = st.slider(
                            'X-Achsen Begrenzung (Kreislauf 1)',
                            min_value=0, max_value=3000, step=100,
                            value=(100, 2200), format='%d kJ/kg', key='2'
                            )
                        ymin1, ymax1 = st.slider(
                            'Y-Achsen Begrenzung (Kreislauf 1)',
                            min_value=-3, max_value=3,
                            value=(0, 2), format='10^%d bar', key='2'
                            )
                        ymin1, ymax1 = 10**ymin1, 10**ymax1
                        xmin2, xmax2 = st.slider(
                            'X-Achsen Begrenzung (Kreislauf 2)',
                            min_value=0, max_value=3000, step=100,
                            value=(100, 2200), format='%d kJ/kg', key='2'
                            )
                        ymin2, ymax2 = st.slider(
                            'Y-Achsen Begrenzung (Kreislauf 2)',
                            min_value=-3, max_value=3,
                            value=(0, 2), format='10^%d bar', key='2'
                            )
                        ymin2, ymax2 = 10**ymin2, 10**ymax2

                with col_right:
                    if nr_cycles == 1:
                        diagram = st.session_state.hp.generate_state_diagram(
                            diagram_type='Ts',
                            xlims=(xmin, xmax), ylims=(ymin, ymax),
                            return_diagram=True, display_info=False,
                            save_file=False
                            )
                        diagram_placeholder.pyplot(diagram.fig)
                    elif nr_cycles == 2:
                        diagram1 = st.session_state.hp.generate_logph(
                            1, xlims=(xmin1, xmax1), ylims=(ymin1, ymax1),
                            return_diagram=True, display_info=False,
                            save_file=False
                            )
                        diagram_placeholder.pyplot(diagram1.fig)
                        diagram2 = st.session_state.hp.generate_logph(
                            2, xlims=(xmin2, xmax2), ylims=(ymin2, ymax2),
                            return_diagram=True, display_info=False,
                            save_file=False
                            )
                        diagram_placeholder.pyplot(diagram2.fig)

            with st.expander('Zustandsgrößen'):
                # %% State Quantities
                state_quantities = (
                    st.session_state.hp.nw.results['Connection'].copy()
                    )
                state_quantities['water'] = state_quantities['water'].apply(
                    lambda x: bool(x)
                    )
                refrig = st.session_state.hp.param['design']['refrigerant']
                state_quantities[refrig] = state_quantities[refrig].apply(
                    lambda x: bool(x)
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
                st.dataframe(data=state_quantities, use_container_width=True)

            with st.expander('Topologie & Kältemittel'):
                # %% Topology & Refrigerant
                col_left, col_right = st.columns([1, 4])

                with col_left:
                    st.subheader('Topologie')

                    # Todo: Andere Topologie einfügen, wenn sie verwendet
                    # werden können
                    top_file = 'src\\img\\topologie\\hp'
                    if nr_cycles == 1:
                        if param['design']['int_heatex']:
                            top_file += '_ih.png'
                        # elif param['design']['intercooler']:
                        #     top_file += '_ic.png'
                        else:
                            top_file += '.png'
                    elif nr_cycles == 2:
                        top_file += '_2_ih.png'

                    st.image(top_file)

                with col_right:
                    st.subheader('Kältemittel')

                    st.table(df_refrig)

                    st.write(
                        """
                        Alle Stoffdaten und Klassifikationen aus
                        [CoolProp](http://www.coolprop.org) oder
                        [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                        """
                        )

            with st.expander('Ökonomische Bewertung'):
                # %% Eco Results
                st.write('Ökonom')

            st.info(
                'Um die Teillast zu berechnen, drücke auf "Teillast '
                + 'simulieren".'
                )

            run_pl = st.button('Teillast simulieren', on_click=switch2partload)

if mode == 'Teillast':
    # %% Offdesign Simulation
    st.header('Betriebscharakteristik')

    if not run_pl_sim and 'partload_char' not in st.session_state:
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
            st.session_state.hp, st.session_state.partload_char = (
                run_partload(st.session_state.hp, param, save_results=True)
                )
            # st.session_state.partload_char = pd.read_csv(
            #     'partload_char.csv', index_col=[0, 1, 2], sep=';'
            #     )
            st.success(
                'Die Simulation der Wärmepumpencharakteristika war '
                + 'erfolgreich.'
                )

    if run_pl_sim or 'partload_char' in st.session_state:
        # %% Results
        with st.spinner('Ergebnisse werden visualisiert...'):

            with st.expander('Diagramme', expanded=True):
                col_left, col_right = st.columns(2)

                with col_left:
                    figs, axes = st.session_state.hp.plot_partload_char(
                        st.session_state.partload_char, cmap_type='COP',
                        return_fig_ax=True
                        )
                    pl_cop_placeholder = st.empty()
                    T_select_cop = st.select_slider(
                        'Quellentemperatur',
                        options=[k for k in figs.keys()],
                        value=float(np.median(
                            [k for k in figs.keys()]
                            )),
                        key='pl_cop_slider'
                        )
                    pl_cop_placeholder.pyplot(figs[T_select_cop])

                with col_right:
                    figs, axes = st.session_state.hp.plot_partload_char(
                        st.session_state.partload_char, cmap_type='T_cons_ff',
                        return_fig_ax=True
                        )
                    pl_T_cons_ff_placeholder = st.empty()
                    T_select_T_cons_ff = st.select_slider(
                        'Quellentemperatur',
                        options=[k for k in figs.keys()],
                        value=float(np.median(
                            [k for k in figs.keys()]
                            )),
                        key='pl_T_cons_ff_slider'
                         )
                    pl_T_cons_ff_placeholder.pyplot(figs[T_select_T_cons_ff])
