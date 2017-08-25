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
from mbalcore.average_pressure import delta_P, productivity_index, reservoir_pressure
import numpy as np

#Getting production variables values
study = api.GetStudy()
field = study.GetField()
well_names = field.GetWellNames()

#Getting Producer Well list
producers = []
injectors = []

if study.subject.GetFileType() == 'Excel Summary Reader results file':
    for well_name in well_names:
        well = field.GetWell(well_name)
        if 'Oil Production Rate' in well.GetCurveNames():
            producers.append(well_name)
        elif 'Water Injection Rate' in well.GetCurveNames():
            injectors.append(well_name)

else:
    for well_name in well_names:
        well = field.GetWell(well_name).GetSubject().GetOutput(time_step_index=0)()
        if 1 in well.GetType(1):
            producers.append(well_name)
        else:
            injectors.append(well_name)

#Create total curves from rates when necessary and add them to get Field Value
def get_field_accumulated_curve_from_wells_rates(well_list, rate_curve_name, total_curve_name):
    field_total = 0

    for well_name in well_list:
        well = field.GetWell(well_name)

        if total_curve_name in well.GetCurveNames():
            total_curve_array = well.GetCurve(total_curve_name).y
            field_total += total_curve_array

        else:
            rate_curve = well.GetCurve(rate_curve_name)
            delta_days = rate_curve.GetTimeSet().CalculateDeltasFromInitialDate(1)
            delta_days = np.ediff1d(delta_days, to_begin=0)
            total_curve_array = np.cumsum(delta_days * rate_curve.y)
            field_total += total_curve_array

    return field_total


field_oil_prod_total = get_field_accumulated_curve_from_wells_rates(producers,'Oil Production Rate', 'Oil Production Total')
field_water_prod_total = get_field_accumulated_curve_from_wells_rates(producers,'Water Production Rate', 'Water Production Total')
field_water_inj_total = get_field_accumulated_curve_from_wells_rates(injectors,'Water Injection Rate', 'Water Injection Total')
field_gas_injection_total = get_field_accumulated_curve_from_wells_rates(injectors,'Gas Injection Rate', 'Gas Injection Total')

random_well = field.GetWell(producers[0])
time_set = random_well.GetCurve('Oil Production Rate').GetTimeSet()

result = show_mbal_dialog()

#Formation Total Volume Factor
Bti = result['Boi']

if 'Gas Oil Ratio' in field.GetCurveNames():
    Rs = field.GetCurve('Gas Oil Ratio').y
elif 'Oil Production Rate' and 'Gas Production Rate' in field.GetCurveNames():
    Rs = field.GetCurve('Gas Production Rate').y / field.GetCurve('Oil Production Rate').y
    np.putmask(Rs, np.isnan(Rs), 0)
else:
    field_opr = 0
    field_gpr = 0

    for well_name in producers:
        well = field.GetWell(well_name)
        opr = well.GetCurve('Oil Production Rate').y
        gpr = well.GetCurve('Gas Production Rate').y
        field_opr += opr
        field_gpr += gpr

    Rs = field_gpr / field_opr
    np.putmask(Rs, np.isnan(Rs), 0)

Bt = mbf.formation_total_volume_factor(result['Bo'], result['Bg'], result['Rsb'], Rs)
print 'Bt = ', Bt

#Underground withdrawal
F, produced_oil, produced_water, injected_gas, injected_water = mbf.production_injection_balance(field_oil_prod_total, Bt, Rs,
                                  result['Rsi'], result['Bg'], field_water_prod_total,
                                  result['Bw'], field_water_inj_total, result['Bwinj'], field_gas_injection_total, result['Bginj'], result['We'])

print "F =", F[-1]
# print "Produced Oil = ", produced_oil
# print "Produced Water = ", produced_water
# print "Injected Water = ", injected_water
# print "Injected Gas = ", injected_gas

#Oil Expansion and dissolved gas
Eo = mbf.dissolved_oil_and_gas_expansion(Bt, Bti)
print "Eo = ", Eo

#Gas Cap Expansion
Eg = mbf.gas_cap_expansion(Bti, result['Bg'], result['Bgi'])
print "Eg = ", Eg

#Initial water expansion and reduction of the pore volume
Efw = mbf.pore_volume_reduction_connate_water_expansion(result['m'], result['Boi'], result['cw'], result['Swi'], result['cf'], result['deltaP'])
print "Efw = ", Efw

#Water Influx
We = result['We']
print "We = ", We

#Oil in Place Volume
N = mbf.oil_in_place(F, Eo, result['m'], Eg, Efw, We)
print 'N = ', N[-1]

field.AddCurve("Oil In Place (mbal)", time_set, N, 'm3')
#field.AddCurve("Dissolved oil and gas expansion", opt_curve.GetTimeSet(), Eo, "bbl/bbl")
field.AddCurve("F", time_set, F, 'm3')
field.AddCurve("Produced Oil (Mbal)", time_set, produced_oil, 'm3')
field.AddCurve("Produced Water (Mbal)", time_set, produced_water, 'm3')
field.AddCurve("Injected Water (Mbal)", time_set, injected_water, 'm3')
field.AddCurve("Bt", time_set, Bt, 'bbl/bbl')
field.AddCurve("Eo", time_set, Eo, 'bbl/bbl')


#No inital gas cap and no water influx
N1 = mbf.oil_in_place_modified(F, Eo)
field.AddCurve("Oil in Place Modified", time_set, N1, 'm3')


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

    position = np.flatnonzero(opr)[0]
    OPR = opr[position]
    BHP_pressure = BHP[position]
    J = OPR/(result['Pi'] - BHP_pressure)

    Ps = BHP + (1/J)*opr
    prod_well.AddCurve("Static Pressure", opr_curve.GetTimeSet(), Ps, "bar")