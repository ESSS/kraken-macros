'''
Created on 19 de jul de 2017

@author: ebio
'''
import numpy as np

def delta_P(Pi, BHP):
    deltaP = Pi - BHP
    return deltaP

def productivity_index(opr, deltaP):
    J = opr/deltaP
    return J 

def reservoir_pressure(BHP, opr, J):
    Ps = BHP + opr/J
    return Ps
