import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit

# read multiple V2/V1 data sets (in folder), collected from VNA using V21.py. V1 (V2) is voltage at input (output) terminal of cell
def readV21s(folder,files):
    V21s = []
    for i in files:
        name=folder+i+'.csv'
        data = pd.read_csv(name,skiprows=13,header=None)
        df = pd.DataFrame(data)
        V21temp = df[df.columns[3]]
        V21temp = [complex(dummy) for dummy in V21temp]
        V21s.append(np.real(V21temp)+1j*np.imag(V21temp))
    f = np.array(df[df.columns[0]])
    return f,V21s

# convert multiple V21 data sets to multiple impedance data sets. R is current measurement resistor
def V21stoZs(V21s,R):
    return R*(1/V21s - 1)

# convert multiple V21 data sets to multiple admittance data sets. R is current measurement resistor
def V21stoYs(V21s,R):
    return 1/(R*(1/V21s - 1))

def CfitImpMag(f,Zmag):
    eps0 = 8.854e-12
    def Zmagfun(ff,K):
        return 1/(2*np.pi*ff*eps0*K)
    bnds=(0,100)
    popt, pcov = curve_fit(Zmagfit,f,Zmag,bounds=bnds)
    K = popt[0]
    C = eps0*K
    Zmagfit = 1/(2*np.pi*f*C)
    return C, Zmagfit

# generate loglog plot y vs. x. ylst contains multiple y-arrays
def lglgplt(hdg,xlbl,ylbl,x,ylst,lblst):
    fig = plt.figure()
    for i in range(len(ylst)):
        plt.loglog(x,ylst[i],'C'+`i`, label=lblst[i])
    fig.suptitle(hdg, fontsize=30)
    plt.xlabel(xlbl, fontsize=30)
    plt.ylabel(ylbl, fontsize=30)
    plt.tick_params(labeltop=True, top=True, labelright=True, right=True, which='both',labelsize=25)
    plt.legend(loc='best', fontsize=30)
    plt.show()
