import os
from datetime import datetime
from time import time

import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI as PSI
from tespy.components import (Compressor, Condenser, CycleCloser,
                              DropletSeparator, HeatExchanger, Merge, Pump,
                              SimpleHeatExchanger, Sink, Source, Splitter,
                              Valve)
from tespy.connections import Bus, Connection, Ref
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

if __name__ == '__main__':
    from HeatPumpBase import HeatPumpBase
else:
    from .HeatPumpBase import HeatPumpBase


class HeatPumpIHXPCIHXTrans(HeatPumpBase):
    """Heat pump with open/closed economizer, parallel compression and ihx."""

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
        self.comps['cons'] = SimpleHeatExchanger('Consumer')

        # Main cycle
        self.comps['trans'] = HeatExchanger('Transcritical Heat Exchanger')
        self.comps['cc'] = CycleCloser('Main Cycle Closer')
        self.comps['mid_valve'] = Valve('Intermediate Valve')
        self.comps['evap_valve'] = Valve('Evaporation Valve')
        self.comps['evap'] = HeatExchanger('Evaporator')
        self.comps['ihx1'] = HeatExchanger('Internal Heat Exchanger 1')
        self.comps['ihx2'] = HeatExchanger('Internal Heat Exchanger 2')
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
            self.comps['trans'], 'out1', self.comps['cc'], 'in1', 'A0'
            )
        self.conns['A1'] = Connection(
            self.comps['cc'], 'out1', self.comps['ihx2'], 'in1', 'A1'
            )
        self.conns['A4'] = Connection(
            self.comps['econ'], 'out1', self.comps['ihx1'], 'in1', 'A4'
            )
        self.conns['A5'] = Connection(
            self.comps['ihx1'], 'out1', self.comps['evap_valve'], 'in1', 'A5'
            )
        self.conns['A6'] = Connection(
            self.comps['evap_valve'], 'out1', self.comps['evap'], 'in2', 'A6'
            )
        self.conns['A7'] = Connection(
            self.comps['evap'], 'out2', self.comps['ihx1'], 'in2', 'A7'
            )
        self.conns['A8'] = Connection(
            self.comps['ihx1'], 'out2', self.comps['comp1'], 'in1', 'A8'
            )
        self.conns['A9'] = Connection(
            self.comps['comp1'], 'out1', self.comps['merge'], 'in1', 'A9'
            )
        self.conns['A10'] = Connection(
            self.comps['merge'], 'out1', self.comps['trans'], 'in1', 'A10'
            )
        self.conns['A11'] = Connection(
            self.comps['econ'], 'out2', self.comps['ihx2'], 'in2', 'A11'
            )
        self.conns['A12'] = Connection(
            self.comps['ihx2'], 'out2', self.comps['comp2'], 'in1', 'A12'
            )
        self.conns['A13'] = Connection(
            self.comps['comp2'], 'out1', self.comps['merge'], 'in2', 'A13'
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
            self.comps['cons_pump'], 'out1', self.comps['trans'], 'in2', 'C2'
            )
        self.conns['C3'] = Connection(
            self.comps['trans'], 'out2', self.comps['cons'], 'in1', 'C3'
            )

        if self.econ_type.lower() == 'closed':
            self.conns['A2'] = Connection(
                self.comps['ihx2'], 'out1', self.comps['split'], 'in1', 'A2'
                )
            self.conns['A3'] = Connection(
                self.comps['split'], 'out1', self.comps['econ'], 'in1', 'A3'
                )
            self.conns['A14'] = Connection(
                self.comps['split'], 'out2',
                self.comps['mid_valve'], 'in1', 'A14'
                )
            self.conns['A15'] = Connection(
                self.comps['mid_valve'], 'out1',
                self.comps['econ'], 'in2', 'A15'
                )
        elif self.econ_type.lower() == 'open':
            self.conns['A2'] = Connection(
                self.comps['ihx2'], 'out1', self.comps['mid_valve'], 'in1', 'A2'
                )
            self.conns['A3'] = Connection(
                self.comps['mid_valve'], 'out1', self.comps['econ'], 'in1', 'A3'
                )

        self.nw.add_conns(*[conn for conn in self.conns.values()])

        # Buses
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
        self.buses['power input'] = Bus('power input')
        self.buses['power input'].add_comps(
            {'comp': self.comps['comp1'], 'char': mot, 'base': 'bus'},
            {'comp': self.comps['comp2'], 'char': mot, 'base': 'bus'},
            {'comp': self.comps['hs_pump'], 'char': mot, 'base': 'bus'},
            {'comp': self.comps['cons_pump'], 'char': mot, 'base': 'bus'}
            )

        self.buses['heat input'] = Bus('heat input')
        self.buses['heat input'].add_comps(
            {'comp': self.comps['hs_ff'], 'base': 'bus'},
            {'comp': self.comps['hs_bf'], 'base': 'component'}
            )

        self.buses['heat output'] = Bus('heat output')
        self.buses['heat output'].add_comps(
            {'comp': self.comps['cons'], 'base': 'component'}
            )

        self.nw.add_busses(*[bus for bus in self.buses.values()])

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
        self.comps['trans'].set_attr(
            pr1=self.params['trans']['pr1'], pr2=self.params['trans']['pr2']
            )
        self.comps['ihx1'].set_attr(
            pr1=self.params['ihx1']['pr1'], pr2=self.params['ihx2']['pr1']
            )
        self.comps['ihx2'].set_attr(
            pr1=self.params['ihx2']['pr1'], pr2=self.params['ihx2']['pr1']
            )
        self.comps['cons'].set_attr(
            pr=self.params['cons']['pr'], Q=self.params['cons']['Q'],
            dissipative=False
            )
        if self.econ_type.lower() == 'closed':
            self.comps['econ'].set_attr(
                pr1=self.params['econ']['pr1'], pr2=self.params['econ']['pr2']
                )

        # Connections
        # Starting values
        p_evap, h_trans_out, p_mid = self.get_pressure_levels()
        self.p_mid = p_mid
        self.p_evap = p_evap
        h_superheat1 = PSI(
            'H', 'P', p_evap*1e5,
            'T', (
                self.params['B2']['T'] - self.params['evap']['ttd_l'] + 273.15
                + self.params['ihx1']['dT_sh']),
            self.wf
            ) * 1e-3
        T_mid = PSI('T', 'Q', 1, 'P', p_mid*1e5, self.wf) - 273.15
        h_superheat2 = PSI(
            'H', 'P', p_mid*1e5,
            'T', (T_mid + 273.15 + self.params['ihx2']['dT_sh']),
            self.wf
            ) * 1e-3

        # Main cycle
        self.conns['A7'].set_attr(x=self.params['A7']['x'], p=p_evap)
        self.conns['A0'].set_attr(
            p=self.params['A0']['p'], h=h_trans_out, fluid={self.wf: 1}
            )
        self.conns['A8'].set_attr(h=h_superheat1)
        self.conns['A12'].set_attr(h=h_superheat2)
        self.conns['A11'].set_attr(p=p_mid)
        if self.econ_type.lower() == 'closed':
            self.conns['A11'].set_attr(x=1)
            self.conns['A3'].set_attr(
                m=Ref(self.conns['A0'], 0.9, 0)
                )

        # Heat source
        self.conns['B1'].set_attr(
            T=self.params['B1']['T'], p=self.params['B1']['p'],
            fluid={self.so: 1}
            )
        self.conns['B2'].set_attr(T=self.params['B2']['T'])
        self.conns['B3'].set_attr(p=self.params['B1']['p'])

        # Heat sink
        self.conns['C3'].set_attr(
            T=self.params['C3']['T'], p=self.params['C3']['p'],
            fluid={self.si: 1}
            )
        self.conns['C1'].set_attr(T=self.params['C1']['T'])

        # Perform initial simulation and unset starting values
        self._solve_model(**kwargs)

        if self.econ_type == 'closed':
            self.conns['A3'].set_attr(m=None)
        self.conns['A7'].set_attr(p=None)
        self.conns['A0'].set_attr(h=None)
        self.conns['A8'].set_attr(h=None)
        self.conns['A12'].set_attr(h=None)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.comps['evap'].set_attr(ttd_l=self.params['evap']['ttd_l'])
        self.comps['trans'].set_attr(ttd_l=self.params['trans']['ttd_l'])
        if self.econ_type == 'closed':
            self.comps['econ'].set_attr(ttd_l=self.params['econ']['ttd_l'])
        self.conns['A8'].set_attr(
            T=Ref(self.conns['A7'], 1, self.params['ihx1']['dT_sh'])
            )
        self.conns['A12'].set_attr(
            T=Ref(self.conns['A11'], 1, self.params['ihx2']['dT_sh'])
            )

        self._solve_model(**kwargs)

        self.m_design = self.conns['A0'].m.val

        self.cop = (
            abs(self.buses['heat output'].P.val)
            / self.buses['power input'].P.val
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

        self.comps['trans'].set_attr(
            kA_char1=kA_char1_cond, kA_char2=kA_char2_default,
            design=['pr2', 'ttd_u'], offdesign=['zeta2', 'kA_char']
            )

        self.comps['cons'].set_attr(design=['pr'], offdesign=['zeta'])

        self.comps['evap'].set_attr(
            kA_char1=kA_char1_default, kA_char2=kA_char2_evap,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char']
            )

        self.comps['ihx1'].set_attr(
            kA_char1=kA_char1_default, kA_char2=kA_char2_default,
            design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2']
            )

        self.comps['ihx2'].set_attr(
            kA_char1=kA_char1_default, kA_char2=kA_char2_default,
            design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2']
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
            index=multiindex, columns=['Q', 'P', 'COP', 'epsilon', 'residual']
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
                self.conns['A11'].set_attr(p=p_mid)

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
                        self.init_path = os.path.abspath(os.path.join(
                            os.path.dirname(__file__), 'stable',
                            f'{self.subdirname}_init'
                         ))

                    self.comps['cons'].set_attr(Q=None)
                    self.conns['A0'].set_attr(m=pl*self.m_design)

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
                                results_offdesign.loc[idx, 'eosilon'] = np.nan
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

    def get_pressure_levels(self, wf=None):
        """Calculate evaporation, condensation and middle pressure in bar."""
        if not wf:
            wf = self.wf
        p_evap = PSI(
            'P', 'Q', 1,
            'T', self.params['B2']['T'] - self.params['evap']['ttd_l'] + 273.15,
            wf
            ) * 1e-5
        h_trans_out = PSI(
            'H', 'P', self.params['A0']['p'] * 1e5,
            'T', self.params['C1']['T'] + self.params['trans']['ttd_l'] + 273.15,
            wf
        ) * 1e-3
        p_mid = np.sqrt(p_evap * self.params['A0']['p'])

        return p_evap, h_trans_out, p_mid

    def get_plotting_states(self, **kwargs):
        """Generate data of states to plot in state diagram."""
        data = {}
        data.update(
            {self.comps['trans'].label:
                self.comps['trans'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['ihx2'].label + ' (hot)':
                self.comps['ihx2'].get_plotting_data()[1]}
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
            {self.comps['ihx1'].label + ' (hot)':
                self.comps['ihx1'].get_plotting_data()[1]}
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
            {self.comps['ihx1'].label + ' (cold)':
                self.comps['ihx1'].get_plotting_data()[2]}
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
            {self.comps['ihx2'].label + ' (cold)':
                self.comps['ihx2'].get_plotting_data()[2]}
        )
        data.update(
            {self.comps['comp2'].label:
                self.comps['comp2'].get_plotting_data()[1]}
        )

        for comp in data:
            if 'Compressor' in comp:
                data[comp]['starting_point_value'] *= 0.999999

        return data

    def check_consistency(self):
        """Perform all necessary checks to protect consistency of parameters."""
        self.check_expansion_into_vapor_liquid_region(
            conn='A5', p=self.p_evap, wf=self.wf
        )
        if self.econ_type == 'open':
            self.check_expansion_into_vapor_liquid_region(
                conn='A2', p=self.p_mid, wf=self.wf
            )
        elif self.econ_type == 'closed':
            self.check_expansion_into_vapor_liquid_region(
                conn='A14', p=self.p_mid, wf=self.wf
            )

    def check_expansion_into_vapor_liquid_region(self, conn, p, wf):
        T = self.conns[conn].T.val

        T_sat = PSI('T', 'Q', 0, 'P', p * 1e5, wf) - 273.15
        if 'econ_type' in self.__dict__.keys():
            if self.econ_type == 'closed':
                T_sat = PSI(
                    'T', 'Q', 0, 'P', p * 1e5 / self.params['econ']['pr2'],
                    wf) - 273.15

        if T < T_sat:
            raise ValueError(
                f'The temperature of {T:.1f} °C at connection {conn} is lower '
                + f'than the saturation temperature {T_sat} °C at {p:2f} bar. '
                + 'Therefore, the vapor-liquid region can not be reached.'
            )
