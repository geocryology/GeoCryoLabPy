import numpy as np

skp_rws = 13 # skp_rws is rows to skip at beginning of file
V21_indx = 3 # V21_indx is column where V2/V1 data is in file
f_indx = 0 # f_indx is column where frequency data is in file
V21s = [] # V21s is matrix into which V2/V1 arrays are written
f = [] # f is array into which frequency values are written

from funs import read_V21s
folder = 'VNAdata/cell1/' # folder from where files need to be read
files = ['noprowat','twoprowat'] # filenames to be read (no need to mention .csv extention)
V21s = read_V21s(folder,files,V21s,skp_rws,V21_indx)
folder = 'VNAdata/cell2/d5mm/'
files = ['air','wat']
V21s = read_V21s(folder,files,V21s,skp_rws,V21_indx)
folder = 'VNAdata/cell2/d2mm/'
files = ['air','wat']
V21s = read_V21s(folder,files,V21s,skp_rws,V21_indx)
file = folder+files[0]+'.csv'
from funs import read_f
f = read_f(file,skp_rws,f_indx)

f = np.array(f)
V21s = np.array(V21s)

Att2 = np.float(20) # attenuation at receiver port-B of VNA
Att1 = np.float(30) # attenuation at receiver port-R of VNA
R = 1e3 # current measurement resistor value
V21s = V21s*(10**((Att2-Att1)/20)) # V2/V1 values compensated to take into account attenuation at VNA receiver ports
Ys = 1/(R*(1/V21s - 1)) # Ys is matrix of admittance values corresponding to V21s matrix
Ymaginvs = 1/np.abs(Ys)
Binvs = 1/np.imag(Ys)

# Binvs data is fit to ideal capacitor data
from funs import Cfit
Cs = []
Binvfits = []
stafre = [1e5,1e3,0,1e3,0,1e3]
Cs, Binvfits = Cfit(f,Binvs,Cs,Binvfits,stafre)

print Cs, len(Binvfits) # Cs has fitted capacitance values corresponding to Binvs data

# generate loglog plot y vs. x using lglgplt
# ylst can contain multiple y data arrays
# lglgplt accepts legends in two locations
# h_lgnd_1 specifies number of labels in location-1 legend
# lblst is array of all labels for legend(s)

hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
lblst = ['$|Y|^{-1}$ without active probes','$|Y|^{-1}$ with active probes','$B^{-1}$ without active probes','$B^{-1}$ with active probes','ideal capacitor','ideal capacitor']
xlbl = '$f$ / $Hz$'
ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
x = f
ylst = Ymaginvs[0:2]
h_lgnd_1 = len(ylst)
ylst = np.concatenate((ylst,Binvs[0:2],Binvfits[0:2]))
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,h_lgnd_1)

hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
lblst = ['$|Y|^{-1}$ with air (data)','$|Y|^{-1}$ with $7 \mu S/m$ water (data)','$B^{-1}$ with air (data)','$B^{-1}$ with $7 \mu S/m$ water (data)','ideal capacitor','ideal capacitor','DI water (expected)','DI water (20% error)','DI water (20% error)']
xlbl = '$f$ / $Hz$'
ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
x = f
ylst = Ymaginvs[2:4]
h_lgnd_1 = len(ylst)
ylst = np.concatenate((ylst,Binvs[2:4],Binvfits[2:4],[Binvfits[2]/78,0.8*Binvfits[2]/78,1.2*Binvfits[2]/78]))
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,h_lgnd_1)

hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
lblst = ['$|Y|^{-1}$ with air (data)','$|Y|^{-1}$ with $7 \mu S/m$ water (data)','$B^{-1}$ with air (data)','$B^{-1}$ with $7 \mu S/m$ water (data)','ideal capacitor','ideal capacitor','DI water (expected)','DI water (20% error)','DI water (20% error)']
xlbl = '$f$ / $Hz$'
ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
x = f
ylst = Ymaginvs[4:6]
h_lgnd_1 = len(ylst)
ylst = np.concatenate((ylst,Binvs[4:6],Binvfits[4:6],[Binvfits[4]/78,0.8*Binvfits[4]/78,1.2*Binvfits[4]/78]))
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,h_lgnd_1)

# Similar to above code, for reading and plotting resistor data
skp_rws = 11
V21_indx = 2
f_indx = 0
V21s = []
f = []
folder = 'VNAdata/resistors/'
files = ['100ohm','1kohm','10kohm','100kohm','1Mohm']
V21s = read_V21s(folder,files,V21s,skp_rws,V21_indx)
file = folder+files[0]+'.csv'
f = read_f(file,skp_rws,f_indx)
f = np.array(f)
V21s = np.array(V21s)
Zmags = np.abs( R*(1/V21s - 1) )
hdg = 'Carbon resistors: impedance ($Z$) vs. frequency ($f$)'
lblst = ['$1M\Omega$','$100k\Omega$','$10k\Omega$','$1k\Omega$','$100\Omega$']
xlbl = '$f$ / $Hz$'
ylbl = '$|Z|$ / $\Omega$'
x = f
ylst = Zmags
h_lgnd_1 = len(ylst)
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,h_lgnd_1)
