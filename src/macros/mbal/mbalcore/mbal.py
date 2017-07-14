# -*- coding: utf-8 -*-
"""
Spyder Editor

Este é um arquivo de script temporário.
"""
import numpy as np
import mbal_functions as mbalf

#Material Balance
ts =  np.array([30, 60, 90, 120])
Np =  np.array([100, 150, 200, 300])
Wp =  np.array([5,25,40,50])
Winj = np.array([2,10,20,30])
Ginj = np.array([0.5,2,3,4])
Rs = 14
Rsi = 1
Bg = 0.00025
Bw = 1.038
Bwinj = 1.05
Bginj = 0.002
Bgi = 0.0052
Boi= 1.9
cw = 0.0000467
cf = 0.0000484
Swi = 0.15
m = 0.33
P = 100 
Pi = 5000
Bo = 1.1


Bt = mbalf.formation_total_volume_factor(Bo, Rs, Rsi, Bg)
Bti = mbalf.formation_total_volume_factor(Boi,Rs, Rsi,Bgi)
Eo = mbalf.dissolved_oil_and_gas_expansion(Bt,Bti)
Eg = mbalf.gas_cap_expansion(Bti, Bg, Bgi)
F = mbalf.production_injection_balance(Np, Bt, Rs, Rsi, Bg, Wp, Bw, Winj, Bwinj, Ginj, Bginj)
Efw = mbalf.pore_volume_reduction_connate_water_expansion(m, Boi, cw, Swi, cf)

print("Eg =", Eg)
print("Eo =", Eo)
print("F = ", F)

deltaP = (P-Pi) 


print("Efw =", Efw)

We = 2 #bbl/d/psi
#Linearized equation

N = mbalf.oil_in_place(F, Eo, m,Eg,Efw,We)

print("N =", N)





