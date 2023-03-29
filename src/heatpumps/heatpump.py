# -*- coding: utf-8 -*-
"""
Generic heat pump model.

@author: Jonas Freißmann and Malte Fritz
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import SWSHplotting as shplt
import CoolProp.CoolProp as CP
from scipy.interpolate import interpn
from sklearn.linear_model import LinearRegression
from tespy.components import (
    CycleCloser, Source, Sink, Pump, HeatExchanger, Condenser,
    HeatExchangerSimple, Compressor, Valve
    )
from tespy.connections import Connection, Bus, Ref
from tespy.networks import Network
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc
from fluprodia import FluidPropertyDiagram


class Heatpump():
    """
    Generic heat pump model.

    Parameters
    ----------
    fluids : list
        list containing all fluids in the heat pump topology

    nr_cycles : int
        number of cycles/stages of the heat pump

    heatex_type : dict
        dictionary where each key is the integer index of the cycle and the
        value is the type of the heat exchanger, that is transfering heat out
        of the cycle. Valid types are 'Condenser' and 'HeatExchanger'.

    int_heatex : dict
        dictionary where each key is the integer index of the cycle of the hot
        side of an internal heat exchanger and the value is either a single
        integer for the cycle of the cold side or a list when multiple
        internal heat exchangers have the hot side of the cycle of the key

    intercooler : dict
        dictionary where each key is the integer index of the cycle in which
        the intercooler(s) are to be placed and where the corresponding value
        is a dictionary with the keys 'amount' (the number of compression
        stages is this number + 1) and 'type' (either 'HeatExchanger' or
        'HeatExchangerSimple')

    kwargs
        currently supported kwargs are the units used for displaying results
        with TESPy (T_unit, p_unit, h_unit and m_unit; see TESPy documentation)

    Note
    ----
    Both for the internal heat exchangers and the intercoolers an integer
    index is used to refer to a cycle/stage of a heatpump. This allows the
    distinct positioning of these components under the premiss that they are
    always placed in certain positions within their respective cycles. For
    intercoolers between compression stages this is trivial, but the internal
    heat exchangers place has to be predeterment for ease of use. From what
    could be gathered from literature these internal heat exchangers are
    used to cool the condensate and preheat the evaporated refrigerant most of
    the time, so this will be the implementation within the model.
    The nomenclature of integer indexes of cycles is also used in the
    labelling of the components.
    """

    def __init__(self, fluids, nr_cycles=1, heatex_type={1: 'Condenser'},
                 int_heatex={}, intercooler={}, **kwargs):
        self.fluids = fluids
        self.nr_cycles = nr_cycles
        self.heatex_type = heatex_type
        self.int_heatex = int_heatex
        self.intercooler = intercooler

        self.init_network(**kwargs)
        self.components = dict()
        self.generate_components()
        self.connections = dict()
        self.generate_topology()

    def init_network(self, **kwargs):
        """Initialize network."""
        if 'T_unit' in kwargs:
            T_unit = kwargs['T_unit']
        else:
            T_unit = 'C'
        if 'p_unit' in kwargs:
            p_unit = kwargs['p_unit']
        else:
            p_unit = 'bar'
        if 'h_unit' in kwargs:
            h_unit = kwargs['h_unit']
        else:
            h_unit = 'kJ / kg'
        if 'm_unit' in kwargs:
            m_unit = kwargs['m_unit']
        else:
            m_unit = 'kg / s'

        self.nw = Network(
            fluids=self.fluids, T_unit=T_unit, p_unit=p_unit, h_unit=h_unit,
            m_unit=m_unit
            )

    def generate_components(self):
        """Generate necessary components based on topology parametrisation."""
        # Heat Source Feed Flow
        self.components['Heat Source Feed Flow'] = Source(
            'Heat Source Feed Flow'
            )

        # Heat Source Back Flow
        self.components['Heat Source Back Flow'] = Sink(
            'Heat Source Back Flow'
            )

        # Heat Source Recirculation Pump
        self.components['Heat Source Recirculation Pump'] = Pump(
            'Heat Source Recirculation Pump'
            )

        # Heat Source evaporator
        self.components['Evaporator 1'] = HeatExchanger('Evaporator 1')

        # Consumer Cycle Closer
        self.components['Consumer Cycle Closer'] = CycleCloser(
            'Consumer Cycle Closer'
            )

        # Consumer Recirculation Pump
        self.components['Consumer Recirculation Pump'] = Pump(
            'Consumer Recirculation Pump'
            )

        # Consumer
        self.components['Consumer'] = HeatExchangerSimple('Consumer')

        for cycle in range(1, self.nr_cycles+1):
            # Cycle closer for each cycle
            self.components[f'Cycle Closer {cycle}'] = CycleCloser(
                f'Cycle Closer {cycle}'
                )

            # Valve for each cycle
            self.components[f'Valve {cycle}'] = Valve(f'Valve {cycle}')

            if self.heatex_type[cycle] == 'HeatExchanger':
                if cycle < self.nr_cycles:
                    self.components[f'Heat Exchanger {cycle}_{cycle+1}'] = (
                        HeatExchanger(f'Heat Exchanger {cycle}_{cycle+1}')
                        )
                else:
                    self.components[f'Heat Exchanger {cycle}'] = (
                        HeatExchanger(f'Heat Exchanger {cycle}')
                        )
            elif self.heatex_type[cycle] == 'Condenser':
                if cycle < self.nr_cycles:
                    self.components[f'Condenser {cycle}_{cycle+1}'] = (
                        Condenser(f'Condenser {cycle}_{cycle+1}')
                        )
                else:
                    self.components[f'Condenser {cycle}'] = (
                        Condenser(f'Condenser {cycle}')
                        )

            # Intercoolers where they are placed by user
            if cycle in self.intercooler.keys():
                nr_intercooler = self.intercooler[cycle]['amount']
                ic_type = self.intercooler[cycle]['type']
                for i in range(1, nr_intercooler+2):
                    if i < nr_intercooler+1:
                        if ic_type == 'HeatExchanger':
                            self.components[f'Intercooler {cycle}-{i}'] = (
                                HeatExchanger(f'Intercooler {cycle}-{i}')
                                )
                        elif ic_type == 'HeatExchangerSimple':
                            self.components[f'Intercooler {cycle}-{i}'] = (
                                HeatExchangerSimple(f'Intercooler {cycle}-{i}')
                                )

                    # Necessary amount of compressors due to intercoolers
                    self.components[f'Compressor {cycle}-{i}'] = Compressor(
                        f'Compressor {cycle}-{i}'
                        )
            else:
                # Single compressors for each cycle without intercooler
                self.components[f'Compressor {cycle}'] = Compressor(
                        f'Compressor {cycle}'
                        )

            if cycle in self.int_heatex.keys():
                if type(self.int_heatex[cycle]) == list:
                    for target_cycle in self.int_heatex[cycle]:
                        label = (
                            f'Internal Heat Exchanger {cycle}_{target_cycle}'
                            )
                        self.components[label] = HeatExchanger(label)
                else:
                    label = (
                        'Internal Heat Exchanger '
                        + f'{cycle}_{self.int_heatex[cycle]}'
                        )
                    self.components[label] = HeatExchanger(label)

    def generate_topology(self):
        """Generate the heat pump topology based on defined components."""
        self.set_conn(
            'valve1_to_evaporator1',
            'Valve 1', 'out1',
            'Evaporator 1', 'in2'
            )

        self.set_conn(
            f'heatsource_ff_to_heatsource_pump',
            'Heat Source Feed Flow', 'out1',
            'Heat Source Recirculation Pump', 'in1'
            )
        self.set_conn(
            'heatsource_pump_to_evaporator1',
            'Heat Source Recirculation Pump', 'out1',
            'Evaporator 1', 'in1'
            )
        self.set_conn(
            'evaporator1_to_heatsource_bf',
            'Evaporator 1', 'out1',
            'Heat Source Back Flow', 'in1'
            )

        self.set_conn(
            f'heatsink_cc_to_heatsink_pump',
            'Consumer Cycle Closer', 'out1',
            'Consumer Recirculation Pump', 'in1'
            )
        self.set_conn(
            'consumer_to_heatsink_cc',
            'Consumer', 'out1',
            'Consumer Cycle Closer', 'in1'
            )

        for cycle in range(1, self.nr_cycles+1):
            self.set_conn(
                f'cc{cycle}_to_valve{cycle}',
                f'Cycle Closer {cycle}', 'out1',
                f'Valve {cycle}', 'in1'
                )

            if self.heatex_type[cycle] == 'HeatExchanger':
                if cycle < self.nr_cycles:
                    self.set_conn(
                       f'valve{cycle+1}_to_heat_ex{cycle}_{cycle+1}',
                       f'Valve {cycle+1}', 'out1',
                       f'Heat Exchanger {cycle}_{cycle+1}', 'in2'
                       )
                else:
                    self.set_conn(
                        f'heatsink_pump_to_heatex{cycle}',
                        'Consumer Recirculation Pump', 'out1',
                        f'Heat Exchanger {cycle}', 'in2'
                        )
                    self.set_conn(
                        f'heatex{cycle}_to_consumer',
                        f'Heat Exchanger {cycle}', 'out2',
                        'Consumer', 'in1'
                        )
            elif self.heatex_type[cycle] == 'Condenser':
                if cycle < self.nr_cycles:
                    self.set_conn(
                       f'valve{cycle+1}_to_cond{cycle}_{cycle+1}',
                       f'Valve {cycle+1}', 'out1',
                       f'Condenser {cycle}_{cycle+1}', 'in2'
                       )
                else:
                    self.set_conn(
                        f'heatsink_pump_to_cond{cycle}',
                        'Consumer Recirculation Pump', 'out1',
                        f'Condenser {cycle}', 'in2'
                        )
                    self.set_conn(
                        f'cond{cycle}_to_consumer',
                        f'Condenser {cycle}', 'out2',
                        'Consumer', 'in1'
                        )

            cycle_int_heatex = list()
            for i in range(1, self.nr_cycles+1):
                if i in self.int_heatex:
                    if type(self.int_heatex[i]) == int:
                        if self.int_heatex[i] == cycle:
                            cycle_int_heatex.append(i)
                    elif type(self.int_heatex[i]) == list:
                        if cycle in self.int_heatex[i]:
                            cycle_int_heatex.append(i)

            last_int_heatex = ''
            for c_int_heatex in cycle_int_heatex:
                if not last_int_heatex:
                    if cycle == 1:
                        self.set_conn(
                            (f'evaporator{cycle}_to_'
                             + f'int_heatex{c_int_heatex}_{cycle}'),
                            f'Evaporator 1', 'out2',
                            f'Internal Heat Exchanger {c_int_heatex}_{cycle}',
                            'in2'
                            )
                    elif cycle <= self.nr_cycles:
                        if self.heatex_type[cycle-1] == 'HeatExchanger':
                            self.set_conn(
                                (f'heatex{cycle-1}_{cycle}_to_'
                                 + f'int_heatex{c_int_heatex}_{cycle}'),
                                f'Heat Exchanger {cycle-1}_{cycle}', 'out2',
                                ('Internal Heat Exchanger '
                                 + f'{c_int_heatex}_{cycle}'), 'in2'
                                )
                        elif self.heatex_type[cycle-1] == 'Condenser':
                            self.set_conn(
                                (f'cond{cycle-1}_{cycle}_to_'
                                 + f'int_heatex{c_int_heatex}_{cycle}'),
                                f'Condenser {cycle-1}_{cycle}', 'out2',
                                ('Internal Heat Exchanger '
                                 + f'{c_int_heatex}_{cycle}'), 'in2'
                                )
                else:
                    self.set_conn(
                        (f'int_heatex{last_int_heatex}_{cycle}'
                         + f'_to_int_heatex{c_int_heatex}_{cycle}'),
                        f'Internal Heat Exchanger {last_int_heatex}_{cycle}',
                        'out2',
                        f'Internal Heat Exchanger {c_int_heatex}_{cycle}',
                        'in2'
                        )
                last_int_heatex = c_int_heatex

            if cycle in self.intercooler:
                if not last_int_heatex:
                    if cycle == 1:
                        self.set_conn(
                            f'evaporator1_to_comp{cycle}-1',
                            f'Evaporator 1', 'out2',
                            f'Compressor {cycle}-1', 'in1'
                            )
                    elif cycle <= self.nr_cycles:
                        if self.heatex_type[cycle-1] == 'HeatExchanger':
                            self.set_conn(
                                f'heatex{cycle-1}_{cycle}_to_comp{cycle}',
                                f'Heat Exchanger {cycle-1}_{cycle}', 'out2',
                                f'Compressor {cycle}-1', 'in1'
                                )
                        elif self.heatex_type[cycle-1] == 'Condenser':
                            self.set_conn(
                                f'cond{cycle-1}_{cycle}_to_comp{cycle}',
                                f'Condenser {cycle-1}_{cycle}', 'out2',
                                f'Compressor {cycle}-1', 'in1'
                                )
                else:
                    self.set_conn(
                        f'int_heatex{last_int_heatex}_{cycle}_to_comp{cycle}',
                        f'Internal Heat Exchanger {last_int_heatex}_{cycle}',
                        'out2',
                        f'Compressor {cycle}-1', 'in1'
                        )
                for i in range(1, self.intercooler[cycle]['amount']+1):
                    self.set_conn(
                        f'comp{cycle}-{i}_to_intercooler{cycle}-{i}',
                        f'Compressor {cycle}-{i}', 'out1',
                        f'Intercooler {cycle}-{i}', 'in1'
                        )
                    self.set_conn(
                        f'intercooler{cycle}-{i}_to_comp{cycle}-{i+1}',
                        f'Intercooler {cycle}-{i}', 'out1',
                        f'Compressor {cycle}-{i+1}', 'in1'
                        )
                if cycle == self.nr_cycles:
                    if self.heatex_type[cycle] == 'HeatExchanger':
                        self.set_conn(
                            (f'comp{cycle}-'
                             + f'{self.intercooler[cycle]["amount"]+1}'
                             + f'_to_heatex{cycle}'),
                            (f'Compressor {cycle}'
                             + f'-{self.intercooler[cycle]["amount"]+1}'),
                            'out1',
                            f'Heat Exchanger {cycle}', 'in1'
                            )
                    elif self.heatex_type[cycle] == 'Condenser':
                        self.set_conn(
                            (f'comp{cycle}-'
                             + f'{self.intercooler[cycle]["amount"]+1}'
                             + f'_to_cond{cycle}'),
                            (f'Compressor {cycle}'
                             + f'-{self.intercooler[cycle]["amount"]+1}'),
                            'out1',
                            f'Condenser {cycle}', 'in1'
                            )
                else:
                    if self.heatex_type[cycle] == 'HeatExchanger':
                        self.set_conn(
                            (f'comp{cycle}-'
                             + f'{self.intercooler[cycle]["amount"]+1}'
                             + f'_to_heatex{cycle}_{cycle+1}'),
                            (f'Compressor {cycle}'
                             + f'-{self.intercooler[cycle]["amount"]+1}'),
                            'out1',
                            f'Heat Exchanger {cycle}_{cycle+1}', 'in1'
                            )
                    elif self.heatex_type[cycle] == 'Condenser':
                        self.set_conn(
                            (f'comp{cycle}-'
                             + f'{self.intercooler[cycle]["amount"]+1}'
                             + f'_to_cond{cycle}_{cycle+1}'),
                            (f'Compressor {cycle}'
                             + f'-{self.intercooler[cycle]["amount"]+1}'),
                            'out1',
                            f'Condenser {cycle}_{cycle+1}', 'in1'
                            )

            else:
                if not last_int_heatex:
                    if cycle == 1:
                        self.set_conn(
                            f'evaporator1_to_comp{cycle}',
                            f'Evaporator 1', 'out2',
                            f'Compressor {cycle}', 'in1'
                            )
                    else:
                        if self.heatex_type[cycle-1] == 'HeatExchanger':
                            self.set_conn(
                                f'heatex{cycle-1}_{cycle}_to_comp{cycle}',
                                f'Heat Exchanger {cycle-1}_{cycle}', 'out2',
                                f'Compressor {cycle}', 'in1'
                                )
                        elif self.heatex_type[cycle-1] == 'Condenser':
                            self.set_conn(
                                f'cond{cycle-1}_{cycle}_to_comp{cycle}',
                                f'Condenser {cycle-1}_{cycle}', 'out2',
                                f'Compressor {cycle}', 'in1'
                                )
                else:
                    self.set_conn(
                        f'int_heatex{last_int_heatex}_{cycle}_to_comp{cycle}',
                        f'Internal Heat Exchanger {last_int_heatex}_{cycle}',
                        'out2',
                        f'Compressor {cycle}', 'in1'
                        )
                if cycle == self.nr_cycles:
                    if self.heatex_type[cycle] == 'HeatExchanger':
                        self.set_conn(
                            f'comp{cycle}_to_heatex{cycle}',
                            f'Compressor {cycle}', 'out1',
                            f'Heat Exchanger {cycle}', 'in1'
                            )
                    elif self.heatex_type[cycle] == 'Condenser':
                        self.set_conn(
                            f'comp{cycle}_to_cond{cycle}',
                            f'Compressor {cycle}', 'out1',
                            f'Condenser {cycle}', 'in1'
                            )
                else:
                    if self.heatex_type[cycle] == 'HeatExchanger':
                        self.set_conn(
                            f'comp{cycle}_to_heatex{cycle}_{cycle+1}',
                            f'Compressor {cycle}', 'out1',
                            f'Heat Exchanger {cycle}_{cycle+1}', 'in1'
                            )
                    elif self.heatex_type[cycle] == 'Condenser':
                        self.set_conn(
                            f'comp{cycle}_to_cond{cycle}_{cycle+1}',
                            f'Compressor {cycle}', 'out1',
                            f'Condenser {cycle}_{cycle+1}', 'in1'
                            )

            int_heatexs = [
                comp for comp in self.components
                if f'Internal Heat Exchanger {cycle}' in comp
                ]
            int_heatexs.sort(reverse=True)
            last_int_heatex = ''
            for int_heatex in int_heatexs:
                int_heatex_idx = int_heatex.split(' ')[-1]
                if not last_int_heatex:
                    if cycle == self.nr_cycles:
                        if self.heatex_type[cycle] == 'HeatExchanger':
                            self.set_conn(
                                f'heatex{cycle}_to_int_heatex{int_heatex_idx}',
                                f'Heat Exchanger {cycle}', 'out1',
                                int_heatex, 'in1'
                                )
                        elif self.heatex_type[cycle] == 'Condenser':
                            self.set_conn(
                                f'cond{cycle}_to_int_heatex{int_heatex_idx}',
                                f'Condenser {cycle}', 'out1',
                                int_heatex, 'in1'
                                )
                    else:
                        if self.heatex_type[cycle] == 'HeatExchanger':
                            self.set_conn(
                                (f'heatex{cycle}_{cycle+1}'
                                 + f'_to_int_heatex{int_heatex_idx}'),
                                f'Heat Exchanger {cycle}_{cycle+1}', 'out1',
                                int_heatex, 'in1'
                                )
                        elif self.heatex_type[cycle] == 'Condenser':
                            self.set_conn(
                                (f'cond{cycle}_{cycle+1}'
                                 + f'_to_int_heatex{int_heatex_idx}'),
                                f'Condenser {cycle}_{cycle+1}', 'out1',
                                int_heatex, 'in1'
                                )
                else:
                    last_int_heatex_idx = last_int_heatex.split(' ')[-1]
                    self.set_conn(
                        (f'int_heatex{last_int_heatex_idx}'
                         + f'_to_int_heatex{int_heatex_idx}'),
                        last_int_heatex, 'out1',
                        int_heatex, 'in1'
                        )
                last_int_heatex = int_heatex

            if not last_int_heatex:
                if cycle == self.nr_cycles:
                    if self.heatex_type[cycle] == 'HeatExchanger':
                        self.set_conn(
                            f'heatex{cycle}_to_cc{cycle}',
                            f'Heat Exchanger {cycle}', 'out1',
                            f'Cycle Closer {cycle}', 'in1'
                            )
                    elif self.heatex_type[cycle] == 'Condenser':
                        self.set_conn(
                            f'cond{cycle}_to_cc{cycle}',
                            f'Condenser {cycle}', 'out1',
                            f'Cycle Closer {cycle}', 'in1'
                            )
                else:
                    if self.heatex_type[cycle] == 'HeatExchanger':
                        self.set_conn(
                            f'heatex{cycle}_{cycle+1}_to_cc{cycle}',
                            f'Heat Exchanger {cycle}_{cycle+1}', 'out1',
                            f'Cycle Closer {cycle}', 'in1'
                            )
                    elif self.heatex_type[cycle] == 'Condenser':
                        self.set_conn(
                            f'cond{cycle}_{cycle+1}_to_cc{cycle}',
                            f'Condenser {cycle}_{cycle+1}', 'out1',
                            f'Cycle Closer {cycle}', 'in1'
                            )
            else:
                last_int_heatex_idx = last_int_heatex.split(' ')[-1]
                self.set_conn(
                    f'int_heatex{last_int_heatex_idx}_to_cc{cycle}',
                    last_int_heatex, 'out1',
                    f'Cycle Closer {cycle}', 'in1'
                    )

    def set_conn(self, label, comp_out, outlet, comp_in, inlet):
        """
        Set connections between components.

        Parameters
        ----------
        label : str
            name of connection (also used as label attribute within the
            generated TESPy object)

        comp_out : tespy.components.component.Component
            component from which the connection originates

        outlet : str
            name of outlet of comp_out (e.g. 'out1')

        comp_in : tespy.components.component.Component
            component where the connection terminates

        inlet : str
            name of inlet of comp_in (e.g. 'in1')
        """
        self.connections[label] = Connection(
            self.components[comp_out], outlet,
            self.components[comp_in], inlet,
            label=label
            )
        self.nw.add_conns(self.connections[label])

    def delete_component(self, component):
        """
        Delete component and all associated connections from Heatpump.

        Parameters
        ----------
        component : str
            label of component to be deleted
        """
        if component not in self.components.keys():
            print(f'No component with label {component} found.')
            return

        del self.components[component]
        print(f'Component {component} succesfully deleted from Heatpump.')

        connections_copy = self.connections.copy()

        for label, connection in self.connections.items():
            is_source = component == connection.source.label
            is_target = component == connection.target.label
            if is_source or is_target:
                self.nw.del_conns(connection)
                del connections_copy[label]
                print(f'Connection {label} succesfully deleted from Heatpump.')

        self.connections = connections_copy

    def solve_design(self):
        """Perform simulation with 'design' mode."""
        self.nw.solve('design')
        self.nw.print_results()
        self.cop = abs(self.busses['heat'].P.val)/self.busses['power'].P.val
        print(f'COP = {self.cop:.4}')

    def offdesign_simulation(self, debug_log=False):
        """Calculate partload characteristic of heat pump."""
        if not self.solved_design:
            print(
                'Heat pump has not been designed via the "design_simulation" '
                + 'method. Therefore the offdesign simulation will fail.'
                )
            return

        self.T_hs_ff_range = np.linspace(
            self.param['offdesign']['T_hs_ff_start'],
            self.param['offdesign']['T_hs_ff_end'],
            self.param['offdesign']['T_hs_ff_steps'],
            endpoint=True
            )
        self.T_cons_ff_range = np.linspace(
            self.param['offdesign']['T_cons_ff_start'],
            self.param['offdesign']['T_cons_ff_end'],
            self.param['offdesign']['T_cons_ff_steps'],
            endpoint=True
            )
        self.pl_range = np.linspace(
            self.param['offdesign']['partload_min'],
            self.param['offdesign']['partload_max'],
            self.param['offdesign']['partload_steps'],
            endpoint=True
            )
        deltaT_hs = (
            self.param['design']['T_heatsource_ff']
            - self.param['design']['T_heatsource_bf']
            )

        self.Q_array = list()
        self.P_array = list()
        self.offdesign_results = dict()
        if debug_log:
            log_text = str()
        for T_hs_ff in self.T_hs_ff_range:
            Q_subarray = list()
            P_subarray = list()
            self.offdesign_results[T_hs_ff] = dict()
            self.connections['heatsource_ff_to_heatsource_pump'].set_attr(
                T=T_hs_ff
                )
            self.connections['evaporator1_to_heatsource_bf'].set_attr(
                T=T_hs_ff-deltaT_hs
                )
            for T_cons_ff in self.T_cons_ff_range:
                self.connections[self.conn_T_cons_ff].set_attr(T=T_cons_ff)
                Q_subsubarray = list()
                P_subsubarray = list()
                self.offdesign_results[T_hs_ff][T_cons_ff] = dict()
                for pl in self.pl_range[::-1]:
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
                        self.init_path = 'hp_init'
                    self.connections[self.conn_T_cons_ff].set_attr(T=T_cons_ff)
                    self.busses['heat'].set_attr(P=None)
                    self.connections[self.conn_massflow].set_attr(
                        m=pl * self.m_design
                        )

                    self.nw.solve(
                        'offdesign', design_path=self.design_path,
                        init_path=self.init_path
                        )

                    if pl == self.pl_range[-1] and self.nw.res[-1] < 1e-3:
                        self.nw.save('hp_init')

                    if debug_log:
                        if self.nw.res[-1] >= 1e-3:
                            log_text += (
                                f'T_hs_ff: {T_hs_ff:.2f} °C, T_cons_ff: '
                                + f'{T_cons_ff:.2f} °C, partload: '
                                + f'{pl*100:.2f} %\n'
                                + f'\tResidual: {self.nw.res[-1]:.2e}\n\n'
                                )

                    Q_subsubarray += [self.busses["heat"].P.val * 1e-6]
                    P_subsubarray += [self.busses["power"].P.val * 1e-6]
                    self.offdesign_results[T_hs_ff][T_cons_ff][pl] = {
                        'P': P_subsubarray[-1],
                        'Q': abs(Q_subsubarray[-1]),
                        'COP':  abs(Q_subsubarray[-1])/P_subsubarray[-1]
                        }
                Q_subarray += [Q_subsubarray[::-1]]
                P_subarray += [P_subsubarray[::-1]]
            self.Q_array += [Q_subarray]
            self.P_array += [P_subarray]
        if self.param['offdesign']['save_results']:
            with open(self.offdesign_path, 'w') as file:
                json.dump(self.offdesign_results, file, indent=4)
        if debug_log:
            with open('debug_log.txt', 'w') as file:
                if not log_text:
                    file.write('### All simulations converged. ###')
                else:
                    file.write(log_text)

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
                pl_rage : 1d array
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
                    print(
                        f'Necessary parameter {nec_param} not '
                        + 'in kwargs. The necessary parameters'
                        + f' are: {necessary_params}'
                        )
                    return
            Q_array = np.asarray(kwargs['Q_array'])
            P_array = np.asarray(kwargs['P_array'])
            pl_range = kwargs['pl_range']
            T_hs_ff_range = kwargs['T_hs_ff_range']
            T_cons_ff_range = kwargs['T_cons_ff_range']
        else:
            for nec_param in necessary_params:
                if nec_param not in self.__dict__:
                    print(
                        f'Necessary parameter {nec_param} can '
                        + 'not be found in the instances '
                        + 'attributes. Please make sure to '
                        + 'perform the offdesign_simulation '
                        + 'method or provide the necessary '
                        + 'parameters as kwargs. These are: '
                        + f'{necessary_params}'
                        )
                    return
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

    def plot_partload_char(self, partload_char, cmap_type='', output_path='',
                           return_fig_ax=False):
        """
        Plot the partload characteristic of the heat pump.

        Parameters
        ----------
        partload_char : pd.DataFrame
            DataFrame of the full partload characteristic containing 'Q', 'P'
            and 'COP' with a MultiIndex of the three variables 'T_hs_ff',
            'T_cons_ff' and 'pl'.

        cmap_type : str
            String of the possible colormap variations, which are 'T_cons_ff'
            and 'COP'.

        output_path : str
            String path to save the generated plots to. If omitted no plots
            will be saved.
        """
        if not cmap_type:
            print(
                'Please provide a cmap_type of eiher "T_cons_ff" or '
                + '"COP" to plot the heat pump partload characteristic.'
                )
            return

        shplt.init_params()

        cmap_colors = [
            shplt.znes_colors()['darkblue'], shplt.znes_colors()['lightblue'],
            shplt.znes_colors()['lightgrey'], shplt.znes_colors()['orange'],
            shplt.znes_colors()['red']
            ]

        cmap = shplt.get_perceptually_uniform_colormap(cmap_colors)

        if cmap_type == 'T_cons_ff':
            colors = cmap(
                np.linspace(
                    0, 1,
                    len(set(
                        partload_char.index.get_level_values('T_cons_ff'))
                        ))
                )
            T_hs_ff_range = set(
                partload_char.index.get_level_values('T_hs_ff')
                )
            figs = dict()
            axes = dict()
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
                    cmap=cmap, norm=plt.Normalize(
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

            if output_path:
                shplt.create_multipage_pdf(output_path)
            elif return_fig_ax:
                return figs, axes
            else:
                plt.show()

        if cmap_type == 'COP':
            T_hs_ff_range = set(
                partload_char.index.get_level_values('T_hs_ff')
                )
            figs = dict()
            axes = dict()
            for T_hs_ff in T_hs_ff_range:
                fig, ax = plt.subplots(figsize=(9.5, 6))

                scatterplot = ax.scatter(
                    partload_char.loc[(T_hs_ff), 'P'],
                    partload_char.loc[(T_hs_ff), 'Q'],
                    c=partload_char.loc[(T_hs_ff), 'COP'],
                    cmap=cmap,
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

            if output_path:
                shplt.create_multipage_pdf(output_path)
            elif return_fig_ax:
                return figs, axes
            else:
                plt.show()

    def linearize_partload_char(self, partload_char, line_type='offset',
                                regression_type='OLS'):
        """
        Linearize partload characteristic for usage in MILP problems.

        Parameters
        ----------
        partload_char : pd.DataFrame
            DataFrame of the full partload characteristic containing 'Q', 'P'
            and 'COP' with a MultiIndex of the three variables 'T_hs_ff',
            'T_cons_ff' and 'pl'.

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
        """
        cols = ['P_max', 'P_min']
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

        for T_hs_ff in T_hs_ff_range:
            for T_cons_ff in T_cons_ff_range:
                idx = (T_hs_ff, T_cons_ff)
                linear_model.loc[idx, 'P_max'] = (
                    partload_char.loc[idx, 'P'].max()
                    )
                linear_model.loc[idx, 'P_min'] = (
                    partload_char.loc[idx, 'P'].min()
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
                    regressor = partload_char.loc[idx, 'P'].to_numpy()
                    regressor = regressor.reshape(-1, 1)
                    response = partload_char.loc[idx, 'Q'].to_numpy()
                    if line_type == 'origin':
                        LinReg = LinearRegression(fit_intercept=False).fit(
                            regressor, response
                            )
                        linear_model.loc[idx, 'COP'] = LinReg.coef_[0]
                    elif line_type == 'offset':
                        LinReg = LinearRegression().fit(regressor, response)
                        linear_model.loc[idx, 'c_1'] = LinReg.coef_[0]
                        linear_model.loc[idx, 'c_0'] = LinReg.intercept_

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


class HeatpumpSingleStage(Heatpump):
    """
    Generic and stable single stage heat pump (opt. internal heat exchanger).

    Parameters
    ----------
    param : dict
        Dictionairy containing key parameters of the heat pump cycle
    """

    def __init__(self, param):
        self.param = param
        fluids = ['water', self.param['design']['refrigerant']]

        if not self.param['design']['int_heatex']:
            Heatpump.__init__(self, fluids, nr_cycles=1)
        else:
            Heatpump.__init__(self, fluids, nr_cycles=1, int_heatex={1: 1})

        self.parametrize_components()
        self.busses = dict()
        self.initialized = False
        self.solved_design = False
        self.offdesign_path = 'hp_ss_partload.json'

    def parametrize_components(self):
        """Parametrize components of single stage heat pump."""
        self.components['Consumer Recirculation Pump'].set_attr(
            eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Heat Source Recirculation Pump'].set_attr(
            eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Compressor 1'].set_attr(
            eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Condenser 1'].set_attr(
            pr1=0.98, pr2=0.98, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char']
                    )

        kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
        kA_char2 = ldc(
            'heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine
            )

        self.components['Evaporator 1'].set_attr(
            pr1=0.98, pr2=0.98, kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char']
            )

        self.components['Consumer'].set_attr(
            pr=0.98, design=['pr'], offdesign=['zeta']
            )

        if self.param['design']['int_heatex']:
            self.components['Internal Heat Exchanger 1_1'].set_attr(
                pr1=0.98, pr2=0.98,
                design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2']
                )

    def init_simulation(self):
        """Perform initial connection parametrization with starting values."""
        h_bottom_right = CP.PropsSI(
            'H', 'Q', 1,
            'T', self.param['design']['T_heatsource_bf'] - 2 + 273,
            self.param['design']['refrigerant']
            ) * 1e-3
        p_evap = CP.PropsSI(
            'P', 'Q', 1,
            'T', self.param['design']['T_heatsource_bf'] - 2 + 273,
            self.param['design']['refrigerant']
            ) * 1e-5

        h_top_left = CP.PropsSI(
            'H', 'Q', 0, 'T', self.param['design']['T_consumer_ff'] + 2 + 273,
            self.param['design']['refrigerant']
            ) * 1e-3
        p_cond = CP.PropsSI(
            'P', 'Q', 0, 'T', self.param['design']['T_consumer_ff'] + 2 + 273,
            self.param['design']['refrigerant']
            ) * 1e-5

        if not self.param['design']['int_heatex']:
            self.connections['evaporator1_to_comp1'].set_attr(x=1, p=p_evap)
            self.connections['cond1_to_cc1'].set_attr(
                p=p_cond,
                fluid={'water': 0, self.param['design']['refrigerant']: 1}
                )
        else:
            self.connections['evaporator1_to_int_heatex1_1'].set_attr(
                x=1, p=p_evap
                )
            self.connections['cond1_to_int_heatex1_1'].set_attr(
                p=p_cond,
                fluid={'water': 0, self.param['design']['refrigerant']: 1}
                )
            self.connections['int_heatex1_1_to_cc1'].set_attr(
                h=(h_top_left - (h_bottom_right - h_top_left) * 0.05)
                )

        self.connections['cond1_to_consumer'].set_attr(
            T=self.param['design']['T_consumer_ff'],
            p=self.param['design']['p_consumer_ff'],
            fluid={'water': 1, self.param['design']['refrigerant']: 0}
            )

        self.connections['consumer_to_heatsink_cc'].set_attr(
            T=self.param['design']['T_consumer_bf']
            )

        self.connections['heatsource_ff_to_heatsource_pump'].set_attr(
            T=self.param['design']['T_heatsource_ff'],
            p=self.param['design']['p_heatsource_ff'],
            fluid={'water': 1, self.param['design']['refrigerant']: 0},
            offdesign=['v']
            )

        self.connections['evaporator1_to_heatsource_bf'].set_attr(
            T=self.param['design']['T_heatsource_bf'],
            p=self.param['design']['p_heatsource_ff'],
            design=['T']
            )

        mot_x = np.array([
            0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
            0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15,
            1.2, 10
            ])
        mot_y = 1 / (np.array([
            0.01, 0.3148, 0.5346, 0.6843, 0.7835, 0.8477, 0.8885, 0.9145,
            0.9318, 0.9443, 0.9546, 0.9638, 0.9724, 0.9806, 0.9878, 0.9938,
            0.9982, 1.0009, 1.002, 1.0015, 1, 0.9977, 0.9947, 0.9909, 0.9853,
            0.9644
            ]) * 0.98)

        mot = CharLine(x=mot_x, y=mot_y)

        self.busses['power'] = Bus('total compressor power')
        self.busses['power'].add_comps(
            {'comp': self.components['Compressor 1'], 'char': mot},
            {'comp': self.components['Consumer Recirculation Pump'],
             'char': mot},
            {'comp': self.components['Heat Source Recirculation Pump'],
             'char': mot}
            )

        self.busses['heat'] = Bus('total delivered heat')
        self.busses['heat'].add_comps({'comp': self.components['Consumer']})

        self.nw.add_busses(self.busses['power'], self.busses['heat'])

        self.busses['heat'].set_attr(P=self.param['design']['Q_N'])

        self.solve_design()
        self.initialized = True

    def design_simulation(self):
        """Perform final connection parametrization with desired values."""
        if not self.initialized:
            print(
                'Heat pump has not been initialized via the "init_simulation" '
                + 'method. Therefore the design simulation probably will not '
                + 'converge.'
                )
            return

        self.solved_design = False

        if not self.param['design']['int_heatex']:
            self.connections['evaporator1_to_comp1'].set_attr(p=None)
            self.components['Evaporator 1'].set_attr(ttd_l=2)

            self.connections['cond1_to_cc1'].set_attr(p=None)
            self.components['Condenser 1'].set_attr(ttd_u=2)

        else:
            self.connections['evaporator1_to_int_heatex1_1'].set_attr(p=None)
            self.components['Evaporator 1'].set_attr(ttd_l=2)

            self.connections['cond1_to_int_heatex1_1'].set_attr(p=None)
            self.components['Condenser 1'].set_attr(ttd_u=2)

            self.connections['int_heatex1_1_to_cc1'].set_attr(h=None)
            self.connections['int_heatex1_1_to_comp1'].set_attr(
                T=Ref(
                    self.connections['evaporator1_to_int_heatex1_1'],
                    1, self.param['design']['deltaT_int_heatex']
                    )
                )

        self.m_design = self.connections['valve1_to_evaporator1'].m.val
        self.conn_massflow = 'valve1_to_evaporator1'
        self.conn_T_cons_ff = 'cond1_to_consumer'

        self.solve_design()
        self.design_path = 'hp_ss_design'
        self.nw.save(self.design_path)
        self.solved_design = True

    def generate_state_diagram(self, diagram_type='logph', xlims=list(),
                               ylims=list(), display_info=True,
                               return_diagram=False, save_file=True,
                               open_file=True):
        """
        Plot the heat pump cycle in a state diagram of chosen refrigerant.

        Parameters
        ----------
        diagram_type : str
            Type of state diagram. Valid options are 'logph' and 'Ts'.
        """
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

        # Get plotting data of each component
        if not self.param['design']['int_heatex']:
            results = {
                self.components['Valve 1'].label:
                    self.components['Valve 1'].get_plotting_data()[1],
                self.components['Evaporator 1'].label:
                    self.components['Evaporator 1'].get_plotting_data()[2],
                self.components['Compressor 1'].label:
                    self.components['Compressor 1'].get_plotting_data()[1],
                self.components['Condenser 1'].label:
                    self.components['Condenser 1'].get_plotting_data()[1]
                }
        else:
            label_int_heatex = 'Internal Heat Exchanger 1_1'

            results = {
                self.components['Internal Heat Exchanger 1_1'].label + ' hot':
                    self.components[label_int_heatex].get_plotting_data()[1],
                self.components['Valve 1'].label:
                    self.components['Valve 1'].get_plotting_data()[1],
                self.components['Evaporator 1'].label:
                    self.components['Evaporator 1'].get_plotting_data()[2],
                self.components['Internal Heat Exchanger 1_1'].label + ' cold':
                    self.components[label_int_heatex].get_plotting_data()[2],
                self.components['Compressor 1'].label:
                    self.components['Compressor 1'].get_plotting_data()[1],
                self.components['Condenser 1'].label:
                    self.components['Condenser 1'].get_plotting_data()[1]
                }

        # Set state diagram properties
        diagram = FluidPropertyDiagram(
            fluid=self.param['design']['refrigerant']
            )
        diagram.set_unit_system(T='°C', h='kJ/kg', p='bar')

        for key, data in results.items():
            results[key]['datapoints'] = diagram.calc_individual_isoline(
                **data
                )

        # Generate isolines
        with open('state_diagram_config.json', 'r') as file:
            config = json.load(file)

        if self.param['design']['refrigerant'] in config:
            state_props = config[self.param['design']['refrigerant']]
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

        # Set and possibly overwrite standard axes limits
        if not xlims:
            xlims = (
                state_props[var['x']]['min'], state_props[var['x']]['max']
                )
        if not ylims:
            ylims = (
                state_props[var['y']]['min'], state_props[var['y']]['max']
                )
        diagram.set_limits(
            x_min=xlims[0], x_max=xlims[1], y_min=ylims[0], y_max=ylims[1]
            )
        diagram.draw_isolines(diagram_type=diagram_type)

        for i, key in enumerate(results.keys()):
            datapoints = results[key]['datapoints']
            if key == 'Compressor 1':
                diagram.ax.plot(
                    datapoints[var['x']][1:], datapoints[var['y']][1:],
                    color='#EC6707'
                    )
                diagram.ax.scatter(
                    datapoints[var['x']][1], datapoints[var['y']][1],
                    color='#B54036',
                    label=f'$\\bf{i+1:.0f}$: {key}', s=100, alpha=0.5
                    )
                diagram.ax.annotate(
                    f'{i+1:.0f}',
                    (datapoints[var['x']][1], datapoints[var['y']][1]),
                    ha='center', va='center', color='w'
                    )
            else:
                diagram.ax.plot(
                    datapoints[var['x']], datapoints[var['y']],
                    color='#EC6707'
                    )
                diagram.ax.scatter(
                    datapoints[var['x']][0], datapoints[var['y']][0],
                    color='#B54036',
                    label=f'$\\bf{i+1:.0f}$: {key}', s=100, alpha=0.5
                    )
                diagram.ax.annotate(
                    f'{i+1:.0f}',
                    (datapoints[var['x']][0], datapoints[var['y']][0]),
                    ha='center', va='center', color='w'
                    )

        if display_info:
            # display info box containing key parameters
            if not self.param['design']['int_heatex']:
                infocoords = (0.01, 0.815)
            else:
                infocoords = (0.01, 0.79)

            info = (
                '$\\bf{{Wärmepumpe}}$\n'
                + f'Setup {self.param["design"]["setup"]}\n'
                + 'Betriebsdaten:\n'
                + f'\t $\\dot{{Q}}_N = '
                + f'${abs(self.param["design"]["Q_N"])*1e-6:.3} $MW$\n'
                + f'\t $COP = ${self.cop:.2f}\n'
                + 'Kältemittel:\n'
                + f'\t ${self.param["design"]["refrigerant"]}$\n'
                + 'Wärmequelle:\n'
                + f'\t $T_{{VL}} = ${self.param["design"]["T_heatsource_ff"]} '
                + '°C\n'
                + f'\t $T_{{RL}} = ${self.param["design"]["T_heatsource_bf"]} '
                + '°C\n'
                )

            if self.param['design']['int_heatex']:
                info += (
                    'Unterkühlung/Überhitzung:\n'
                    + f'\t $\\Delta T_{{IHX}} = $'
                    + f'{self.param["design"]["deltaT_int_heatex"]} °C\n'
                    )

            info += (
                'Wärmesenke:\n'
                + f'\t $T_{{VL}} = ${self.param["design"]["T_consumer_ff"]} '
                + '°C\n'
                + f'\t $T_{{RL}} = ${self.param["design"]["T_consumer_bf"]} °C'
                )

            diagram.ax.annotate(
                info, infocoords, xycoords='axes fraction',
                ha='left', va='center', color='k',
                bbox=dict(boxstyle='round,pad=0.3', fc='white')
                )

        # Additional plotting parameters
        diagram.ax.legend(loc='upper right')
        if diagram_type == 'logph':
            diagram.ax.set_xlabel('Spezifische Enthalpie in $kJ/kg$')
            diagram.ax.set_ylabel('Druck in $bar$')
        elif diagram_type == 'Ts':
            diagram.ax.set_xlabel('Spezifische Entropie in $kJ/(kg \\cdot K)$')
            diagram.ax.set_ylabel('Temperatur in $°C$')
        diagram.ax.set_xlim(xlims[0], xlims[1])
        diagram.ax.set_ylim(ylims[0], ylims[1])

        if save_file:
            if not self.param['design']['int_heatex']:
                filename = (
                    f'Diagramme\\Setup_{self.param["design"]["setup"]}\\'
                    + f'logph_{self.param["design"]["refrigerant"]}'
                    + f'_{self.param["design"]["T_heatsource_bf"]}'
                    + f'_{self.param["design"]["T_consumer_ff"]}.pdf'
                    )
            else:
                filename = (
                    f'Diagramme\\Setup_{self.param["design"]["setup"]}\\'
                    + f'logph_{self.param["design"]["refrigerant"]}'
                    + f'_{self.param["design"]["T_heatsource_bf"]}'
                    + f'_{self.param["design"]["T_consumer_ff"]}'
                    + f'_dT{self.param["design"]["deltaT_int_heatex"]}K.pdf'
                    )

            diagram.save(filename)
            if open_file:
                os.startfile(filename)

        if return_diagram:
            return diagram


# hübschen Namen für p_high ausdenken, der in die Parameter.json muss
class HeatpumpSingleStageTranscritical(Heatpump):
    """
    Generic and stable single stage heat pump with a transcritical fluid (opt.
    internal heat exchanger).

    Parameters
    ----------
    param : dict
        Dictionairy containing key parameters of the heat pump cycle
    """

    def __init__(self, param):
        self.param = param
        fluids = ['water', self.param['design']['refrigerant']]

        if not self.param['design']['int_heatex']:
            Heatpump.__init__(
                self, fluids, heatex_type={1: 'HeatExchanger'}, nr_cycles=1
                )
        else:
            Heatpump.__init__(
                self, fluids, nr_cycles=1, heatex_type={1: 'HeatExchanger'},
                int_heatex={1: 1}
                )

        self.parametrize_components()
        self.busses = dict()
        self.initialized = False
        self.solved_design = False
        self.offdesign_path = 'hp_ss_tc_partload.json'

    def parametrize_components(self):
        """Parametrize components of single stage heat pump."""
        self.components['Consumer Recirculation Pump'].set_attr(
            eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Heat Source Recirculation Pump'].set_attr(
            eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Compressor 1'].set_attr(
            eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char']
            )

        kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
        kA_char2 = ldc(
            'heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine
            )

        self.components['Evaporator 1'].set_attr(
            pr1=0.98, pr2=0.98, kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char']
            )

        kA_char2 = ldc('heat exchanger', 'kA_char2', 'DEFAULT', CharLine)

        self.components['Heat Exchanger 1'].set_attr(
            pr1=0.98, pr2=0.98, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char']
                    )

        self.components['Consumer'].set_attr(
            pr=0.98, design=['pr'], offdesign=['zeta']
            )

        if self.param['design']['int_heatex']:
            self.components['Internal Heat Exchanger 1_1'].set_attr(
                pr1=0.98, pr2=0.98,
                design=['pr1', 'pr2'], offdesign=['zeta1', 'zeta2']
                )

    def init_simulation(self):
        """Perform initial connection parametrization with starting values."""
        h_bottom_right = CP.PropsSI(
            'H', 'Q', 1,
            'T', self.param['design']['T_heatsource_bf'] - 2 + 273,
            self.param['design']['refrigerant']
            ) * 1e-3
        p_evap = CP.PropsSI(
            'P', 'Q', 1,
            'T', self.param['design']['T_heatsource_bf'] - 2 + 273,
            self.param['design']['refrigerant']
            ) * 1e-5

        h_top_left = CP.PropsSI(
            'H', 'P', self.param['design']['p_high'] * 1e5,
            'T', self.param['design']['T_consumer_ff'] + 2 + 273,
            self.param['design']['refrigerant']
            ) * 1e-3

        if not self.param['design']['int_heatex']:
            self.connections['evaporator1_to_comp1'].set_attr(x=1, p=p_evap)
            self.connections['heatex1_to_cc1'].set_attr(
                p=self.param['design']['p_high'], h=h_top_left,
                fluid={'water': 0, self.param['design']['refrigerant']: 1}
                )
        else:
            self.connections['evaporator1_to_int_heatex1_1'].set_attr(
                x=1, p=p_evap
                )
            self.connections['heatex1_to_int_heatex1_1'].set_attr(
                p=self.param['design']['p_high'], h=h_top_left,
                fluid={'water': 0, self.param['design']['refrigerant']: 1}
                )
            self.connections['int_heatex1_1_to_cc1'].set_attr(
                h=(h_top_left - (h_bottom_right - h_top_left) * 0.05)
                )

        self.connections['heatex1_to_consumer'].set_attr(
            T=self.param['design']['T_consumer_ff'],
            p=self.param['design']['p_consumer_ff'],
            fluid={'water': 1, self.param['design']['refrigerant']: 0}
            )

        self.connections['consumer_to_heatsink_cc'].set_attr(
            T=self.param['design']['T_consumer_bf']
            )

        self.connections['heatsource_ff_to_heatsource_pump'].set_attr(
            T=self.param['design']['T_heatsource_ff'],
            p=self.param['design']['p_heatsource_ff'],
            fluid={'water': 1, self.param['design']['refrigerant']: 0},
            offdesign=['v']
            )

        self.connections['evaporator1_to_heatsource_bf'].set_attr(
            T=self.param['design']['T_heatsource_bf'],
            p=self.param['design']['p_heatsource_ff'],
            design=['T']
            )

        mot_x = np.array([
            0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
            0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15,
            1.2, 10
            ])
        mot_y = 1 / (np.array([
            0.01, 0.3148, 0.5346, 0.6843, 0.7835, 0.8477, 0.8885, 0.9145,
            0.9318, 0.9443, 0.9546, 0.9638, 0.9724, 0.9806, 0.9878, 0.9938,
            0.9982, 1.0009, 1.002, 1.0015, 1, 0.9977, 0.9947, 0.9909, 0.9853,
            0.9644
            ]) * 0.98)

        mot = CharLine(x=mot_x, y=mot_y)

        self.busses['power'] = Bus('total compressor power')
        self.busses['power'].add_comps(
            {'comp': self.components['Compressor 1'], 'char': mot},
            {'comp': self.components['Consumer Recirculation Pump'],
             'char': mot},
            {'comp': self.components['Heat Source Recirculation Pump'],
             'char': mot}
            )

        self.busses['heat'] = Bus('total delivered heat')
        self.busses['heat'].add_comps({'comp': self.components['Consumer']})

        self.nw.add_busses(self.busses['power'], self.busses['heat'])

        self.busses['heat'].set_attr(P=self.param['design']['Q_N'])

        self.solve_design()
        self.initialized = True

    def design_simulation(self):
        """Perform final connection parametrization with desired values."""
        if not self.initialized:
            print(
                'Heat pump has not been initialized via the "init_simulation" '
                + 'method. Therefore the design simulation probably will not '
                + 'converge.'
                )
            return

        self.solved_design = False

        if not self.param['design']['int_heatex']:
            self.connections['evaporator1_to_comp1'].set_attr(p=None)
            self.components['Evaporator 1'].set_attr(ttd_l=2)

            self.connections['heatex1_to_cc1'].set_attr(h=None)
            self.components['Heat Exchanger 1'].set_attr(ttd_l=2)

        else:
            self.connections['evaporator1_to_int_heatex1_1'].set_attr(p=None)
            self.components['Evaporator 1'].set_attr(ttd_l=2)

            self.connections['heatex1_to_int_heatex1_1'].set_attr(h=None)
            self.components['Heat Exchanger 1'].set_attr(ttd_l=2)

            self.connections['int_heatex1_1_to_cc1'].set_attr(h=None)
            self.connections['int_heatex1_1_to_comp1'].set_attr(
                T=Ref(
                    self.connections['evaporator1_to_int_heatex1_1'],
                    1, self.param['design']['deltaT_int_heatex']
                    )
                )

        self.m_design = self.connections['valve1_to_evaporator1'].m.val
        self.conn_massflow = 'valve1_to_evaporator1'
        self.conn_T_cons_ff = 'cond1_to_consumer'

        self.solve_design()
        self.design_path = 'hp_ss_design'
        self.nw.save(self.design_path)
        self.solved_design = True

    def generate_state_diagram(self, diagram_type='logph', xlims=list(),
                               ylims=list(), display_info=True,
                               return_diagram=False, save_file=True,
                               open_file=True):
        """
        Plot the heat pump cycle in a state diagram of chosen refrigerant.

        Parameters
        ----------
        diagram_type : str
            Type of state diagram. Valid options are 'logph' and 'Ts'.
        """
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

        # Get plotting data of each component
        if not self.param['design']['int_heatex']:
            results = {
                self.components['Valve 1'].label:
                    self.components['Valve 1'].get_plotting_data()[1],
                self.components['Evaporator 1'].label:
                    self.components['Evaporator 1'].get_plotting_data()[2],
                self.components['Compressor 1'].label:
                    self.components['Compressor 1'].get_plotting_data()[1],
                self.components['Heat Exchanger 1'].label:
                    self.components['Heat Exchanger 1'].get_plotting_data()[1]
                }
        else:
            label_int_heatex = 'Internal Heat Exchanger 1_1'

            results = {
                self.components['Internal Heat Exchanger 1_1'].label + ' hot':
                    self.components[label_int_heatex].get_plotting_data()[1],
                self.components['Valve 1'].label:
                    self.components['Valve 1'].get_plotting_data()[1],
                self.components['Evaporator 1'].label:
                    self.components['Evaporator 1'].get_plotting_data()[2],
                self.components['Internal Heat Exchanger 1_1'].label + ' cold':
                    self.components[label_int_heatex].get_plotting_data()[2],
                self.components['Compressor 1'].label:
                    self.components['Compressor 1'].get_plotting_data()[1],
                self.components['Heat Exchanger 1'].label:
                    self.components['Heat Exchanger 1'].get_plotting_data()[1]
                }

        # Set state diagram properties
        diagram = FluidPropertyDiagram(
            fluid=self.param['design']['refrigerant']
            )
        diagram.set_unit_system(T='°C', h='kJ/kg', p='bar')

        for key, data in results.items():
            results[key]['datapoints'] = diagram.calc_individual_isoline(
                **data
                )

        # Generate isolines
        with open('state_diagram_config.json', 'r') as file:
            config = json.load(file)

        if self.param['design']['refrigerant'] in config:
            state_props = config[self.param['design']['refrigerant']]
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

        # Set and possibly overwrite standard axes limits
        if not xlims:
            xlims = (
                state_props[var['x']]['min'], state_props[var['x']]['max']
                )
        if not ylims:
            ylims = (
                state_props[var['y']]['min'], state_props[var['y']]['max']
                )
        diagram.set_limits(
            x_min=xlims[0], x_max=xlims[1], y_min=ylims[0], y_max=ylims[1]
            )
        diagram.draw_isolines(diagram_type=diagram_type)

        for i, key in enumerate(results.keys()):
            datapoints = results[key]['datapoints']
            if key == 'Compressor 1':
                diagram.ax.plot(
                    datapoints[var['x']][1:], datapoints[var['y']][1:],
                    color='#EC6707'
                    )
                diagram.ax.scatter(
                    datapoints[var['x']][1], datapoints[var['y']][1],
                    color='#B54036',
                    label=f'$\\bf{i+1:.0f}$: {key}', s=100, alpha=0.5
                    )
                diagram.ax.annotate(
                    f'{i+1:.0f}',
                    (datapoints[var['x']][1], datapoints[var['y']][1]),
                    ha='center', va='center', color='w'
                    )
            else:
                diagram.ax.plot(
                    datapoints[var['x']], datapoints[var['y']],
                    color='#EC6707'
                    )
                diagram.ax.scatter(
                    datapoints[var['x']][0], datapoints[var['y']][0],
                    color='#B54036',
                    label=f'$\\bf{i+1:.0f}$: {key}', s=100, alpha=0.5
                    )
                diagram.ax.annotate(
                    f'{i+1:.0f}',
                    (datapoints[var['x']][0], datapoints[var['y']][0]),
                    ha='center', va='center', color='w'
                    )

        if display_info:
            # display info box containing key parameters
            if not self.param['design']['int_heatex']:
                infocoords = (0.01, 0.815)
            else:
                infocoords = (0.01, 0.79)

            info = (
                '$\\bf{{Wärmepumpe}}$\n'
                + f'Setup {self.param["design"]["setup"]}\n'
                + 'Betriebsdaten:\n'
                + f'\t $\\dot{{Q}}_N = '
                + f'${abs(self.param["design"]["Q_N"])*1e-6:.3} $MW$\n'
                + f'\t $COP = ${self.cop:.2f}\n'
                + 'Kältemittel:\n'
                + f'\t ${self.param["design"]["refrigerant"]}$\n'
                + 'Wärmequelle:\n'
                + f'\t $T_{{VL}} = ${self.param["design"]["T_heatsource_ff"]} '
                + '°C\n'
                + f'\t $T_{{RL}} = ${self.param["design"]["T_heatsource_bf"]} '
                + '°C\n'
                )

            if self.param['design']['int_heatex']:
                info += (
                    'Unterkühlung/Überhitzung:\n'
                    + f'\t $\\Delta T_{{IHX}} = $'
                    + f'{self.param["design"]["deltaT_int_heatex"]} °C\n'
                    )

            info += (
                'Wärmesenke:\n'
                + f'\t $T_{{VL}} = ${self.param["design"]["T_consumer_ff"]} '
                + '°C\n'
                + f'\t $T_{{RL}} = ${self.param["design"]["T_consumer_bf"]} °C'
                )

            diagram.ax.annotate(
                info, infocoords, xycoords='axes fraction',
                ha='left', va='center', color='k',
                bbox=dict(boxstyle='round,pad=0.3', fc='white')
                )

        # Additional plotting parameters
        diagram.ax.legend(loc='upper right')
        if diagram_type == 'logph':
            diagram.ax.set_xlabel('Spezifische Enthalpie in $kJ/kg$')
            diagram.ax.set_ylabel('Druck in $bar$')
        elif diagram_type == 'Ts':
            diagram.ax.set_xlabel('Spezifische Entropie in $kJ/(kg \\cdot K)$')
            diagram.ax.set_ylabel('Temperatur in $°C$')
        diagram.ax.set_xlim(xlims[0], xlims[1])
        diagram.ax.set_ylim(ylims[0], ylims[1])

        if save_file:
            if not self.param['design']['int_heatex']:
                filename = (
                    f'Diagramme\\Setup_{self.param["design"]["setup"]}\\'
                    + f'logph_{self.param["design"]["refrigerant"]}'
                    + f'_{self.param["design"]["T_heatsource_bf"]}'
                    + f'_{self.param["design"]["T_consumer_ff"]}.pdf'
                    )
            else:
                filename = (
                    f'Diagramme\\Setup_{self.param["design"]["setup"]}\\'
                    + f'logph_{self.param["design"]["refrigerant"]}'
                    + f'_{self.param["design"]["T_heatsource_bf"]}'
                    + f'_{self.param["design"]["T_consumer_ff"]}'
                    + f'_dT{self.param["design"]["deltaT_int_heatex"]}K.pdf'
                    )

            diagram.save(filename)
            if open_file:
                os.startfile(filename)

        if return_diagram:
            return diagram


class HeatpumpDualStage(Heatpump):
    """
    Generic and stable dual stage heat pump (opt. internal heat exchanger).

    Parameters
    ----------
    param : dict
        Dictionairy containing key parameters of the heat pump cycles
    """

    def __init__(self, param):
        self.param = param
        fluids = [
            'water',
            self.param['design']['refrigerant1'],
            self.param['design']['refrigerant2']
            ]

        int_heatex1 = self.param['design']['int_heatex1']
        int_heatex2 = self.param['design']['int_heatex2']

        if not int_heatex1 and not int_heatex2:
            Heatpump.__init__(self, fluids, nr_cycles=2)
        elif int_heatex1 and not int_heatex2:
            Heatpump.__init__(self, fluids, nr_cycles=2, int_heatex={1: 1})
        elif not int_heatex1 and int_heatex2:
            Heatpump.__init__(self, fluids, nr_cycles=2, int_heatex={2: 2})
        elif int_heatex1 and int_heatex2:
            Heatpump.__init__(
                self, fluids, nr_cycles=2, int_heatex={1: 1, 2: 2}
                )

        self.parametrize_components()
        self.busses = dict()
        self.initialized = False
        self.solved_design = False
        self.offdesign_path = 'hp_ds_partload.json'

    def parametrize_components(self):
        """Parametrize components of dual stage heat pump."""
        self.delete_component('Heat Exchanger 1_2')
        self.components['Heat Exchanger 1_2'] = Condenser('Heat Exchanger 1_2')

        self.set_conn(
            'comp1_to_heatex1_2',
            'Compressor 1', 'out1',
            'Heat Exchanger 1_2', 'in1'
            )
        if not self.param['design']['int_heatex1']:
            self.set_conn(
                'heatex1_2_to_cc1',
                'Heat Exchanger 1_2', 'out1',
                'Cycle Closer 1', 'in1'
                )
        else:
            self.set_conn(
                'heatex1_2_to_int_heatex1_1',
                'Heat Exchanger 1_2', 'out1',
                'Internal Heat Exchanger 1_1', 'in1'
                )
        if not self.param['design']['int_heatex2']:
            self.set_conn(
                'heatex1_2_to_comp2',
                'Heat Exchanger 1_2', 'out2',
                'Compressor 2', 'in1'
                )
        else:
            self.set_conn(
                'heatex1_2_to_int_heatex2_2',
                'Heat Exchanger 1_2', 'out2',
                'Internal Heat Exchanger 2_2', 'in2'
                )
        self.set_conn(
            'valve2_to_heatex1_2',
            'Valve 2', 'out1',
            'Heat Exchanger 1_2', 'in2'
            )

        self.components['Consumer Recirculation Pump'].set_attr(
            eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Heat Source Recirculation Pump'].set_attr(
            eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Compressor 1'].set_attr(
            eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char']
            )

        self.components['Compressor 2'].set_attr(
            eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char']
            )

        kA_char1_default = ldc(
            'heat exchanger', 'kA_char1', 'DEFAULT', CharLine
            )
        kA_char1_cond = ldc(
            'heat exchanger', 'kA_char1', 'CONDENSING FLUID', CharLine
            )
        kA_char2_eva = ldc(
            'heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine
            )
        kA_char2_default = ldc(
            'heat exchanger', 'kA_char2', 'DEFAULT', CharLine
            )

        self.components['Evaporator 1'].set_attr(
            pr1=0.98, pr2=0.98,
            kA_char1=kA_char1_default, kA_char2=kA_char2_eva,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char']
            )

        self.components['Heat Exchanger 1_2'].set_attr(
            pr1=0.98, pr2=0.98,
            kA_char1=kA_char1_cond, kA_char2=kA_char2_eva,
            design=['pr1', 'ttd_u'], offdesign=['zeta1', 'kA_char']
            )

        self.components['Condenser 2'].set_attr(
            pr1=0.98, pr2=0.98,
            kA_char1=kA_char1_cond, kA_char2=kA_char2_default,
            design=['pr2', 'ttd_u'], offdesign=['zeta2', 'kA_char']
            )

        self.components['Consumer'].set_attr(
            pr=0.98, design=['pr'], offdesign=['zeta']
            )

        if self.param['design']['int_heatex1']:
            self.components['Internal Heat Exchanger 1_1'].set_attr(
                pr1=0.98, pr2=0.98,
                offdesign=['zeta1', 'zeta2']
                )

        if self.param['design']['int_heatex2']:
            self.components['Internal Heat Exchanger 2_2'].set_attr(
                pr1=0.98, pr2=0.98,
                offdesign=['zeta1', 'zeta2']
                )

    def init_simulation(self):
        """Perform initial connection parametrization with starting values."""
        # Low pressure cycle
        h_bottom_right1 = CP.PropsSI(
            'H', 'Q', 1,
            'T', self.param['design']['T_heatsource_bf'] - 2 + 273,
            self.param['design']['refrigerant1']
            ) * 1e-3
        p_evap1 = CP.PropsSI(
            'P', 'Q', 1,
            'T', self.param['design']['T_heatsource_bf'] - 2 + 273,
            self.param['design']['refrigerant1']
            ) * 1e-5

        h_top_left1 = CP.PropsSI(
            'H', 'Q', 0, 'T', self.param['design']['T_mid'] + 2 + 273,
            self.param['design']['refrigerant1']
            ) * 1e-3
        p_cond1 = CP.PropsSI(
            'P', 'Q', 0, 'T', self.param['design']['T_mid'] + 2 + 273,
            self.param['design']['refrigerant1']
            ) * 1e-5

        # High pressure cycle
        h_bottom_right2 = CP.PropsSI(
            'H', 'Q', 1, 'T', self.param['design']['T_mid'] - 2 + 273,
            self.param['design']['refrigerant2']
            ) * 1e-3
        p_evap2 = CP.PropsSI(
            'P', 'Q', 1, 'T', self.param['design']['T_mid'] - 2 + 273,
            self.param['design']['refrigerant2']
            ) * 1e-5

        h_top_left2 = CP.PropsSI(
            'H', 'Q', 0, 'T', self.param['design']['T_consumer_ff'] + 2 + 273,
            self.param['design']['refrigerant2']
            ) * 1e-3
        p_cond2 = CP.PropsSI(
            'P', 'Q', 0, 'T', self.param['design']['T_consumer_ff'] + 2 + 273,
            self.param['design']['refrigerant2']
            ) * 1e-5

        if not self.param['design']['int_heatex1']:
            self.connections['evaporator1_to_comp1'].set_attr(x=1, p=p_evap1)
            self.connections['heatex1_2_to_cc1'].set_attr(
                p=p_cond1, fluid={
                    'water': 0,
                    self.param['design']['refrigerant1']: 1,
                    self.param['design']['refrigerant2']: 0
                    }
                )
        else:
            self.connections['evaporator1_to_int_heatex1_1'].set_attr(
                x=1, p=p_evap1
                )
            self.connections['heatex1_2_to_int_heatex1_1'].set_attr(
                p=p_cond1, fluid={
                    'water': 0,
                    self.param['design']['refrigerant1']: 1,
                    self.param['design']['refrigerant2']: 0
                    }
                )
            self.connections['int_heatex1_1_to_cc1'].set_attr(
                h=(h_top_left1 - (h_bottom_right1 - h_top_left1) * 0.05)
                )
        if not self.param['design']['int_heatex2']:
            self.connections['heatex1_2_to_comp2'].set_attr(x=1, p=p_evap2)
            self.connections['cond2_to_cc2'].set_attr(
                p=p_cond2, fluid={
                    'water': 0,
                    self.param['design']['refrigerant1']: 0,
                    self.param['design']['refrigerant2']: 1
                    }
                )
        else:
            self.connections['heatex1_2_to_int_heatex2_2'].set_attr(
                x=1, p=p_evap2
                )
            self.connections['cond2_to_int_heatex2_2'].set_attr(
                p=p_cond2, fluid={
                    'water': 0,
                    self.param['design']['refrigerant1']: 0,
                    self.param['design']['refrigerant2']: 1
                    }
                )
            self.connections['int_heatex2_2_to_cc2'].set_attr(
                h=(h_top_left2 - (h_bottom_right2 - h_top_left2) * 0.05)
                )

        self.connections['cond2_to_consumer'].set_attr(
            T=self.param['design']['T_consumer_ff'],
            p=self.param['design']['p_consumer_ff'],
            fluid={
                'water': 1,
                self.param['design']['refrigerant1']: 0,
                self.param['design']['refrigerant2']: 0
                }
            )

        self.connections['consumer_to_heatsink_cc'].set_attr(
            T=self.param['design']['T_consumer_bf']
            )

        self.connections['heatsource_ff_to_heatsource_pump'].set_attr(
            T=self.param['design']['T_heatsource_ff'],
            p=self.param['design']['p_heatsource_ff'],
            fluid={
                'water': 1,
                self.param['design']['refrigerant1']: 0,
                self.param['design']['refrigerant2']: 0
                },
            offdesign=['v']
            )

        self.connections['evaporator1_to_heatsource_bf'].set_attr(
            T=self.param['design']['T_heatsource_bf'],
            p=self.param['design']['p_heatsource_ff'],
            design=['T']
            )

        mot_x = np.array([
            0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
            0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.15,
            1.2, 10
            ])
        mot_y = 1 / (np.array([
            0.01, 0.3148, 0.5346, 0.6843, 0.7835, 0.8477, 0.8885, 0.9145,
            0.9318, 0.9443, 0.9546, 0.9638, 0.9724, 0.9806, 0.9878, 0.9938,
            0.9982, 1.0009, 1.002, 1.0015, 1, 0.9977, 0.9947, 0.9909, 0.9853,
            0.9644
            ]) * 0.98)

        mot = CharLine(x=mot_x, y=mot_y)

        self.busses['power'] = Bus('total compressor power')
        self.busses['power'].add_comps(
            {'comp': self.components['Compressor 1'], 'char': mot},
            {'comp': self.components['Compressor 2'], 'char': mot},
            {'comp': self.components['Consumer Recirculation Pump'],
             'char': mot},
            {'comp': self.components['Heat Source Recirculation Pump'],
             'char': mot}
            )

        self.busses['heat'] = Bus('total delivered heat')
        self.busses['heat'].add_comps({'comp': self.components['Consumer']})

        self.nw.add_busses(self.busses['power'], self.busses['heat'])

        self.busses['heat'].set_attr(P=self.param['design']['Q_N'])

        self.solve_design()
        self.initialized = True

    def design_simulation(self):
        """Perform final connection parametrization with desired values."""
        if not self.initialized:
            print(
                'Heat pump has not been initialized via the "init_simulation" '
                + 'method. Therefore the design simulation probably will not '
                + 'converge.'
                )
            return

        self.solved_design = False

        if not self.param['design']['int_heatex1']:
            self.connections['evaporator1_to_comp1'].set_attr(p=None)
            self.connections['heatex1_2_to_cc1'].set_attr(
                p=None, T=self.param['design']['T_mid']
                )
        else:
            self.connections['evaporator1_to_int_heatex1_1'].set_attr(p=None)
            self.connections['heatex1_2_to_int_heatex1_1'].set_attr(
                p=None, T=self.param['design']['T_mid']
                )
            self.connections['int_heatex1_1_to_cc1'].set_attr(h=None)
            self.connections['int_heatex1_1_to_comp1'].set_attr(
                T=Ref(
                    self.connections['evaporator1_to_int_heatex1_1'],
                    1, self.param['design']['deltaT_int_heatex1']
                    )
                )

        self.components['Evaporator 1'].set_attr(ttd_l=2)
        self.components['Heat Exchanger 1_2'].set_attr(ttd_u=2)

        if not self.param['design']['int_heatex2']:
            self.connections['heatex1_2_to_comp2'].set_attr(p=None)
            self.connections['cond2_to_cc2'].set_attr(p=None)
        else:
            self.connections['heatex1_2_to_int_heatex2_2'].set_attr(p=None)
            self.connections['cond2_to_int_heatex2_2'].set_attr(p=None)
            self.connections['int_heatex2_2_to_cc2'].set_attr(h=None)
            self.connections['int_heatex2_2_to_comp2'].set_attr(
                T=Ref(
                    self.connections['heatex1_2_to_int_heatex2_2'],
                    1, self.param['design']['deltaT_int_heatex2']
                    )
                )

        self.components['Condenser 2'].set_attr(ttd_u=2)

        self.m_design = self.connections['cc2_to_valve2'].m.val
        self.conn_massflow = 'cc2_to_valve2'
        self.conn_T_cons_ff = 'cond2_to_consumer'

        self.solve_design()
        self.design_path = 'hp_ds_design'
        self.nw.save(self.design_path)
        self.solved_design = True

    def generate_logph(self, cycle, xlims=(100, 600), ylims=(1e0, 3e2),
                       display_info=True, return_diagram=False,
                       save_file=True, open_file=True):
        """Plot the heat pump cycle in logp-h-diagram of chosen refrigerant."""
        label_he = 'Heat Exchanger 1_2'
        if cycle == 1:
            if not self.param['design']['int_heatex1']:
                results = {
                    self.components['Valve 1'].label:
                        self.components['Valve 1'].get_plotting_data()[1],
                    self.components['Evaporator 1'].label:
                        self.components['Evaporator 1'].get_plotting_data()[2],
                    self.components['Compressor 1'].label:
                        self.components['Compressor 1'].get_plotting_data()[1],
                    self.components[label_he].label:
                        self.components[label_he].get_plotting_data()[1]
                    }
            else:
                label_ih = 'Internal Heat Exchanger 1_1'

                results = {
                    self.components[label_ih].label + ' hot':
                        self.components[label_ih].get_plotting_data()[1],
                    self.components['Valve 1'].label:
                        self.components['Valve 1'].get_plotting_data()[1],
                    self.components['Evaporator 1'].label:
                        self.components['Evaporator 1'].get_plotting_data()[2],
                    self.components[label_ih].label + ' cold':
                        self.components[label_ih].get_plotting_data()[2],
                    self.components['Compressor 1'].label:
                        self.components['Compressor 1'].get_plotting_data()[1],
                    self.components['Condenser 1'].label:
                        self.components['Condenser 1'].get_plotting_data()[1]
                    }
        elif cycle == 2:
            if not self.param['design']['int_heatex2']:
                results = {
                    self.components['Valve 2'].label:
                        self.components['Valve 2'].get_plotting_data()[1],
                    self.components[label_he].label:
                        self.components[label_he].get_plotting_data()[2],
                    self.components['Compressor 2'].label:
                        self.components['Compressor 2'].get_plotting_data()[1],
                    self.components['Condenser 2'].label:
                        self.components['Condenser 2'].get_plotting_data()[1]
                    }
            else:
                label_ih = 'Internal Heat Exchanger 2_2'

                results = {
                    self.components[label_ih].label + ' hot':
                        self.components[label_ih].get_plotting_data()[1],
                    self.components['Valve 2'].label:
                        self.components['Valve 2'].get_plotting_data()[1],
                    self.components[label_he].label:
                        self.components[label_he].get_plotting_data()[2],
                    self.components[label_ih].label + ' cold':
                        self.components[label_ih].get_plotting_data()[2],
                    self.components['Compressor 2'].label:
                        self.components['Compressor 2'].get_plotting_data()[1],
                    self.components['Condenser 2'].label:
                        self.components['Condenser 2'].get_plotting_data()[1]
                    }

        diagram = FluidPropertyDiagram(
            fluid=self.param['design'][f'refrigerant{cycle}']
            )
        diagram.set_unit_system(T='°C', h='kJ/kg', p='bar')

        for key, data in results.items():
            results[key]['datapoints'] = diagram.calc_individual_isoline(
                **data
                )

        isoT = np.arange(-100, 350, 25)
        isoS = np.arange(0, 10000, 500)

        ymin = 1e0
        ymax = 3e2

        if self.param['design'][f'refrigerant{cycle}'] == 'NH3':
            isoS = np.arange(0, 10000, 500)

            xmin = 250
            xmax = 2250

            infocoords = (0.9, 0.87)

        elif self.param['design'][f'refrigerant{cycle}'] == 'R1234ZE':
            isoS = np.arange(0, 2200, 50)

            xmin = 150
            xmax = 500

            infocoords = (0.9, 0.87)

        elif self.param['design'][f'refrigerant{cycle}'] == 'R134A':
            isoS = np.arange(0, 3000, 100)

            xmin = 100
            xmax = 600

            infocoords = (0.895, 0.8775)

        elif self.param['design'][f'refrigerant{cycle}'] == 'R245FA':
            isoS = np.arange(0, 4000, 100)

            xmin = 100
            xmax = 600
            ymin = 1e-1

            infocoords = (0.865, 0.86)

        elif self.param['design'][f'refrigerant{cycle}'] == 'R718':
            isoS = np.arange(0, 14000, 1000)
            isoT = np.arange(50, 750, 50)

            xmin = 100
            xmax = 4000
            ymin = 1e-2

            infocoords = (0.897, 0.85)

        else:
            isoS = np.arange(0, 4000, 500)

            xmin = 100
            xmax = 8000

            infocoords = (0.865, 0.86)

        # draw isolines
        diagram.set_isolines(T=isoT, s=isoS)
        diagram.calc_isolines()
        diagram.set_limits(
            x_min=xlims[0], x_max=xlims[1], y_min=ylims[0], y_max=ylims[1]
            )
        diagram.draw_isolines(diagram_type='logph')

        for i, key in enumerate(results.keys()):
            datapoints = results[key]['datapoints']
            if key == f'Compressor {cycle}':
                diagram.ax.plot(
                    datapoints['h'][1:], datapoints['p'][1:], color='#EC6707'
                    )
                diagram.ax.scatter(
                    datapoints['h'][1], datapoints['p'][1], color='#B54036',
                    label=f'$\\bf{i+1:.0f}$: {key}', s=100, alpha=0.5
                    )
                diagram.ax.annotate(
                    f'{i+1:.0f}', (datapoints['h'][1], datapoints['p'][1]),
                    ha='center', va='center', color='w'
                    )
            else:
                diagram.ax.plot(
                    datapoints['h'], datapoints['p'], color='#EC6707'
                    )
                diagram.ax.scatter(
                    datapoints['h'][0], datapoints['p'][0], color='#B54036',
                    label=f'$\\bf{i+1:.0f}$: {key}', s=100, alpha=0.5
                    )
                diagram.ax.annotate(
                    f'{i+1:.0f}', (datapoints['h'][0], datapoints['p'][0]),
                    ha='center', va='center', color='w'
                    )

        if display_info:
            # display info box containing key parameters
            info = (
                '$\\bf{{Wärmepumpe}}$\n'
                + f'Setup {self.param["design"]["setup"]}\n'
                + 'Betriebsdaten:\n'
                + f'\t $\\dot{{Q}}_N = '
                + f'${abs(self.param["design"]["Q_N"])*1e-6:.3} $MW$\n'
                + f'\t $COP = ${self.cop:.2f}\n'
                + 'Kältemittel:\n'
                + '\t $' + self.param['design'][f'refrigerant{cycle}'] + '$\n'
                + 'Wärmequelle:\n'
                + f'\t $T_{{VL}} = ${self.param["design"]["T_heatsource_ff"]} '
                + '°C\n'
                + f'\t $T_{{RL}} = ${self.param["design"]["T_heatsource_bf"]} '
                + '°C\n'
                + 'Mitteltemperatur:\n'
                + f'\t $T_{{mid}} = $' + str(self.param['design']['T_mid'])
                + '°C\n'
                )

            if self.param['design'][f'int_heatex{cycle}']:
                info += (
                    'Unterkühlung/Überhitzung:\n'
                    + '\t $\\Delta T_{{IHX}} = $'
                    + self.param['design'][f'deltaT_int_heatex{cycle}']
                    + ' °C\n'
                    )

            info += (
                'Wärmesenke:\n'
                + f'\t $T_{{VL}} = ${self.param["design"]["T_consumer_ff"]} '
                + '°C\n'
                + f'\t $T_{{RL}} = ${self.param["design"]["T_consumer_bf"]} °C'
                )

            diagram.ax.annotate(
                info, infocoords, xycoords='axes fraction',
                ha='left', va='center', color='k',
                bbox=dict(boxstyle='round,pad=0.3', fc='white')
                )

        diagram.ax.legend(loc='upper left')
        diagram.ax.set_xlim(xlims[0], xlims[1])
        diagram.ax.set_ylim(ylims[0], ylims[1])

        if save_file:
            if cycle == 1:
                temp_level = 'lowtemp'
            elif cycle == 2:
                temp_level = 'hightemp'

            if not self.param['design'][f'int_heatex{cycle}']:
                filename = (
                    f'Diagramme\\Setup_{self.param["design"]["setup"]}\\'
                    + 'logph_'
                    + self.param['design'][f'refrigerant{cycle}']
                    + f'_{self.param["design"]["T_heatsource_bf"]}'
                    + f'_{self.param["design"]["T_consumer_ff"]}_'
                    + f'{temp_level}.pdf'
                    )
            else:
                filename = (
                    f'Diagramme\\Setup_{self.param["design"]["setup"]}\\'
                    + f'logph_'
                    + self.param['design'][f'refrigerant{cycle}']
                    + f'_{self.param["design"]["T_heatsource_bf"]}'
                    + f'_{self.param["design"]["T_consumer_ff"]}_dT'
                    + self.param['design'][f'deltaT_int_heatex{cycle}']
                    + f'K_{temp_level}.pdf'
                    )

            diagram.save(filename)
            if open_file:
                os.startfile(filename)

        if return_diagram:
            return diagram


# %% Executable
if __name__ == '__main__':
    # hp = Heatpump(
    #     ['water', 'NH3'], nr_cycles=2, int_heatex={2: [1, 2]},
    #     intercooler={1: {'amount': 2, 'type': 'HeatExchanger'}}
    #     )
    # hp = Heatpump(
    #     ['water', 'NH3'], nr_cycles=2,
    #     heatex_type={1: 'HeatExchanger', 2: 'Condenser'}
    #     )

    import json
    with open('parameter.json', 'r') as file:
        param = json.load(file)

    hp = HeatpumpSingleStage(param)
    hp.init_simulation()
    hp.design_simulation()
    # hp.generate_logph()

    # with open('parameter_dual.json', 'r') as file:
    #     param = json.load(file)

    # hp = HeatpumpDualStage(param)
    # hp.init_simulation()
    # hp.design_simulation()
    # # hp.generate_logph(cycle=1)
    # hp.generate_logph(cycle=2)
