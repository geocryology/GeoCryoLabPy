# Input: ***_avg csv file outputted by calibration code 

# Creates a results csv file like: | Therm name | date of calibration | a | b | c | d | Mode uncertainty | Avg residual
# Creates a stats csv file with additional error and uncertainty info
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
import pandas as pd 

# Input
dir = ''   # Directory of input csv and where outputted csv files will go
file = ''                             # Name of input csv file
point = "0.0"

# Define function to fit 
def func(x, a, b, c, d):                      # Where x is Rt/R0 and a, b, c and d are the parameters
    return 1/(a + b * np.log(x) + c * (np.log(x))**2 + d * (np.log(x))**3)

# Import data
table = pd.read_csv(dir + file)
ThermRes = table.iloc[:, 4:]
        
# Prepares data for plotting
ind = table[table['Setpoint']==0.0].index.values.astype(int)[0]

xdata = []
for therm in ThermRes:
    res = ThermRes[therm]            
    res = [i/res[ind] for i in res]   # Resistance divided by resistance at 0 degrees C
    xdata.append(res)

ydata = table['ProbeTemp']         
ydata = [i+273.15 for i in ydata]      # Convert celcius to kelvin

# Fit curves to function, calculates uncertainties, residuals, prepare plots
results = pd.DataFrame()
stats = pd.DataFrame()           

for i in range(0, len(xdata)):
    x = xdata[i]
    # Fitting curve
    popt, pcov = curve_fit(func, x, ydata, bounds=(0, [1.0e-1, 1.0e-2, 1.0e-4, 1.0e-5]))  # popt is the parameter values and pvoc is the covariance matrix
    
    # Calculating uncertainties
    a, b, c, d = unc.correlated_values(popt, pcov)     # Calculates +/- uncertainty of parameters using sqrt of diagonal of pcov. http://scipyscriptrepo.com/wp/?p=104
    py = 1/(a + b * unp.log(x) + c * (unp.log(x))**2 + d * (unp.log(x))**3)   # calculates the temp with uncertainties for every temp step
    nom = unp.nominal_values(py)        # Creates array of temp value at each temp step
    std = unp.std_devs(py)              # Creates array of uncertainty (1 standard deviation) at each temp step
    std_mma = [median(std *3.92), max(std)*3.92, min(std)*3.92]  # Calculates mode, max and min of the uncertainties over all temps of thermistor for csv file
    
    # Calculating residuals
    dif = func(x, *popt) - ydata   # Calculates difference between curve and data points
    dif_mma = [np.mean(abs(dif)), max(dif), min(dif)]    # Calculates mean, max and min residual over the temp range of a thermistor for csv file
    
    # Calculate standard uncertainty (1.96 sigma: 95%, 1.65 sigma: 90%)
    cov = np.sqrt(np.diag(pcov)) * 1.96  # Not used anymore as unc.correlated_values does this. But still used for stats csv

    # Prepare data for results csv
    result = pd.DataFrame({'Date': [table["Time"][0][:10]], 
                        'Thermistor': [ThermRes.columns.values[i]],
                        'a': popt[0], 'b': popt[1], 'c': popt[2], 'd': popt[3],
                        'std_median': std_mma[0], 'err_avg': dif_mma[0]})
    results = results.append(result, ignore_index=True)
    # Prepare data for stats csv
    stat = pd.DataFrame({'Date': [table["Time"][0][:10]], 
                        'Thermistor': [ThermRes.columns.values[i]],
                        'a': popt[0], 'b': popt[1], 'c': popt[2], 'd': popt[3],
                        'stu_a': cov[0], 'stu_b': cov[1], 'stu_c': cov[2], 'stu_d': cov[3],
                        'std_median': std_mma[0], 'std_max': std_mma[1], 'std_min': std_mma[2],
                        'err_avg': dif_mma[0], 'err_max': std_mma[1], 'err_min': std_mma[2]})
    stats = stats.append(stat, ignore_index=True)
    
    ## PLOTTING
    # Plot Curves and points
    plt.subplot(311)
    plt.plot(x, func(x, *popt), 'g-')
    plt.ylabel('Temperature (k)')
    plt.plot(x, ydata, 'c.', markersize = 1)
    # Plotting residuals
    plt.subplot(312)
    plt.plot(x, dif, 'r.', markersize = 2)
    plt.xlabel('Rt/R0')
    plt.ylabel('Error (K)') 
    # Plot T uncertainty over T range
    plt.subplot(313)
    plt.plot(ydata, 3.92 * std)   # 3.92 is 2 * 1.96 (95 % confidence)
    plt.xlabel('Temperature (K)')
    plt.ylabel('Uncertainty (K)')
   
# Write results csv
results.to_csv(dir + 'results.csv', index = False)

# Write stats csv
stats.to_csv(dir + 'stats.csv', index = False)   
    
# Plot data and save file
plt.tight_layout()
plt.savefig(dir + 'Plot.pdf')
plt.show()
 
