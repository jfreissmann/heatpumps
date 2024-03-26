import json
import os

import matplotlib.pyplot as plt
import numpy as np
from CoolProp.CoolProp import PropsSI as PSI
from fluprodia import FluidPropertyDiagram
from tespy.networks import Network
from tespy.tools import ExergyAnalysis


class HeatPumpBase:
    """Super class of all concrete heat pump models."""

    def __init__(self, params):
        """Initialize model and set necessary attributes."""
        self.params = params
        self.wf = self.params['fluids']['wf']
        self.si = self.params['fluids']['si']
        self.so = self.params['fluids']['so']

        if self.si == self.so:
            self.fluid_vec_wf = {self.wf: 1, self.si:0}
            self.fluid_vec_si = {self.wf: 0, self.si: 1}
            self.fluid_vec_so = {self.wf: 0, self.si: 1}
        else:
            self.fluid_vec_wf = {self.wf: 1, self.si: 0, self.so: 0}
            self.fluid_vec_si = {self.wf: 0, self.si: 1, self.so: 0}
            self.fluid_vec_so = {self.wf: 0, self.si: 0, self.so: 1}

        self.comps = dict()
        self.conns = dict()
        self.busses = dict()

        self.nw = Network(
            fluids=[fluid for fluid in self.fluid_vec_wf],
            T_unit='C', p_unit='bar', h_unit='kJ / kg',
            m_unit='kg / s'
            )

        self.cop = np.nan
        self.epsilon = np.nan

        self.solved_design = False
        self.subdirname = (
            f"{self.params['setup']['type']}_"
            + f"{self.params['setup']['refrig']}"
            )
        self.design_path = os.path.join(
            __file__, '..', 'stable', f'{self.subdirname}_design'
            )
        self.validate_dir()

    def generate_components(self):
        """Initialize components of heat pump."""

    def generate_connections(self):
        """Initialize and add connections and busses to network."""

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
            abs(self.busses['heat output'].P.val)
            / self.busses['power input'].P.val
            )

        if 'print_results' in kwargs:
            if kwargs['print_results']:
                self.nw.print_results()
        if self.nw.res[-1] < 1e-3:
            self.solved_design = True
            self.nw.save(self.design_path)

    def run_model(self, print_cop=False, **kwargs):
        """Run the initialization and design simulation routine."""
        self.generate_components()
        self.generate_connections()
        self.init_simulation(**kwargs)
        self.design_simulation(**kwargs)
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
        """Create 3D arrays of heat output and power input from DataFrame."""
        self.Q_array = []
        self.P_array = []
        for i, T_hs_ff in enumerate(self.T_hs_ff_range):
            self.Q_array.append([])
            self.P_array.append([])
            for T_cons_ff in self.T_cons_ff_range:
                self.Q_array[i].append(
                    results_offdesign.loc[(T_hs_ff, T_cons_ff), 'Q'].tolist()
                    )
                self.P_array[i].append(
                    results_offdesign.loc[(T_hs_ff, T_cons_ff), 'P'].tolist()
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

    def calc_cost(self, ref_year, current_year):
        """
        Calculate CAPEX based on cost relevant components.
        
        Method as defined by Kosmadakis & Arpagaus et al. in:
        "Techno-economic analysis of high-temperature heat pumps with low-global
        warming potential refrigerants for upgrading waste heat up to 150 ◦C"

        DOI: https://doi.org/10.1016/j.enconman.2020.113488
        """
        cepcipath = os.path.join(__file__, '..', 'input', 'CEPCI.json')
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
                    val = comp.kA.val / 1500
                elif 'Transcritical' in complabel:
                    val = comp.kA.val / 60
                else:
                    val = comp.kA.val / 50
                self.cost[complabel] = self.eval_costfunc(
                    val, 42, 15526, 0.80
                    ) * cepci_factor
                self.design_params[complabel] = val

            elif comptype == 'Condenser':
                val = comp.kA.val / 3500
                self.cost[complabel] = self.eval_costfunc(
                    val, 42, 15526, 0.80
                    ) * cepci_factor
                self.design_params[complabel] = val

            elif comptype == 'DropletSeparator' or comptype == 'Drum':
                residence_time = 10
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
                p_flash = self.nw.get_conn(conn_vapor).p.val
                dens_liquid = PSI('D', 'Q', 0, 'P', p_flash*1e5, self.wf)
                dens_vapor = PSI('D', 'Q', 1, 'P', p_flash*1e5, self.wf)
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
            E_F=[self.busses['power input'], self.busses['heat input']],
            E_P=[self.busses['heat output']]
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
                               figsize=(16, 10), legend=True,
                               return_diagram=False, savefig=True,
                               open_file=True, **kwargs):
        """Generate log(p)-h-diagram of heat pump process."""
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

        # Initialize fluid property diagram
        fig, ax = plt.subplots(figsize=figsize)
        diagram = FluidPropertyDiagram(refrig)
        diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')

        # Calculate components process data
        for compdata in result_dict.values():
            compdata['datapoints'] = (
                diagram.calc_individual_isoline(**compdata)
                )

        # Generate isolines
        path = os.path.join(
            __file__, '..', 'input', 'state_diagram_config.json'
            )
        with open(path, 'r', encoding='utf-8') as file:
            config = json.load(file)

        if refrig in config:
            state_props = config[refrig]
        else:
            state_props = config['MISC']

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

        # Set axes limits
        xlims = (
            state_props[var['x']]['min'], state_props[var['x']]['max']
            )
        ylims = (
            state_props[var['y']]['min'], state_props[var['y']]['max']
            )
        diagram.draw_isolines(
            diagram_type=diagram_type, fig=fig, ax=ax,
            x_min=xlims[0], x_max=xlims[1], y_min=ylims[0], y_max=ylims[1]
            )

        # Draw heat pump process over fluid property diagram
        # Note: 1st and last value is ommited, as they're sometimes error prone
        for i, key in enumerate(result_dict.keys()):
            datapoints = result_dict[key]['datapoints']
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

        # Additional plotting parameters
        if diagram_type == 'logph':
            ax.set_xlabel('Spezifische Enthalpie in $kJ/kg$')
            ax.set_ylabel('Druck in $bar$')
        elif diagram_type == 'Ts':
            ax.set_xlabel('Spezifische Entropie in $kJ/(kg \\cdot K)$')
            ax.set_ylabel('Temperatur in $°C$')

        if legend:
            ax.legend()

        if savefig:
            filename = (
                f'logph_{self.params["setup"]["type"]}_{refrig}.pdf'
                )
            filepath = os.path.join(
                __file__, '..', 'output', diagram_type, filename
                )
            plt.tight_layout()
            plt.savefig(filepath, dpi=300)

            if open_file:
                os.startfile(filepath)

        if return_diagram:
            return diagram

    def validate_dir(self):
        """Check for a 'stable' directory and create it if necessary."""
        if not os.path.exists(os.path.join(__file__, '..', 'stable')):
            os.mkdir(os.path.join(__file__, '..', 'stable'))
        if not os.path.exists(os.path.join(__file__, '..', 'output')):
            os.mkdir(os.path.join(__file__, '..', 'output'))
