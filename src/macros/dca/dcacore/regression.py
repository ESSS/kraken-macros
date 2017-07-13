'''
Created on 5 de out de 2015

@author: viniciusgs
'''
# Import an utility package for manipulating rate curves
from __future__ import unicode_literals
import numpy as np
from scipy.optimize import curve_fit
import bisect
from scipy import stats


def ExponentialFit(time_array_in_years, opr_history):
    bissection = SmartIntervalSearcher(opr_history)
    x = time_array_in_years[bissection:]
    y = opr_history.y[bissection:]
    curve_fit_model = lambda x, a, b: a * np.exp(-b * x)
    popt, pcov = curve_fit(curve_fit_model, x, y)
    return popt[1]


def WCFitCoeff(wcut, opt):

    if np.sum(wcut) < 0.01:
        slope = 0
        intercept = 0
    else:
        water_break_index = np.argwhere(wcut > 0)[0, 0] # Get the first position where WOR is > 0
        new_wc, new_opt = np.array(wcut[water_break_index:]), np.array(opt[water_break_index:]) * 0.0062898
        slope, intercept, r_value, p_value, slope_std_error = stats.linregress(new_opt, new_wc)

        if r_value < 0.99:
            ratio = float(len(new_wc)) / float(len(wcut))

            if ratio > 0.1:

                if ratio/2 > 0.1:
                    ration2_index = water_break_index + int(len(new_wc)/2)
                    new_wc, new_opt = np.array(wcut[ration2_index:]), np.array(opt[ration2_index:]) * 0.0062898
                    slope, intercept, r_value, p_value, slope_std_error = stats.linregress(new_opt, new_wc)

                    if r_value < 0.99:
                        r90_index = int(0.9 * len(wcut))
                        new_wc, new_opt = np.array(wcut[r90_index:]), np.array(opt[r90_index:]) * 0.0062898
                        slope, intercept, r_value, p_value, slope_std_error = stats.linregress(new_opt, new_wc)

    return slope, intercept


def WORFitCoeff(wor, opt):
    if np.sum(wor) < 0.01:
        popt = np.array([0.0, 0.0])

    else:
        position = np.argwhere(wor > 0)[0,0] # Get the first position where WOR is > 0
        opt_cut = np.array(opt[position:]) * 0.0062898
        wor_cut = np.array(wor[position:])
        wor_log = np.log10(wor_cut)
        wor_log_derivative = np.zeros(len(wor_log)-1)

        for i in xrange(len(wor_log_derivative)):
            wor_log_derivative[i] =  (wor_log[i+1] - wor_log[i]) / (opt_cut[i+1] - opt_cut[i])

        curve_average = np.average(wor_log_derivative)
        curve_std_deviation = np.std(wor_log_derivative)

        first_cut_position = 0
        if curve_std_deviation > 0.2*curve_average:

            first_cut_position = int(len(wor_log_derivative)/2)
            wor_log_derivative = wor_log_derivative[first_cut_position:]
            curve_average = np.average(wor_log_derivative)
            curve_std_deviation = np.std(wor_log_derivative)

        second_cut_position = 0
        if curve_std_deviation > 0.2*curve_average and len(wor_log_derivative) > 0.2*len(wor_log):
            second_cut_position = int(len(wor_log_derivative)/2)
            wor_log_derivative = wor_log_derivative[second_cut_position:]
            curve_average = np.average(wor_log_derivative)
            curve_std_deviation = np.std(wor_log_derivative)

        final_position = first_cut_position + second_cut_position

        new_opt = opt_cut[final_position:]
        new_wor = wor_log[final_position:]

        curve_fit_model = lambda x,a,b: a * x + b
        popt, pcov = curve_fit(curve_fit_model, new_opt, new_wor)

    return popt.tolist()


def SmartIntervalSearcher(curve_to_be_analysed):
    new_x_axis = np.empty(len(curve_to_be_analysed.x), dtype = np.datetime64('2015-01-01'))
    derivative = np.zeros(len(curve_to_be_analysed.x))

    for i,data in enumerate(curve_to_be_analysed.x):
        new_x_axis[i] = np.datetime64(data.date)

    if len(curve_to_be_analysed.x) > 20:
        for i in xrange(len(curve_to_be_analysed)-1):
            delta = (new_x_axis[i+1] - new_x_axis[i]) / np.timedelta64(1,'D')
            derivative[i] = (curve_to_be_analysed.y[i+1] - curve_to_be_analysed.y[i]) / delta

        position = 0
        for i in xrange(len(derivative)):
            if derivative[-2-i] < 0:
                pass
            else:
                position = len(derivative) - i + 2
                break

        if position > 0.9*len(curve_to_be_analysed.x):
            if int(0.9*len(curve_to_be_analysed.x)) < 20:
                position = len(curve_to_be_analysed.x) - 20
            else:
                position = int(0.9*len(curve_to_be_analysed.x))
    else:
        position = 0

    return position
