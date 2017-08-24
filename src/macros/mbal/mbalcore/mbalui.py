# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 10:24:55 2017

@author: ebio
"""
import PyQt5
from formlayout import fedit

def pvt_datalist():
    return [('B<sub>oi</sub>', 1.8),
            ('R<sub>si</sub>', 14.0),
            ('B<sub>gi</sub>', 0.058),
            ('P<sub>i</sub> (psi)', 4000.0 ),
            ('B<sub>o</sub>', 1.2),
            ('B<sub>g</sub>', 0.0032),
            ('B<sub>w</sub>', 1.04),
            ('B<sub>t</sub>', 2.05 ),
            ('R<sub>sb</sub>', 16.0),
            ('Average Pressure (psi)', 2000.0),
            ]
    
def production_injection_datalist():
    return [('N<sub>p<\sub> (bbl)', 12000000.0),
            ('W<sub>p<\sub> (bbl)', 11600000.0),
            ('G<sub>p<\sub> (scf)', 1000.0),
            (None, None),
            (None, 'Injection Data:'),
            ('W<sub>inj<\sub> (bbl)', 1100000.0),
            ('B<sub>winj<\sub>', 1.03),
            ('G<sub>inj<\sub> (bbl)', 200.0),
            ('B<sub>ginj<\sub>', 0.002)
            ]
    
def drive_mechanisms_datalist():
    return [('Gas Cap', True),
            ('m', 0.33),
            (None, None),
            ('Water Influx', True),
            ('W<sub>e<\sub> (bbl)', 1000000.0),
            (None, None),
            ('Pore Volume reduction and Connate Water expansion', True),
            ('c<sub>w<\sub> (psi<sup>-1</sup>)', 0.0000467),
            ('c<sub>f<\sub> (psi<sup>-1</sup>)', 0.0000484),
            ('S<sub>wi<\sub>',0.15),
            ('deltaP (psi)', 2000.0),
            ]
            
def show_mbal_dialog():
    mbal_params = [
        (pvt_datalist(), "PVT", "Insert PVT Data: "),
        (production_injection_datalist(), "Production and Injection", "Insert Production/Injection Data: "),
        (drive_mechanisms_datalist(), "Drive Mechanisms", "")
            ]
    dialog_result = fedit(mbal_params, "Material Balance", "")
    result = {}

    result['Boi'] = dialog_result[0][0] 
    result['Rsi'] = dialog_result[0][1]
    result['Bgi'] = dialog_result[0][2]
    result['Pi'] = dialog_result[0][3]
    result['Bo'] = dialog_result[0][4]
    result['Bg'] = dialog_result[0][5]
    result['Bw'] = dialog_result[0][6]
    result['Bt'] = dialog_result[0][7]
    result['Rsb'] = dialog_result[0][8]
    result['Average Pressure'] = dialog_result[0][9]

    result['Np'] = dialog_result[1][0]
    result['Wp'] = dialog_result[1][1]
    result['Gp'] = dialog_result[1][2]
    result['Winj'] = dialog_result[1][3]
    result['Bwinj'] = dialog_result[1][4]
    result['Ginj'] = dialog_result[1][5]
    result['Bginj'] = dialog_result[1][6]
    
    result['GasCap'] = dialog_result[2][0]
    result['m'] = dialog_result[2][1]
    result['WaterInflux'] = dialog_result[2][2]
    result['We'] = dialog_result[2][3]
    result['PoreVolumereductionandConnateWaterexpansion'] = dialog_result[2][4]
    result['cw'] = dialog_result[2][5]
    result['cf'] = dialog_result[2][6]
    result['Swi'] = dialog_result[2][7]
    result['deltaP'] = dialog_result[2][8]
    
    return result
    
