import gettext
import json
import os
import pathlib

import darkdetect
import numpy as np
import pandas as pd
import streamlit as st
import variables as var
from simulation import run_design, run_partload
from streamlit import session_state as ss

__PRJDIR = pathlib.Path(__file__).parent.parent.absolute()
LOCDIR = __PRJDIR / "locales"

# Initialize gettext
gettext.bindtextdomain("dashboard", localedir=LOCDIR)
gettext.textdomain("dashboard")
_ = gettext.gettext


def switch2design():
    """Switch to design simulation tab."""
    ss.select = _("Design")


def switch2partload():
    """Switch to partload simulation tab."""
    ss.select = _("Partload")


def reset2design():
    """Reset session state and switch to design simulation tab."""
    keys = list(ss.keys())
    for key in keys:
        ss.pop(key)
    ss.select = _("Design")


def info_df(label, refrigs):
    """Create DataFrame with info of chosen refrigerant."""
    df_refrig = pd.DataFrame(
        columns=["Type", "T_NBP", "T_critical", "p_critical", "SK", "ODP", "GWP"]
    )
    df_refrig.loc[label, "Type"] = refrigs[label]["type"]
    df_refrig.loc[label, "T_NBP"] = str(refrigs[label]["T_NBP"])
    df_refrig.loc[label, "T_critical"] = str(refrigs[label]["T_crit"])
    df_refrig.loc[label, "p_critical"] = str(refrigs[label]["p_crit"])
    df_refrig.loc[label, "SK"] = refrigs[label]["ASHRAE34"]
    df_refrig.loc[label, "ODP"] = str(refrigs[label]["ODP"])
    df_refrig.loc[label, "GWP"] = str(refrigs[label]["GWP100"])

    return df_refrig


def calc_limits(wf, prop, padding_rel, scale="lin"):
    """
    Calculate the limits for a state diagram based on the given property.

    Parameters
    ----------

    wf : str
        Working fluid to filter heat pump simulation results.

    prop : str
        Fluid property to calculate limits for.

    padding_rel : float
        Padding from minimum and maximum value to axis limit in relation
        to the full range between minimum and maximum.

    scale : str
        Either 'lin' or 'log'. Scale on which padding is applied. Defaults to 'lin'.
    """
    if scale not in ["lin", "log"]:
        raise ValueError(
            _("Parameter 'scale' must be either 'lin' or 'log'.")
            + f" '{scale}' "
            + _("is not allowed.")
        )

    wfmask = ss.hp.nw.results["Connection"][wf] == 1.0

    min_val = ss.hp.nw.results["Connection"].loc[wfmask, prop].min()
    max_val = ss.hp.nw.results["Connection"].loc[wfmask, prop].max()
    if scale == "lin":
        delta_val = max_val - min_val
        ax_min_val = min_val - padding_rel * delta_val
        ax_max_val = max_val + padding_rel * delta_val
    elif scale == "log":
        delta_val = np.log10(max_val) - np.log10(min_val)
        ax_min_val = 10 ** (np.log10(min_val) - padding_rel * delta_val)
        ax_max_val = 10 ** (np.log10(max_val) + padding_rel * delta_val)

    return ax_min_val, ax_max_val


src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))

# %% MARK: Initialization
refrigpath = os.path.join(src_path, "refrigerants.json")
with open(refrigpath, "r", encoding="utf-8") as file:
    refrigerants = json.load(file)

st.set_page_config(
    layout="wide",
    page_title=_("Heat Pump Dashboard"),
    page_icon=os.path.join(src_path, "img", "page_icon_ZNES.png"),
)

is_dark = darkdetect.isDark()

