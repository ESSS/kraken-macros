'''
Name for generated for macro: Material Balance

Commands Description for Macro: 
Perform Material Balance Calculations
Oil in place volume
Generate plots with the results

@author: ebio
'''

from __future__ import unicode_literals
from mbalcore.mbalui import show_mbal_dialog
from mbalcore.mbal_functions import oil_in_place, production_injection_balance, formation_total_volume_factor, dissolved_oil_and_gas_expansion, gas_cap_expansion, pore_volume_reduction_connate_water_expansion
from mbalcore.average_pressure import delta_P, productivity_index, reservoir_pressure 
from ben10.foundation import log

#Getting production variables values
study = api.GetStudy()
field = study.GetField()
opt_curve = field.GetCurve("Oil Production Total")
opt = opt_curve.y
wpt_curve = field.GetCurve("Water Production Total")
wpt = wpt_curve.y
rs_curve = field.GetCurve("Gas Oil Ratio")
rs = rs_curve.y
wit_curve = field.GetCurve("Water Injection Total")
wit = wit_curve.y
git_curve = field.GetCurve("Gas Injection Total")
git = git_curve.y
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

#log.Info("Eo = '{}'".format(Eo))

field.AddCurve("Oil In Place (mbal)", opt_curve.GetTimeSet(), N, opt_curve.GetUnit())
#field.AddCurve("Dissolved oil and gas expansion", opt_curve.GetTimeSet(), Eo, "bbl/scf")

#Average Reservoir Pressure
well_names = field.GetWellNames()
producers = field.GetProducerWellNames()

# for well_name in well_names:
#         well = api.GetProd(well_name)
#         if 'Oil Production Rate' in well.GetCurveNames():
#             producers.append(well)
#         if 'Bottom Hole Pressure' in well.GetCurveNames():
#             producers.append(well)
            
for prod_well_name in producers:
    #prod_wells = []          
    prod_well = field.GetWell(prod_well_name)
    #prod_wells.append(prod_well)
    opr_curve = prod_well.GetCurve('Oil Production Rate')
    opr = opr_curve.y
    BHP_curve = prod_well.GetCurve('Bottom-hole Pressure')
    BHP = BHP_curve.y
    DD = result['Pi'] - BHP
print DD

J = opr/DD
print J

#Ps = BHP + opr/J
#print Ps

prod_wells.AddCurve("Productivity Index", opr_curve.GetTimeSet(), J, " ")

