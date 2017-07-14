'''
Name for generated for macro: Material Balance

Perform Material Balance Calculations
Oil in place volume
Generate plots with the results
Created on 14 de jul de 2017

@author: ebio
'''
from mbalcore.mbalui import show_mbal_dialog
from mbalcore.mbal_functions import oil_in_place, production_injection_balance, formation_total_volume_factor, dissolved_oil_and_gas_expansion, gas_cap_expansion, pore_volume_reduction_connate_water_expansion

study = api.GetStudy()
field = study.GetField()
opt_curve = field.GetCurve("Oil Production Total")
opt = opt_curve.y
wpt = field.GetCurve("Water Production Total").y
rs = field.GetCurve("Gas Oil Ratio").y
wit = field.GetCurve("Water Injection Total").y
git = field.GetCurve("Gas Injection Total").y
result = show_mbal_dialog()

FTVF = formation_total_volume_factor(result['Bo'], result['Bg'], result['Rs'], result['Rsi'])

F = production_injection_balance(opt, result['Bt'], rs, 
                                 result['Rsi'], result['Bg'], wpt, 
                                 result['Bw'], wit, result['Bwinj'], 
                                 git, result['Bginj'])

Eo = dissolved_oil_and_gas_expansion(result['Bt'], FTVF)
Eg = gas_cap_expansion(result['Bg'], result['Bgi'], FTVF)
Efw = pore_volume_reduction_connate_water_expansion(result['m'], result['Boi'], result['cf'], result['cw'], result['Swi'], result['deltaP'])
N = oil_in_place(F, Eo, result['m'], Eg, Efw, We = 0)

field.AddCurve("Oil In Place (mbal)", opt_curve.GetTimeSet(), N, opt_curve.GetUnit())


#ctrl+b envia a macro ro Kraken