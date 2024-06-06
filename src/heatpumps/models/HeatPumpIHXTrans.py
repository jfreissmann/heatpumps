import os
from datetime import datetime
from time import time

import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI as PSI
from tespy.components import (Compressor, Condenser, CycleCloser,
                              HeatExchanger, HeatExchangerSimple, Pump, Sink,
                              Source, Valve)
from tespy.connections import Bus, Connection, Ref
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

if __name__ == '__main__':
    from HeatPumpBase import HeatPumpBase
else:
    from .HeatPumpBase import HeatPumpBase


class HeatPumpIHXTrans(HeatPumpBase):
    """Heat pump with internal heat exchanger between condesate and vapor."""

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
        self.comps['trans'] = HeatExchanger('Transcritical Heat Exchanger')
        self.comps['cc'] = CycleCloser('Main Cycle Closer')
        self.comps['ihx'] = HeatExchanger('Internal Heat Exchanger')
        self.comps['valve'] = Valve('Valve')
        self.comps['evap'] = HeatExchanger('Evaporator')
        self.comps['comp'] = Compressor('Compressor')

    def generate_connections(self):
        """Initialize and add connections and busses to network."""
        # Connections
        self.conns['A0'] = Connection(
            self.comps['trans'], 'out1', self.comps['cc'], 'in1', 'A0'
            )
        self.conns['A1'] = Connection(
            self.comps['cc'], 'out1', self.comps['ihx'], 'in1', 'A1'
            )
        self.conns['A2'] = Connection(
            self.comps['ihx'], 'out1', self.comps['valve'], 'in1', 'A2'
            )
        self.conns['A3'] = Connection(
            self.comps['valve'], 'out1', self.comps['evap'], 'in2', 'A3'
            )
        self.conns['A4'] = Connection(
            self.comps['evap'], 'out2', self.comps['ihx'], 'in2', 'A4'
            )
        self.conns['A5'] = Connection(
            self.comps['ihx'], 'out2', self.comps['comp'], 'in1', 'A5'
            )
        self.conns['A6'] = Connection(
            self.comps['comp'], 'out1', self.comps['trans'], 'in1', 'A6'
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
            {'comp': self.comps['comp'], 'char': mot, 'base': 'bus'},
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
        self.comps['comp'].set_attr(eta_s=self.params['comp']['eta_s'])
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
        self.comps['ihx'].set_attr(
            pr1=self.params['ihx']['pr1'], pr2=self.params['ihx']['pr1']
            )
        self.comps['cons'].set_attr(
            pr=self.params['cons']['pr'], Q=self.params['cons']['Q'],
            dissipative=False
            )

        # Connections
        # Starting values
        p_evap, h_trans_out = self.get_pressure_levels()
        self.p_evap = p_evap
        h_superheat = PSI(
            'H', 'P', p_evap*1e5,
            'T', (
                self.params['B2']['T'] - self.params['evap']['ttd_l'] + 273.15
                + self.params['ihx']['dT_sh']),
            self.wf
            ) * 1e-3

        # Main cycle
        self.conns['A4'].set_attr(x=self.params['A4']['x'], p=p_evap)
        self.conns['A0'].set_attr(p=self.params['A0']['p'], h=h_trans_out, fluid=self.fluid_vec_wf)
        self.conns['A5'].set_attr(h=h_superheat)
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

        self.conns['A4'].set_attr(p=None)
        self.conns['A0'].set_attr(h=None)
        self.conns['A5'].set_attr(h=None)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.comps['evap'].set_attr(ttd_l=self.params['evap']['ttd_l'])
        self.comps['trans'].set_attr(ttd_l=self.params['trans']['ttd_l'])
        self.conns['A5'].set_attr(
            T=Ref(self.conns['A4'], 1, self.params['ihx']['dT_sh'])
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
        self.comps['comp'].set_attr(
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

        self.comps['ihx'].set_attr(
            kA_char1=kA_char1_default, kA_char2=kA_char2_default,
            design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2']
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
                            or (self.nw.res[-1]
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
                                self.nw.res[-1]
                                )

        if self.params['offdesign']['save_results']:
            resultpath = os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'output',
                f'{self.subdirname}_partload.csv'
                ))
            results_offdesign.to_csv(resultpath, sep=';')

        self.df_to_array(results_offdesign)

    def get_pressure_levels(self, wf=None):
        """
        Calculate evaporation pressure in bar and heat sink outlet enthalpy
        (hot side).
        """
        if not wf:
            wf = self.wf
        p_evap = PSI(
            'P', 'Q', 1,
            'T', self.params['B2']['T']-self.params['evap']['ttd_l'] + 273.15,
            wf
            ) * 1e-5
        h_trans_out = PSI(
            'H', 'P', self.params['A0']['p']*1e5,
            'T', self.params['C0']['T']+self.params['trans']['ttd_l'] + 273.15,
            wf
            ) * 1e-3

        return p_evap, h_trans_out

    def get_plotting_states(self, **kwargs):
        """Generate data of states to plot in state diagram."""
        data = {}
        data.update(
            {self.comps['trans'].label:
             self.comps['trans'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['ihx'].label + ' (hot)':
             self.comps['ihx'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['valve'].label:
             self.comps['valve'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['evap'].label:
             self.comps['evap'].get_plotting_data()[2]}
        )
        data.update(
            {self.comps['ihx'].label + ' (cold)':
             self.comps['ihx'].get_plotting_data()[2]}
        )
        data.update(
            {self.comps['comp'].label:
             self.comps['comp'].get_plotting_data()[1]}
        )

        for comp in data:
            if 'Compressor' in comp:
                data[comp]['starting_point_value'] *= 0.999999

        return data

    # def simulation_condiion_check(self):
    #     """Checks the state after the expansion process,
    #     to avoid the position of the state after expansion outside the liquid vapor region"""
    #
    #     errors = []
    #     T_valve_in = self.conns['A2'].T.val # ihx outlet temperature
    #     T_sat_evap = PSI(
    #         'T', 'Q', 0, 'P', self.p_evap * 1e5,
    #         self.wf) - 273.15
    #
    #     if T_valve_in > T_sat_evap:
    #         pass
    #     else:
    #         errors.append(
    #             f'Error: Inlet temperature before the expansion {round(T_valve_in, 2)} °C '
    #             f'should be greater than the saturation temperature {round(T_sat_evap, 2)}°C '
    #             f'corresponding evaporator pressure.')
    #     if errors:
    #         return errors
    #     else:
    #         return 'Die Simulation der Wärmepumpenauslegung war erfolgreich.'

    def simulation_condiion_check(self):
        result = set()
        error = self.evap_state_condition_check(
            conn_valve_in='A2', p_evap=self.p_evap, wf=self.wf
        )
        result.update(error)

        if result:
            return result
        else:
            return f'Die Simulation der Wärmepumpenauslegung war erfolgreich.'