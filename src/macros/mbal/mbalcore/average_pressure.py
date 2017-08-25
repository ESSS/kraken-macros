'''
Created on 19 de jul de 2017

@author: ebio
'''
import numpy as np

def pressure_drop(Pi, BHP):
    delta_Pressure = Pi - BHP
    return delta_Pressure

def productivity_index(opr, deltaP):
    J = opr/deltaP
    return J 

def reservoir_pressure(BHP, opr, J):
    Ps = BHP + opr/J
    return Ps
