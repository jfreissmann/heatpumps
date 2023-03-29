# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 12:49:42 2022

@author: Jonas Freißmann
"""

from heatpump import HeatpumpSingleStage, HeatpumpDualStage


def run_design(param, nr_cycles):
    """Run TESPy design simulation of heat pump."""
    if nr_cycles == 1:
        hp = HeatpumpSingleStage(param)
    elif nr_cycles == 2:
        hp = HeatpumpDualStage(param)

    hp.init_simulation()
    hp.design_simulation()

    return hp


def run_partload(hp, param, save_results=False):
    """Run TESPy offdesign simulation of heat pump."""
    param['offdesign']['save_results'] = save_results
    hp.param = param
    hp.offdesign_simulation()
    partload_char = hp.calc_partload_char()

    if save_results:
        partload_char.to_csv('partload_char.csv', sep=';')

    return hp, partload_char
