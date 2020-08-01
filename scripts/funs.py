import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit

# read multiple V2/V1 data sets (in folder), collected from VNA using Agi4395A_V21.py. V1 (V2) is voltage at input (output) terminal of cell
def read_V21s(folder,files,V21s,skp_rws,V21_indx):
    for i in files:
        name=folder+i+'.csv'
        data = pd.read_csv(name,skiprows=skp_rws,header=None)
        df = pd.DataFrame(data)
        V21temp = df[df.columns[V21_indx]]
        V21temp = [complex(dummy) for dummy in V21temp]
        V21temp = np.real(V21temp)+1j*np.imag(V21temp)
        V21s.append(V21temp)
    return V21s

# read frequency (f) array associated with V2/V1 data array
def read_f(name,skp_rws,f_indx):
    data = pd.read_csv(name,skiprows=skp_rws,header=None)
    df = pd.DataFrame(data)
    f = df[df.columns[f_indx]]
    return f

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

# generate loglog plot y vs. x using lglgplt
# ylst can contain multiple y data arrays
# lglgplt accepts legends in two locations
# h_lgnd_1 specifies number of labels in location-1 legend
# lblst is array of all labels for legend(s)
def lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,h_lgnd_1):
    if len(ylst.shape) == 1:
        h_lgnd_1_2 = 1
        h = plt.loglog(x,ylst,'C0', label=lblst[0])
    elif len(ylst.shape) > 1:
        h_lgnd_1_2 = len(ylst)
        h = range(h_lgnd_1_2)
        for i in range(h_lgnd_1_2):
            h[i], = plt.loglog(x,ylst[i],'C'+`i`, label=lblst[i])
    plt.suptitle(hdg, fontsize=30)
    plt.xlabel(xlbl, fontsize=30)
    plt.ylabel(ylbl, fontsize=30)
    plt.tick_params(labeltop=True, top=True, labelright=True, right=True, which='both',labelsize=25)
    first_legend = plt.legend(handles=h[:h_lgnd_1], loc='upper right', fontsize=30, frameon=False)
    plt.gca().add_artist(first_legend)
    if h_lgnd_1 < h_lgnd_1_2:
        plt.legend(handles=h[h_lgnd_1:], loc='lower left', fontsize=30, frameon=False)
    plt.show()
