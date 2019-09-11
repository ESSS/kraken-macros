'''
Name for generated for macro: Forecasting

Commands Description for Macro:
    Compute a Forecast using different methods

'''
# Import an utility package for manipulating rate curves

from coilib50.time.time_step import TimeStep
from coilib50.time.time_set import TimeSet
from kraken20.plugins.api.ka_model import KAModel
from dcacore import regression
import numpy as np
import bisect


class Forecaster:
    
    
    def __init__(self, study):
        assert isinstance(study,KAModel), 'Not a Study'
        self.study = study
    
    
    def CreateForecastDatesArray(self, final_date, initial_date, base_well):
        # Obtain the Field of the current study
        field = self.study.GetField()
        # Obtain the curve array (values and dates)
        well = field.GetWell(base_well.name)
        curve = well.GetCurve('Oil Production Rate')
        # Obtain the time array
        timeset = curve.GetTimeSet()
        initial_step = TimeStep.Create(initial_date.year, initial_date.month, initial_date.day)
        forecasting_delta = final_date - initial_date           
        forecasting_timeset = timeset.CreateFromAbsoluteDeltasInDays(initial_step, range(forecasting_delta.days))
        return forecasting_timeset



    def ExponentialForecast(self, Di, time_array, well_name, initial_cumulative_oil = None, initial_oil_rate = None):
        cumulative_oil_array = np.zeros(len(time_array))
        curve_name = 'Oil Production Rate'
        # Get Well
        well = self.study.GetWell(well_name)
        #Get Curve
        curve = well.GetCurve(curve_name)
        
        if not initial_oil_rate:
            initial_oil_rate = curve.y[-1]

        if initial_cumulative_oil:
            cumulative_oil_array[0] = initial_cumulative_oil
        else:
            opt = well.GetCurve('Oil Production Total')
            cumulative_oil_array[0] = opt.y[-1]
        
        delta_in_years = self.ConvertDatesInDeltaYears(time_array)
        
        oil_rate = initial_oil_rate*np.exp(-Di*delta_in_years)
             
        for i in range(len(oil_rate)-1):
            
            cumulative_oil_array[i+1] = cumulative_oil_array[i] + oil_rate[i+1] #delta of 1 day        
        
        exponential_curve_names = ['Oil Production Rate (Exponential Forecast)', 'Oil Production Total (Exponential Forecast)']
                
        well.AddCurve(exponential_curve_names[0], time_array , oil_rate, 'm3/d')
        well.AddCurve(exponential_curve_names[1], time_array , cumulative_oil_array, 'm3')
        
        return tuple(exponential_curve_names)
    
    
    def HyperbolicForecast(self, b, Di, time_array, well_name, initial_cumulative_oil = None, initial_oil_rate = None):
        cumulative_oil_array = np.zeros(len(time_array))
        opr = 'Oil Production Rate'
        # Get Well
        well = self.study.GetWell(well_name)
        #Get Curve
        curve = well.GetCurve(opr)
        
        if not initial_oil_rate:
            initial_oil_rate = curve.y[-1]

        if initial_cumulative_oil:
            cumulative_oil_array[0] = initial_cumulative_oil
        else:
            opt = well.GetCurve('Oil Production Total')
            cumulative_oil_array[0] = opt.y[-1]
            
        delta_in_years = self.ConvertDatesInDeltaYears(time_array)
        
        oil_rate = initial_oil_rate*(1 + Di*b*delta_in_years)**(-1/b)
        
        for i in range(len(oil_rate)-1):
            
            cumulative_oil_array[i+1] = cumulative_oil_array[i] + oil_rate[i+1] #delta of 1 day
        
        hyperbolic_curve_names = ['Oil Production Rate (Hyperbolic Forecast)', 'Oil Production Total (Hyperbolic Forecast)']
        
        well.AddCurve(hyperbolic_curve_names[0], time_array , oil_rate, 'm3/d')
        well.AddCurve(hyperbolic_curve_names[1], time_array , cumulative_oil_array, 'm3')
        
        return tuple(hyperbolic_curve_names)
    
    
    def WORForecast(self, m, c, time_array, well_name, initial_liquid_rate = None, initial_cumulative_oil = None):
        #arrays initialization
        cumulative_oil_array = np.zeros(len(time_array))    #total produced oil in [Mstb]
        wor = np.zeros(len(time_array))                     #water oil rate 
        produced_oil = np.zeros(len(time_array))            #oil produced during the interval between 2 time-steps in [Mstb]

        #Get Well
        well = self.study.GetWell(well_name)
            
        #initial value for liquid production
        if initial_liquid_rate:
            initial_liquid_rate_bbl = initial_liquid_rate * 6.2898105697751
        
        else:
            initial_liquid_rate_bbl = (well.GetCurve('Oil Production Rate').y[-1] + well.GetCurve('Water Production Rate').y[-1] )* 6.2898105697751
        
        #initial values for each array
        if initial_cumulative_oil:
            cumulative_oil_array[0] = initial_cumulative_oil * 0.0062898105697751
        else:
            curve = well.GetCurve('Oil Production Total')
            cumulative_oil_array[0] = curve.y[-1] * 0.0062898105697751
                  
        wor[0] = 10**(m * cumulative_oil_array[0] + c)
        
        produced_oil[0] = (initial_liquid_rate_bbl / (wor[0]+1) * 0.001)
        
        #arrays calculations    
        for i in range(len(time_array)-1):
            
            cumulative_oil_array[i+1] = cumulative_oil_array[i] + produced_oil[i]
            
            wor[i+1] = 10**(m*cumulative_oil_array[i+1] + c)
            
            produced_oil[i+1] = initial_liquid_rate_bbl / (wor[i+1]+1) * 0.001
            
        cumulative_oil_array_m3 = 158.9873 * cumulative_oil_array # constant is 1000 / 6.2898 (m3 to bbl)
        produced_oil_m3 = 158.9873 * produced_oil
       
        wor_curve_names = ['Oil Production Rate (WOR Forecast)', 'Oil Production Total (WOR Forecast)','Water Oil Ratio (WOR Forecast)']
        
        well.AddCurve(wor_curve_names[0], time_array , produced_oil_m3, 'm3/d')
        well.AddCurve(wor_curve_names[1], time_array , cumulative_oil_array_m3, 'm3')
        well.AddCurve(wor_curve_names[2], time_array , wor, 'm3/m3')
        
        return tuple(wor_curve_names[0:2])
    
    
    def WCForecast(self, m, c, time_array, well_name, initial_liquid_rate = None, initial_cumulative_oil = None):
        #arrays initialization
        cumulative_oil_array_wc = np.zeros(len(time_array))    #total produced oil in [Mstb]
        wc = np.zeros(len(time_array))                     #water oil rate 
        produced_oil = np.zeros(len(time_array))            #oil produced during the interval between 2 time-steps in [Mstb]

        #Get Well
        well = self.study.GetWell(well_name)
        
        #initial value for liquid production
        if initial_liquid_rate:
            initial_liquid_rate = initial_liquid_rate * 6.2898105697751
        
        else:
            initial_liquid_rate = (well.GetCurve('Oil Production Rate').y[-1] + well.GetCurve('Water Production Rate').y[-1] )* 6.2898105697751
        
        #initial values for each array
        if initial_cumulative_oil:
            cumulative_oil_array_wc[0] = initial_cumulative_oil * 0.0062898105697751
        else:
            curve = well.GetCurve('Oil Production Total')
            cumulative_oil_array_wc[0] = curve.y[-1] * 0.0062898105697751
        
        wc[0] = m * cumulative_oil_array_wc[0] + c
        
        produced_oil[0] = 0.001 * initial_liquid_rate * (1 - wc[0])
        
        #arrays calculations    
        for i in range(len(time_array)-1):
            
            cumulative_oil_array_wc[i+1] = cumulative_oil_array_wc[i] + produced_oil[i]
            
            wc[i+1] = m * cumulative_oil_array_wc[i+1] + c
            
            produced_oil[i+1] = initial_liquid_rate * (1 - wc[i+1]) * 0.001
        
        cumulative_oil_array_m3 = 158.9873 * cumulative_oil_array_wc # constant is 1000 / 6.2898 (m3 to bbl)
        produced_oil_m3 = 158.9873 * produced_oil
        
        wc_curve_names = ['Oil Production Rate (WC Forecast)', 'Oil Production Total (WC Forecast)', 'Water Cut (WC Forecast)']
        
        well.AddCurve(wc_curve_names[0], time_array , produced_oil_m3, 'm3/d')
        well.AddCurve(wc_curve_names[1], time_array , cumulative_oil_array_m3, 'm3')
        well.AddCurve(wc_curve_names[2], time_array , wc, 'm3/m3')
        
        return tuple(wc_curve_names[0:2])
    
    
    def ConvertDatesInDeltaYears(self, time_array):
        time_array_years = np.zeros(len(time_array))           
        for i in range(len(time_array)):
            time_array_years[i] = (np.datetime64(time_array[i].date) - np.datetime64(time_array[0].date)) / np.timedelta64(1,'D') / 365.25
        return time_array_years
    
    
    def InterpolateValuesForInitialDate(self, well_name, initial_date):
        initial_forecasting_date = TimeStep.Create(initial_date.year, initial_date.month, initial_date.day)
        opr = self.study.GetWell(well_name).GetCurve('Oil Production Rate')    
        interpolated_oil_rate = opr.Interpolate(initial_forecasting_date)
        opt = self.study.GetWell(well_name).GetCurve('Oil Production Total')
        interpolated_oil_total = opt.Interpolate(initial_forecasting_date)
        wpr = self.study.GetWell(well_name).GetCurve('Water Production Rate')
        interpolated_liquid_rate = wpr.Interpolate(initial_forecasting_date) + interpolated_oil_rate
            
        
        return interpolated_oil_rate, interpolated_oil_total, interpolated_liquid_rate
    
    
    def BisectArrays(self, well_name, initial_date, signal):
        well = self.study.GetWell(well_name)
        original_time_set = well.GetCurve('Oil Production Rate').GetTimeSet()        
        original_values_array_opr = well.GetCurve('Oil Production Rate').GetY()
        original_values_array_opt = well.GetCurve('Oil Production Total').GetY()
        original_values_array_wpr = well.GetCurve('Water Production Rate').GetY()
        original_values_array_opt += 0.0001
        initial_date = TimeStep.Create(initial_date.year, initial_date.month, initial_date.day)
        splitted_curve_names = ['Oil Production Rate (History)', 'Oil Production Total (History)']
        if signal:
            position = bisect.bisect_left(original_time_set, initial_date)
            splitted_time_set = TimeSet.CreateFromTimeSteps(original_time_set[0], original_time_set[0:position])
            well.AddCurve(splitted_curve_names[0], splitted_time_set, original_values_array_opr[0:position], 'm3/d')
            well.AddCurve(splitted_curve_names[1], splitted_time_set, original_values_array_opt[0:position], 'm3')
            well.AddCurve('Water Production Rate (History)',splitted_time_set, original_values_array_wpr[0:position], 'm3/d')   
        else:
            well.AddCurve(splitted_curve_names[0], original_time_set, original_values_array_opr, 'm3/d')
            well.AddCurve(splitted_curve_names[1], original_time_set, original_values_array_opt, 'm3')
            well.AddCurve('Water Production Rate (History)',original_time_set, original_values_array_wpr, 'm3/d')
        return tuple(splitted_curve_names)


