import os
from datetime import datetime
from time import time

import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI as PSI
from tespy.components import (Compressor, CycleCloser, HeatExchanger, Motor,
                              PowerBus, PowerSource, Pump,
                              SimpleHeatExchanger, Sink, Source, Valve)
from tespy.connections import Connection, PowerConnection, Ref
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

if __name__ == '__main__':
    from HeatPumpBase import HeatPumpBase, LegacyBusAdapter
else:
    from .HeatPumpBase import HeatPumpBase, LegacyBusAdapter


class HeatPumpSimpleTrans(HeatPumpBase):
    """Basic heat pump cycle."""

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
        self.comps['valve'] = Valve('Valve')
        self.comps['evap'] = HeatExchanger('Evaporator')
        self.comps['comp'] = Compressor('Compressor')

        # Power input
        self.comps['grid'] = PowerSource('Grid')
        self.comps['power_distribution'] = PowerBus(
            'Power Distribution', num_in=1, num_out=3
            )
        self.comps['motor_comp'] = Motor('Compressor Motor')
        self.comps['motor_hs_pump'] = Motor('Heat Source Pump Motor')
        self.comps['motor_cons_pump'] = Motor('Consumer Pump Motor')

    def generate_connections(self):
        """Initialize and add connections and power connections to network."""
        # Connections
        self.conns['A0'] = Connection(
            self.comps['trans'], 'out1', self.comps['cc'], 'in1', 'A0'
            )
        self.conns['A1'] = Connection(
            self.comps['cc'], 'out1', self.comps['valve'], 'in1', 'A1'
            )
        self.conns['A2'] = Connection(
            self.comps['valve'], 'out1', self.comps['evap'], 'in2', 'A2'
            )
        self.conns['A3'] = Connection(
            self.comps['evap'], 'out2', self.comps['comp'], 'in1', 'A3'
            )
        self.conns['A4'] = Connection(
            self.comps['comp'], 'out1', self.comps['trans'], 'in1', 'A4'
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

        # Power input
        # Motor efficiency as function of partload, used for compressor and
        # recirculation pump drives alike.
        mot_x = np.array([
            0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
            0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15,
            1.2, 10
            ])
        # Normalized to 1 at x=1 (rated load): the design-point efficiency
        # (0.98, set below) is applied separately via Motor.eta, so this
        # curve must not also bake it in, or eta_char_func would apply it
        # twice during offdesign (eta_out = eta_in * eta.design * f(x)).
        mot_y = np.array([
            0.01, 0.3148, 0.5346, 0.6843, 0.7835, 0.8477, 0.8885, 0.9145,
            0.9318, 0.9443, 0.9546, 0.9638, 0.9724, 0.9806, 0.9878, 0.9938,
            0.9982, 1.0009, 1.002, 1.0015, 1, 0.9977, 0.9947, 0.9909, 0.9853,
            0.9644
            ])
        mot = CharLine(x=mot_x, y=mot_y)
        for motor in (
                self.comps['motor_comp'], self.comps['motor_hs_pump'],
                self.comps['motor_cons_pump']
                ):
            motor.set_attr(eta_char=mot)

        self.conns['E_grid'] = PowerConnection(
            self.comps['grid'], 'power',
            self.comps['power_distribution'], 'power_in1', 'E_grid'
            )
        self.conns['E_comp_in'] = PowerConnection(
            self.comps['power_distribution'], 'power_out1',
            self.comps['motor_comp'], 'power_in', 'E_comp_in'
            )
        self.conns['E_comp_out'] = PowerConnection(
            self.comps['motor_comp'], 'power_out',
            self.comps['comp'], 'power', 'E_comp_out'
            )
        self.conns['E_hs_pump_in'] = PowerConnection(
            self.comps['power_distribution'], 'power_out2',
            self.comps['motor_hs_pump'], 'power_in', 'E_hs_pump_in'
            )
        self.conns['E_hs_pump_out'] = PowerConnection(
            self.comps['motor_hs_pump'], 'power_out',
            self.comps['hs_pump'], 'power', 'E_hs_pump_out'
            )
        self.conns['E_cons_pump_in'] = PowerConnection(
            self.comps['power_distribution'], 'power_out3',
            self.comps['motor_cons_pump'], 'power_in', 'E_cons_pump_in'
            )
        self.conns['E_cons_pump_out'] = PowerConnection(
            self.comps['motor_cons_pump'], 'power_out',
            self.comps['cons_pump'], 'power', 'E_cons_pump_out'
            )

        self.nw.add_conns(*[conn for conn in self.conns.values()])

        # Aggregated energy stream accessors, replacing the removed tespy
        # ``Bus`` class. Kept under the ``buses`` dict name and ``.P.val``
        # access pattern so that ``HeatPumpBase`` does not need to know about
        # the specific topology of each model.
        self.buses['power input'] = LegacyBusAdapter(
            lambda: self.conns['E_grid'].E.val_SI
            )
        self.buses['heat input'] = LegacyBusAdapter(
            lambda: self.conns['B1'].m.val_SI * (
                self.conns['B1'].h.val_SI - self.conns['B3'].h.val_SI
                )
            )
        self.buses['heat output'] = LegacyBusAdapter(
            lambda: self.comps['cons'].Q.val_SI
            )

        # Connection labels bounding the system for the exergy analysis,
        # replacing the connections previously aggregated through Buses.
        self.exergy_boundary = {
            'fuel': {
                'inputs': ['E_grid', 'B1'], 'outputs': ['B3']
                },
            'product': {
                'inputs': ['C3'], 'outputs': ['C1']
                }
            }

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""
        # Components
        self.conns['A4'].set_attr(
            h=Ref(self.conns['A3'], self._init_vals['dh_rel_comp'], 0)
            )
        self.comps['hs_pump'].set_attr(eta_s=self.params['hs_pump']['eta_s'])
        self.comps['cons_pump'].set_attr(
            eta_s=self.params['cons_pump']['eta_s']
            )
        for motor in (
                self.comps['motor_comp'], self.comps['motor_hs_pump'],
                self.comps['motor_cons_pump']
                ):
            motor.set_attr(eta=0.98)

        self.comps['evap'].set_attr(
            pr1=self.params['evap']['pr1'], pr2=self.params['evap']['pr2']
            )
        self.comps['trans'].set_attr(
            pr1=self.params['trans']['pr1'], pr2=self.params['trans']['pr2']
            )
        self.comps['cons'].set_attr(
            pr=self.params['cons']['pr'], Q=self.params['cons']['Q'],
            dissipative=False
            )

        # Connections
        # Starting values
        p_evap, h_trans_out = self.get_pressure_levels()
        self.p_evap = p_evap

        # Main cycle
        self.conns['A3'].set_attr(x=self.params['A3']['x'], p=p_evap)
        self.conns['A0'].set_attr(
            p=self.params['A0']['p'], h=h_trans_out, fluid={self.wf: 1}
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

        self.conns['A3'].set_attr(p=None)
        self.conns['A0'].set_attr(h=None)
        self.conns['A4'].set_attr(h=None)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.comps['comp'].set_attr(eta_s=self.params['comp']['eta_s'])
        self.comps['evap'].set_attr(ttd_l=self.params['evap']['ttd_l'])
        self.comps['trans'].set_attr(ttd_l=self.params['trans']['ttd_l'])

        self._solve_model(**kwargs)

        self.m_design = self.conns['A0'].m.val

        self.cop = (
            abs(self.buses['heat output'].P.val)
            / self.buses['power input'].P.val
            )

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
            'T', self.params['C1']['T']+self.params['trans']['ttd_l'] + 273.15,
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
            {self.comps['valve'].label:
             self.comps['valve'].get_plotting_data()[1]}
        )
        data.update(
            {self.comps['evap'].label:
             self.comps['evap'].get_plotting_data()[2]}
        )
        data.update(
            {self.comps['comp'].label:
             self.comps['comp'].get_plotting_data()[1]}
        )

        for comp in data:
            if 'Compressor' in comp:
                data[comp]['starting_point_value'] *= 0.999999

        return data
