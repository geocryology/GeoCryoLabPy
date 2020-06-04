from funs import readV21s
folder = 'data/cell1/' # folder from where files need to be read
files = ['noprowat','twoprowat'] # filenames to be read (no need to mention .csv extention)
V21s = []
f, V21s =  readV21s(folder,files,V21s)
folder = 'data/cell2/d5mm/' # folder from where files need to be read
files = ['air','wat'] # filenames to be read (no need to mention .csv extention)
f, V21s =  readV21s(folder,files,V21s)
folder = 'data/cell2/d2mm/' # folder from where files need to be read
files = ['air','wat'] # filenames to be read (no need to mention .csv extention)
f, V21s =  readV21s(folder,files,V21s)

# folder = 'data/cell1modified/' # folder from where files need to be read
# files = ['air','DIwater'] # filenames to be read (no need to mention .csv extention)
# fr, V21s =  readV21s(folder,files,V21s)
#
# folder = 'data/resistors/' # folder from where files need to be read
# files = ['8Mohm','1Mohm','100kohm','10kohm','1kohm','100ohm','10ohm'] # filenames to be read (no need to mention .csv extention)
# fr, V21s =  readV21s(folder,files,V21s)
#
import numpy as np
from matplotlib import pyplot as plt
plt.loglog(f,np.real((1e3*(1/V21s[2] - 1))),'k')
plt.loglog(f,np.real((1e3*(1/V21s[3] - 1))),'b')
plt.show()
#
# # plt.figure(1)
# # #plt.loglog(f,np.abs((1e3*(1/V21s[8] - 1))),'k',label='$8 M \Omega$')
# # plt.loglog(fr,np.abs((1e3*(1/V21s[9] - 1))),'r',label='$1 M \Omega$')
# # plt.loglog(fr,np.abs((1e3*(1/V21s[10] - 1))),'b',label='$100 k \Omega$')
# # plt.loglog(fr,np.abs((1e3*(1/V21s[11] - 1))),'g',label='$10 k \Omega$')
# # plt.loglog(fr,np.abs((1e3*(1/V21s[12] - 1))),'k',label='$1 k \Omega$')
# # plt.loglog(fr,np.abs((1e3*(1/V21s[13] - 1))),'m',label='$100 \Omega$')
# # #plt.loglog(f,np.abs((1e3*(1/V21s[14] - 1))),'m',label='$10 \Omega$')
# # plt.suptitle('Carbon resistors: impedance ($Z$) vs. frequency ($f$)', fontsize=30)
# # plt.xlabel('$f$ / $Hz$', fontsize=30)
# # plt.ylabel('$|Z|$ / $\Omega$', fontsize=30)
# # plt.tick_params(labeltop=True, top=True, labelright=True, right=True, which='both',labelsize=25)
# # plt.legend(loc='best', fontsize=30, frameon=False)
#
# #f = np.linspace(10,1e6)
#
R = 55e4
Rs = 1e3
Rp = 1e5
C = 55e-12
Z = 1/(1/R + 1j*2*np.pi*f*C)

Z2 =  1/(1/Rp + 1/Rs)
Z1 = Z + Z2
# Z2 = 1/(1/Z + 1/Rp)
# Z1 = Rs + Z2

Zin = 1/(1/Rp + 1/Z1)

Pin_by_P1 = np.real(Zin)*Rp/((np.abs(Zin))**2)
Pin_by_P2 = np.real(Zin)*Rp/((np.abs(1-Zin/Rp)*np.abs(Z2))**2)
Pin_by_Pz1 = np.real(Zin)/(((np.abs(Zin))**2)*np.real(1/np.conj(Z1)))
check = 10**(-Pin_by_P1/10) + 10**(-Pin_by_Pz1/10)
plt.figure(4)
plt.loglog(f,10*np.log10(Pin_by_P1),'k',label='probe-1 power')
plt.loglog(f,10*np.log10(Pin_by_P2),'r',label='probe-2 power')
plt.loglog(f,10*np.log10(Pin_by_Pz1),'--k',label='Z1 power')
plt.loglog(f,check,':k',label='probe-1 + Z1 power')
plt.tick_params(labeltop=True, top=True, labelright=True, right=True, which='both',labelsize=25)
plt.suptitle('source power in dB w.r.t.', fontsize=30)
plt.legend(loc='best', fontsize=30, frameon=False)
plt.show()



# from funs import V21stoYmaginvsBinvs
# Ymaginvs = []
# Binvs = []
# R = 1e3
# Ymaginvs,Binvs = V21stoYmaginvsBinvs(V21s,R,Ymaginvs,Binvs)
#
# from funs import Cfit
# Cs = []
# Binvfits = []
# stafre = [1e5,1e3,0,1e3,0,1e3]
# Cs, Binvfits = Cfit(f,Binvs,Cs,Binvfits,stafre)
#
# print Cs, len(Binvfits)
#
# hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
# lblst = ['$|Y|^{-1}$ without active probes','$|Y|^{-1}$ with active probes','$B^{-1}$ without active probes','$B^{-1}$ with active probes','ideal capacitor','ideal capacitor']
# xlbl = '$f$ / $Hz$'
# ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
# x = f
# ylst = Ymaginvs[0:2]
# cou = len(ylst)
# ylst.append(Binvs[0])
# ylst.append(Binvs[1])
# ylst.append(Binvfits[0])
# ylst.append(Binvfits[1])
# from funs import lglgplt
# lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,cou)
#
# hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
# lblst = ['$|Y|^{-1}$ with air (data)','$|Y|^{-1}$ with $7 \mu S/m$ water (data)','$B^{-1}$ with air (data)','$B^{-1}$ with $7 \mu S/m$ water (data)','ideal capacitor','ideal capacitor','DI water (expected)','DI water (20% error)','DI water (20% error)']
# xlbl = '$f$ / $Hz$'
# ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
# x = f
# ylst = Ymaginvs[2:4]
# cou = len(ylst)
# ylst.append(Binvs[2])
# ylst.append(Binvs[3])
# ylst.append(Binvfits[2])
# ylst.append(Binvfits[3])
# ylst.append(Binvfits[2]/78)
# ylst.append(0.8*Binvfits[2]/78)
# ylst.append(1.2*Binvfits[2]/78)
# from funs import lglgplt
# lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,cou)
#
# hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
# lblst = ['$|Y|^{-1}$ with air (data)','$|Y|^{-1}$ with $7 \mu S/m$ water (data)','$B^{-1}$ with air (data)','$B^{-1}$ with $7 \mu S/m$ water (data)','ideal capacitor','ideal capacitor','DI water (expected)','DI water (20% error)','DI water (20% error)']
# xlbl = '$f$ / $Hz$'
# ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
# x = f
# ylst = Ymaginvs[4:6]
# cou = len(ylst)
# ylst.append(Binvs[4])
# ylst.append(Binvs[5])
# ylst.append(Binvfits[4])
# ylst.append(Binvfits[5])
# ylst.append(Binvfits[4]/78)
# ylst.append(0.8*Binvfits[4]/78)
# ylst.append(1.2*Binvfits[4]/78)
# from funs import lglgplt
# lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,cou)