class GroupForecaster:
    
    def __init__(self, study):
        self.study = study
    
    def GroupCalculations(self, groups_dict, time_array, opr_history, opt_history, wpr_history):
        
        for group_name in list(groups_dict.keys()):
              
            group = self.study.GetWellGroup(group_name)
            wells_in_group = groups_dict[group_name]
            
            opr_group_history = opr_history.y*0
            opt_group_history = opt_history.y*0
            wpr_group_history = wpr_history.y*0
            
            exp_group_forecast = np.zeros(len(time_array))
            exp_group_forecast_ttl = np.zeros(len(time_array))
            
            hyp_group_forecast = np.zeros(len(time_array))
            hyp_group_forecast_ttl = np.zeros(len(time_array))
            
            opr_wor_group_forecast = np.zeros(len(time_array))
            opt_wor_group_forecast = np.zeros(len(time_array))
            wor_group_forecast = np.zeros(len(time_array))
            
            opr_wc_group_forecast = np.zeros(len(time_array))
            opt_wc_group_forecast = np.zeros(len(time_array))
            wc_group_forecast = np.zeros(len(time_array))
            
            for prd_well_name in wells_in_group:
                prd_well = group.GetWell(prd_well_name) 
            
                opr_group_history += prd_well.GetCurve('Oil Production Rate (History) (User)').y
                opt_group_history += prd_well.GetCurve('Oil Production Total (History) (User)').y
                wpr_group_history += prd_well.GetCurve('Water Production Rate (History) (User)').y
                  
                exp_group_forecast += prd_well.GetCurve('Oil Production Rate (Exponential Forecast) (User)').y
                exp_group_forecast_ttl += prd_well.GetCurve('Oil Production Total (Exponential Forecast) (User)').y
                
                hyp_group_forecast += prd_well.GetCurve('Oil Production Rate (Hyperbolic Forecast) (User)').y
                hyp_group_forecast_ttl += prd_well.GetCurve('Oil Production Total (Hyperbolic Forecast) (User)').y
                
                opr_wor_group_forecast += prd_well.GetCurve('Oil Production Rate (WOR Forecast) (User)').y
                opt_wor_group_forecast += prd_well.GetCurve('Oil Production Total (WOR Forecast) (User)').y
                
                opr_wc_group_forecast += prd_well.GetCurve('Oil Production Rate (WC Forecast) (User)').y
                opt_wc_group_forecast += prd_well.GetCurve('Oil Production Total (WC Forecast) (User)').y
            
