
import os
import numpy as np
from dca.dcacore import regression


def test_regression():
    data_dir = os.path.dirname(__file__)
    sample_filename = os.path.join(data_dir, 'hercilio-well.csv')
    ts, wpr, opr, opt = np.genfromtxt(sample_filename, delimiter=b";", skip_header=4, filling_values=0, unpack=True)

    wor = wpr / opr
    wcut = wpr / (wpr + opr)

    slope, intercept = regression.WCFitCoeff(wcut, opt)
    assert round(slope, 8) == 3.3978e-4
    assert round(intercept, 5) == -0.01859

    popt = regression.WORFitCoeff(wor, opt)
    assert round(popt[0], 6) == 0.000652
    assert round(popt[1], 6) == -0.968265
