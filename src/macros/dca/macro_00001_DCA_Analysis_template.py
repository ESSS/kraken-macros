'''
Name for generated for macro: (DCA) DCA Analysis Template

Commands Description for Macro:
Creates Forecast Template
Generate plots with the results
 
@author: Vinicius Girardi 
'''

import os
import json
import numpy as np
from dcacore.forecaster import Forecaster, GroupForecaster, regression
from ben10.foundation import log
from coilib50.path.path_mapper import PathMapper
from datetime import date

path_mapper = PathMapper.GetSingleton()
config_filename = os.path.join(path_mapper['/scripts_output'], "last_dca.txt")

WOR_CURVE_NAME = 'Water-Oil Ratio'
WCT_CURVE_NAME = 'Water Cut'
FORECAST_DEFAULT_YEARS = 10


def run():

    study = api.GetStudy()
    field = study.GetField()
    well_names = field.GetWellNames()
    open_producers = []

    #Select the producers that are open in the last history time step
    for well_name in well_names:
        well = field.GetWell(well_name)
        if 'Oil Production Rate' in well.GetCurveNames():
            last_opr_value = well.GetCurve('Oil Production Rate').GetY()[-1]
            if last_opr_value > 0.001:
                open_producers.append(well)

    # Get any well to do some guesses about simulation time
    base_well = field.GetWell(open_producers[0].name)
    base_time_set = base_well.GetCurve('OPR').GetTimeSet()
    guess_initial_date = base_time_set[-1].GetDateTime().date()
    guess_final_date = date(
        guess_initial_date.year + FORECAST_DEFAULT_YEARS,
        guess_initial_date.month,
        guess_initial_date.day
        )
    # This section opens dialogs and get initial and final forecasting dates from the user, study name and history file
    # to be used in the forecasting

    datalist = [
        ("Prediction Initial Date", guess_initial_date),
        ("Prediction Final Date", guess_final_date)
    ]
    input_answer = api.AskInput(datalist, "DCA Analysis", "DCA Analysis for '{}'".format(study.GetName()))

    if not input_answer:
        return

    init_date, final_date = input_answer
    forecast = Forecaster(study)
    group_forecast = GroupForecaster(study)

    time_array = forecast.CreateForecastDatesArray(final_date, init_date, base_well)

    # This loop automatically calculates the slopes and trends from the history to set the forecast coefficients
    exp_coeff_dict = {}
    wcfit_coeff_dict = {}
    worfit_coeff_dict = {}
    worfit_coeff = []
    wcfit_coeff = []

    macro_context = script.GetMacroContext()
    ordereddict = script.GetOrderedDictClass()

    script.CreateCrossPlotWindow()
    app.GetWindow().SetName('auxiliar')
    cross_plot = app.GetWindow('auxiliar')


    for prod_well in open_producers:
        log.Info("Calculation WOR/WCT for '{}'".format(prod_well.GetName()))
        splitted_curve_names = forecast.BisectArrays(prod_well.GetName(), init_date, 1)

        opr_curve = prod_well.GetCurve('Oil Production Rate')
        opt_curve = prod_well.GetCurve('Oil Production Total')
        wpr_curve = prod_well.GetCurve('Water Production Rate')

        wor = wpr_curve.y / opr_curve.y
        wct = wpr_curve.y / (wpr_curve.y + opr_curve.y)

        np.putmask(wor, np.isnan(wor), 0)
        np.putmask(wct, np.isnan(wct), 0)

        prod_well.AddCurve(WOR_CURVE_NAME, opr_curve.GetTimeSet(), wor, "m3/m3")
        prod_well.AddCurve(WCT_CURVE_NAME, opr_curve.GetTimeSet(), wct, "m3/m3")

        # create exponential regression and export the coefficients
        time_array_years = forecast.ConvertDatesInDeltaYears(opr_curve.GetX())
        exp_coeff = regression.ExponentialFit(time_array_years, opr_curve)
        exp_coeff_dict[prod_well.GetName()] = exp_coeff

        # create linear regression and export the coefficients for WC Fit
        wcfit_coeff = regression.WCFitCoeff(wct, opt_curve.y)
        wcfit_coeff_dict[prod_well.GetName()] = wcfit_coeff
        log.Info("Water Cut Coeffs. for '{}': {}".format(prod_well.GetName(), wcfit_coeff))

        # create linear regression and export the coefficients for WOR Fit
        worfit_coeff = regression.WORFitCoeff(wor, opt_curve.y)
        worfit_coeff_dict[prod_well.GetName()] = worfit_coeff
        log.Info("WOR Coeffs. for '{}': {}".format(prod_well.GetName(), worfit_coeff))

    cross_plot.CloseWindow()

    path = GetFilePath(study.name)

    with open(os.path.join(path, 'Coeffs_file.txt'), 'w') as out_file:
        producer_names = [producer.GetName() for producer in open_producers]
        json.dump([study.name, producer_names, exp_coeff_dict, wcfit_coeff_dict, worfit_coeff_dict], out_file)

    if not os.path.isdir(path_mapper['/scripts_output']):
        os.mkdir(path_mapper['/scripts_output'])

    with open(config_filename, 'w') as last_dca_file:
        json.dump(path, last_dca_file)

    # This loop calculates the forecast curves based on the information provided above, for all producer wells in
    # the study
    for prod_well in open_producers:
        well_name = prod_well.GetName()
        log.Info("Forecasting for '{}'".format(prod_well.GetName()))

        initial_oil_rate, initial_oil_total, initial_liquid_rate = \
            forecast.InterpolateValuesForInitialDate(prod_well.GetName(), init_date)
        exponential_curve_names = forecast.ExponentialForecast(exp_coeff_dict[well_name],
                                                               time_array,
                                                               well_name,
                                                               initial_oil_total,
                                                               initial_oil_rate
                                                               )
        hyperbolic_curve_names = forecast.HyperbolicForecast(1.0,
                                                             exp_coeff_dict[well_name],
                                                             time_array,
                                                             well_name,
                                                             initial_oil_total,
                                                             initial_oil_rate
                                                             )
        wor_curve_names = forecast.WORForecast(worfit_coeff_dict[well_name][0],
                                               worfit_coeff_dict[well_name][1],
                                               time_array,
                                               well_name,
                                               initial_liquid_rate,
                                               initial_oil_total
                                               )
        wc_curve_names = forecast.WCForecast(wcfit_coeff_dict[well_name][0],
                                             wcfit_coeff_dict[well_name][1],
                                             time_array,
                                             well_name,
                                             initial_liquid_rate,
                                             initial_oil_total
                                             )
        all_curve_names = exponential_curve_names, hyperbolic_curve_names, wor_curve_names, wc_curve_names, \
                          splitted_curve_names

    # same procedure applied for the well groups
    group_names = study.GetWellGroupNames()
    groups_dict = {}

    for group_name in group_names:
        group = study.GetWellGroup(group_name)
        wells = group.GetWellNames()
        ProdList = []

        for well_name in wells:
            prod = study.GetWell(well_name).GetSubject().GetOutput(time_step_index=0)()
            if 1 in prod.GetType(1):
                ProdList.append(well_name)

        if ProdList:
            groups_dict[group_name] = ProdList

    group_forecast.GroupCalculations(groups_dict, time_array, opr_curve, opt_curve, wpr_curve)

    # This part generates all the cross plot windows and workspaces, showing the results of the DCA analysis
    properties = []

    for curve in all_curve_names:
        log.Info(f"Cross plot for '{curve}'")
        oil_production_total_forecast = script.GetPropertyTemplate(
            str('_unknown_' + curve[1] + '__realization_user'))
        oil_production_rate_forecast = script.GetPropertyTemplate(
            str('_unknown_' + curve[0] + '__realization_user'))

        properties.append(
            script.GetPropertyTemplateCrossedWithSource(oil_production_total_forecast, oil_production_rate_forecast,
                                                        'Curve'))

    # Create workspace and change its attributes
    ws = script.CreateWorkspace()
    object_id_ws = macro_context.GetWorkspaceId(macro_id=('Created', 'CreateWorkspace', ws, 0), name='DCA Analysis')
    script.ChangeAttrs(expected_class_name='WorkspaceInTabSubject', attrs={'name': 'DCA Analysis'},
                       object_id=object_id_ws)
    well_name = open_producers[0].GetName()

    # Create Cross plot #1
    cpw = script.CreateCrossPlotWindow()
    app.GetWindow().SetName('Production forecast')

    study_id_0 = macro_context.GetStudyId('InputReader', name=study.name)
    data_id_0 = macro_context.GetDataId('WellSelectorProcessSubject', name=well_name, study_id=study_id_0)

    coloring_id_0 = macro_context.GetColoringId('CrossPlotCurveCollectionColoringProcessSubject', data_id=data_id_0,
                                                window_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotCurveCollectionColoringProcessSubject', attrs={
        'crossed_curve_associations': [properties[0], properties[1], properties[2], properties[3], properties[4]]},
                       object_id=coloring_id_0)

    # change layout
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject',
                       attrs={'axis_allocation_rule': 'axis_allocation_by_quantity'}, object_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'coloring_strategy_id': 'Property Based'},
                       object_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'enable_title': True}, object_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'title': '$e'}, object_id=cpw)

    object_id_1 = cpw + '.plot_window_axis_subject_0'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_1)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': 'Oil Production Rate ($unit)'},
                       object_id=object_id_1)

    object_id_2 = cpw + '.plot_window_axis_subject_8'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_2)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': 'Oil Production Total ($unit)'},
                       object_id=object_id_2)

    for prod_well in open_producers:
        well_name = prod_well.GetName()
        script.ChangeApplicationSettings(setting_name=str(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (Exponential Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (Exponential Forecast):^:Curve'),
                                         value={'pen_color': (0, 0, 0), 'symbol_color': (138, 43, 226),
                                                'symbol_style': -1, 'symbol_size': 10, 'curve_style': 1,
                                                'pen_width': 3, 'pen_style': 3})

        script.ChangeApplicationSettings(setting_name=str(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (Hyperbolic Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (Hyperbolic Forecast):^:Curve'),
                                         value={'pen_color': (210, 105, 30), 'symbol_color': (50, 205, 50),
                                                'symbol_style': -1, 'symbol_size': 10, 'curve_style': 1,
                                                'pen_width': 3, 'pen_style': 3})

        script.ChangeApplicationSettings(setting_name=str(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (WC Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (WC Forecast):^:Curve'),
                                         value={'pen_color': (65, 105, 225), 'symbol_color': (255, 20, 147),
                                                'symbol_style': -1, 'symbol_size': 10, 'curve_style': 1,
                                                'pen_width': 3, 'pen_style': 3})

        script.ChangeApplicationSettings(setting_name=str(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (WOR Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (WOR Forecast):^:Curve'),
                                         value={'pen_color': (34, 139, 34), 'symbol_color': (184, 134, 11),
                                                'symbol_style': -1, 'symbol_size': 10, 'curve_style': 1,
                                                'pen_width': 3, 'pen_style': 3})

        if init_date:
            script.ChangeApplicationSettings(setting_name=str(
                'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (History):^:realization#^user#^unknown_data#^Oil Production Rate (History):^:Curve'),
                                             value={'pen_color': (0, 0, 0), 'symbol_color': (138, 43, 226),
                                                    'symbol_style': -1, 'symbol_size': 10, 'curve_style': 1,
                                                    'pen_width': 3, 'pen_style': 1})

    # Create Cross plot #2
    cpw_2 = script.CreateCrossPlotWindow()
    app.GetWindow().SetName('Water Oil Ratio Forecast')
    data_id_1 = macro_context.GetDataId('WellSelectorProcessSubject', name=well_name, study_id=study_id_0)

    oil_production_total__splitted = script.GetPropertyTemplate(
        '_unknown_Oil Production Total (History)__realization_user')
    wor__realization_custom = script.GetPropertyTemplate('_unknown_Water-Oil Ratio__realization_user')
    cross_1 = script.GetPropertyTemplateCrossedWithSource(oil_production_total__splitted, wor__realization_custom,
                                                          'Curve')

    oil_production_total_wor = script.GetPropertyTemplate(
        '_unknown_Oil Production Total (WOR Forecast)__realization_user')
    wor_forecast_user = script.GetPropertyTemplate('_unknown_Water Oil Ratio (WOR Forecast)__realization_user')
    cross_2 = script.GetPropertyTemplateCrossedWithSource(oil_production_total_wor, wor_forecast_user, 'Curve')

    coloring_id_1 = macro_context.GetColoringId('CrossPlotCurveCollectionColoringProcessSubject', data_id=data_id_1,
                                                window_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotCurveCollectionColoringProcessSubject',
                       attrs={'crossed_curve_associations': [cross_1, cross_2]}, object_id=coloring_id_1)

    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject',
                       attrs={'axis_allocation_rule': 'axis_allocation_by_quantity'}, object_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'coloring_strategy_id': 'Property Based'},
                       object_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'enable_title': True}, object_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'title': '$e'}, object_id=cpw_2)

    object_id_4 = cpw_2 + '.plot_window_axis_subject_0'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_4)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': 'Water Oil Ratio'},
                       object_id=object_id_4)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'axis_scale_logarithmic': True},
                       object_id=object_id_4)

    object_id_5 = cpw_2 + '.plot_window_axis_subject_8'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_5)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': 'Oil Production Total ($unit)'},
                       object_id=object_id_5)

    for prod_well in open_producers:
        script.ChangeApplicationSettings(
            setting_name='CURVE_PROPS_input_reader_00001.' + prod_well.GetName() + '.realization#^user#^unknown_data#^Oil Production Total (History):^:realization#^custom#^unknown_data#^WOR:^:Curve',
            value={'pen_color': (34, 139, 34), 'symbol_color': (184, 134, 11), 'symbol_style': -1,
                   'symbol_size': 10, 'curve_style': 1, 'pen_width': 3, 'pen_style': 1})

    # Create Cross plot #3
    cpw_3 = script.CreateCrossPlotWindow()
    app.GetWindow().SetName('Water Cut Forecast')
    data_id_2 = macro_context.GetDataId('WellSelectorProcessSubject', name=well_name, study_id=study_id_0)

    water_cut_sc = script.GetPropertyTemplate('WATER_CUT_SC__realization_user')
    cross_3 = script.GetPropertyTemplateCrossedWithSource(oil_production_total__splitted, water_cut_sc, 'Curve')

    oil_production_total_wc = script.GetPropertyTemplate(
        '_unknown_Oil Production Total (WC Forecast)__realization_user')
    wc_forecast_user = script.GetPropertyTemplate('_unknown_Water Cut (WC Forecast)__realization_user')
    cross_4 = script.GetPropertyTemplateCrossedWithSource(oil_production_total_wc, wc_forecast_user, 'Curve')

    coloring_id_2 = macro_context.GetColoringId('CrossPlotCurveCollectionColoringProcessSubject', data_id=data_id_2,
                                                window_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotCurveCollectionColoringProcessSubject',
                       attrs={'crossed_curve_associations': [cross_3, cross_4]}, object_id=coloring_id_2)

    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject',
                       attrs={'axis_allocation_rule': 'axis_allocation_by_quantity'}, object_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'coloring_strategy_id': 'Property Based'},
                       object_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'enable_title': True}, object_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'title': '$e'}, object_id=cpw_3)

    object_id_7 = cpw_3 + '.plot_window_axis_subject_0'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_7)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': 'Water Cut'},
                       object_id=object_id_7)

    object_id_8 = cpw_3 + '.plot_window_axis_subject_8'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_8)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': 'Oil Production Total ($unit)'},
                       object_id=object_id_8)


def GetFilePath(study_name):
    study = api.GetStudy(study_name)
    file_path = os.path.dirname(study.GetFilename())
    return file_path


run()
