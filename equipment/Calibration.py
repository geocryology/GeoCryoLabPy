# Input: ***_avg csv file outputted by calibration code 

# Creates a results csv file like: | Therm name | date of calibration | a | b | c | d | Mode uncertainty | Avg residual
# Creates a statistics csv file
# Creates a figure with - a plot of temp vs res points and fitted curves
#                       - a plot with residual errors
#                       - a plot of fitted curve uncertainties over temperature range

# Set things up
import csv as csv                
import numpy as np
import matplotlib.pyplot as plt        
from scipy.optimize import curve_fit   # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html
from statistics import median 
import operator
import uncertainties as unc   # https://pypi.org/project/uncertainties/
import uncertainties.unumpy as unp

# Input
file = '2018-05-23T13_54_10_avg.csv'   #'2018-05-18T20_39_23_avg_2'
point = "0.0"

# Define function to fit 
def func(x, a, b, c, d):                      # Where x is Rt/R0 and a, b, c and d are the parameters
    return 1/(a + b * np.log(x) + c * (np.log(x))**2 + d * (np.log(x))**3)

# Import data
with open(file, 'rb') as file:
    reader = csv.reader(file, dialect='excel', delimiter =',')
    data_r = np.array(list(reader))
    names = list(data_r[0, 4:])
    data = map(list, zip(*data_r[1:]))
    time = data[0][0]
    time = [time[:10]] * len(names)
    SetPoint = list(data[1])
    ProbeTemp = data[2]
    ThermRes = data[4:]
        
# Prepares data for plotting
ind = int(SetPoint.index(point))
# preparing thermistor resistance data (xdata)
xdata = []
for therm in ThermRes:
    res = map(float, therm)
    res = [i/res[ind] for i in res]   # Resistance divided by resistance at 25 degrees C
    xdata.append(res)

# preparing probe temperature data (ydata)
ydata = map(float, ProbeTemp)          # Probe temperature is the y axis data
ydata = [i+273.15 for i in ydata]      # Convert celcius to kelvin

# Fit curves to function, calculates uncertainties, residuals and prepares plots
par = []             # List for results csv
stats = []           # List for stats csv
for x in range(0, len(xdata)):
    # Fitting curve
    popt, pcov = curve_fit(func, xdata[x], ydata, bounds=(0, [1.0e-1, 1.0e-2, 1.0e-4, 1.0e-5]))  # popt is the parameter values and pvoc is the vovariance matrix
   
   # Calculating uncertainties
    a, b, c, d = unc.correlated_values(popt, pcov)     # Calculates +/- uncertainty of parameters using sqrt of diagonal of pcov. http://scipyscriptrepo.com/wp/?p=104
    py = 1/(a + b * unp.log(xdata[x]) + c * (unp.log(xdata[x]))**2 + d * (unp.log(xdata[x]))**3)   # calculates the temp with uncertainties for every temp step
    nom = unp.nominal_values(py)        # Creates array of temp value at each temp step
    std = unp.std_devs(py)              # Creates array of uncertainty (1 standard deviation) at each temp step
    std_mma = [median(std *3.92), max(std)*3.92, min(std)*3.92]  # Calculates mode, max and min of the uncertainties over all temps of thermistor for csv file
    
    # Calculating residuals
    dif = func(xdata[x], *popt) - ydata   # Calculates difference between curve and data points
    dif_mma = [np.mean(abs(dif)), max(dif), min(dif)]    # Calculates mean, max and min residual over the temp range of a thermistor for csv file
    # Calculate standard uncertainty (1.96 sigma: 95%, 1.65 sigma: 90%)
    cov = np.sqrt(np.diag(pcov)) * 1.96  # Not used anymore as unc.correlated_values does this. But still used for stats csv
    
    # Prepare data for stats csv
    stat = [time[x]] + [names[x]] + list(popt) + list(cov) + list(std_mma) + list(dif_mma)   
    stats.append(stat)
    # Prepare data for results csv
    tab = [time[x]] + [names[x]] + list(popt) + [std_mma[0], dif_mma[0]] 
    par.append(tab)
    
    ## PLOTTING
    # Plot Curves and points
    plt.subplot(311)
    plt.plot(xdata[x], func(xdata[x], *popt), 'g-')
    plt.ylabel('Temperature (k)')
    plt.plot(xdata[x], ydata, 'c.', markersize = 1)
    # Plotting residuals
    plt.subplot(312)
    plt.plot(xdata[x], dif, 'r.', markersize = 2)
    plt.xlabel('Rt/R0')
    plt.ylabel('Error (K)') 
    # Plot T uncertainty over T range
    plt.subplot(313)
    plt.plot(ydata, 3.92 * std)   # 3.92 is 2 * 1.96 (95 % confidence)
    plt.xlabel('Temperature (K)')
    plt.ylabel('Uncertainty (K)')
   

# Write uncertainties csv (not currently working)
with open("stats.csv", "w") as output:
    output.write("Date, Thermistor, a, b, c, d, stu_a, stu_b, stu_c, stu_d, std_median, std_max, std_min, err_avg, err_max, err_min\n")

with open('stats.csv', 'a') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    writer.writerows(stats)    

# Write results csv
with open("results.csv", "w") as output:
    output.write("Date, Thermistor, a, b, c, d, std_median, err_avg\n")

with open('results.csv', 'a') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    writer.writerows(par)
    
# Plot data and save file
plt.tight_layout()
plt.savefig('Plot.pdf')
plt.show()
 