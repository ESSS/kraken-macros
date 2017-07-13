'''
Name for generated for macro: (DCA) Change Coefficients in DCA Analysis for a Well
Commands Description for Macro: 
Create Time Plot
For each producer well:

'''
from esss_qt10 import qt_traits as qt
from simplewidgets.fields import NumberField, GroupField, Button
from simplewidgets.simplewidget import SimpleWidget, SimpleDialog
from ben10.foundation import log
import json


class ExponentialForecast(SimpleWidget):

    decline_rate = NumberField(0.5, label="Decline Rate")

class WCForecast(SimpleWidget):
 
    slope = NumberField(0.5, label="Slope (m)")
    intercept = NumberField(0.5, label="Intercept (c)")

class WORForecast(SimpleWidget):
 
    slope = NumberField(0.5, label="Slope (m)")
    intercept = NumberField(0.5, label="Intercept (c)")


class WellForecastUI(SimpleDialog):

    exponential_forecast = GroupField(ExponentialForecast, "Exponential and Hyperbolic Forecasts")
    wc_forecast = GroupField(WCForecast, "Water Cut Forecast")
    wor_forecast = GroupField(WCForecast, "Water Oil Ratio Forecast")
    apply = Button("Apply", "update_forecast")

    def __init__(self,parent, app, forecast, cross_utils, params, well_and_studies, well):
        SimpleDialog.__init__(self, parent)
        self.app = app
        self.forecast = forecast
        self.cross_utils = cross_utils
        self.dca_params = params
        self.well_and_studies = well_and_studies
        self.well = well
        

    def update_forecast(self):
        
        new_value = self.get_data()     
        log.Info(self.get_data())
        
        selected_well_name = self.dca_params.well_list[self.well_and_studies[0]+1]
        
        time_array = self.well.GetCurve('Oil Production Rate (Exponential Forecast) (User)').GetX()
        initial_oil_rate, initial_oil_total, initial_liquid_rate = self.forecast.InterpolateValuesForInitialDate(selected_well_name, unicode(time_array[0].date))
    
        self.forecast.ExponentialForecast(new_value.exponential_forecast.decline_rate, time_array, selected_well_name, initial_oil_total, initial_oil_rate)
        self.forecast.HyperbolicForecast(1.0, new_value.exponential_forecast.decline_rate, time_array, selected_well_name, initial_oil_total, initial_oil_rate)
        self.forecast.WCForecast(new_value.wc_forecast.slope, new_value.wc_forecast.intercept, time_array, selected_well_name, initial_liquid_rate, initial_oil_total)
        self.forecast.WORForecast(new_value.wor_forecast.slope, new_value.wor_forecast.intercept, time_array, selected_well_name, initial_liquid_rate, initial_oil_total)
        
        self.cross_utils.ClearCrossedCurvesFromModel(self.well)
        
        self.dca_params.exp_dict[selected_well_name] = new_value.exponential_forecast.decline_rate

        with open(self.dca_params.coefficients_file,'w') as out_file:
            json.dump(self.dca_params.variables, out_file)
          
        wd = self.app.GetWindow('Production forecast')
        wd_2 = self.app.GetWindow('Water Cut Forecast')
        wd_3 = self.app.GetWindow('Water Oil Ratio Forecast')
        wd_4 = self.app.GetWindow()
        window = wd.subject.gui
        window_2 = wd_2.subject.gui
        window_3 = wd_3.subject.gui
        window_4 = wd_4.subject.gui
        window.ForceModifiedAndRequestUpdate()
        window_2.ForceModifiedAndRequestUpdate()
        window_3.ForceModifiedAndRequestUpdate()
        window_4.ForceModifiedAndRequestUpdate()
        
        