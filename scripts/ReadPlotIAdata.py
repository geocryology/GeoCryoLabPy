import numpy as np

skp_rws = 10 # skp_rws is rows to skip at beginning of file
Zmag_indx = 1 # V21_indx is column where V2/V1 data is in file
f_indx = 0 # f_indx is column where frequency data is in file
Zmags = [] # V21s is matrix into which V2/V1 arrays are written
f = [] # f is array into which frequency values are written

from funs import read_V21s
folder = 'IAdata/' # folder from where files need to be read
files = ['10ohm','100ohm','1kohm','10kohm','100kohm','1Mohm'] # filenames to be read (no need to mention .csv extention)
Zmags = read_V21s(folder,files,Zmags,skp_rws,Zmag_indx)
file = folder+files[0]+'.csv'
from funs import read_f
f = read_f(file,skp_rws,f_indx)

f = np.array(f)
Zmags = np.array(Zmags)

# generate loglog plot y vs. x using lglgplt
# ylst can contain multiple y data arrays
# lglgplt accepts legends in two locations
# h_lgnd_1 specifies number of labels in location-1 legend
# lblst is array of all labels for legend(s)

hdg = 'Impedance ($Z$) vs. frequency ($f$)'
lblst = ['10ohm','100ohm','1kohm','10kohm','100kohm','1Mohm']
xlbl = '$f$ / $Hz$'
ylbl = '$|Z|$ / $\Omega$'
x = f
ylst = Zmags[0:6]
h_lgnd_1 = len(ylst)
# ylst = np.concatenate((ylst,Zmags[0:5]))
from funs import lglgplt
lglgplt(hdg,xlbl,ylbl,x,ylst,lblst,h_lgnd_1)
