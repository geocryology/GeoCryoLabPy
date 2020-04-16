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

from funs import V21stoYmaginvsBinvs
Ymaginvs = []
Binvs = []
R = 1e3
Ymaginvs,Binvs = V21stoYmaginvsBinvs(V21s,R,Ymaginvs,Binvs)

from funs import Cfit
Cs = []
Binvfits = []
stafre = [1e5,1e3,0,1e3,0,1e3]
Cs, Binvfits = Cfit(f,Binvs,Cs,Binvfits,stafre)

print Cs, len(Binvfits)

hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
lblst = ['$|Y|^{-1}$ without active probes','$|Y|^{-1}$ with active probes','$B^{-1}$ without active probes','$B^{-1}$ with active probes','ideal capacitor','ideal capacitor']
xlbl = '$f$ / $Hz$'
ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
x = f
ylst = Ymaginvs[0:2]
cou = len(ylst)
ylst.append(Binvs[0])
ylst.append(Binvs[1])
ylst.append(Binvfits[0])
ylst.append(Binvfits[1])
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,cou)

hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
lblst = ['$|Y|^{-1}$ with air (data)','$|Y|^{-1}$ with $7 \mu S/m$ water (data)','$B^{-1}$ with air (data)','$B^{-1}$ with $7 \mu S/m$ water (data)','ideal capacitor','ideal capacitor','DI water (expected)','DI water (20% error)','DI water (20% error)']
xlbl = '$f$ / $Hz$'
ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
x = f
ylst = Ymaginvs[2:4]
cou = len(ylst)
ylst.append(Binvs[2])
ylst.append(Binvs[3])
ylst.append(Binvfits[2])
ylst.append(Binvfits[3])
ylst.append(Binvfits[2]/78)
ylst.append(0.8*Binvfits[2]/78)
ylst.append(1.2*Binvfits[2]/78)
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,cou)

hdg = 'Cell admittance ($Y$) or susceptance ($B$) vs. frequency ($f$)'
lblst = ['$|Y|^{-1}$ with air (data)','$|Y|^{-1}$ with $7 \mu S/m$ water (data)','$B^{-1}$ with air (data)','$B^{-1}$ with $7 \mu S/m$ water (data)','ideal capacitor','ideal capacitor','DI water (expected)','DI water (20% error)','DI water (20% error)']
xlbl = '$f$ / $Hz$'
ylbl = '$|Y|^{-1}$ or $B^{-1}$ / $\Omega$'
x = f
ylst = Ymaginvs[4:6]
cou = len(ylst)
ylst.append(Binvs[4])
ylst.append(Binvs[5])
ylst.append(Binvfits[4])
ylst.append(Binvfits[5])
ylst.append(Binvfits[4]/78)
ylst.append(0.8*Binvfits[4]/78)
ylst.append(1.2*Binvfits[4]/78)
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,cou)
