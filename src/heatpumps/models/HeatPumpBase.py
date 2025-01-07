import json
import os
from datetime import datetime
from time import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from CoolProp.CoolProp import PropsSI as PSI
from fluprodia import FluidPropertyDiagram
from scipy.interpolate import interpn
from sklearn.linear_model import LinearRegression
from tespy.networks import Network
from tespy.tools import ExergyAnalysis
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc


class HeatPumpBase:
    """Super class of all concrete heat pump models."""

    def __init__(self, params):
        """Initialize model and set necessary attributes."""
        self.params = params
        self.wf = self.params['fluids']['wf']
        self.si = self.params['fluids']['si']
        self.so = self.params['fluids']['so']

        self.comps = dict()
        self.conns = dict()
        self.buses = dict()

        self.nw = Network(
            T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
            )

        self.cop = np.nan
        self.epsilon = np.nan

        self._init_vals = {
            'm_dot_rel_econ_closed': 0.9,
            'dh_rel_comp': 1.15
            }

        self.solved_design = False
        self.subdirname = (
            f"{self.params['setup']['type']}_"
            + f"{self.params['setup']['refrig']}"
            )
        self.design_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'stable', f'{self.subdirname}_design'
            ))
        self.validate_dir()

    def generate_components(self):
        """Initialize components of heat pump."""

    def generate_connections(self):
        """Initialize and add connections and buses to network."""

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""

    def _solve_model(self, **kwargs):
        """Solve the model in design mode."""
        if 'iterinfo' in kwargs:
            self.nw.set_attr(iterinfo=kwargs['iterinfo'])
        self.nw.solve('design')
        self.cop = (
            abs(self.buses['heat output'].P.val)
            / self.buses['power input'].P.val
            )

        if 'print_results' in kwargs:
            if kwargs['print_results']:
                self.nw.print_results()
        if self.nw.residual[-1] < 1e-3:
            self.solved_design = True
            self.nw.save(self.design_path)

    def run_model(self, print_cop=False, exergy_analysis=True, **kwargs):
        """Run the initialization and design simulation routine."""
        self.generate_components()
        self.generate_connections()
        self.init_simulation(**kwargs)
        self.design_simulation(**kwargs)
        self.check_consistency()
        if exergy_analysis:
            self.perform_exergy_analysis(**kwargs)
        if print_cop:
            print(f'COP = {self.cop:.3f}')

    def create_ranges(self):
        """Create stable and base ranges for T_hs_ff, T_cons_ff and pl."""
        self.T_hs_ff_range = np.linspace(
            self.params['offdesign']['T_hs_ff_start'],
            self.params['offdesign']['T_hs_ff_end'],
            self.params['offdesign']['T_hs_ff_steps'],
            endpoint=True
            ).round(decimals=3)
        half_len_hs = int(len(self.T_hs_ff_range)/2) - 1
        self.T_hs_ff_stablerange = np.concatenate([
            self.T_hs_ff_range[half_len_hs::-1],
            self.T_hs_ff_range,
            self.T_hs_ff_range[:half_len_hs:-1]
            ])

        self.T_cons_ff_range = np.linspace(
            self.params['offdesign']['T_cons_ff_start'],
            self.params['offdesign']['T_cons_ff_end'],
            self.params['offdesign']['T_cons_ff_steps'],
            endpoint=True
            ).round(decimals=3)
        half_len_cons = int(len(self.T_cons_ff_range)/2) - 1
        self.T_cons_ff_stablerange = np.concatenate([
            self.T_cons_ff_range[half_len_cons::-1],
            self.T_cons_ff_range,
            self.T_cons_ff_range[:half_len_cons:-1]
            ])

        self.pl_range = np.linspace(
            self.params['offdesign']['partload_min'],
            self.params['offdesign']['partload_max'],
            self.params['offdesign']['partload_steps'],
            endpoint=True
            ).round(decimals=3)
        self.pl_stablerange = np.concatenate(
            [self.pl_range[::-1], self.pl_range]
            )

    def df_to_array(self, results_offdesign):
        """Create 3D arrays of heat output, power input and epsilon from DataFrame."""
        self.Q_array = []
        self.P_array = []
        self.epsilon_array = []
        for i, T_hs_ff in enumerate(self.T_hs_ff_range):
            self.Q_array.append([])
            self.P_array.append([])
            self.epsilon_array.append([])
            for T_cons_ff in self.T_cons_ff_range:
                self.Q_array[i].append(
                    results_offdesign.loc[(T_hs_ff, T_cons_ff), 'Q'].tolist()
                    )
                self.P_array[i].append(
                    results_offdesign.loc[(T_hs_ff, T_cons_ff), 'P'].tolist()
                    )
                self.epsilon_array[i].append(
                    results_offdesign.loc[(T_hs_ff, T_cons_ff), 'epsilon'].tolist()
                    )

    def get_pressure_levels(self, T_evap, T_cond, wf=None):
        """Calculate evaporation, condensation and middle pressure in bar."""
        if not wf:
            wf = self.wf
        p_evap = PSI(
            'P', 'Q', 1,
            'T', T_evap - self.params['evap']['ttd_l'] + 273.15,
            wf
            ) * 1e-5
        p_cond = PSI(
            'P', 'Q', 0,
            'T', T_cond + self.params['cond']['ttd_u'] + 273.15,
            wf
            ) * 1e-5
        p_mid = np.sqrt(p_evap * p_cond)

        return p_evap, p_cond, p_mid

    def calc_cost(self, ref_year, current_year, k_evap=1500, k_cond=3500,
                  k_trans=60, k_misc=50, residence_time=10):
        r"""
        Calculate CAPEX based on cost relevant components.

        Method as defined by Kosmadakis & Arpagaus et al. in:
        "Techno-economic analysis of high-temperature heat pumps with low-global
        warming potential refrigerants for upgrading waste heat up to 150 ◦C"

        DOI: https://doi.org/10.1016/j.enconman.2020.113488

        Parameters
        ----------

        ref_year : int or str
            Reference year of component cost for calculation of CEPCI factor.

        current_year : int or str
            The year the component cost are calculated for.

        k_xxxx : int or float
            Heat transfer coefficients of various heat exchangers in
            $\frac{W}{m^2\cdotK}$

        residence_time : int or float
            Time of residence in seconds of the refrigerant in flash tanks.
        """
        cepcipath = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'input', 'CEPCI.json'
            ))
        with open(cepcipath, 'r', encoding='utf-8') as file:
            cepci = json.load(file)
        if isinstance(ref_year, int):
            ref_year = str(ref_year)
        if isinstance(current_year, int):
            current_year = str(current_year)
        cepci_factor = cepci[current_year] / cepci[ref_year]

        self.cost = {}
        self.design_params = {}
        compcost_total = 0
        for complabel in self.nw.comps.index:
            comp = self.nw.comps.loc[complabel, 'object']
            comptype = self.nw.comps.loc[complabel, 'comp_type']

            if comptype == 'Compressor':
                val = comp.inl[0].v.val_SI * 3600
                self.cost[complabel] = self.eval_costfunc(
                    val, 279.8, 19850, 0.73
                    ) * cepci_factor
                self.design_params[complabel] = val

            elif comptype == 'HeatExchanger':
                if 'Evaporator' in complabel or 'Economizer' in complabel:
                    val = comp.kA.val / k_evap
                elif 'Transcritical' in complabel:
                    val = comp.kA.val / k_trans
                else:
                    val = comp.kA.val / k_misc
                self.cost[complabel] = self.eval_costfunc(
                    val, 42, 15526, 0.80
                    ) * cepci_factor
                self.design_params[complabel] = val

            elif comptype == 'Condenser':
                val = comp.kA.val / k_cond
                self.cost[complabel] = self.eval_costfunc(
                    val, 42, 15526, 0.80
                    ) * cepci_factor
                self.design_params[complabel] = val

            elif comptype == 'DropletSeparator' or comptype == 'Drum':
                conn_liquid = (
                    self.nw.conns[
                        (self.nw.conns['source'].apply(lambda x: x.label) == complabel)
                        & (self.nw.conns['source_id'] == 'out1')].index
                )[0]
                conn_vapor = (
                    self.nw.conns[
                        (self.nw.conns['source'].apply(lambda x: x.label) == complabel)
                        & (self.nw.conns['source_id'] == 'out2')].index
                )[0]
                fluid = list(self.nw.get_conn(conn_vapor).fluid.val.keys())[0]
                p_flash = self.nw.get_conn(conn_vapor).p.val
                dens_liquid = PSI('D', 'Q', 0, 'P', p_flash*1e5, fluid)
                dens_vapor = PSI('D', 'Q', 1, 'P', p_flash*1e5, fluid)
                V_flash = (
                    (self.nw.get_conn(conn_liquid).m.val  / dens_liquid
                     + self.nw.get_conn(conn_vapor).m.val / dens_vapor)
                    * residence_time
                    )
                self.cost[complabel] = self.eval_costfunc(
                    V_flash, 0.089, 1444, 0.63
                    ) * cepci_factor
                self.design_params[complabel] = V_flash

            else:
                continue

            compcost_total += self.cost[complabel]

        self.cost['Piping & Tanks'] = 0.1 * compcost_total
        self.cost['Electrical Equipment'] = 0.1 * compcost_total
        # "the contribution of [refrigerant] cost to the total one is less than 4%."
        self.cost['Refrigerant'] = (1.2 * compcost_total) * (1/0.96 - 1)

        self.cost_equipment = sum(c for c in self.cost.values())
        self.cost_total = 6.32 * self.cost_equipment

    def eval_costfunc(self, val, val_ref, cost_ref, alpha):
        r"""
        Evaluate cost function for given variable value.

        cost function of type:
        $C = C_{ref} \cdot \left(\frac{X}{X_{ref}}\right)^\alpha$
        """
        return cost_ref * (val/val_ref)**alpha

    def perform_exergy_analysis(self, print_results=False, **kwargs):
        """Perform exergy analysis."""
        self.ean = ExergyAnalysis(
            self.nw,
            E_F=[self.buses['power input'], self.buses['heat input']],
            E_P=[self.buses['heat output']]
            )
        self.ean.analyse(
            pamb=self.params['ambient']['p'], Tamb=self.params['ambient']['T']
            )
        if print_results:
            self.ean.print_results(**kwargs)

        self.epsilon = self.ean.network_data['epsilon']

    def get_plotting_states(self):
        """Generate data of states to plot in state diagram."""
        return {}

    def generate_state_diagram(self, refrig='', diagram_type='logph',
                               style='light', figsize=(16, 10), legend=True,
                               legend_loc='upper left', return_diagram=False,
                               savefig=False, open_file=False, filepath=None,
                               **kwargs):
        """
        Generate log(p)-h-diagram of heat pump process.

        Parameters
        ----------

        refrig : str
            Name of refrigerant to use for plot. Can be left as an empty string
            in single cycle heat pumps.

        diagram_type : str
            Fluid property diagram type. Either 'logph' or 'Ts'. Default is
            'logph'.

        style : str
            Diagram style to chose. Either 'light' or 'dark'. Default is
            'light'.

        figsize : tuple/list of numbers
            Size of matplotlib figure in inches. Default is (16, 10), so the
            figure is 16 inches wide and 10 inches tall.

        legend : bool
            Flag to set if legend should be shown. Default is `True`.

        legend_loc : str
            Location to place legend to. Accepts options as matplotlib allows.
            Default is 'upper left'. Is only used if 'legend' parameter is set
            to `True`.

        return_diagram : bool
            Flag to set if diagram object should be returned by method. Default
            is False.

        savefig : bool
            Flag to set if diagram should be saved to disk. Default is `False`.

        filepath : str
            Path to save the file to. If `None` and `savefig` is `True`, a
            default name is given and saved to the current working directory.
            Default is `None`.

        open_file : bool
            Flag to set if saved file should be opend by the os. Default is
            `False`.

        **kwargs
            Additional keyword arguments to pass through to the
            `get_plotting_states` method of the heat pump class.
        """
        if not refrig:
            refrig = self.params['setup']['refrig']
        # Define axis and isoline state variables
        if diagram_type == 'logph':
            var = {'x': 'h', 'y': 'p', 'isolines': ['T', 's']}
        elif diagram_type == 'Ts':
            var = {'x': 's', 'y': 'T', 'isolines': ['h', 'p']}
        else:
            print(
                'Parameter "diagram_type" has to be set correctly. Valid '
                + 'diagram types are "logph" and "Ts".'
                )
            return

        # Get plotting state data
        result_dict = self.get_plotting_states(**kwargs)
        if len(result_dict) == 0:
            print(
                "'get_plotting_states'-method of heat pump "
                + f"'{self.params['setup']['type']}' seems to not be implemented."
                )
            return

        if style == 'light':
            plt.style.use('default')
            isoline_data = None
        elif style == 'dark':
            plt.style.use('dark_background')
            isoline_data = {
                'T': {'style': {'color': 'dimgrey'}},
                'v': {'style': {'color': 'dimgrey'}},
                'Q': {'style': {'color': '#FFFFFF'}},
                'h': {'style': {'color': 'dimgrey'}},
                'p': {'style': {'color': 'dimgrey'}},
                's': {'style': {'color': 'dimgrey'}}
            }

        # Initialize fluid property diagram
        fig, ax = plt.subplots(figsize=figsize)

        diagram_data_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'input', 'diagrams', f"{refrig}.json"
        ))

        # Generate isolines
        path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'input', 'state_diagram_config.json'
            ))
        with open(path, 'r', encoding='utf-8') as file:
            config = json.load(file)

        if refrig in config:
            state_props = config[refrig]
        else:
            state_props = config['MISC']

        if os.path.isfile(diagram_data_path):
            diagram = FluidPropertyDiagram.from_json(diagram_data_path)
        else:
            diagram = FluidPropertyDiagram(refrig)
            diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')

            iso1 = np.arange(
                state_props[var['isolines'][0]]['isorange_low'],
                state_props[var['isolines'][0]]['isorange_high'],
                state_props[var['isolines'][0]]['isorange_step']
                )
            iso2 = np.arange(
                state_props[var['isolines'][1]]['isorange_low'],
                state_props[var['isolines'][1]]['isorange_high'],
                state_props[var['isolines'][1]]['isorange_step']
                )

            diagram.set_isolines(**{
                var['isolines'][0]: iso1,
                var['isolines'][1]: iso2
                })
            diagram.calc_isolines()
            diagram.to_json(diagram_data_path)


        # Calculate components process data
        for compdata in result_dict.values():
            compdata['datapoints'] = (
                diagram.calc_individual_isoline(**compdata)
            )
        diagram.fig = fig
        diagram.ax = ax

        # Set axes limits
        if 'xlims' in kwargs:
            xlims = kwargs['xlims']
        else:
            xlims = (
                state_props[var['x']]['min'], state_props[var['x']]['max']
                )
        if 'ylims' in kwargs:
            ylims = kwargs['ylims']
        else:
            ylims = (
                state_props[var['y']]['min'], state_props[var['y']]['max']
                )

        diagram.draw_isolines(
            diagram_type=diagram_type, fig=fig, ax=ax,
            x_min=xlims[0], x_max=xlims[1], y_min=ylims[0], y_max=ylims[1],
            isoline_data=isoline_data
            )

        # Draw heat pump process over fluid property diagram
        for i, key in enumerate(result_dict.keys()):
            datapoints = result_dict[key]['datapoints']
            has_xvals = len(datapoints[var['x']]) > 0
            has_yvals = len(datapoints[var['y']]) > 0
            if has_xvals and has_yvals:
                ax.plot(
                    datapoints[var['x']][:], datapoints[var['y']][:],
                    color='#EC6707'
                    )
                ax.scatter(
                    datapoints[var['x']][0], datapoints[var['y']][0],
                    color='#B54036',
                    label=f'$\\bf{i+1:.0f}$: {key}', s=100, alpha=0.5
                    )
                ax.annotate(
                    f'{i+1:.0f}',
                    (datapoints[var['x']][0], datapoints[var['y']][0]),
                    ha='center', va='center', color='w'
                    )
            else:
                ax.scatter(
                    0, 0,
                    color='#FFFFFF', s=0, alpha=1.0,
                    label=f'$\\bf{i+1:.0f}$: {key}'
                    )
                ax.annotate(
                    'Error\nMissing Plotting Data', (0.5, 0.5),
                    xycoords='axes fraction', ha='center', va='center',
                    fontsize=60, color='#B54036'
                    )

        # Additional plotting parameters
        if diagram_type == 'logph':
            ax.set_xlabel('Spezifische Enthalpie in $kJ/kg$')
            ax.set_ylabel('Druck in $bar$')
        elif diagram_type == 'Ts':
            ax.set_xlabel('Spezifische Entropie in $kJ/(kg \\cdot K)$')
            ax.set_ylabel('Temperatur in $°C$')

        if legend:
            ax.legend(
                loc=legend_loc,
                prop={'size': 10 * (1 - 0.02 * len(result_dict))},
                markerscale=(1 - 0.02 * len(result_dict))
                )

        if savefig:
            if filepath is None:
                filename = (
                    f'logph_{self.params["setup"]["type"]}_{refrig}.pdf'
                    )
                filepath = os.path.abspath(os.path.join(
                    os.getcwd(), filename
                    ))

            plt.tight_layout()
            plt.savefig(filepath, dpi=300)

            if open_file:
                os.startfile(filepath)

        if return_diagram:
            return diagram

    def generate_sankey_diagram(self, width=None, height=None):
        """Sankey Diagram of Heat Pump model"""
        links, nodes = self.ean.generate_plotly_sankey_input(
            colors={
                'E_F': '#00395B',
                'E_P': '#B54036',
                'E_L': '#EC6707',
                'E_D': '#EC6707',
                'work': '#BFBFBF',
                'heat': '#BFBFBF',
                'two-phase-fluid': '#74ADC0'
            }
        )
        fig = go.Figure(
            go.Sankey(
                arrangement='snap',
                node={
                    'label': nodes,
                    'pad': 15,
                    'color': '#EC6707'
                    },
                link=links
            )
        )

        if width is not None:
            fig.update_layout(width=width)

        if height is not None:
            fig.update_layout(width=height)

        return fig

    def generate_waterfall_diagram(self, figsize=(16, 10), legend=True,
                                   return_fig_ax=False, show_epsilon=True):
        """Generates waterfall diagram of exergy analysis"""
        comps = ['Fuel Exergy']
        E_F = self.ean.network_data.E_F
        E_D = [0]
        E_P = [E_F]
        for comp in self.ean.aggregation_data.sort_values(by='E_D', ascending=False).index:
            # only plot components with exergy destruction > 1 W
            if self.ean.aggregation_data.E_D[comp] > 1:
                comps.append(comp)
                E_D.append(self.ean.aggregation_data.E_D[comp])
                E_F = E_F - self.ean.aggregation_data.E_D[comp]
                E_P.append(E_F)
        comps.append('Product Exergy')
        E_D.append(0)
        E_P.append(E_F)

        E_D = [E * 1e-3 for E in E_D]
        E_P = [E * 1e-3 for E in E_P]

        colors_E_P = ['#74ADC0'] * len(comps)
        colors_E_P[0] = '#00395B'
        colors_E_P[-1] = '#B54036'

        fig, ax = plt.subplots(figsize=figsize)

        ax.barh(
            np.arange(len(comps)), E_P,
            align='center', color=colors_E_P
            )
        ax.barh(
            np.arange(len(comps)), E_D,
            align='center', left=E_P, label='E_D', color='#EC6707'
            )

        if legend:
            ax.legend()

        if show_epsilon:
            ax.annotate(
                f'$\epsilon_{{tot}} = ${self.ean.network_data.epsilon:.3f}',
                (0.96, 0.06),
                xycoords='axes fraction',
                ha='right', va='center', color='k',
                bbox=dict(boxstyle='round,pad=0.3', fc='white')
            )

        ax.set_xlabel('Exergy in kW')
        ax.set_yticks(np.arange(len(comps)))
        ax.set_yticklabels(comps)
        ax.set_xlim([0, ((self.ean.network_data.E_F) / 1000) + 1000])
        ax.set_xticks(
            np.linspace(0, ((self.ean.network_data.E_F) / 1000) + 1000, 9)
            )
        ax.invert_yaxis()
        ax.grid(axis='x')
        ax.set_axisbelow(True)

        if return_fig_ax:
            return fig, ax

    def calc_partload_char(self, **kwargs):
        """
        Interpolate data points of heat output, power input and epsilon.

        Return functions to interpolate values heat output power input
        and epsilon based on the partload and the feed flow
        temperatures of the heat source and sink. If there is
        no data given through keyword arguments, the instances
        attributes will be searched for the necessary data.

        Parameters
        ----------
        kwargs : dict
            Necessary data is:
                Q_array : 3d array
                P_array : 3d array
                epsilon_array : 3d array
                pl_range : 1d array
                T_hs_ff_range : 1d array
                T_cons_ff_range : 1d array
        """
        necessary_params = [
            'Q_array', 'P_array', 'epsilon_array', 'pl_range', 'T_hs_ff_range',
            'T_cons_ff_range'
            ]
        if len(kwargs):
            for nec_param in necessary_params:
                if nec_param not in kwargs:
                    raise KeyError(
                        f'Necessary parameter {nec_param} not '
                        + 'in kwargs. The necessary parameters'
                        + f' are: {necessary_params}'
                        )
            Q_array = np.asarray(kwargs['Q_array'])
            P_array = np.asarray(kwargs['P_array'])
            epsilon_array = np.asarray(kwargs['epsilon_array'])
            pl_range = kwargs['pl_range']
            T_hs_ff_range = kwargs['T_hs_ff_range']
            T_cons_ff_range = kwargs['T_cons_ff_range']
        else:
            for nec_param in necessary_params:
                if nec_param not in self.__dict__:
                    raise AttributeError(
                        f'Necessary parameter {nec_param} can '
                        + 'not be found in the instances '
                        + 'attributes. Please make sure to '
                        + 'perform the offdesign_simulation '
                        + 'method or provide the necessary '
                        + 'parameters as kwargs. These are: '
                        + f'{necessary_params}'
                        )
            Q_array = np.asarray(self.Q_array)
            P_array = np.asarray(self.P_array)
            epsilon_array = np.asarray(self.epsilon_array)
            pl_range = self.pl_range
            T_hs_ff_range = self.T_hs_ff_range
            T_cons_ff_range = self.T_cons_ff_range

        pl_step = 0.01
        T_hs_ff_step = 1
        T_cons_ff_step = 1

        pl_fullrange = np.arange(
            pl_range[0],
            pl_range[-1]+pl_step,
            pl_step
            )
        T_hs_ff_fullrange = np.arange(
            T_hs_ff_range[0], T_hs_ff_range[-1]+T_hs_ff_step, T_hs_ff_step
            )
        T_cons_ff_fullrange = np.arange(
            T_cons_ff_range[0], T_cons_ff_range[-1]+T_cons_ff_step,
            T_cons_ff_step
            )

        multiindex = pd.MultiIndex.from_product(
                        [T_hs_ff_fullrange, T_cons_ff_fullrange, pl_fullrange],
                        names=['T_hs_ff', 'T_cons_ff', 'pl']
                        )

        partload_char = pd.DataFrame(
            index=multiindex, columns=['Q', 'P', 'COP', 'epsilon']
            )

        for T_hs_ff in T_hs_ff_fullrange:
            for T_cons_ff in T_cons_ff_fullrange:
                for pl in pl_fullrange:
                    partload_char.loc[(T_hs_ff, T_cons_ff, pl), 'Q'] = abs(
                        interpn(
                            (T_hs_ff_range, T_cons_ff_range, pl_range),
                            Q_array,
                            (round(T_hs_ff, 3), round(T_cons_ff, 3),
                             round(pl, 3)),
                            bounds_error=False
                            )[0]
                        )
                    partload_char.loc[(T_hs_ff, T_cons_ff, pl), 'P'] = interpn(
                        (T_hs_ff_range, T_cons_ff_range, pl_range),
                        P_array,
                        (round(T_hs_ff, 3), round(T_cons_ff, 3), round(pl, 3)),
                        bounds_error=False
                        )[0]
                    partload_char.loc[(T_hs_ff, T_cons_ff, pl), 'COP'] = (
                        partload_char.loc[(T_hs_ff, T_cons_ff, pl), 'Q']
                        / partload_char.loc[(T_hs_ff, T_cons_ff, pl), 'P']
                        )
                    partload_char.loc[(T_hs_ff, T_cons_ff, pl), 'epsilon'] = interpn(
                        (T_hs_ff_range, T_cons_ff_range, pl_range),
                        epsilon_array,
                        (round(T_hs_ff, 3), round(T_cons_ff, 3), round(pl, 3)),
                        bounds_error=False
                        )[0]

        return partload_char

    def linearize_partload_char(self, partload_char, variable='P',
                                line_type='offset', regression_type='OLS',
                                normalize=None):
        """
        Linearize partload characteristic for usage in MILP problems.

        Parameters
        ----------
        partload_char : pd.DataFrame
            DataFrame of the full partload characteristic containing 'Q', 'P'
            and 'COP' with a MultiIndex of the three variables 'T_hs_ff',
            'T_cons_ff' and 'pl'.

        variable : str
            The variable 'x' in the equation 'y = m * x + b'. Either 'P' or 'Q'.
            Defaults to 'P' if it is not set.

        line_type : str
            Type of linear model to generate. Options are 'origin' for a line
            through the origin or 'offset' for mixed integer offset model.
            Defaults to 'offset' if it is not set.

        regression_type : str
            Type of regression method to use for linearization of the partload
            characteristic. Options are 'OLS' for the method of ordinary least
            squares or 'MinMax' for a line from the minimum to the maximum
            value.
            Defaults to 'OLS' if it is not set.

        normalize : dict
            Dictionairy containing the keys 'T_hs_ff' and 'T_cons_ff'. These
            values are interpreted as the nominal operating temperatures. All
            linear parameters are normalized to the chosen variable at this
            operating point.
            Defaults to None and therefore no normalization if it is not set.
        """
        cols = [f'{variable}_max', f'{variable}_min']
        if line_type == 'origin':
            cols += ['COP']
        elif line_type == 'offset':
            cols += ['c_1', 'c_0']

        T_hs_ff_range = set(
            partload_char.index.get_level_values('T_hs_ff')
            )
        T_cons_ff_range = set(
            partload_char.index.get_level_values('T_cons_ff')
            )

        multiindex = pd.MultiIndex.from_product(
            [T_hs_ff_range, T_cons_ff_range],
            names=['T_hs_ff', 'T_cons_ff']
            )
        linear_model = pd.DataFrame(index=multiindex, columns=cols)

        if variable == 'P':
            resp_variable = 'Q'
        elif variable == 'Q':
            resp_variable = 'P'
        else:
            raise ValueError(
                f"Argument {variable} for parameter 'variable' is not valid."
                + "Choose either 'P' or 'Q'."
                )

        for T_hs_ff in T_hs_ff_range:
            for T_cons_ff in T_cons_ff_range:
                idx = (T_hs_ff, T_cons_ff)
                linear_model.loc[idx, f'{variable}_max'] = (
                    partload_char.loc[idx, variable].max()
                    )
                linear_model.loc[idx, f'{variable}_min'] = (
                    partload_char.loc[idx, variable].min()
                    )
                if regression_type == 'MinMax':
                    if line_type == 'origin':
                        linear_model.loc[idx, 'COP'] = (
                            partload_char.loc[idx, 'Q'].max()
                            / partload_char.loc[idx, 'P'].max()
                            )
                    elif line_type == 'offset':
                        linear_model.loc[idx, 'c_1'] = (
                            (partload_char.loc[idx, 'Q'].max()
                             - partload_char.loc[idx, 'Q'].min())
                            / (partload_char.loc[idx, 'P'].max()
                               - partload_char.loc[idx, 'P'].min())
                            )
                        linear_model.loc[idx, 'c_0'] = (
                            partload_char.loc[idx, 'Q'].max()
                            - partload_char.loc[idx, 'P'].max()
                            * linear_model.loc[idx, 'c_1']
                            )
                elif regression_type == 'OLS':
                    regressor = partload_char.loc[idx, variable].to_numpy()
                    regressor = regressor.reshape(-1, 1)
                    response = partload_char.loc[idx, resp_variable].to_numpy()
                    if line_type == 'origin':
                        LinReg = LinearRegression(fit_intercept=False).fit(
                            regressor, response
                            )
                        linear_model.loc[idx, 'COP'] = LinReg.coef_[0]
                    elif line_type == 'offset':
                        LinReg = LinearRegression().fit(regressor, response)
                        linear_model.loc[idx, 'c_1'] = LinReg.coef_[0]
                        linear_model.loc[idx, 'c_0'] = LinReg.intercept_

        if normalize:
            variable_nom = partload_char.loc[
                (np.round(normalize['T_hs_ff'], 3),
                 np.round(normalize['T_cons_ff'], 3)),
                variable
                ].max()

            linear_model[f'{variable}_max'] /= variable_nom
            linear_model[f'{variable}_min'] /= variable_nom
            if line_type == 'offset':
                linear_model['c_0'] /= variable_nom
                linear_model['c_1'] /= variable_nom

        return linear_model

    def arrange_char_timeseries(self, linear_model, temp_ts):
        """
        Arrange a timeseries of the characteristics based on temperature data.

        If T_cons_ff in temperature timeseries is out of bounds, the closest
        characteristic (min. or max. temperature).

        Parameters
        ----------
        linear_model : pd.DataFrame
            DataFrame of the linearized partload characteristic with a
            MultiIndex of the three variables 'T_hs_ff' and 'T_cons_ff'.

        temp_ts : pd.DataFrame
            Timeseries of 'T_hs_ff' and 'T_cons_ff' as they occur in the period
            observed.
        """
        char_ts = pd.DataFrame(
            index=temp_ts.index, columns=linear_model.columns
            )
        for i in temp_ts.index:
            try:
                char_ts.loc[i, :] = linear_model.loc[
                    (temp_ts.loc[i, 'T_hs_ff'], temp_ts.loc[i, 'T_cons_ff']), :
                    ]
            except KeyError:
                print(temp_ts.loc[i, 'T_cons_ff'], 'not in linear_model.')
                T_cons_ff_range = linear_model.index.get_level_values('T_cons_ff')
                if temp_ts.loc[i, 'T_cons_ff'] < min(T_cons_ff_range):
                    multi_idx = (
                        temp_ts.loc[i, 'T_hs_ff'], min(T_cons_ff_range)
                        )
                elif temp_ts.loc[i, 'T_cons_ff'] > max(T_cons_ff_range):
                    multi_idx = (
                        temp_ts.loc[i, 'T_hs_ff'], max(T_cons_ff_range)
                        )
                char_ts.loc[i, :] = linear_model.loc[multi_idx, :]

        return char_ts

    def plot_partload_char(self, partload_char, cmap_type='', cmap='viridis',
                           return_fig_ax=False, savefig=False, open_file=False):
        """
        Plot the partload characteristic of the heat pump.

        Parameters
        ----------
        partload_char : pd.DataFrame
            DataFrame of the full partload characteristic containing 'Q', 'P',
            'COP' and epsilon with a MultiIndex of the three variables 'T_hs_ff',
            'T_cons_ff' and 'pl'.

        cmap_type : str
            String of the possible colormap variations, which are 'T_cons_ff',
            'COP' and epsilon.

        cmap : str
            Name of colormap. Valid names are all colormaps implemented in
            matplotlib. Defaults to 'veridis'.
        """
        if not cmap_type:
            print(
                'Please provide a cmap_type of eiher "T_cons_ff" or '
                + '"COP" or' + '"epsilon" to plot the heat pump partload characteristic.'
                )
            return

        colormap = plt.get_cmap(cmap)
        T_hs_ff_range = set(
            partload_char.index.get_level_values('T_hs_ff')
            )

        if cmap_type == 'T_cons_ff':
            colors = colormap(
                np.linspace(
                    0, 1,
                    len(set(
                        partload_char.index.get_level_values('T_cons_ff'))
                        ))
                )
            figs = {}
            axes = {}
            for T_hs_ff in T_hs_ff_range:
                fig, ax = plt.subplots(figsize=(9.5, 6))

                T_cons_ff_range = set(
                    partload_char.index.get_level_values('T_cons_ff')
                    )
                for i, T_cons_ff in enumerate(T_cons_ff_range):
                    ax.plot(
                        partload_char.loc[(T_hs_ff, T_cons_ff), 'P'],
                        partload_char.loc[(T_hs_ff, T_cons_ff), 'Q'],
                        color=colors[i]
                        )

                ax.grid()
                sm = plt.cm.ScalarMappable(
                    cmap=colormap, norm=plt.Normalize(
                        vmin=np.min(
                            partload_char.index.get_level_values('T_cons_ff')
                            ),
                        vmax=np.max(
                            partload_char.index.get_level_values('T_cons_ff')
                            )
                        )
                    )
                cbar = plt.colorbar(sm, ax=ax)
                cbar.set_label('Senkentemperatur in $°C$')
                ax.set_xlim(0, partload_char['P'].max() * 1.05)
                ax.set_ylim(0, partload_char['Q'].max() * 1.05)
                ax.set_xlabel('Elektrische Leistung $P$ in $MW$')
                ax.set_ylabel('Wärmestrom $\\dot{{Q}}$ in $MW$')
                ax.set_title(f'Quellentemperatur: {T_hs_ff:.0f} °C')
                figs[T_hs_ff] = fig
                axes[T_hs_ff] = ax

        if cmap_type == 'COP':
            figs = {}
            axes = {}
            for T_hs_ff in T_hs_ff_range:
                fig, ax = plt.subplots(figsize=(9.5, 6))

                scatterplot = ax.scatter(
                    partload_char.loc[(T_hs_ff), 'P'],
                    partload_char.loc[(T_hs_ff), 'Q'],
                    c=partload_char.loc[(T_hs_ff), 'COP'],
                    cmap=colormap,
                    vmin=(
                        partload_char['COP'].min()
                        - partload_char['COP'].max() * 0.05
                        ),
                    vmax=(
                        partload_char['COP'].max()
                        + partload_char['COP'].max() * 0.05
                        )
                    )

                cbar = plt.colorbar(scatterplot, ax=ax)
                cbar.set_label('Leistungszahl $COP$')

                ax.grid()
                ax.set_xlim(0, partload_char['P'].max() * 1.05)
                ax.set_ylim(0, partload_char['Q'].max() * 1.05)
                ax.set_xlabel('Elektrische Leistung $P$ in $MW$')
                ax.set_ylabel('Wärmestrom $\\dot{{Q}}$ in $MW$')
                ax.set_title(f'Quellentemperatur: {T_hs_ff:.0f} °C')
                figs[T_hs_ff] = fig
                axes[T_hs_ff] = ax

        if cmap_type == 'epsilon':
            figs = {}
            axes = {}
            for T_hs_ff in T_hs_ff_range:
                fig, ax = plt.subplots(figsize=(9.5, 6))
                scatterplot = ax.scatter(
                    partload_char.loc[T_hs_ff, 'P'],
                    partload_char.loc[T_hs_ff, 'Q'],
                    c=partload_char.loc[T_hs_ff, 'epsilon'],
                    cmap=colormap,
                    vmin=(
                        partload_char['epsilon'].min()
                        - partload_char['epsilon'].max() * 0.05
                        ),
                    vmax=(
                        partload_char['epsilon'].max()
                        + partload_char['epsilon'].max() * 0.05
                        )
                    )

                cbar = plt.colorbar(scatterplot, ax=ax)
                cbar.set_label('Exergetische Effizienz $ε$')

                ax.grid()
                ax.set_xlim(0, partload_char['P'].max() * 1.05)
                ax.set_ylim(0, partload_char['Q'].max() * 1.05)
                ax.set_xlabel('Elektrische Leistung $P$ in $MW$')
                ax.set_ylabel('Wärmestrom $\\dot{{Q}}$ in $MW$')
                ax.set_title(f'Quellentemperatur: {T_hs_ff:.0f} °C')
                figs[T_hs_ff] = fig
                axes[T_hs_ff] = ax

        if savefig:
            try:
                filename = (
                    f'partload_{cmap_type}_{self.params["setup"]["type"]}_'
                    + f'{self.params["setup"]["refrig"]}.pdf'
                    )
            except KeyError:
                filename = (
                    f'partload_{cmap_type}_{self.params["setup"]["type"]}_'
                    + f'{self.params["setup"]["refrig1"]}_and_'
                    + f'{self.params["setup"]["refrig2"]}.pdf'
                    )
            filepath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'output', filename
                ))
            plt.tight_layout()
            plt.savefig(filepath, dpi=300)

            if open_file:
                os.startfile(filepath)

        elif return_fig_ax:
            return figs, axes
        else:
            plt.show()

    def validate_dir(self):
        """Check for a 'stable' directory and create it if necessary."""
        stablepath = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'stable'
            ))
        if not os.path.exists(stablepath):
            os.mkdir(stablepath)
        outputpath = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'output'
            ))
        if not os.path.exists(outputpath):
            os.mkdir(outputpath)

    def check_consistency(self):
        """Perform all necessary checks to protect consistency of parameters."""
        pass

    def offdesign_simulation(self, log_simulations=False):
        """Perform offdesign parametrization and simulation."""
        if not self.solved_design:
            raise RuntimeError(
                'Heat pump has not been designed via the "design_simulation" '
                + 'method. Therefore the offdesign simulation will fail.'
            )

        # Parametrization
        kA_char1_default = ldc(
            'heat exchanger', 'kA_char1', 'DEFAULT', CharLine
        )
        kA_char1_cond = ldc(
            'heat exchanger', 'kA_char1', 'CONDENSING FLUID', CharLine
        )
        kA_char2_evap = ldc(
            'heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine
        )
        kA_char2_default = ldc(
            'heat exchanger', 'kA_char2', 'DEFAULT', CharLine
        )

        tespy_components = ['Condenser', 'HeatExchanger', 'Compressor', 'Pump', 'SimpleHeatExchanger']

        # Extract the label of the above necessary tespy components.
        # And then extracts the object of the components for parametrization
        for comp in tespy_components:
            df = self.nw.comps
            labels = df[df['comp_type'] == comp].index.tolist()
            for label in labels:
                object = self.nw.get_comp(label)

                if comp == 'Compressor':
                    object.set_attr(
                        design=['eta_s'], offdesign=['eta_s_char']
                    )
                elif comp == 'Pump':
                    object.set_attr(
                        design=['eta_s'], offdesign=['eta_s_char']
                    )
                elif comp == 'HeatExchanger':
                    # for models with internal heat exchanger
                    if 'Internal Heat Exchanger' in label:
                        object.set_attr(
                            kA_char1=kA_char1_default, kA_char2=kA_char2_default,
                            design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2']
                        )

                    # For models with Transcritical heat exchanger
                    elif 'Transcritical' in label:
                        object.set_attr(
                            kA_char1=kA_char1_default, kA_char2=kA_char2_default,
                            design=['pr2', 'ttd_l'], offdesign=['zeta2', 'kA_char']
                        )

                    # For cascade model's Intermediate heat exchanger
                    elif 'Intermediate Heat Exchanger' in label:
                        object.set_attr(
                            kA_char1=kA_char1_cond, kA_char2=kA_char2_evap,
                            design=['pr1', 'ttd_u'], offdesign=['zeta1', 'kA_char']
                        )
                    else:
                        # For models with evaporator and economizer
                        object.set_attr(
                            kA_char1=kA_char1_default, kA_char2=kA_char2_evap,
                            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char']
                        )
                elif comp == 'Condenser':
                    object.set_attr(
                        kA_char1=kA_char1_cond, kA_char2=kA_char2_default,
                        design=['pr2', 'ttd_u'], offdesign=['zeta2', 'kA_char']
                    )
                elif comp == 'SimpleHeatExchanger':
                    object.set_attr(
                        design=['pr'], offdesign=['zeta']
                    )
                else:
                    raise ValueError(
                        f'Check wheather offdesign parametrization is given to the component {comp}'
                        + f' in the heat pump base class.'
                    )


        self.conns['B1'].set_attr(offdesign=['v'])
        self.conns['B2'].set_attr(design=['T'])

        # Simulation
        print('Using improved offdesign simulation method.')
        self.create_ranges()

        deltaT_hs = (
                self.params['B1']['T']
                - self.params['B2']['T']
        )

        multiindex = pd.MultiIndex.from_product(
            [self.T_hs_ff_range, self.T_cons_ff_range, self.pl_range],
            names=['T_hs_ff', 'T_cons_ff', 'pl']
        )

        results_offdesign = pd.DataFrame(
            index=multiindex, columns=['Q', 'P', 'COP', 'epsilon', 'residual']
        )

        for T_hs_ff in self.T_hs_ff_stablerange:
            self.conns['B1'].set_attr(T=T_hs_ff)
            if T_hs_ff <= 7:
                self.conns['B2'].set_attr(T=2)
            else:
                self.conns['B2'].set_attr(T=T_hs_ff - deltaT_hs)

            for T_cons_ff in self.T_cons_ff_stablerange:
                self.conns['C3'].set_attr(T=T_cons_ff)

                self.intermediate_states_offdesign(T_hs_ff, T_cons_ff, deltaT_hs)

                for pl in self.pl_stablerange[::-1]:
                    print(
                        f'### Temp. HS = {T_hs_ff} °C, Temp. Cons = '
                        + f'{T_cons_ff} °C, Partload = {pl * 100} % ###'
                    )
                    self.init_path = None
                    no_init_path = (
                            (T_cons_ff != self.T_cons_ff_range[0])
                            and (pl == self.pl_range[-1])
                    )
                    if no_init_path:
                        self.init_path = os.path.abspath(os.path.join(
                            os.path.dirname(__file__), 'stable',
                            f'{self.subdirname}_init'
                        ))

                    self.comps['cons'].set_attr(Q=None)
                    self.conns['A0'].set_attr(m=pl * self.m_design)

                    try:
                        self.nw.solve(
                            'offdesign', design_path=self.design_path
                        )
                        self.perform_exergy_analysis()
                        failed = False
                    except ValueError:
                        failed = True

                    # Logging simulation
                    if log_simulations:
                        logdirpath = os.path.abspath(os.path.join(
                            os.path.dirname(__file__), 'output', 'logging'
                        ))
                        if not os.path.exists(logdirpath):
                            os.mkdir(logdirpath)
                        logpath = os.path.join(
                            logdirpath, f'{self.subdirname}_offdesign_log.csv'
                        )
                        timestamp = datetime.fromtimestamp(time()).strftime(
                            '%H:%M:%S'
                        )
                        log_entry = (
                                f'{timestamp};{(self.nw.residual[-1] < 1e-3)};'
                                + f'{T_hs_ff:.2f};{T_cons_ff:.2f};{pl:.1f};'
                                + f'{self.nw.residual[-1]:.2e}\n'
                        )
                        if not os.path.exists(logpath):
                            with open(logpath, 'w', encoding='utf-8') as file:
                                file.write(
                                    'Time;converged;Temp HS;Temp Cons;Partload;'
                                    + 'Residual\n'
                                )
                                file.write(log_entry)
                        else:
                            with open(logpath, 'a', encoding='utf-8') as file:
                                file.write(log_entry)

                    if pl == self.pl_range[-1] and self.nw.residual[-1] < 1e-3:
                        self.nw.save(os.path.abspath(os.path.join(
                            os.path.dirname(__file__), 'stable',
                            f'{self.subdirname}_init'
                        )))

                    inranges = (
                            (T_hs_ff in self.T_hs_ff_range)
                            & (T_cons_ff in self.T_cons_ff_range)
                            & (pl in self.pl_range)
                    )
                    idx = (T_hs_ff, T_cons_ff, pl)
                    if inranges:
                        empty_or_worse = (
                                pd.isnull(results_offdesign.loc[idx, 'Q'])
                                or (self.nw.residual[-1]
                                    < results_offdesign.loc[idx, 'residual']
                                    )
                        )
                        if empty_or_worse:
                            if failed:
                                results_offdesign.loc[idx, 'Q'] = np.nan
                                results_offdesign.loc[idx, 'P'] = np.nan
                                results_offdesign.loc[idx, 'epsilon'] = np.nan
                            else:
                                results_offdesign.loc[idx, 'Q'] = abs(
                                    self.buses['heat output'].P.val * 1e-6
                                )
                                results_offdesign.loc[idx, 'P'] = (
                                        self.buses['power input'].P.val * 1e-6
                                )
                                results_offdesign.loc[idx, 'epsilon'] = round(
                                    self.ean.network_data['epsilon'], 3
                                )

                            results_offdesign.loc[idx, 'COP'] = (
                                    results_offdesign.loc[idx, 'Q']
                                    / results_offdesign.loc[idx, 'P']
                            )
                            results_offdesign.loc[idx, 'residual'] = (
                                self.nw.residual[-1]
                            )

        if self.params['offdesign']['save_results']:
            resultpath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'output',
                f'{self.subdirname}_partload.csv'
            ))
            results_offdesign.to_csv(resultpath, sep=';')

        self.df_to_array(results_offdesign)

    def intermediate_states_offdesign(self, T_hs_ff, T_cons_ff, deltaT_hs):
        """Calculates intermediate states during part-load simulation"""
        pass

    def get_compressor_results(self):
        """Return key results for each compressor used in the heat pump."""
        results = {}
        for c in self.comps.values():
            if 'Compressor' in c.label:
                comp = c.label
                results[comp] = {}

                results[comp]['V_dot'] = c.inl[0].vol.val_SI * 3600
                results[comp]['p_in'] = c.inl[0].p.val
                results[comp]['p_out'] = c.outl[0].p.val
                results[comp]['PI'] = c.outl[0].p.val / c.inl[0].p.val
                results[comp]['T_in'] = c.inl[0].T.val
                results[comp]['T_out'] = c.outl[0].T.val

        return results
