'''
Name for generated for macro: (DCA) Change DCA Coefficients for a well

Commands Description for Macro: 
Creates Forecast Template
Generate plots with the results

@author: Vinicius Girardi
'''

from __future__ import unicode_literals
from shared.GUIforDCA import WellForecastUI
from shared.forecaster import Forecaster
from apiCrossUtils.CrossCurveManipulations import CrossApiUtils
from coilib50.path.path_mapper import PathMapper
from plugins10.plugins.selection.selectionplugins import EPSelectionService
from plugins10.core.pluginmanager import PluginManager
from plugins10.plugins.uiapplication.model_eps import EPModel
import json
import os
from collections import namedtuple
from esss_qt10.qt_traits import qApp

path_mapper = PathMapper.GetSingleton()
config_filename = os.path.join(path_mapper['/scripts_output'], "last_dca.txt")

selection_service = PluginManager.GetSingleton(EPSelectionService)
selected_object = selection_service.GetSelection()
pool = PluginManager.GetSingleton(EPModel)
input_reader = pool[selected_object[0]]

DCAParameters = namedtuple("DCAParameters",
                           ["study_names",
                            "hist_names",
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
   hist_names = study_aux.GetAvailableHistoryNames(),
   well_list = variables[2][:],
   exp_dict = variables[3],
   wc_exp_dict = variables[4],
   wor_exp_dict = variables[5],
   coefficients_file = coeff_file,
   variables = variables
   )

if input_reader.name in params.well_list:
    params.well_list.insert(0,params.well_list.index(input_reader.name))
else:
    params.well_list.insert(0,0)
    
params.study_names.insert(0,params.study_names.index(study_aux.name))
params.hist_names.insert(0,params.hist_names.index(variables[1]))

forecast = Forecaster(api.GetStudy())
cross_utils = CrossApiUtils()

datalist = [('Well', params.well_list), ('Study', params.study_names), ('History file', params.hist_names)]
well_and_studies = api.AskInput(datalist, 'DCA Analysis - Exponential', 'Please select well to change the fit exponent')

selected_well_name = params.well_list[well_and_studies[0]+1]
well = api.GetWell(selected_well_name)

old_exp = params.exp_dict[selected_well_name]
old_wc_exp = params.wc_exp_dict[selected_well_name]
old_wor_exp = params.wor_exp_dict[selected_well_name]

gui_window = WellForecastUI(qApp.desktop(), app, forecast, cross_utils, params, well_and_studies, well)
gui_window.exponential_forecast.child_widget.decline_rate.set_value(old_exp)
gui_window.wc_forecast.child_widget.slope.set_value(old_wc_exp[0])
gui_window.wc_forecast.child_widget.intercept.set_value(old_wc_exp[1])
gui_window.wor_forecast.child_widget.slope.set_value(old_wor_exp[0])
gui_window.wor_forecast.child_widget.intercept.set_value(old_wor_exp[1])
gui_window.show()
study = api.GetStudy()
study.subject._dca_window = gui_window
    
def GetFilePath(study):
    file_path = os.path.dirname(study.GetFilename())
    return file_path
