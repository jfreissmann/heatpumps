import json
import os
from datetime import datetime
from time import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI as PSI
from fluprodia import FluidPropertyDiagram
from scipy.interpolate import interpn
from sklearn.linear_model import LinearRegression
from tespy.components import (Compressor, Condenser, CycleCloser,
                              DropletSeparator, HeatExchanger,
                              HeatExchangerSimple, Merge, Pump, Sink, Source,
                              Splitter, Valve)
from tespy.connections import Bus, Connection, Ref
from tespy.tools import ExergyAnalysis
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

if __name__ == '__main__':
    from HeatPumpBase import HeatPumpBase
else:
    from .HeatPumpBase import HeatPumpBase


class HeatPumpPC(HeatPumpBase):
    """Heat pump with open or closed economizer and parallel compression."""

    def __init__(self, params, econ_type='closed'):
        """Initialize model and set necessary attributes."""
        super().__init__(params)
        self.econ_type = econ_type

    def generate_components(self):
        """Initialize components of heat pump."""
        # Heat source
        self.comps['hs_ff'] = Source('Heat Source Feed Flow')
        self.comps['hs_bf'] = Sink('Heat Source Back Flow')
        self.comps['hs_pump'] = Pump('Heat Source Recirculation Pump')

        # Heat sink
        self.comps['cons_cc'] = CycleCloser('Consumer Cycle Closer')
        self.comps['cons_pump'] = Pump('Consumer Recirculation Pump')
        self.comps['cons'] = HeatExchangerSimple('Consumer')

        # Main cycle
        self.comps['cond'] = Condenser('Condenser')
        self.comps['cc'] = CycleCloser('Main Cycle Closer')
        self.comps['mid_valve'] = Valve('Intermediate Valve')
        self.comps['evap_valve'] = Valve('Evaporation Valve')
        self.comps['evap'] = HeatExchanger('Evaporator')
        self.comps['comp1'] = Compressor('Compressor 1')
        self.comps['comp2'] = Compressor('Compressor 2')
        self.comps['merge'] = Merge('Compressor Merge')

        if self.econ_type.lower() == 'closed':
            self.comps['split'] = Splitter('Condensate Splitter')
            self.comps['econ'] = HeatExchanger('Economizer')
        elif self.econ_type.lower() == 'open':
            self.comps['econ'] = DropletSeparator('Economizer')
        else:
            raise ValueError(
                f"Parameter '{self.econ_type}' is not a valid econ_type. "
                + "Supported values are 'open' and 'closed'."
                )

    def generate_connections(self):
        """Initialize and add connections and busses to network."""
        # Connections
        self.conns['A0'] = Connection(
            self.comps['cond'], 'out1', self.comps['cc'], 'in1', 'A0'
            )
        self.conns['A3'] = Connection(
            self.comps['econ'], 'out1', self.comps['evap_valve'], 'in1', 'A3'
            )
        self.conns['A4'] = Connection(
            self.comps['evap_valve'], 'out1', self.comps['evap'], 'in2', 'A4'
            )
        self.conns['A5'] = Connection(
            self.comps['evap'], 'out2', self.comps['comp1'], 'in1', 'A5'
            )
        self.conns['A6'] = Connection(
            self.comps['comp1'], 'out1', self.comps['merge'], 'in1', 'A6'
            )
        self.conns['A7'] = Connection(
            self.comps['merge'], 'out1', self.comps['cond'], 'in1', 'A7'
            )
        self.conns['A8'] = Connection(
            self.comps['econ'], 'out2', self.comps['comp2'], 'in1', 'A8'
            )
        self.conns['A9'] = Connection(
            self.comps['comp2'], 'out1', self.comps['merge'], 'in2', 'A9'
            )

        self.conns['B1'] = Connection(
            self.comps['hs_ff'], 'out1', self.comps['evap'], 'in1', 'B1'
            )
        self.conns['B2'] = Connection(
            self.comps['evap'], 'out1', self.comps['hs_pump'], 'in1', 'B2'
            )
        self.conns['B3'] = Connection(
            self.comps['hs_pump'], 'out1', self.comps['hs_bf'], 'in1', 'B3'
            )

        self.conns['C0'] = Connection(
            self.comps['cons'], 'out1', self.comps['cons_cc'], 'in1', 'C0'
            )
        self.conns['C1'] = Connection(
            self.comps['cons_cc'], 'out1', self.comps['cons_pump'], 'in1', 'C1'
            )
        self.conns['C2'] = Connection(
            self.comps['cons_pump'], 'out1', self.comps['cond'], 'in2', 'C2'
            )
        self.conns['C3'] = Connection(
            self.comps['cond'], 'out2', self.comps['cons'], 'in1', 'C3'
            )

        if self.econ_type.lower() == 'closed':
            self.conns['A1'] = Connection(
                self.comps['cc'], 'out1', self.comps['split'], 'in1', 'A1'
                )
            self.conns['A2'] = Connection(
                self.comps['split'], 'out1', self.comps['econ'], 'in1', 'A2'
                )
            self.conns['A10'] = Connection(
                self.comps['split'], 'out2',
                self.comps['mid_valve'], 'in1', 'A10'
                )
            self.conns['A11'] = Connection(
                self.comps['mid_valve'], 'out1',
                self.comps['econ'], 'in2', 'A11'
                )
        elif self.econ_type.lower() == 'open':
            self.conns['A1'] = Connection(
                self.comps['cc'], 'out1', self.comps['mid_valve'], 'in1', 'A1'
                )
            self.conns['A2'] = Connection(
                self.comps['mid_valve'], 'out1', self.comps['econ'], 'in1', 'A2'
                )

        self.nw.add_conns(*[conn for conn in self.conns.values()])

        # Busses
        mot_x = np.array([
            0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
            0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15,
            1.2, 10
            ])
        mot_y = (np.array([
            0.01, 0.3148, 0.5346, 0.6843, 0.7835, 0.8477, 0.8885, 0.9145,
            0.9318, 0.9443, 0.9546, 0.9638, 0.9724, 0.9806, 0.9878, 0.9938,
            0.9982, 1.0009, 1.002, 1.0015, 1, 0.9977, 0.9947, 0.9909, 0.9853,
            0.9644
            ]) * 0.98)
        mot = CharLine(x=mot_x, y=mot_y)
        self.busses['power input'] = Bus('power input')
        self.busses['power input'].add_comps(
            {'comp': self.comps['comp1'], 'char': mot, 'base': 'bus'},
            {'comp': self.comps['comp2'], 'char': mot, 'base': 'bus'},
            {'comp': self.comps['hs_pump'], 'char': mot, 'base': 'bus'},
            {'comp': self.comps['cons_pump'], 'char': mot, 'base': 'bus'}
            )

        self.busses['heat input'] = Bus('heat input')
        self.busses['heat input'].add_comps(
            {'comp': self.comps['hs_ff'], 'base': 'bus'},
            {'comp': self.comps['hs_bf'], 'base': 'component'}
            )

        self.busses['heat output'] = Bus('heat output')
        self.busses['heat output'].add_comps(
            {'comp': self.comps['cons'], 'base': 'component'}
            )

        self.nw.add_busses(*[bus for bus in self.busses.values()])

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""
        # Components
        self.comps['comp1'].set_attr(eta_s=self.params['comp1']['eta_s'])
        self.comps['comp2'].set_attr(eta_s=self.params['comp2']['eta_s'])
        self.comps['hs_pump'].set_attr(eta_s=self.params['hs_pump']['eta_s'])
        self.comps['cons_pump'].set_attr(
            eta_s=self.params['cons_pump']['eta_s']
            )

        self.comps['evap'].set_attr(
            pr1=self.params['evap']['pr1'], pr2=self.params['evap']['pr2']
            )
        self.comps['cond'].set_attr(
            pr1=self.params['cond']['pr1'], pr2=self.params['cond']['pr2']
            )
        self.comps['cons'].set_attr(
            pr=self.params['cons']['pr'], Q=self.params['cons']['Q']
            , dissipative=False
            )
        if self.econ_type.lower() == 'closed':
            self.comps['econ'].set_attr(
                pr1=self.params['econ']['pr1'], pr2=self.params['econ']['pr2']
                )

        # Connections
        # Starting values
        p_evap, p_cond, p_mid = self.get_pressure_levels(
            T_evap=self.params['B2']['T'], T_cond=self.params['C3']['T']
            )

        # Main cycle
        self.conns['A5'].set_attr(x=self.params['A5']['x'], p=p_evap)
        self.conns['A0'].set_attr(p=p_cond, fluid=self.fluid_vec_wf)
        self.conns['A8'].set_attr(p=p_mid)
        if self.econ_type.lower() == 'closed':
            self.conns['A8'].set_attr(x=1)
            self.conns['A2'].set_attr(
                m=Ref(self.conns['A0'], 0.9, 0)
                )

        # Heat source
        self.conns['B1'].set_attr(
            T=self.params['B1']['T'], p=self.params['B1']['p'],
            fluid=self.fluid_vec_so
            )
        self.conns['B2'].set_attr(T=self.params['B2']['T'])
        self.conns['B3'].set_attr(p=self.params['B1']['p'])

        # Heat sink
        self.conns['C3'].set_attr(
            T=self.params['C3']['T'], p=self.params['C3']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['C0'].set_attr(T=self.params['C0']['T'])

        # Perform initial simulation and unset starting values
        self._solve_model(**kwargs)

        if self.econ_type == 'closed':
            self.conns['A2'].set_attr(m=None)
        self.conns['A5'].set_attr(p=None)
        self.conns['A0'].set_attr(p=None)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.comps['evap'].set_attr(ttd_l=self.params['evap']['ttd_l'])
        self.comps['cond'].set_attr(ttd_u=self.params['cond']['ttd_u'])
        if self.econ_type == 'closed':
            self.comps['econ'].set_attr(ttd_l=self.params['econ']['ttd_l'])

        self._solve_model(**kwargs)

        self.m_design = self.conns['A0'].m.val

        self.cop = (
            abs(self.busses['heat output'].P.val)
            / self.busses['power input'].P.val
            )

    def offdesign_simulation(self, log_simulations=False):
        """Perform offdesign parametrization and simulation."""
        if not self.solved_design:
            raise RuntimeError(
                'Heat pump has not been designed via the "design_simulation" '
                + 'method. Therefore the offdesign simulation will fail.'
                )

        # Parametrization
        self.comps['comp1'].set_attr(
            design=['eta_s'], offdesign=['eta_s_char']
            )
        self.comps['comp2'].set_attr(
            design=['eta_s'], offdesign=['eta_s_char']
            )
        self.comps['hs_pump'].set_attr(
            design=['eta_s'], offdesign=['eta_s_char']
            )
        self.comps['cons_pump'].set_attr(
            design=['eta_s'], offdesign=['eta_s_char']
            )

        self.conns['B1'].set_attr(offdesign=['v'])
        self.conns['B2'].set_attr(design=['T'])

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

        self.comps['cond'].set_attr(
            kA_char1=kA_char1_cond, kA_char2=kA_char2_default,
            design=['pr2', 'ttd_u'], offdesign=['zeta2', 'kA_char']
            )

        self.comps['cons'].set_attr(design=['pr'], offdesign=['zeta'])

        self.comps['evap'].set_attr(
            kA_char1=kA_char1_default, kA_char2=kA_char2_evap,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char']
            )

        if self.econ_type == 'closed':
            self.comps['econ'].set_attr(
                kA_char1=kA_char1_default, kA_char2=kA_char2_evap,
                design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char']
                )

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
            index=multiindex, columns=['Q', 'P', 'COP', 'residual']
            )

        for T_hs_ff in self.T_hs_ff_stablerange:
            self.conns['B1'].set_attr(T=T_hs_ff)
            if T_hs_ff <= 7:
                self.conns['B2'].set_attr(T=2)
            else:
                self.conns['B2'].set_attr(T=T_hs_ff-deltaT_hs)

            for T_cons_ff in self.T_cons_ff_stablerange:
                self.conns['C3'].set_attr(T=T_cons_ff)

                _, _, p_mid = self.get_pressure_levels(
                    T_evap=T_hs_ff, T_cond=T_cons_ff
                    )
                self.conns['A8'].set_attr(p=p_mid)
                for pl in self.pl_stablerange[::-1]:
                    print(
                        f'### Temp. HS = {T_hs_ff} °C, Temp. Cons = '
                        + f'{T_cons_ff} °C, Partload = {pl*100} % ###'
                        )
                    self.init_path = None
                    no_init_path = (
                        (T_cons_ff != self.T_cons_ff_range[0])
                        and (pl == self.pl_range[-1])
                        )
                    if no_init_path:
                        self.init_path = os.path.join(
                            __file__, '..', 'stable', f'{self.subdirname}_init'
                         )

                    self.comps['cons'].set_attr(Q=None)
                    self.conns['A0'].set_attr(m=pl*self.m_design)

                    try:
                        self.nw.solve(
                            'offdesign', design_path=self.design_path
                            )
                        failed = False
                    except ValueError:
                        failed = True

                    # Logging simulation
                    if log_simulations:
                        logdirpath = os.path.join(
                            __file__, '..', 'output', 'logging'
                            )
                        if not os.path.exists(logdirpath):
                            os.mkdir(logdirpath)
                        logpath = os.path.join(
                            logdirpath, f'{self.subdirname}_offdesign_log.csv'
                            )
                        timestamp = datetime.fromtimestamp(time()).strftime(
                            '%H:%M:%S'
                            )
                        log_entry = (
                            f'{timestamp};{(self.nw.res[-1] < 1e-3)};'
                            + f'{T_hs_ff:.2f};{T_cons_ff:.2f};{pl:.1f};'
                            + f'{self.nw.res[-1]:.2e}\n'
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

                    if pl == self.pl_range[-1] and self.nw.res[-1] < 1e-3:
                        self.nw.save(os.path.join(
                            __file__, '..', 'stable', f'{self.subdirname}_init'
                         ))

                    inranges = (
                        (T_hs_ff in self.T_hs_ff_range)
                        & (T_cons_ff in self.T_cons_ff_range)
                        & (pl in self.pl_range)
                        )
                    idx = (T_hs_ff, T_cons_ff, pl)
                    if inranges:
                        empty_or_worse = (
                            pd.isnull(results_offdesign.loc[idx, 'Q'])
                            or (self.nw.res[-1]
                                < results_offdesign.loc[idx, 'residual']
                                )
                        )
                        if empty_or_worse:
                            if failed:
                                results_offdesign.loc[idx, 'Q'] = np.nan
                                results_offdesign.loc[idx, 'P'] = np.nan
                            else:
                                results_offdesign.loc[idx, 'Q'] = abs(
                                    self.busses['heat output'].P.val * 1e-6
                                    )
                                results_offdesign.loc[idx, 'P'] = (
                                    self.busses['power input'].P.val * 1e-6
                                    )

                            results_offdesign.loc[idx, 'COP'] = (
                                results_offdesign.loc[idx, 'Q']
                                / results_offdesign.loc[idx, 'P']
                            )
                            results_offdesign.loc[idx, 'residual'] = (
                                self.nw.res[-1]
                                )

        if self.params['offdesign']['save_results']:
            resultpath = os.path.join(
                __file__, '..', 'output', f'{self.subdirname}_partload.csv'
                )
            results_offdesign.to_csv(resultpath, sep=';')

        self.df_to_array(results_offdesign)

    def calc_partload_char(self, **kwargs):
        """
        Interpolate data points of heat output and power input.

        Return functions to interpolate values heat output and
        power input based on the partload and the feed flow
        temperatures of the heat source and sink. If there is
        no data given through keyword arguments, the instances
        attributes will be searched for the necessary data.

        Parameters
        ----------
        kwargs : dict
            Necessary data is:
                Q_array : 3d array
                P_array : 3d array
                pl_range : 1d array
                T_hs_ff_range : 1d array
                T_cons_ff_range : 1d array
        """
        necessary_params = [
            'Q_array', 'P_array', 'pl_range', 'T_hs_ff_range',
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
            index=multiindex, columns=['Q', 'P', 'COP']
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
            char_ts.loc[i, :] = linear_model.loc[
                (temp_ts.loc[i, 'T_hs_ff'], temp_ts.loc[i, 'T_cons_ff']), :
                ]

        return char_ts

    def get_plotting_states(self, **kwargs):
        """Generate data of states to plot in state diagram."""
        data = {}
        data.update(
            {self.comps['cond'].label:
             self.comps['cond'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['mid_valve'].label:
             self.comps['mid_valve'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['econ'].label + ' (hot)':
                self.comps['econ'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['econ'].label + ' (cold)':
                self.comps['econ'].get_plotting_data()[2]}
        )
        data.update(
            {self.comps['evap_valve'].label:
             self.comps['evap_valve'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['evap'].label:
             self.comps['evap'].get_plotting_data()[2]}
        )
        data.update(
            {self.comps['comp1'].label:
             self.comps['comp1'].get_plotting_data()[1]}
        )
        data.update(
            {'Main gas stream': self.comps['merge'].get_plotting_data()[1]}
            )
        data.update(
            {'Parallel gas stream': self.comps['merge'].get_plotting_data()[2]}
            )
        data.update(
            {self.comps['comp2'].label:
             self.comps['comp2'].get_plotting_data()[1]}
        )

        for comp in data:
            if 'Compressor' in comp:
                data[comp]['starting_point_value'] *= 0.999999

        return data

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
