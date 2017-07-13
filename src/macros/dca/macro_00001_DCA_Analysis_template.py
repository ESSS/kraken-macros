'''
Name for generated for macro: (DCA) DCA Analysis Template

Commands Description for Macro:
Creates Forecast Template
Generate plots with the results

@author: Vinicius Girardi
'''
from __future__ import unicode_literals
import os
import json
import numpy as np
from dcacore.forecaster import Forecaster, GroupForecaster, regression
from ben10.foundation import log
from coilib50.path.path_mapper import PathMapper

path_mapper = PathMapper.GetSingleton()
config_filename = os.path.join(path_mapper['/scripts_output'], "last_dca.txt")

WOR_CURVE_NAME = 'Water-Oil Ratio'
WCT_CURVE_NAME = 'Water Cut'


def run():
    study_names = api.GetStudyNames()
    study_aux = api.GetStudy(study_names[0])
    hist_names = study_aux.GetAvailableHistoryNames()
    study_names_list = [0] + study_names
    hist_names_list = [0] + hist_names

    # This section opens dialogs and get initial and final forecasting dates from the user, study name and history file
    # to be used in the forecasting
    datalist = [
        ('Initial date (Leave empty to use last simulation Time-Step)', '2015-09-01'),
        ('Final Date', '2028-01-01'),
        ('Study', study_names_list),
    ]
    input_answer = api.AskInput(datalist, 'DCA Analysis', 'Please input initial and final dates')
    if input_answer:
        init_time, final_time, study_idx = input_answer
    else:
        return

    study = api.GetStudy(study_names[study_idx])
    # history_name = hist_names[parameters[3]]
    forecast = Forecaster(study)
    group_forecast = GroupForecaster(study)

    # Get the last time step in case the user didn't provide the initial Forecasting date
    field = study.GetField()
    last_time_step = field.GetCurve('Oil Production Rate').GetTimeSet()[-1]
    last_time_step_str = last_time_step.date

    # if the user defined an initial interpolation date, then a new time set will be created for it
    if init_time:
        time_array = forecast.CreateForecastDatesArray(final_time, init_time)

    # if an initial date was not defined by the user all the calculations will be done using the last
    # simulation time-step
    else:
        init_time = unicode(last_time_step_str)
        time_array = forecast.CreateForecastDatesArray(final_time, init_time)

    # This loop automatically calculates the slopes and trends from the history to set the forecast coefficients
    exp_coeff_dict = {}
    wcfit_coeff_dict = {}
    worfit_coeff_dict = {}
    worfit_coeff = []
    wcfit_coeff = []

    macro_context = script.GetMacroContext()
    ordereddict = script.GetOrderedDictClass()

    script.CreateCrossPlotWindow()
    app.GetWindow().SetName(u'auxiliar')
    cross_plot = app.GetWindow(u'auxiliar')

    well_names = field.GetWellNames()
    producers = []

    for well_name in well_names:
        well = api.GetWell(well_name)
        if well_name == "HERCILIO":
        # if 'Oil Production Rate' in well.GetCurveNames():
            producers.append(well)

    for prod_well in producers:
        log.Info("Calculation WOR/WCT for '{}'".format(prod_well.GetName()))
        if init_time:
            splitted_curve_names = forecast.BisectArrays(prod_well.GetName(), init_time, 1)
        else:
            splitted_curve_names = forecast.BisectArrays(prod_well.GetName(), unicode(last_time_step_str), 0)

        opr_curve = prod_well.GetCurve('Oil Production Rate')
        opt_curve = prod_well.GetCurve('Oil Production Total')
        wpr_curve = prod_well.GetCurve('Water Production Rate')

        wor = wpr_curve.y / opr_curve.y
        wct = wpr_curve.y / (wpr_curve.y + opr_curve.y)

        np.putmask(wor, np.isnan(wor), 0)
        np.putmask(wct, np.isnan(wct), 0)

        prod_well.AddCurve(WOR_CURVE_NAME, opr_curve.GetTimeSet(), wor, "<unknown>")
        prod_well.AddCurve(WCT_CURVE_NAME, opr_curve.GetTimeSet(), wct, "<unknown>")

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
        producer_names = [producer.GetName() for producer in producers]
        json.dump([study.name, producer_names, exp_coeff_dict, wcfit_coeff_dict, worfit_coeff_dict], out_file)

    if not os.path.isdir(path_mapper['/scripts_output']):
        os.mkdir(path_mapper['/scripts_output'])

    with open(config_filename, 'w') as last_dca_file:
        json.dump(path, last_dca_file)

    # This loop calculates the forecast curves based on the information provided above, for all producer wells in
    # the study
    for prod_well in producers:
        well_name = prod_well.GetName()
        log.Info("Forecasting for '{}'".format(prod_well.GetName()))

        initial_oil_rate, initial_oil_total, initial_liquid_rate = \
            forecast.InterpolateValuesForInitialDate(prod_well.GetName(), init_time)
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
        log.Info("Cross plot for '{}'".format(curve))
        oil_production_total_forecast = script.GetPropertyTemplate(
            unicode('_unknown_' + curve[1] + '__realization_user'))
        oil_production_rate_forecast = script.GetPropertyTemplate(
            unicode('_unknown_' + curve[0] + '__realization_user'))

        properties.append(
            script.GetPropertyTemplateCrossedWithSource(oil_production_total_forecast, oil_production_rate_forecast,
                                                        u'Curve'))

    # Create workspace and change its attributes
    ws = script.CreateWorkspace()
    object_id_ws = macro_context.GetWorkspaceId(macro_id=(u'Created', u'CreateWorkspace', ws, 0), name='DCA Analysis')
    script.ChangeAttrs(expected_class_name='WorkspaceInTabSubject', attrs={'name': 'DCA Analysis'},
                       object_id=object_id_ws)
    well_name = producers[0].GetName()

    # Create Cross plot #1
    cpw = script.CreateCrossPlotWindow()
    app.GetWindow().SetName('Production forecast')

    study_id_0 = macro_context.GetStudyId(u'InputReader', name=study.name)
    data_id_0 = macro_context.GetDataId(u'WellSelectorProcessSubject', name=well_name, study_id=study_id_0)

    coloring_id_0 = macro_context.GetColoringId(u'CrossPlotCurveCollectionColoringProcessSubject', data_id=data_id_0,
                                                window_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotCurveCollectionColoringProcessSubject', attrs={
        u'crossed_curve_associations': [properties[0], properties[1], properties[2], properties[3], properties[4]]},
                       object_id=coloring_id_0)

    # change layout
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject',
                       attrs={'axis_allocation_rule': u'axis_allocation_by_quantity'}, object_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'coloring_strategy_id': u'Property Based'},
                       object_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'enable_title': True}, object_id=cpw)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'title': u'$e'}, object_id=cpw)

    object_id_1 = cpw + u'.plot_window_axis_subject_0'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_1)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': u'Oil Production Rate ($unit)'},
                       object_id=object_id_1)

    object_id_2 = cpw + u'.plot_window_axis_subject_8'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_2)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': u'Oil Production Total ($unit)'},
                       object_id=object_id_2)

    for prod_well in producers:
        well_name = prod_well.GetName()
        script.ChangeApplicationSettings(setting_name=unicode(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (Exponential Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (Exponential Forecast):^:Curve'),
                                         value={u'pen_color': (0, 0, 0), u'symbol_color': (138, 43, 226),
                                                u'symbol_style': -1, u'symbol_size': 10, u'curve_style': 1,
                                                u'pen_width': 3, u'pen_style': 3})

        script.ChangeApplicationSettings(setting_name=unicode(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (Hyperbolic Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (Hyperbolic Forecast):^:Curve'),
                                         value={u'pen_color': (210, 105, 30), u'symbol_color': (50, 205, 50),
                                                u'symbol_style': -1, u'symbol_size': 10, u'curve_style': 1,
                                                u'pen_width': 3, u'pen_style': 3})

        script.ChangeApplicationSettings(setting_name=unicode(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (WC Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (WC Forecast):^:Curve'),
                                         value={u'pen_color': (65, 105, 225), u'symbol_color': (255, 20, 147),
                                                u'symbol_style': -1, u'symbol_size': 10, u'curve_style': 1,
                                                u'pen_width': 3, u'pen_style': 3})

        script.ChangeApplicationSettings(setting_name=unicode(
            'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (WOR Forecast):^:realization#^user#^unknown_data#^Oil Production Rate (WOR Forecast):^:Curve'),
                                         value={u'pen_color': (34, 139, 34), u'symbol_color': (184, 134, 11),
                                                u'symbol_style': -1, u'symbol_size': 10, u'curve_style': 1,
                                                u'pen_width': 3, u'pen_style': 3})

        if init_time:
            script.ChangeApplicationSettings(setting_name=unicode(
                'CURVE_PROPS_input_reader_00001.' + well_name + '.realization#^user#^unknown_data#^Oil Production Total (History):^:realization#^user#^unknown_data#^Oil Production Rate (History):^:Curve'),
                                             value={u'pen_color': (0, 0, 0), u'symbol_color': (138, 43, 226),
                                                    u'symbol_style': -1, u'symbol_size': 10, u'curve_style': 1,
                                                    u'pen_width': 3, u'pen_style': 1})

    # Create Cross plot #2
    cpw_2 = script.CreateCrossPlotWindow()
    app.GetWindow().SetName('Water Oil Ratio Forecast')
    data_id_1 = macro_context.GetDataId(u'WellSelectorProcessSubject', name=well_name, study_id=study_id_0)

    oil_production_total__splitted = script.GetPropertyTemplate(
        u'_unknown_Oil Production Total (History)__realization_user')
    wor__realization_custom = script.GetPropertyTemplate(u'_unknown_WOR__realization_custom')
    cross_1 = script.GetPropertyTemplateCrossedWithSource(oil_production_total__splitted, wor__realization_custom,
                                                          u'Curve')

    oil_production_total_wor = script.GetPropertyTemplate(
        u'_unknown_Oil Production Total (WOR Forecast)__realization_user')
    wor_forecast_user = script.GetPropertyTemplate(u'_unknown_Water Oil Ratio (WOR Forecast)__realization_user')
    cross_2 = script.GetPropertyTemplateCrossedWithSource(oil_production_total_wor, wor_forecast_user, u'Curve')

    coloring_id_1 = macro_context.GetColoringId(u'CrossPlotCurveCollectionColoringProcessSubject', data_id=data_id_1,
                                                window_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotCurveCollectionColoringProcessSubject',
                       attrs={u'crossed_curve_associations': [cross_1, cross_2]}, object_id=coloring_id_1)

    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject',
                       attrs={'axis_allocation_rule': u'axis_allocation_by_quantity'}, object_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'coloring_strategy_id': u'Property Based'},
                       object_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'enable_title': True}, object_id=cpw_2)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'title': u'$e'}, object_id=cpw_2)

    object_id_4 = cpw_2 + u'.plot_window_axis_subject_0'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_4)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': u'Water Oil Ratio'},
                       object_id=object_id_4)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'axis_scale_logarithmic': True},
                       object_id=object_id_4)

    object_id_5 = cpw_2 + u'.plot_window_axis_subject_8'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_5)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': u'Oil Production Total ($unit)'},
                       object_id=object_id_5)

    for prod_well in producers:
        script.ChangeApplicationSettings(
            setting_name=u'CURVE_PROPS_input_reader_00001.' + prod_well.GetName() + '.realization#^user#^unknown_data#^Oil Production Total (History):^:realization#^custom#^unknown_data#^WOR:^:Curve',
            value={u'pen_color': (34, 139, 34), u'symbol_color': (184, 134, 11), u'symbol_style': -1,
                   u'symbol_size': 10, u'curve_style': 1, u'pen_width': 3, u'pen_style': 1})

    # Create Cross plot #3
    cpw_3 = script.CreateCrossPlotWindow()
    app.GetWindow().SetName('Water Cut Forecast')
    data_id_2 = macro_context.GetDataId(u'WellSelectorProcessSubject', name=well_name, study_id=study_id_0)

    water_cut_sc = script.GetPropertyTemplate('WATER_CUT_SC')
    cross_3 = script.GetPropertyTemplateCrossedWithSource(oil_production_total__splitted, water_cut_sc, u'Curve')

    oil_production_total_wc = script.GetPropertyTemplate(
        u'_unknown_Oil Production Total (WC Forecast)__realization_user')
    wc_forecast_user = script.GetPropertyTemplate(u'_unknown_Water Cut (WC Forecast)__realization_user')
    cross_4 = script.GetPropertyTemplateCrossedWithSource(oil_production_total_wc, wc_forecast_user, u'Curve')

    coloring_id_2 = macro_context.GetColoringId(u'CrossPlotCurveCollectionColoringProcessSubject', data_id=data_id_2,
                                                window_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotCurveCollectionColoringProcessSubject',
                       attrs={u'crossed_curve_associations': [cross_3, cross_4]}, object_id=coloring_id_2)

    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject',
                       attrs={'axis_allocation_rule': u'axis_allocation_by_quantity'}, object_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'coloring_strategy_id': u'Property Based'},
                       object_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'enable_title': True}, object_id=cpw_3)
    script.ChangeAttrs(expected_class_name='CrossPlotWindowSubject', attrs={'title': u'$e'}, object_id=cpw_3)

    object_id_7 = cpw_3 + u'.plot_window_axis_subject_0'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_7)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': u'Water Cut'},
                       object_id=object_id_7)

    object_id_8 = cpw_3 + u'.plot_window_axis_subject_8'
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'use_local_title': True},
                       object_id=object_id_8)
    script.ChangeAttrs(expected_class_name='PlotWindowAxisSubject', attrs={'title': u'Oil Production Total ($unit)'},
                       object_id=object_id_8)


def GetFilePath(study_name):
    study = api.GetStudy(study_name)
    file_path = os.path.dirname(study.GetFilename())
    return file_path


run()
