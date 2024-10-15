import os
from datetime import datetime
from time import time

import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI as PSI
from tespy.components import (Compressor, Condenser, CycleCloser,
                              HeatExchanger, Pump, SimpleHeatExchanger, Sink,
                              Source, Valve)
from tespy.connections import Bus, Connection
from tespy.networks import Network
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

if __name__ == '__main__':
    from HeatPumpBase import HeatPumpBase
else:
    from .HeatPumpBase import HeatPumpBase
    from .HeatPumpBase import model_registry


@model_registry
class HeatPumpCascadeTrans(HeatPumpBase):
    """Two stage cascading heat pump with two refrigerants."""

    def __init__(self, params):
        """Initialize model and set necessary attributes."""
        self.params = params

        self.wf1 = self.params['fluids']['wf1']
        self.wf2 = self.params['fluids']['wf2']
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

        self.solved_design = False
        self.subdirname = (
            f"{self.params['setup']['type']}_"
            + f"{self.params['setup']['refrig1']}_"
            + f"{self.params['setup']['refrig2']}"
            )
        self.design_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'stable', f'{self.subdirname}_design'
            ))
        self.validate_dir()

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
        self.comps['cc1'] = CycleCloser('Main Cycle Closer 1')
        self.comps['cc2'] = CycleCloser('Main Cycle Closer 2')
        self.comps['valve1'] = Valve('Valve 1')
        self.comps['valve2'] = Valve('Valve 2')
        self.comps['inter'] = Condenser('Intermediate Heat Exchanger')
        self.comps['evap'] = HeatExchanger('Evaporator')
        self.comps['LT_comp'] = Compressor('Low Temperature Compressor')
        self.comps['HT_comp'] = Compressor('High Temperature Compressor')

    def generate_connections(self):
        """Initialize and add connections and busses to network."""
        # Connections
        self.conns['A0'] = Connection(
            self.comps['trans'], 'out1', self.comps['cc2'], 'in1', 'A0'
            )
        self.conns['A1'] = Connection(
            self.comps['cc2'], 'out1', self.comps['valve2'], 'in1', 'A1'
            )
        self.conns['A2'] = Connection(
            self.comps['valve2'], 'out1', self.comps['inter'], 'in2', 'A2'
            )
        self.conns['A3'] = Connection(
            self.comps['inter'], 'out2', self.comps['HT_comp'], 'in1', 'A3'
            )
        self.conns['A4'] = Connection(
            self.comps['HT_comp'], 'out1', self.comps['trans'], 'in1', 'A4'
            )

        self.conns['D0'] = Connection(
            self.comps['inter'], 'out1', self.comps['cc1'], 'in1', 'D0'
            )
        self.conns['D1'] = Connection(
            self.comps['cc1'], 'out1', self.comps['valve1'], 'in1', 'D1'
            )
        self.conns['D2'] = Connection(
            self.comps['valve1'], 'out1', self.comps['evap'], 'in2', 'D2'
            )
        self.conns['D3'] = Connection(
            self.comps['evap'], 'out2', self.comps['LT_comp'], 'in1', 'D3'
            )
        self.conns['D4'] = Connection(
            self.comps['LT_comp'], 'out1', self.comps['inter'], 'in1', 'D4'
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
            {'comp': self.comps['LT_comp'], 'char': mot, 'base': 'bus'},
            {'comp': self.comps['HT_comp'], 'char': mot, 'base': 'bus'},
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
        self.comps['LT_comp'].set_attr(eta_s=self.params['LT_comp']['eta_s'])
        self.comps['HT_comp'].set_attr(eta_s=self.params['HT_comp']['eta_s'])
        self.comps['hs_pump'].set_attr(eta_s=self.params['hs_pump']['eta_s'])
        self.comps['cons_pump'].set_attr(
            eta_s=self.params['cons_pump']['eta_s']
            )

        self.comps['evap'].set_attr(
            pr1=self.params['evap']['pr1'], pr2=self.params['evap']['pr2']
            )
        self.comps['inter'].set_attr(
            pr1=self.params['inter']['pr1'], pr2=self.params['inter']['pr2']
            )
        self.comps['trans'].set_attr(
            pr1=self.params['trans']['pr1'], pr2=self.params['trans']['pr2']
            )
        self.comps['cons'].set_attr(
            pr=self.params['cons']['pr'], Q=self.params['cons']['Q'],
            dissipative=False
            )

        # Connections
        self.T_mid = (self.params['B2']['T'] + self.params['C1']['T']) / 2

        # Starting values
        p_evap1, p_cond1, p_evap2, h_trans_out = self.get_pressure_levels(
            T_mid=self.T_mid
            )
        self.p_evap2 = p_evap2
        self.p_evap1 = p_evap1

        # Main cycle
        self.conns['A3'].set_attr(x=self.params['A3']['x'], p=p_evap2)
        self.conns['A0'].set_attr(
            p=self.params['A0']['p'], h=h_trans_out, fluid={self.wf2: 1}
            )
        self.conns['D3'].set_attr(x=self.params['D3']['x'], p=p_evap1)
        self.conns['D0'].set_attr(p=p_cond1, fluid={self.wf1: 1})
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

        self.conns['A0'].set_attr(h=None)
        self.conns['A3'].set_attr(p=None)
        self.conns['D0'].set_attr(p=None)
        self.conns['D3'].set_attr(p=None)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.comps['evap'].set_attr(ttd_l=self.params['evap']['ttd_l'])
        self.comps['trans'].set_attr(ttd_l=self.params['trans']['ttd_l'])
        self.comps['inter'].set_attr(ttd_u=self.params['inter']['ttd_u'])
        self.conns['A3'].set_attr(T=self.T_mid-self.params['inter']['ttd_u']/2)

        self._solve_model(**kwargs)

        self.m_design = self.conns['A0'].m.val

        self.cop = (
            abs(self.buses['heat output'].P.val)
            / self.buses['power input'].P.val
            )

    def intermediate_states_offdesign(self, T_hs_ff, T_cons_ff, deltaT_hs):
        """Calculates intermediate states during part-load simulation"""
        self.T_mid = ((T_hs_ff - deltaT_hs) + T_cons_ff) / 4
        self.conns['A3'].set_attr(
            T=self.T_mid - self.params['inter']['ttd_u'] / 2
        )

    def get_pressure_levels(self, T_mid):
        """Calculate evaporation and condensation pressure for both cycles."""
        p_evap1 = PSI(
            'P', 'Q', 1,
            'T', self.params['B2']['T']-self.params['evap']['ttd_l'] + 273.15,
            self.wf1
            ) * 1e-5
        p_cond1 = PSI(
            'P', 'Q', 0,
            'T', T_mid + self.params['inter']['ttd_u']/2 + 273.15,
            self.wf1
            ) * 1e-5
        p_evap2 = PSI(
            'P', 'Q', 1,
            'T', T_mid - self.params['inter']['ttd_u']/2 + 273.15,
            self.wf2
            ) * 1e-5
        h_trans_out = PSI(
            'H', 'P', self.params['A0']['p']*1e5,
            'T', self.params['C1']['T']+self.params['trans']['ttd_l'] + 273.15,
            self.wf2
            ) * 1e-3

        return p_evap1, p_cond1, p_evap2, h_trans_out

    def get_plotting_states(self, **kwargs):
        """Generate data of states to plot in state diagram."""
        data = {}
        if kwargs['cycle'] == 1:
            data.update(
                {self.comps['inter'].label:
                self.comps['inter'].get_plotting_data()[1]}
            )
            data.update(
                {self.comps['valve1'].label:
                self.comps['valve1'].get_plotting_data()[1]}
            )
            data.update(
                {self.comps['evap'].label:
                self.comps['evap'].get_plotting_data()[2]}
            )
            data.update(
                {self.comps['LT_comp'].label:
                self.comps['LT_comp'].get_plotting_data()[1]}
            )
        elif kwargs['cycle'] == 2:
            data.update(
                {self.comps['trans'].label:
                self.comps['trans'].get_plotting_data()[1]}
            )
            data.update(
                {self.comps['valve2'].label:
                self.comps['valve2'].get_plotting_data()[1]}
            )
            data.update(
                {self.comps['inter'].label:
                self.comps['inter'].get_plotting_data()[2]}
            )
            data.update(
                {self.comps['HT_comp'].label:
                self.comps['HT_comp'].get_plotting_data()[1]}
            )
        else:
            raise ValueError(
                f'Cycle {kwargs["cycle"]} not defined for heat pump '
                + f"'{self.params['setup']['type']}'."
                )

        for comp in data:
            if 'Compressor' in comp:
                data[comp]['starting_point_value'] *= 0.999999

        return data

    def generate_state_diagram(self, refrig='', diagram_type='logph',
                               style='light', figsize=(16, 10),
                               legend=True, legend_loc='upper left',
                               return_diagram=False, savefig=True,
                               open_file=True, **kwargs):
        kwargs1 = {}
        kwargs2 = {}
        if 'xlims' in kwargs:
            kwargs1['xlims'] = kwargs['xlims'][0]
            kwargs2['xlims'] = kwargs['xlims'][1]
        if 'ylims' in kwargs:
            kwargs1['ylims'] = kwargs['ylims'][0]
            kwargs2['ylims'] = kwargs['ylims'][1]
        if return_diagram:
            diagram1 = super().generate_state_diagram(
                refrig=self.params['setup']['refrig1'],
                style=style, figsize=figsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=1, **kwargs1
            )
            diagram2 = super().generate_state_diagram(
                refrig=self.params['setup']['refrig2'],
                style=style, figsize=figsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=2, **kwargs2
            )
            return diagram1, diagram2
        else:
            super().generate_state_diagram(
                refrig=self.params['setup']['refrig1'],
                style=style, figsize=figsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=1, **kwargs1
            )
            super().generate_state_diagram(
                refrig=self.params['setup']['refrig2'],
                style=style, figsize=figsize,
                diagram_type=diagram_type, legend=legend,
                legend_loc=legend_loc,
                return_diagram=return_diagram, savefig=savefig,
                open_file=open_file, cycle=2, **kwargs2
            )

    def check_consistency(self):
        """Perform all necessary checks to protect consistency of parameters."""
        self.check_expansion_into_vapor_liquid_region(
            conn='A0', p=self.p_evap2, wf=self.wf2
        )
        self.check_expansion_into_vapor_liquid_region(
            conn='D0', p=self.p_evap1, wf=self.wf1
        )
        self.check_mid_pressure(p_mid=self.p_evap2, wf=self.wf2)
        self.check_mid_temperature(wf=self.wf1)

    def check_mid_pressure(self, p_mid, wf):
        """Check if the intermediate pressure is below the critical pressure."""
        p_crit = PSI('p_critical', wf) * 1e-5
        if p_mid > p_crit:
            raise ValueError(
                f'Intermediate pressure of {p_mid:2f} bar must be below the '
                + f'critical pressure of {wf} of {p_crit:.2f} bar'
                )

    def check_mid_temperature(self, wf):
        """Check if the intermediate pressure is below the critical pressure."""
        T_crit = PSI('T_critical', wf) - 273.15
        if self.T_mid > T_crit:
            raise ValueError(
                f'Intermediate temperature of {self.T_mid:1f} °C must be below '
                + f'the  critical temperature of {wf} of {T_crit:.1f} °C'
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
