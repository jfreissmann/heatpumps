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


class HeatPumpIHXPCTrans(HeatPumpBase):
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
        self.comps['ihx'] = HeatExchanger('Internal Heat Exchanger')
        self.comps['mid_valve'] = Valve('Intermediate Valve')
        self.comps['evap_valve'] = Valve('Evaporation Valve')
        self.comps['evap'] = HeatExchanger('Evaporator')
        self.comps['comp1'] = Compressor('Compressor 1')
        self.comps['comp2'] = Compressor('Compressor 2')
        self.comps['merge'] = Merge('Economizer Injection')

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
            self.comps['cc'], 'out1', self.comps['ihx'], 'in1', 'A1'
            )
        self.conns['A4'] = Connection(
            self.comps['econ'], 'out1', self.comps['evap_valve'], 'in1', 'A4'
            )
        self.conns['A5'] = Connection(
            self.comps['evap_valve'], 'out1', self.comps['evap'], 'in2', 'A5'
            )
        self.conns['A6'] = Connection(
            self.comps['evap'], 'out2', self.comps['ihx'], 'in2', 'A6'
            )
        self.conns['A7'] = Connection(
            self.comps['ihx'], 'out2', self.comps['comp1'], 'in1', 'A7'
            )
        self.conns['A8'] = Connection(
            self.comps['comp1'], 'out1', self.comps['merge'], 'in1', 'A8'
            )
        self.conns['A9'] = Connection(
            self.comps['merge'], 'out1', self.comps['trans'], 'in1', 'A9'
            )
        self.conns['A10'] = Connection(
            self.comps['econ'], 'out2', self.comps['comp2'], 'in1', 'A10'
            )
        self.conns['A11'] = Connection(
            self.comps['comp2'], 'out1', self.comps['merge'], 'in2', 'A11'
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
                self.comps['ihx'], 'out1', self.comps['split'], 'in1', 'A2'
                )
            self.conns['A3'] = Connection(
                self.comps['split'], 'out1', self.comps['econ'], 'in1', 'A3'
                )
            self.conns['A12'] = Connection(
                self.comps['split'], 'out2',
                self.comps['mid_valve'], 'in1', 'A12'
                )
            self.conns['A13'] = Connection(
                self.comps['mid_valve'], 'out1',
                self.comps['econ'], 'in2', 'A13'
                )
        elif self.econ_type.lower() == 'open':
            self.conns['A2'] = Connection(
                self.comps['ihx'], 'out1', self.comps['mid_valve'], 'in1', 'A2'
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
        self.conns['A8'].set_attr(
            h=Ref(self.conns['A7'], self._init_vals['dh_rel_comp'], 0)
            )
        self.conns['A11'].set_attr(
            h=Ref(self.conns['A10'], self._init_vals['dh_rel_comp'], 0)
            )
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
        if self.econ_type.lower() == 'closed':
            self.comps['econ'].set_attr(
                pr1=self.params['econ']['pr1'], pr2=self.params['econ']['pr2']
                )

        # Connections
        # Starting values
        p_evap, h_trans_out, p_mid = self.get_pressure_levels(
            T_evap=self.params['B2']['T']
        )
        self.p_mid = p_mid
        self.p_evap = p_evap
        h_superheat = PSI(
            'H', 'P', p_evap*1e5,
            'T', (
                self.params['B2']['T'] - self.params['evap']['ttd_l'] + 273.15
                + self.params['ihx']['dT_sh']),
            self.wf
            ) * 1e-3

        # Main cycle
        self.conns['A6'].set_attr(x=self.params['A6']['x'], p=p_evap)
        self.conns['A0'].set_attr(
            p=self.params['A0']['p'], h=h_trans_out, fluid={self.wf: 1}
            )
        self.conns['A7'].set_attr(h=h_superheat)
        self.conns['A10'].set_attr(p=p_mid)
        if self.econ_type.lower() == 'closed':
            self.conns['A10'].set_attr(x=1)
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
        self.conns['A6'].set_attr(p=None)
        self.conns['A0'].set_attr(h=None)
        self.conns['A7'].set_attr(h=None)
        self.conns['A8'].set_attr(h=None)
        self.conns['A11'].set_attr(h=None)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.comps['comp1'].set_attr(eta_s=self.params['comp1']['eta_s'])
        self.comps['comp2'].set_attr(eta_s=self.params['comp2']['eta_s'])
        self.comps['evap'].set_attr(ttd_l=self.params['evap']['ttd_l'])
        self.comps['trans'].set_attr(ttd_l=self.params['trans']['ttd_l'])
        if self.econ_type == 'closed':
            self.comps['econ'].set_attr(ttd_l=self.params['econ']['ttd_l'])
        self.conns['A7'].set_attr(
            T=Ref(self.conns['A6'], 1, self.params['ihx']['dT_sh'])
            )

        self._solve_model(**kwargs)

        self.m_design = self.conns['A0'].m.val

        self.cop = (
            abs(self.buses['heat output'].P.val)
            / self.buses['power input'].P.val
            )

    def intermediate_states_offdesign(self, T_hs_ff, T_cons_ff, deltaT_hs):
        """Calculates intermediate states during part-load simulation"""
        _, _, p_mid = self.get_pressure_levels(
            T_evap=T_hs_ff
        )
        self.conns['A10'].set_attr(p=p_mid)

    def get_pressure_levels(self,T_evap, wf=None):
        """Calculate evaporation, condensation and middle pressure in bar."""
        if not wf:
            wf = self.wf
        p_evap = PSI(
            'P', 'Q', 1,
            'T', T_evap - self.params['evap']['ttd_l'] + 273.15,
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
            {self.comps['ihx'].label + ' (hot)':
                self.comps['ihx'].get_plotting_data()[1]}
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
            {self.comps['ihx'].label + ' (cold)':
                self.comps['ihx'].get_plotting_data()[2]}
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
