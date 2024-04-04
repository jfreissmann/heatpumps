# -*- coding: utf-8 -*-
"""
Created on Thu Jun  2 12:49:42 2022

@author: Jonas Freißmann
"""
import variables as var


def run_design(hp_model_name, param):
    """Run TESPy design simulation of heat pump."""
    if 'econ' in hp_model_name:
        hp = var.hp_model_classes[hp_model_name](
            param, econ_type=var.hp_models[hp_model_name]['econ_type']
            )
    else:
        hp = var.hp_model_classes[hp_model_name](param)

    hp.run_model()

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
