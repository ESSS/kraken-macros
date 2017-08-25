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
import mbalcore.mbal_functions as mbf
from mbalcore.average_pressure import pressure_drop, productivity_index, reservoir_pressure
from ben10.foundation import log
import numpy

#Getting production variables values
study = api.GetStudy()
field = study.GetField()
well_names = field.GetWellNames()

#Getting Producer Well list
producers = []

for well_name in well_names:
    well = field.GetWell(well_name).GetSubject().GetOutput(time_step_index=0)()
    if 1 in well.GetType(1):
        producers.append(well_name)

field_oil_prod_total = 0
#summing productions to Get Field Value
for prod_well in producers:
    well = field.GetWell(prod_well)
    oil_prod_total_curve = well.GetCurve('Oil Production Total')
    oil_prod_total = oil_prod_total_curve.y
    field_oil_prod_total = field_oil_prod_total + oil_prod_total[-1]

opt_curve = well.GetCurve("Oil Production Total")
Np = field_oil_prod_total
wpt_curve = field.GetCurve("Water Production Total")
Wp = wpt_curve.y
random_well = field.GetWell(producers[0])
rs_curve = random_well.GetCurve("Gas Oil Ratio")
Rs = rs_curve.y
wit_curve = field.GetCurve("Water Injection Total")
Winj = wit_curve.y
git_curve = field.GetCurve("Gas Injection Total")
Ginj = git_curve.y
result = show_mbal_dialog()

#Formation Total Volume Factor
Bti = result['Boi']
Bt = mbf.formation_total_volume_factor(result['Rsb'], Rs, result['Bo'], result['Bg'])

print "Bti = ", Bti
print "Bt = ", Bt
print "Rsi = ", result['Rsi']
print "Rsb = ", result['Rsb']
print "Bg = ", result['Bg']
print "Bw = ", result['Bw']
print "Bwinj = ", result['Bwinj']
print "Bginj = ", result['Bginj']

#Underground withdrawal
F, produced_oil, produced_water, injected_gas, injected_water = mbf.production_injection_balance(Np, Bt, Rs,
                                  result['Rsi'], result['Bg'], Wp,
                                  result['Bw'], Winj, result['Bwinj'],
                                  Ginj, result['Bginj'], result['We'])

print "F =", F
print "Produced Oil = ", produced_oil
print "Produced Water = ", produced_water
print "Injected Water = ", injected_water
print "Injected Gas = ", injected_gas

#Oil Expansion and dissolved gas
Eo = mbf.dissolved_oil_and_gas_expansion(Bt, Bti)
print "Eo = ", Eo

#Gas Cap Expansion
Eg = mbf.gas_cap_expansion(Bti, result['Bg'], result['Bgi'])
print "Eg = ", Eg

#Delta Pressure
deltaP = result['Pi'] - result['Pavg']

#Initial water expansion and reduction of the pore volume
Efw = mbf.pore_volume_reduction_connate_water_expansion(result['m'], result['Boi'], result['cw'], result['Swi'], result['cf'], deltaP)
print "Efw = ", Efw

#Water Influx
We = result['We']
print "We = ", We

#Oil in Place Volume
N = mbf.oil_in_place(F, Eo, result['m'], Eg, Efw, We)
field.AddCurve("Oil In Place (mbal)", opt_curve.GetTimeSet(), N, opt_curve.GetUnit())
#field.AddCurve("Dissolved oil and gas expansion", opt_curve.GetTimeSet(), Eo, "bbl/bbl")
field.AddCurve("Produced oil", opt_curve.GetTimeSet(), F, "<mult>")

#No inital gas cap and no water influx
N1 = mbf.oil_in_place_oil_gas_expansion(F, Eo)
field.AddCurve("Oil in Place (Oil and Gas Expansion)", opt_curve.GetTimeSet(), N1, opt_curve.GetUnit())

#Initial Gas Cap Reservoirs
N2 = mbf.oil_in_place_gas_cap(F, Eo, result['m'], Eg)
#field.AddCurve("Oil in Place (Gas Cap)", opt_curve.GetTimeSet(), N2, "bbl")

#Water Influx
N3 = mbf.oil_in_place_water_influx(F, We, Eo)
#field.AddCurve("Oil in Place (Water Influx)", opt_curve.GetTimeSet(), N3, "bbl")


#Average Reservoir Pressure
well_names = field.GetWellNames()

prod_wells = []

for prod_well_name in producers:
    prod_well = field.GetWell(prod_well_name)
    prod_wells.append(prod_well)
    opr_curve = prod_well.GetCurve('Oil Production Rate')
    opr = opr_curve.y
    BHP_curve = prod_well.GetCurve('Bottom-hole Pressure')
    BHP = BHP_curve.y

    DD = result['Pi'] - BHP
    prod_well.AddCurve("Drawdown", opr_curve.GetTimeSet(), DD, "bar")

    position = numpy.flatnonzero(opr)[0]
    OPR = opr[position]
    BHP_pressure = BHP[position]
    J = OPR/(result['Pi'] - BHP_pressure)

    Ps = BHP + (1/J)*opr
    prod_well.AddCurve("Static Pressure", opr_curve.GetTimeSet(), Ps, "bar")

print OPR
print BHP_pressure
print J


