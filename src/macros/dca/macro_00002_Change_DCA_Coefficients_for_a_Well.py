'''
Name for generated for macro: (DCA) Change DCA Coefficients for a well

Commands Description for Macro: 
Creates Forecast Template
Generate plots with the results

@author: Vinicius Girardi
'''

from __future__ import unicode_literals
from dcacore.dcaui import show_curve_coeffs_dialog
from dcacore.forecaster import Forecaster
from dcacore.CrossCurveManipulations import CrossApiUtils
from coilib50.path.path_mapper import PathMapper
from plugins10.plugins.selection.selectionplugins import EPSelectionService
from plugins10.core.pluginmanager import PluginManager
from plugins10.plugins.uiapplication.model_eps import EPModel
import json
import os
from collections import namedtuple

path_mapper = PathMapper.GetSingleton()
config_filename = os.path.join(path_mapper['/scripts_output'], "last_dca.txt")

selection_service = PluginManager.GetSingleton(EPSelectionService)
selected_object = selection_service.GetSelection()
pool = PluginManager.GetSingleton(EPModel)
input_reader = pool[selected_object[0]]

DCAParameters = namedtuple("DCAParameters",
                           ["study_names",
                            "well_list",
                            "exp_dict",
                            "wc_exp_dict",
                            "wor_exp_dict",
                            "coefficients_file",
                            "variables"
                            ])

with open(config_filename) as path_to_last:
    path = json.load(path_to_last)

coeff_file = os.path.join(path,'Coeffs_file.txt')

with open(coeff_file) as out_file:
    variables = json.load(out_file)

study_aux = api.GetStudy(variables[0])
params = DCAParameters(
   study_names = api.GetStudyNames(),
   well_list = variables[1][:],
   exp_dict = variables[2],
   wc_exp_dict = variables[3],
   wor_exp_dict = variables[4],
   coefficients_file = coeff_file,
   variables = variables
   )

if input_reader.name in params.well_list:
    params.well_list.insert(0,params.well_list.index(input_reader.name))
else:
    params.well_list.insert(0,0)

params.study_names.insert(0,params.study_names.index(study_aux.name))

forecast = Forecaster(api.GetStudy())
cross_utils = CrossApiUtils()

datalist = [('Well', params.well_list), ('Study', params.study_names)]
well_and_studies = api.AskInput(datalist, 'DCA Analysis - Exponential', 'Please select well to change the fit exponent')

selected_well_name = params.well_list[well_and_studies[0]+1]
well = api.GetWell(selected_well_name)

old_exp = params.exp_dict[selected_well_name]
old_wc_exp = params.wc_exp_dict[selected_well_name]
old_wor_exp = params.wor_exp_dict[selected_well_name]


def update_forecast(new_value):
    log.Info(new_value)

    selected_well_name = params.well_list[well_and_studies[0] + 1]

    time_array = well.GetCurve('Oil Production Rate (Exponential Forecast) (User)').GetX()
    initial_oil_rate, initial_oil_total, initial_liquid_rate = \
        forecast.InterpolateValuesForInitialDate(selected_well_name, unicode(time_array[0].date))

    forecast.ExponentialForecast(new_value[0], time_array, selected_well_name, initial_oil_total, initial_oil_rate)
    forecast.HyperbolicForecast(1.0, new_value[0], time_array, selected_well_name, initial_oil_total, initial_oil_rate)
    forecast.WCForecast(new_value[1], new_value[2], time_array, selected_well_name, initial_liquid_rate, initial_oil_total)
    forecast.WORForecast(new_value[3], new_value[4], time_array, selected_well_name, initial_liquid_rate, initial_oil_total)

    cross_utils.ClearCrossedCurvesFromModel(well)

    params.exp_dict[selected_well_name] = new_value[0]

    with open(params.coefficients_file, 'w') as out_file:
        json.dump(params.variables, out_file)

    wd = app.GetWindow('Production forecast')
    wd_2 = app.GetWindow('Water Cut Forecast')
    wd_3 = app.GetWindow('Water Oil Ratio Forecast')
    wd_4 = app.GetWindow()
    window = wd.subject.gui
    window_2 = wd_2.subject.gui
    window_3 = wd_3.subject.gui
    window_4 = wd_4.subject.gui
    window.ForceModifiedAndRequestUpdate()
    window_2.ForceModifiedAndRequestUpdate()
    window_3.ForceModifiedAndRequestUpdate()
    window_4.ForceModifiedAndRequestUpdate()

show_curve_coeffs_dialog(old_exp, old_wc_exp, old_wor_exp, update_forecast)

# study.subject._dca_window = gui_window

def GetFilePath(study):
    file_path = os.path.dirname(study.GetFilename())
    return file_path