# ---
# %% MARK: Sidebar
with st.sidebar:
    if is_dark:
        logo = os.path.join(src_path, "img", "Logo_ZNES_mitUnisV2_dark.svg")
    else:
        logo = os.path.join(src_path, "img", "Logo_ZNES_mitUnisV2.svg")
    st.image(logo, use_column_width=True)

    language = st.selectbox("", ["en", "de", "it"])
    try:
        localizator = gettext.translation(
            "dashboard", localedir=LOCDIR, languages=[language]
        )
        localizator.install()
        _ = localizator.gettext
    except Exception:
        pass

    mode = st.selectbox(
        _("Select Mode"),
        [_("Start"), _("Design"), _("Partload")],
        key="select",
        label_visibility="hidden",
    )

    st.markdown("""---""")

    # %% MARK: Design
    if mode == _("Design"):
        ss.rerun_req = True
        st.header(_("Design of the Heat Pump"))

        with st.expander(_("Setup"), expanded=True):
            base_topology = st.selectbox(
                _("Base Topology"), var.base_topologies, index=0, key="base_topology"
            )

            models = []
            for model, mdata in var.hp_models.items():
                if mdata["base_topology"] == base_topology:
                    if mdata["process_type"] != "transcritical":
                        models.append(mdata["display_name"])

            model_name = st.selectbox(
                _("Heat Pump Model"), models, index=0, key="model"
            )

            process_type = st.radio(
                _("Process Type"),
                options=(_("subcritical"), _("transcritical")),
                horizontal=True,
            )

            if process_type == _("transcritical"):
                model_name = f"{model_name} | {_('Transcritical')}"

            for model, mdata in var.hp_models.items():
                correct_base = mdata["base_topology"] == base_topology
                correct_model_name = mdata["display_name"] == model_name
                if correct_base and correct_model_name:
                    hp_model = mdata
                    hp_model_name = model
                    if "trans" in hp_model_name:
                        hp_model_name_topology = hp_model_name.replace("_trans", "")
                    else:
                        hp_model_name_topology = hp_model_name
                    break

            parampath = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "models",
                    "input",
                    f"params_hp_{hp_model_name}.json",
                )
            )
            with open(parampath, "r", encoding="utf-8") as file:
                params = json.load(file)
        if hp_model["nr_ihx"] == 1:
            with st.expander(_("Internal Heat Exchange")):
                params["ihx"]["dT_sh"] = st.slider(
                    _("Superheating/Subcooling"),
                    value=5,
                    min_value=0,
                    max_value=25,
                    format="%d°C",
                    key="dT_sh",
                )
        if hp_model["nr_ihx"] > 1:
            with st.expander(_("Internal Heat Exchange")):
                dT_ihx = {}
                for i in range(1, hp_model["nr_ihx"] + 1):
                    dT_ihx[i] = st.slider(
                        _("No. {i}: Superheating/Subcooling"),
                        value=5,
                        min_value=0,
                        max_value=25,
                        format="%d°C",
                        key=f"dT_ihx{i}",
                    )
                    params[f"ihx{i}"]["dT_sh"] = dT_ihx[i]

        with st.expander(_("Refrigerant")):
            if hp_model["nr_refrigs"] == 1:
                refrig_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params["setup"]["refrig"]:
                        refrig_index = ridx
                        break
                    elif rdata["CP"] == params["setup"]["refrig"]:
                        refrig_index = ridx
                        break

                refrig_label = st.selectbox(
                    "", refrigerants.keys(), index=refrig_index, key="refrigerant"
                )
                params["setup"]["refrig"] = refrigerants[refrig_label]["CP"]
                params["fluids"]["wf"] = refrigerants[refrig_label]["CP"]
                df_refrig = info_df(refrig_label, refrigerants)

            elif hp_model["nr_refrigs"] == 2:
                refrig2_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params["setup"]["refrig2"]:
                        refrig2_index = ridx
                        break
                    elif rdata["CP"] == params["setup"]["refrig2"]:
                        refrig2_index = ridx
                        break

                refrig2_label = st.selectbox(
                    _("Refrigerant (High Temperature Circuit)"),
                    refrigerants.keys(),
                    index=refrig2_index,
                    key="refrigerant2",
                )
                params["setup"]["refrig2"] = refrigerants[refrig2_label]["CP"]
                params["fluids"]["wf2"] = refrigerants[refrig2_label]["CP"]
                df_refrig2 = info_df(refrig2_label, refrigerants)

                refrig1_index = None
                for ridx, (rlabel, rdata) in enumerate(refrigerants.items()):
                    if rlabel == params["setup"]["refrig1"]:
                        refrig1_index = ridx
                        break
                    elif rdata["CP"] == params["setup"]["refrig1"]:
                        refrig1_index = ridx
                        break

                refrig1_label = st.selectbox(
                    _("Refrigerant (Low Temperature Circuit)"),
                    refrigerants.keys(),
                    index=refrig1_index,
                    key="refrigerant1",
                )
                params["setup"]["refrig1"] = refrigerants[refrig1_label]["CP"]
                params["fluids"]["wf1"] = refrigerants[refrig1_label]["CP"]
                df_refrig1 = info_df(refrig1_label, refrigerants)

        if hp_model["nr_refrigs"] == 1:
            T_crit = int(np.floor(refrigerants[refrig_label]["T_crit"]))
            p_crit = int(np.floor(refrigerants[refrig_label]["p_crit"]))
        elif hp_model["nr_refrigs"] == 2:
            T_crit = int(np.floor(refrigerants[refrig2_label]["T_crit"]))
            p_crit = int(np.floor(refrigerants[refrig2_label]["p_crit"]))

        ss.T_crit = T_crit
        ss.p_crit = p_crit

        if "trans" in hp_model_name:
            with st.expander(_("Transcritical Pressure")):
                params["A0"]["p"] = st.slider(
                    _("Value in bar"),
                    min_value=ss.p_crit,
                    value=params["A0"]["p"],
                    max_value=300,
                    format="%d bar",
                    key="p_trans_out",
                )

        # ---
        with st.expander(_("Thermal Nominal Power")):
            params["cons"]["Q"] = st.number_input(
                _("Value in MW"),
                value=abs(params["cons"]["Q"] / 1e6),
                step=0.1,
                key="Q_N",
            )
            params["cons"]["Q"] *= -1e6

        with st.expander(_("Heat Source")):
            params["B1"]["T"] = st.slider(
                _("Forward Temperature"),
                min_value=0,
                max_value=T_crit,
                value=params["B1"]["T"],
                format="%d°C",
                key="T_heatsource_ff",
            )
            params["B2"]["T"] = st.slider(
                _("Return Temperature"),
                min_value=0,
                max_value=T_crit,
                value=params["B2"]["T"],
                format="%d°C",
                key="T_heatsource_bf",
            )

            invalid_temp_diff = params["B2"]["T"] >= params["B1"]["T"]
            if invalid_temp_diff:
                st.error(
                    _(
                        "The return temperature must be lower than the forward temperature."
                    )
                )

        # TODO: Currently, T_mid in the model is formed as the average between the
        # evaporation and condensation temperature. It would certainly be interesting
        # analytically to be able to set this value manually.
        # if hp_model['nr_refrigs'] == 2:
        #     with st.expander(_('Intermediate Heat Exchanger')):
        #         param['design']['T_mid'] = st.slider(
        #             _('Average Temperature'), min_value=0, max_value=T_crit,
        #             value=40, format='%d°C', key='T_mid'
        #         )

        with st.expander(_("Heat Sink")):
            T_max_sink = T_crit
            if "trans" in hp_model_name:
                T_max_sink = 200  # °C -- Ad hoc value, maybe find better one

            params["C3"]["T"] = st.slider(
                _("Forward Temperature"),
                min_value=0,
                max_value=T_max_sink,
                value=params["C3"]["T"],
                format="%d°C",
                key="T_consumer_ff",
            )
            params["C1"]["T"] = st.slider(
                _("Return Temperature"),
                min_value=0,
                max_value=T_max_sink,
                value=params["C1"]["T"],
                format="%d°C",
                key="T_consumer_bf",
            )

            invalid_temp_diff = params["C1"]["T"] >= params["C3"]["T"]
            if invalid_temp_diff:
                st.error(
                    _(
                        "The return temperature must be lower than the forward temperature."
                    )
                )
            invalid_temp_diff = params["C1"]["T"] <= params["B1"]["T"]
            if invalid_temp_diff:
                st.error(
                    _(
                        "The temperature of the heat sink must be higher than the heat source."
                    )
                )

        with st.expander(_("Compressor")):
            if hp_model["comp_var"] is None and hp_model["nr_refrigs"] == 1:
                params["comp"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_s$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["comp"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
            elif hp_model["comp_var"] is not None and hp_model["nr_refrigs"] == 1:
                params["comp1"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,1}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["comp1"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
                params["comp2"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,2}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["comp2"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
            elif hp_model["comp_var"] is None and hp_model["nr_refrigs"] == 2:
                params["HT_comp"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,HTK}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["HT_comp"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
                params["LT_comp"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,NTK}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["LT_comp"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
            elif hp_model["comp_var"] is not None and hp_model["nr_refrigs"] == 2:
                params["HT_comp1"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,HTK,1}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["HT_comp1"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
                params["HT_comp2"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,HTK,2}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["HT_comp2"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
                params["LT_comp1"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,NTK,1}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["LT_comp1"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )
                params["LT_comp2"]["eta_s"] = (
                    st.slider(
                        _("Efficiency $\eta_{s,NTK,2}$"),
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(params["LT_comp2"]["eta_s"] * 100),
                        format="%d%%",
                    )
                    / 100
                )

        # ---
        with st.expander(_("Ambient Conditions (Exergy)")):
            params["ambient"]["T"] = st.slider(
                _("Temperature"),
                min_value=1,
                max_value=45,
                step=1,
                value=params["ambient"]["T"],
                format="%d°C",
                key="T_env",
            )
            params["ambient"]["p"] = st.number_input(
                _("Pressure in bar"),
                value=float(params["ambient"]["p"]),
                step=0.01,
                format="%.4f",
                key="p_env",
            )

        with st.expander(_("Parameters for Cost Calculation")):
            costcalcparams = {}
            costcalcparams["k_evap"] = st.slider(
                _("Heat Transfer Coefficient (Evaporation)"),
                min_value=0,
                max_value=5000,
                step=10,
                value=1500,
                format="%d W/m²K",
                key="k_evap",
            )

            costcalcparams["k_cond"] = st.slider(
                _("Heat Transfer Coefficient (Condensation)"),
                min_value=0,
                max_value=5000,
                step=10,
                value=3500,
                format="%d W/m²K",
                key="k_cond",
            )

            if "trans" in hp_model_name:
                costcalcparams["k_trans"] = st.slider(
                    _("Heat Transfer Coefficient (Transcritical)"),
                    min_value=0,
                    max_value=1000,
                    step=5,
                    value=60,
                    format="%d W/m²K",
                    key="k_trans",
                )

            costcalcparams["k_misc"] = st.slider(
                _("Heat Transfer Coefficient (Miscellaneous)"),
                min_value=0,
                max_value=1000,
                step=5,
                value=50,
                format="%d W/m²K",
                key="k_misc",
            )

            costcalcparams["residence_time"] = st.slider(
                _("Residence Time Flash Tank"),
                min_value=0,
                max_value=60,
                step=1,
                value=10,
                format="%d s",
                key="residence_time",
            )

        ss.hp_params = params

        run_sim = st.button(_("🧮 Execute Design"))
        # run_sim = True
    # autorun = st.checkbox(_('AutoRun Simulation'), value=True)

    # %% MARK: Offdesign
    if mode == _("Part Load") and "hp" in ss:
        params = ss.hp_params
        st.header(_("Part Load Simulation of the Heat Pump"))

        with st.expander(_("Part Load")):
            (
                params["offdesign"]["partload_min"],
                params["offdesign"]["partload_max"],
            ) = st.slider(
                _("Relative to Nominal Mass Flow"),
                min_value=0,
                max_value=120,
                step=5,
                value=(30, 100),
                format="%d%%",
                key="pl_slider",
            )

            params["offdesign"]["partload_min"] /= 100
            params["offdesign"]["partload_max"] /= 100

            params["offdesign"]["partload_steps"] = int(
                np.ceil(
                    (
                        params["offdesign"]["partload_max"]
                        - params["offdesign"]["partload_min"]
                    )
                    / 0.1
                )
                + 1
            )

        with st.expander(_("Heat Source")):
            type_hs = st.radio(
                "",
                (_("Constant"), _("Variable")),
                index=1,
                horizontal=True,
                key="temp_hs",
            )
            if type_hs == _("Constant"):
                params["offdesign"]["T_hs_ff_start"] = ss.hp.params["B1"]["T"]
                params["offdesign"]["T_hs_ff_end"] = (
                    params["offdesign"]["T_hs_ff_start"] + 1
                )
                params["offdesign"]["T_hs_ff_steps"] = 1

                text = (
                    f'{_("Temperature")} <p style="color:{var.st_color_hex}">'
                    + f'{params["offdesign"]["T_hs_ff_start"]} °C'
                    + r"</p>"
                )
                st.markdown(text, unsafe_allow_html=True)

            elif type_hs == _("Variable"):
                params["offdesign"]["T_hs_ff_start"] = st.slider(
                    _("Start Temperature"),
                    min_value=0,
                    max_value=ss.T_crit,
                    step=1,
                    value=int(ss.hp.params["B1"]["T"] - 5),
                    format="%d°C",
                    key="T_hs_ff_start_slider",
                )
                params["offdesign"]["T_hs_ff_end"] = st.slider(
                    _("End Temperature"),
                    min_value=0,
                    max_value=ss.T_crit,
                    step=1,
                    value=int(ss.hp.params["B1"]["T"] + 5),
                    format="%d°C",
                    key="T_hs_ff_end_slider",
                )
                params["offdesign"]["T_hs_ff_steps"] = int(
                    np.ceil(
                        (
                            params["offdesign"]["T_hs_ff_end"]
                            - params["offdesign"]["T_hs_ff_start"]
                        )
                        / 3
                    )
                    + 1
                )

        # ---
        with st.expander(_("Heat Sink")):
            type_cons = st.radio(
                "",
                (_("Constant"), _("Variable")),
                index=1,
                horizontal=True,
                key="temp_cons",
            )
            if type_cons == _("Constant"):
                params["offdesign"]["T_cons_ff_start"] = ss.hp.params["C3"]["T"]
                params["offdesign"]["T_cons_ff_end"] = (
                    params["offdesign"]["T_cons_ff_start"] + 1
                )
                params["offdesign"]["T_cons_ff_steps"] = 1

                text = (
                    f'{_("Temperature")} <p style="color:{var.st_color_hex}">'
                    + f'{params["offdesign"]["T_cons_ff_start"]} °C'
                    + r"</p>"
                )
                st.markdown(text, unsafe_allow_html=True)

            elif type_cons == _("Variable"):
                params["offdesign"]["T_cons_ff_start"] = st.slider(
                    _("Start Temperature"),
                    min_value=0,
                    max_value=ss.T_crit,
                    step=1,
                    value=int(ss.hp.params["C3"]["T"] - 10),
                    format="%d°C",
                    key="T_cons_ff_start_slider",
                )
                params["offdesign"]["T_cons_ff_end"] = st.slider(
                    _("End Temperature"),
                    min_value=0,
                    max_value=ss.T_crit,
                    step=1,
                    value=int(ss.hp.params["C3"]["T"] + 10),
                    format="%d°C",
                    key="T_cons_ff_end_slider",
                )
                params["offdesign"]["T_cons_ff_steps"] = int(
                    np.ceil(
                        (
                            params["offdesign"]["T_cons_ff_end"]
                            - params["offdesign"]["T_cons_ff_start"]
                        )
                        / 1
                    )
                    + 1
                )

        ss.hp_params = params
        run_pl_sim = st.button(_("🧮 Simulate Part Load"))

# %% MARK: Main Content
st.title(_("*heatpumps*"))

if mode == "Start":
    # %% MARK: Landing Page
    st.write(
        _(
            """
            The heat pump simulator *heatpumps* is a powerful simulation software
            for analyzing and evaluating heat pumps.

            This dashboard allows you to control a variety of complex
            thermodynamic plant models using numerical methods via a
            simple interface, without requiring expert knowledge.
            This includes both the design of heat pumps
            as well as the simulation of their steady-state part load operation. The
            simulation results provide insights into the pump's behavior, COP,
            state variables, and costs of individual components as well as
            total investment costs. This enables access to complex questions
            that frequently arise in the design and planning of heat pumps.

            ### Key Features

            - Steady-state design and part load simulation based on [TESPy](https://github.com/oemof/tespy)
            - Parameterization and result visualization via a [Streamlit](https://github.com/streamlit/streamlit) dashboard
            - Common circuit topologies used in industry, research, and development
            - Subcritical and transcritical processes
            - Large selection of working fluids thanks to [CoolProp](https://github.com/CoolProp/CoolProp) integration
            """
        )
    )

    st.button(_("Start Design"), on_click=switch2design)

    st.markdown("""---""")

    with st.expander(_("Used Software")):
        st.info(
            _(
                """
                #### Used Software:

                The open-source software TESPy is used for modeling and simulating the systems.
                Additionally, a number of other Python packages are used for data processing,
                preparation, and visualization.

                ---

                #### TESPy:

                TESPy (Thermal Engineering Systems in Python) is a powerful
                simulation tool for thermal process engineering, such as power plants,
                district heating systems, or heat pumps. The TESPy package allows for
                system design and steady-state operation simulation. After that,
                part load behavior can be determined based on the characteristics of
                each component of the system. The component-based structure combined
                with the solution method offers great flexibility regarding the
                system topology and parameterization. More information on TESPy can
                be found in its [online documentation](https://tespy.readthedocs.io) (in English).

                #### Other Packages:

                - [Streamlit](https://docs.streamlit.io) (Graphical User Interface)
                - [NumPy](https://numpy.org) (Data Processing)
                - [pandas](https://pandas.pydata.org) (Data Processing)
                - [SciPy](https://scipy.org/) (Interpolation)
                - [scikit-learn](https://scikit-learn.org) (Regression)
                - [Matplotlib](https://matplotlib.org) (Data Visualization)
                - [FluProDia](https://fluprodia.readthedocs.io) (Data Visualization)
                - [CoolProp](http://www.coolprop.org) (Fluid Properties)
                """
            )
        )

    with st.expander(_("Disclaimer")):
        st.warning(
            _(
                """
                #### Simulation Results:

                Numerical simulations are calculations performed using appropriate
                iterative methods based on the specified boundary conditions and parameters.
                In some cases, it is not possible to account for all possible influences,
                so deviations from real-world experience may occur and should be taken into
                account when evaluating the results. The results provide sufficient to exact
                insights into the heat pump's general behavior, COP, and state variables in
                each component. Nevertheless, all information and results are provided
                without guarantee.
                """
            )
        )

    with st.expander(_("Copyright")):
        st.success(
            _(
                """
                #### Software License
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
        )

# ---
if mode == "Design":
    # %% MARK: Design Simulation
    if not run_sim:
        # %% Topology & Refrigerant
        col_left, col_right = st.columns([1, 4])

        with col_left:
            st.subheader(str(_("Topology")))

            if is_dark:
                try:
                    top_file = os.path.join(
                        src_path,
                        "img",
                        "topologies",
                        f"hp_{hp_model_name_topology}_dark.svg",
                    )
                    st.image(top_file)
                except:  # noqa: E722
                    top_file = os.path.join(
                        src_path,
                        "img",
                        "topologies",
                        f"hp_{hp_model_name_topology}.svg",
                    )
                    st.image(top_file)

            else:
                top_file = os.path.join(
                    src_path, "img", "topologies", f"hp_{hp_model_name_topology}.svg"
                )
                st.image(top_file)

        with col_right:
            st.subheader(str(_("Refrigerant")))

            if hp_model["nr_refrigs"] == 1:
                st.dataframe(df_refrig, use_container_width=True)
            elif hp_model["nr_refrigs"] == 2:
                st.markdown(_("#### High-Temperature Circuit"))
                st.dataframe(df_refrig2, use_container_width=True)
                st.markdown(_("#### Low-Temperature Circuit"))
                st.dataframe(df_refrig1, use_container_width=True)

            st.write(
                _(
                    """
                    All substance data and classifications from
                    [CoolProp](http://www.coolprop.org) or
                    [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                    """
                )
            )

        with st.expander(_("Instructions")):
            st.info(
                _(
                    """
                    #### Instructions

                    You are now on the design simulation interface
                    for your heat pump. In the left sidebar, next to the
                    dimensioning and the choice of refrigerant, several central parameters
                    for the cycle process must be specified.

                    These include, for example, the temperatures of the heat source and sink,
                    but also the associated network pressures. Additionally, an internal
                    heat exchanger can be optionally added. The resulting superheat of the
                    evaporated refrigerant must also be specified.

                    Once the design simulation is successfully completed, the
                    generated results are processed graphically in state diagrams
                    and quantified. Key metrics such as the coefficient of performance (COP),
                    as well as relevant heat flows and power outputs, will be shown.
                    Furthermore, thermodynamic state variables at each process step will
                    be listed in a table.

                    After the design simulation, a button will appear allowing you to switch
                    to the partial load interface. This can also be done via the
                    dropdown menu in the sidebar. Information on how to perform
                    partial load simulations is available on the start page of this interface.
                    """
                )
            )

    if run_sim:
        # %% Run Design Simulation
        with st.spinner(_("Running simulation...")):
            try:
                ss.hp = run_design(hp_model_name, params)
                sim_succeeded = True
                st.success(_("The heat pump design simulation was successful."))
            except ValueError as e:
                sim_succeeded = False
                print(f"ValueError: {e}")
                st.error(
                    _(
                        "An error occurred during the heat pump simulation. "
                        "Please correct the input parameters and try again.\n\n"
                    )
                    + f'"{e}"'
                )

        # %% MARK: Results
        if sim_succeeded:
            with st.spinner(_("Visualizing results...")):
                stateconfigpath = os.path.abspath(
                    os.path.join(
                        os.path.dirname(__file__),
                        "models",
                        "input",
                        "state_diagram_config.json",
                    )
                )
                with open(stateconfigpath, "r", encoding="utf-8") as file:
                    config = json.load(file)
                if hp_model["nr_refrigs"] == 1:
                    if ss.hp.params["setup"]["refrig"] in config:
                        state_props = config[ss.hp.params["setup"]["refrig"]]
                    else:
                        state_props = config["MISC"]
                if hp_model["nr_refrigs"] == 2:
                    if ss.hp.params["setup"]["refrig1"] in config:
                        state_props1 = config[ss.hp.params["setup"]["refrig1"]]
                    else:
                        state_props1 = config["MISC"]
                    if ss.hp.params["setup"]["refrig2"] in config:
                        state_props2 = config[ss.hp.params["setup"]["refrig2"]]
                    else:
                        state_props2 = config["MISC"]

                st.header(_("Design Results"))

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("COP", round(ss.hp.cop, 2))
                Q_dot_ab = abs(ss.hp.buses["heat output"].P.val / 1e6)
                col2.metric("Q_dot_ab", f"{Q_dot_ab:.2f} MW")
                col3.metric("P_zu", f"{ss.hp.buses['power input'].P.val/1e6:.2f} MW")
                Q_dot_zu = abs(ss.hp.comps["evap"].Q.val / 1e6)
                col4.metric("Q_dot_zu", f"{Q_dot_zu:.2f} MW")

                with st.expander(_("Topology & Refrigerant")):
                    # %% Topology & Refrigerant
                    col_left, col_right = st.columns([1, 4])

                    with col_left:
                        st.subheader(str(_("Topology")))

                        top_file = os.path.join(
                            src_path,
                            "img",
                            "topologies",
                            f"hp_{hp_model_name_topology}_label.svg",
                        )
                        if is_dark:
                            top_file_dark = os.path.join(
                                src_path,
                                "img",
                                "topologies",
                                f"hp_{hp_model_name_topology}_label_dark.svg",
                            )
                            if os.path.exists(top_file_dark):
                                top_file = top_file_dark

                        st.image(top_file)

                    with col_right:
                        st.subheader(str(_("Refrigerant")))

                        if hp_model["nr_refrigs"] == 1:
                            st.dataframe(df_refrig, use_container_width=True)
                        elif hp_model["nr_refrigs"] == 2:
                            st.markdown(_("#### High-Temperature Circuit"))
                            st.dataframe(df_refrig2, use_container_width=True)
                            st.markdown(_("#### Low-Temperature Circuit"))
                            st.dataframe(df_refrig1, use_container_width=True)

                        st.write(
                            _(
                                """
                                All substance data and classifications from
                                [CoolProp](http://www.coolprop.org) or
                                [Arpagaus et al. (2018)](https://doi.org/10.1016/j.energy.2018.03.166)
                                """
                            )
                        )

                with st.expander(_("State Diagrams")):
                    # %% State Diagrams
                    col_left, _, col_right = st.columns([0.495, 0.01, 0.495])
                    _, slider_left, _, slider_right, _ = st.columns([0.5, 8, 1, 8, 0.5])

                    if is_dark:
                        state_diagram_style = "dark"
                    else:
                        state_diagram_style = "light"

                    with col_left:
                        # %% Log(p)-h-Diagram
                        st.subheader("Log(p)-h Diagram")
                        if hp_model["nr_refrigs"] == 1:
                            xmin, xmax = calc_limits(
                                wf=ss.hp.wf, prop="h", padding_rel=0.35
                            )
                            ymin, ymax = calc_limits(
                                wf=ss.hp.wf, prop="p", padding_rel=0.25, scale="log"
                            )

                            diagram = ss.hp.generate_state_diagram(
                                diagram_type="logph",
                                figsize=(12, 7.5),
                                xlims=(xmin, xmax),
                                ylims=(ymin, ymax),
                                style=state_diagram_style,
                                return_diagram=True,
                                display_info=False,
                                open_file=False,
                                savefig=False,
                            )
                            st.pyplot(diagram.fig)

                        elif hp_model["nr_refrigs"] == 2:
                            xmin1, xmax1 = calc_limits(
                                wf=ss.hp.wf1, prop="h", padding_rel=0.35
                            )
                            ymin1, ymax1 = calc_limits(
                                wf=ss.hp.wf1, prop="p", padding_rel=0.25, scale="log"
                            )

                            xmin2, xmax2 = calc_limits(
                                wf=ss.hp.wf2, prop="h", padding_rel=0.35
                            )
                            ymin2, ymax2 = calc_limits(
                                wf=ss.hp.wf2, prop="p", padding_rel=0.25, scale="log"
                            )

                            diagram1, diagram2 = ss.hp.generate_state_diagram(
                                diagram_type="logph",
                                figsize=(12, 7.5),
                                xlims=((xmin1, xmax1), (xmin2, xmax2)),
                                ylims=((ymin1, ymax1), (ymin2, ymax2)),
                                style=state_diagram_style,
                                return_diagram=True,
                                display_info=False,
                                savefig=False,
                                open_file=False,
                            )
                            st.pyplot(diagram1.fig)
                            st.pyplot(diagram2.fig)

                    with col_right:
                        # %% T-s-Diagram
                        st.subheader("T-s Diagram")
                        if hp_model["nr_refrigs"] == 1:
                            xmin, xmax = calc_limits(
                                wf=ss.hp.wf, prop="s", padding_rel=0.35
                            )
                            ymin, ymax = calc_limits(
                                wf=ss.hp.wf, prop="T", padding_rel=0.25
                            )

                            diagram = ss.hp.generate_state_diagram(
                                diagram_type="Ts",
                                figsize=(12, 7.5),
                                xlims=(xmin, xmax),
                                ylims=(ymin, ymax),
                                style=state_diagram_style,
                                return_diagram=True,
                                display_info=False,
                                open_file=False,
                                savefig=False,
                            )
                            st.pyplot(diagram.fig)

                        elif hp_model["nr_refrigs"] == 2:
                            xmin1, xmax1 = calc_limits(
                                wf=ss.hp.wf1, prop="s", padding_rel=0.35
                            )
                            ymin1, ymax1 = calc_limits(
                                wf=ss.hp.wf1, prop="T", padding_rel=0.25
                            )

                            xmin2, xmax2 = calc_limits(
                                wf=ss.hp.wf2, prop="s", padding_rel=0.35
                            )
                            ymin2, ymax2 = calc_limits(
                                wf=ss.hp.wf2, prop="T", padding_rel=0.25
                            )

                            diagram1, diagram2 = ss.hp.generate_state_diagram(
                                diagram_type="Ts",
                                figsize=(12, 7.5),
                                xlims=((xmin1, xmax1), (xmin2, xmax2)),
                                ylims=((ymin1, ymax1), (ymin2, ymax2)),
                                style=state_diagram_style,
                                return_diagram=True,
                                display_info=False,
                                savefig=False,
                                open_file=False,
                            )
                            st.pyplot(diagram1.fig)
                            st.pyplot(diagram2.fig)
                # ---
                with st.expander("State Quantities"):
                    # %% State Quantities
                    state_quantities = ss.hp.nw.results["Connection"].copy()
                    state_quantities = state_quantities.loc[
                        :,
                        ~state_quantities.columns.str.contains(
                            "_unit", case=False, regex=False
                        ),
                    ]
                    try:
                        state_quantities["water"] = state_quantities["water"] == 1.0
                    except KeyError:
                        state_quantities["H2O"] = state_quantities["H2O"] == 1.0
                    if hp_model["nr_refrigs"] == 1:
                        refrig = ss.hp.params["setup"]["refrig"]
                        state_quantities[refrig] = state_quantities[refrig] == 1.0
                    elif hp_model["nr_refrigs"] == 2:
                        refrig1 = ss.hp.params["setup"]["refrig1"]
                        state_quantities[refrig1] = state_quantities[refrig1] == 1.0
                        refrig2 = ss.hp.params["setup"]["refrig2"]
                        state_quantities[refrig2] = state_quantities[refrig2] == 1.0
                    if "Td_bp" in state_quantities.columns:
                        del state_quantities["Td_bp"]
                    for col in state_quantities.columns:
                        if state_quantities[col].dtype == np.float64:
                            state_quantities[col] = state_quantities[col].apply(
                                lambda x: f"{x:.5}"
                            )
                    state_quantities["x"] = state_quantities["x"].apply(
                        lambda x: "-" if float(x) < 0 else x
                    )
                    state_quantities.rename(
                        columns={
                            "m": "m in kg/s",
                            "p": "p in bar",
                            "h": "h in kJ/kg",
                            "T": "T in °C",
                            "v": "v in m³/kg",
                            "vol": "vol in m³/s",
                            "s": "s in kJ/(kgK)",
                        },
                        inplace=True,
                    )
                    st.dataframe(data=state_quantities, use_container_width=True)

                with st.expander("Economic Assessment"):
                    # %% Eco Results
                    ss.hp.calc_cost(
                        ref_year="2013", current_year="2019", **costcalcparams
                    )

                    col1, col2 = st.columns(2)
                    invest_total = ss.hp.cost_total
                    col1.metric("Total Investment Costs", f"{invest_total:,.0f} €")
                    inv_sepc = invest_total / abs(ss.hp.params["cons"]["Q"] / 1e6)
                    col2.metric("Specific Investment Costs", f"{inv_sepc:,.0f} €/MW")
                    costdata = pd.DataFrame(
                        {k: [round(v, 2)] for k, v in ss.hp.cost.items()}
                    )
                    st.dataframe(costdata, use_container_width=True, hide_index=True)

                    st.write(
                        # _(
                        """
                            Methodology for cost calculation analogous to
                            [Kosmadakis et al. (2020)](https://doi.org/10.1016/j.enconman.2020.113488),
                            based on [Bejan et al. (1995)](https://www.wiley.com/en-us/Thermal+Design+and+Optimization-p-9780471584674).
                            """
                        # )
                    )

                with st.expander("Exergy Assessment"):
                    # %% Exergy Analysis
                    st.header("Results of the Exergy Analysis")

                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric(
                        "Epsilon", f"{ss.hp.ean.network_data.epsilon*1e2:.2f} %"
                    )
                    col2.metric("E_F", f"{(ss.hp.ean.network_data.E_F)/1e6:.2f} MW")
                    col3.metric("E_P", f"{(ss.hp.ean.network_data.E_P)/1e6:.2f} MW")
                    col4.metric("E_D", f"{(ss.hp.ean.network_data.E_D)/1e6:.2f} MW")
                    col5.metric("E_L", f"{(ss.hp.ean.network_data.E_L)/1e3:.2f} kW")

                    st.subheader("Results by Component")
                    exergy_component_result = ss.hp.ean.component_data.copy()
                    exergy_component_result = exergy_component_result.drop(
                        "group", axis=1
                    )
                    exergy_component_result.dropna(subset=["E_F"], inplace=True)
                    for col in ["E_F", "E_P", "E_D"]:
                        exergy_component_result[col] = exergy_component_result[
                            col
                        ].round(2)
                    for col in ["epsilon", "y_Dk", "y*_Dk"]:
                        exergy_component_result[col] = exergy_component_result[
                            col
                        ].round(4)
                    exergy_component_result.rename(
                        columns={
                            "E_F": "E_F in W",
                            "E_P": "E_P in W",
                            "E_D": "E_D in W",
                        },
                        inplace=True,
                    )
                    st.dataframe(data=exergy_component_result, use_container_width=True)

                    col6, _, col7 = st.columns([0.495, 0.01, 0.495])
                    with col6:
                        st.subheader("Grassmann Diagram")
                        diagram_placeholder_sankey = st.empty()

                        diagram_sankey = ss.hp.generate_sankey_diagram()
                        diagram_placeholder_sankey.plotly_chart(
                            diagram_sankey, use_container_width=True
                        )

                    with col7:
                        st.subheader("Waterfall Diagram")
                        diagram_placeholder_waterfall = st.empty()

                        diagram_waterfall = ss.hp.generate_waterfall_diagram()
                        diagram_placeholder_waterfall.pyplot(
                            diagram_waterfall, use_container_width=True
                        )

                    st.write(
                        # _(
                        """
                            Definitions and methodology of the exergy analysis based on
                            [Morosuk and Tsatsaronis (2019)](https://doi.org/10.1016/j.energy.2018.10.090),
                            its implementation in TESPy described in [Witte and Hofmann et al. (2022)](https://doi.org/10.3390/en15114087)
                            and pedagogically prepared in [Witte, Freißmann and Fritz (2023)](https://fwitte.github.io/TESPy_teaching_exergy/).
                            """
                        # )
                    )

                st.info(
                    # _(
                    'To calculate the partial load, click on "Simulate Partial Load".'
                    # )
                )

                st.button("Simulate Partial Load", on_click=switch2partload)

# ---
if mode == "Partial Load":
    # %% MARK: Offdesign Simulation
    st.header(_("Operating Characteristics"))

    if "hp" not in ss:
        st.warning(
            _(
                """
                To perform a partial load simulation, a heat pump must first be
                designed. Please switch to the "Design" mode first.
                """
            )
        )
    else:
        if not run_pl_sim and "partload_char" not in ss:
            # %% Landing Page
            st.write(
                _(
                    """
                    Parameterization of the partial load calculation:
                    + Percentage share of partial load
                    + Range of source temperature
                    + Range of sink temperature
                    """
                )
            )

        if run_pl_sim:
            # %% Run Offdesign Simulation
            with st.spinner(
                _("Partial load simulation is running... This may take a while.")
            ):
                ss.hp, ss.partload_char = run_partload(ss.hp)
                # ss.partload_char = pd.read_csv(
                #     'partload_char.csv', index_col=[0, 1, 2], sep=';'
                #     )
                st.success(
                    _("The simulation of the heat pump characteristics was successful.")
                )

        if run_pl_sim or "partload_char" in ss:
            # %% Results
            with st.spinner(_("Results are being visualized...")):
                with st.expander(_("Diagrams"), expanded=True):
                    col_left, col_right = st.columns(2)

                    with col_left:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char,
                            cmap_type="COP",
                            cmap="plasma",
                            return_fig_ax=True,
                        )
                        pl_cop_placeholder = st.empty()

                        if type_hs == "Constant":
                            T_select_cop = ss.hp.params["offdesign"]["T_hs_ff_start"]
                        elif type_hs == "Variable":
                            T_hs_min = ss.hp.params["offdesign"]["T_hs_ff_start"]
                            T_hs_max = ss.hp.params["offdesign"]["T_hs_ff_end"]
                            T_select_cop = st.slider(
                                _("Source Temperature"),
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max + T_hs_min) / 2),
                                format="%d °C",
                                key="pl_cop_slider",
                            )

                        pl_cop_placeholder.pyplot(figs[T_select_cop])

                    with col_right:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char,
                            cmap_type="T_cons_ff",
                            cmap="plasma",
                            return_fig_ax=True,
                        )
                        pl_T_cons_ff_placeholder = st.empty()

                        if type_hs == "Constant":
                            T_select_T_cons_ff = ss.hp.params["offdesign"][
                                "T_hs_ff_start"
                            ]
                        elif type_hs == "Variable":
                            T_select_T_cons_ff = st.slider(
                                _("Source Temperature"),
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max + T_hs_min) / 2),
                                format="%d °C",
                                key="pl_T_cons_ff_slider",
                            )
                        pl_T_cons_ff_placeholder.pyplot(figs[T_select_T_cons_ff])

                with st.expander(_("Exergy Analysis Partial Load"), expanded=True):
                    col_left_1, col_right_1 = st.columns(2)

                    with col_left_1:
                        figs, axes = ss.hp.plot_partload_char(
                            ss.partload_char,
                            cmap_type="epsilon",
                            cmap="plasma",
                            return_fig_ax=True,
                        )
                        pl_epsilon_placeholder = st.empty()

                        if type_hs == "Constant":
                            T_select_epsilon = ss.hp.params["offdesign"][
                                "T_hs_ff_start"
                            ]
                        elif type_hs == "Variable":
                            T_hs_min = ss.hp.params["offdesign"]["T_hs_ff_start"]
                            T_hs_max = ss.hp.params["offdesign"]["T_hs_ff_end"]
                            T_select_epsilon = st.slider(
                                _("Source Temperature"),
                                min_value=T_hs_min,
                                max_value=T_hs_max,
                                value=int((T_hs_max + T_hs_min) / 2),
                                format="%d °C",
                                key="pl_epsilon_slider",
                            )

                        pl_epsilon_placeholder.pyplot(figs[T_select_epsilon])

                st.button(_("Design New Heat Pump"), on_click=reset2design)
