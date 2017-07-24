# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 09:42:17 2017

@author: ebio
"""

def formation_total_volume_factor(Bo, Bg, Rs, Rsi):
    
    if Rs == Rsi:
        Bti = Bo
    else:
        Bti = Bo + Bg*(Rs - Rsi)
       
    return Bti 

def production_injection_balance(Np, Bt, Rs, Rsi, Bg, Wp, Bw, Winj, Bwinj, Ginj, Bginj):
    
    F = Np * (Bt + (Rs - Rsi)*Bg)+ Wp*Bw - Winj*Bwinj - Ginj*Bginj
    
    return F

def dissolved_oil_and_gas_expansion(Bt,Bti):
    
    Eo = Bt-Bti
    
    return Eo

def gas_cap_expansion(Bti, Bg, Bgi):
    
    Eg = Bti*((Bg/Bgi)-1)
    
    return Eg

def delta_P(Pi, BHP):
    
    deltaP = Pi - BHP
    
    return deltaP

def pore_volume_reduction_connate_water_expansion(m , Boi, cw, Swi, cf, deltaP):
    
    Efw = (1.0 + m)*Boi*((cw*Swi+cf)/(1.0-Swi))*deltaP
    
    return Efw

def oil_in_place(F, Eo, m, Eg, Efw, We):
    
    oil_in_place = F/(Eo + m*Eg + Efw) + We
    
    return oil_in_place