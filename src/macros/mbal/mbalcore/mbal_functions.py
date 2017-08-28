# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 09:42:17 2017

@author: ebio
"""
import numpy as np

def formation_total_volume_factor(Bo, Bg, Rsb, Rs):

    return np.where(Rs >= Rsb, Bo, Bo + Bg*(Rsb - Rs))

'''
 DOCUMENTACAO
'''
def production_injection_balance(Np, Bt, Rs, Rsi, Bg, Wp, Bw, Winj, Bwinj, Ginj, Bginj, We):

    produced_oil = (Np * (Bt + (Rs - Rsi) * Bg))
    produced_water = Wp * Bw
    injected_water = Winj * Bwinj
    injected_gas = Ginj * Bginj
    water_influx = We

    F = (produced_oil + produced_water - injected_water - injected_gas + water_influx)
    
    return F, produced_oil, produced_water, injected_gas, injected_water

def dissolved_oil_and_gas_expansion(Bt, Bti):
    
    Eo = (Bt - Bti)
    
    return Eo

def gas_cap_expansion(Bti, Bg, Bgi):
    
    Eg = ((Bti)*((Bg/Bgi) - 1))
    
    return Eg

def deltaP(Pi, Pavg):
    
    deltaP = Pi - Pavg
    
    return deltaP

def pore_volume_reduction_connate_water_expansion(m , Boi, cw, Swi, cf, deltaP):
    
    Efw = (1.0 + m)*Boi*((cw*Swi+cf)/(1.0-Swi))*deltaP
    
    return Efw

def oil_in_place(F, We, Eo, m, Eg, Efw):
    
    oil_in_place = (F - We)/(Eo + m*Eg + Efw)
    
    return oil_in_place

def oil_in_place_underg_withdrawal(F, Eo):

    oil_in_place_underg_withdrawal = F/Eo


    return oil_in_place_underg_withdrawal

def oil_in_place_gas_cap(F, Eo, m, Eg):

    oil_in_place_gas_cap = F/(Eo + m*Eg)

def oil_in_place_water_influx (F, We, Eo):

    oil_in_place_water_influx = (F - We)/Eo

    return oil_in_place_water_influx