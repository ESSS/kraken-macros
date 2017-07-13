from __future__ import unicode_literals
from formlayout import fedit


def show_curve_coeffs_dialog(exp_params, wcut_params, wor_params, apply_callback):
    forecast_ui_params = [
        (None, "Exponential and Hyperbolic Forecasts"),
        ("Decline Rate", exp_params),

        (None, "Water Cut Forecast"),
        ("Slope", wcut_params[0]),
        ("Intercept", wcut_params[1]),

        (None, "Water Oil Ratio Forecast"),
        ("Slope", wor_params[0]),
        ("Intercept", wor_params[1]),
    ]

    return fedit(forecast_ui_params, title="Decline Curve Coefficients", apply=apply_callback)
