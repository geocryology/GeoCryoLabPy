import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit

# read multiple V2/V1 data sets (in folder), collected from VNA using V21.py. V1 (V2) is voltage at input (output) terminal of cell
def readV21s(folder,files,V21s):
    for i in files:
        name=folder+i+'.csv'
        data = pd.read_csv(name,skiprows=13,header=None)
        df = pd.DataFrame(data)
        V21temp = df[df.columns[3]]
        V21temp = [complex(dummy) for dummy in V21temp]
        V21temp = np.real(V21temp)+1j*np.imag(V21temp)
        #V21s.append(V21temp)
        V21s.append(V21temp/(10**0.5))
    f = np.array(df[df.columns[0]])
    return f,V21s

# convert multiple V21 data sets to multiple data sets of Y-magnitude-inverse and B-inverse. R is current measurement resistor
def V21stoYmaginvsBinvs(V21s,R,Ymaginvs,Binvs):
    for V21 in V21s:
        Ytemp = 1/(R*(1/V21 - 1))
        Ymaginvs.append(1/np.abs(Ytemp))
        Binvs.append(1/np.imag(Ytemp))
    return Ymaginvs, Binvs

# fit multiple data sets to ideal capacitor's impedance magnitude function to find capacitance values (Cs) and fitted data sets
def Cfit(f,dats,Cs,fitdats,stafre):
    bnds=(0,np.inf)
    def Cimpmagfun(ff,C):
        return 1/(2*np.pi*ff*C*1e-12)
    for i in range(len(dats)):
        staind = np.argmin([np.abs(x-stafre[i]) for x in f])
        dat = dats[i]
        popt, pcov = curve_fit(Cimpmagfun,f[staind:],dat[staind:],bounds=bnds)
        Cs.append(popt[0]*1e-12)
        fitdats.append(1/(2*np.pi*f*popt[0]*1e-12))
    return Cs, fitdats

# generate loglog plot y vs. x. ylst contains multiple y-arrays
def lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,cou):
    h = range(len(ylst))
    for i in range(len(ylst)):
        h[i], = plt.loglog(x,ylst[i],'C'+`i`, label=lblst[i])
    plt.suptitle(hdg, fontsize=30)
    plt.xlabel(xlbl, fontsize=30)
    plt.ylabel(ylbl, fontsize=30)
    plt.tick_params(labeltop=True, top=True, labelright=True, right=True, which='both',labelsize=25)
    first_legend = plt.legend(handles=h[:cou], loc='upper right', fontsize=30, frameon=False)
    plt.gca().add_artist(first_legend)
    plt.legend(handles=h[cou:], loc='lower left', fontsize=30, frameon=False)
    plt.show()