#             wor_group_forecast = 
#             wc_group_forecast = 
            
            group.AddCurve('Oil Production Rate (History)',  opr_history.x, opr_group_history, 'm3/d')
            group.AddCurve('Oil Production Total (History)',  opt_history.x, opt_group_history, 'm3')
            group.AddCurve('Water Production Rate (History)',  wpr_history.x, wpr_group_history, 'm3/d')
            
            group.AddCurve('Oil Production Rate (Exponential Forecast)', time_array , exp_group_forecast, 'm3/d')
            group.AddCurve('Oil Production Total (Exponential Forecast)', time_array , exp_group_forecast_ttl, 'm3')
            
            group.AddCurve('Oil Production Rate (Hyperbolic Forecast)', time_array , hyp_group_forecast, 'm3/d')
            group.AddCurve('Oil Production Total (Hyperbolic Forecast)', time_array , hyp_group_forecast_ttl, 'm3')
            
            group.AddCurve('Oil Production Rate (WOR Forecast)', time_array , opr_wor_group_forecast, 'm3/d')
            group.AddCurve('Oil Production Total (WOR Forecast)', time_array , opt_wor_group_forecast, 'm3')
#             group.AddCurve(u'Water Oil Ratio (WOR Forecast)', time_array, wor_group_forecast, 'm3/m3')
            
            group.AddCurve('Oil Production Rate (WC Forecast)', time_array , opr_wc_group_forecast, 'm3/d')
            group.AddCurve('Oil Production Total (WC Forecast)', time_array , opt_wc_group_forecast, 'm3')
#             group.AddCurve(u'Water Cut (WC Forecast)', time_array , wc_group_forecast, 'm3/m3')
