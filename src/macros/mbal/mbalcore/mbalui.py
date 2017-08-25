# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 10:24:55 2017

@author: ebio
"""
import PyQt5
from formlayout import fedit

def pvt_datalist():
    return [('B<sub>oi</sub>', 1.35),
            ('B<sub>gi</sub>', 0.001),
            ('B<sub>o</sub>', 1.3),
            ('B<sub>g</sub>', 0.0001),
            ('B<sub>w</sub>', 1.008),
            ('B<sub>winj<\sub>', 1.008),
            ('B<sub>ginj<\sub>', 0.0001),
            ('R<sub>si</sub>', 120.0),
            ('R<sub>sb</sub>', 110.0),
            ('P<sub>i</sub> (psi)', 4000.0),
            ('Average Pressure (psi)', 2000.0),
            ]

def drive_mechanisms_datalist():
    return [('Gas Cap', True),
            ('m', 0.33),
            (None, None),
            ('Water Influx', True),
            ('W<sub>e<\sub> (bbl)', 0.0),
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
        (drive_mechanisms_datalist(), "Drive Mechanisms", "")
            ]
    dialog_result = fedit(mbal_params, "Material Balance", "")
    result = {}

    result['Boi'] = dialog_result[0][0] 
    result['Bgi'] = dialog_result[0][1]
    result['Bo'] = dialog_result[0][2]
    result['Bg'] = dialog_result[0][3]
    result['Bw'] = dialog_result[0][4]
    result['Bwinj'] = dialog_result[0][5]
    result['Bginj'] = dialog_result[0][6]
    result['Rsi'] = dialog_result[0][7]
    result['Rsb'] = dialog_result[0][8]
    result['Pi'] = dialog_result[0][9]
    result['Average Pressure'] = dialog_result[0][10]
    
    result['GasCap'] = dialog_result[1][0]
    result['m'] = dialog_result[1][1]
    result['WaterInflux'] = dialog_result[1][2]
    result['We'] = dialog_result[1][3]
    result['PoreVolumereductionandConnateWaterexpansion'] = dialog_result[1][4]
    result['cw'] = dialog_result[1][5]
    result['cf'] = dialog_result[1][6]
    result['Swi'] = dialog_result[1][7]
    result['deltaP'] = dialog_result[1][8]
    
    return result
    
