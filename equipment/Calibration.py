# Input:  - ***_avg csv file outputted by calibration code 
#         - csv with reference thermometer uncertainty at every temp step 
# Output: - results csv file 
#         - figure with - a plot of fitted curve
#                       - a plot with residual errors
#                       - a plot of fitted curve uncertainties
        
import numpy as np
import matplotlib.pyplot as plt        
from scipy.optimize import curve_fit   
import uncertainties as unc   
import uncertainties.unumpy as unp 
import pandas as pd 

# Input
dir = ''                                              # Where input and output are located
file = ''                                             # _avg file from calibration                             
file_ru = ''                                          # File with uncertainties of reference thermometer at every temp step
point = "0.0"                                         # Temperature by which Rt is divided by

# Define function to fit 
def func(x, a, b, c, d):                              # Where x is Rt/R0 and a, b, c and d are the parameters
    return 1/(a + b * np.log(x) + c * (np.log(x))**2 + d * (np.log(x))**3)
# Function for uncertainty calculation
def ufunc(x, a, b, c, d):                     
    return 1/(a + b * unp.log(x) + c * (unp.log(x))**2 + d * (unp.log(x))**3)

# Import data
table = pd.read_csv(dir + file)
table_ru = pd.read_csv(dir + file_ru)                 # Reference thermometer uncertanity
ThermRes = table.iloc[:, 4:]                          # Resistance values
        
# Gets index of setpoint = 0 degrees C
ind = table[table['Setpoint']==0.0].index.values.astype(int)[0]

# Prepare xdata (thermistor resistance)
xdata = []
zeros = []
for therm in ThermRes:
    res = ThermRes[therm] 
    zero = res[ind]
    zeros.append(zero)
    xdata.append(res)

# Prepare ydata (Reference thermometer temperature)
ydata = table['ProbeTemp']         
ydata = [i+273.15 for i in ydata]                      # Convert celcius to kelvin 


# Fit curves to function, calculates uncertainties and residuals, write results to csv and prepare plots
results = pd.DataFrame()      
difs = []

for i in range(0, len(xdata)):

    x = xdata[i]
    res = [n/zeros[i] for n in x] 

    ## Fitting curve
    popt, pcov = curve_fit(func, res, ydata, bounds=(0, [1.0e-1, 1.0e-2, 1.0e-4, 1.0e-5]),
                          absolute_sigma = True, sigma = table_ru['Uncert']) 
    
    ## Calculating uncertainties 
    a, b, c, d = unc.correlated_values(popt, pcov)     # Calculates correlated +/- uncertainty of parameters 
    x = np.array([unc.ufloat(n, 0.15) for n in x])
    R0 =  unc.ufloat(zeros[i], 0.15)          
    R = x/R0
    py = ufunc(R, a, b, c, d)                          # calculates the temp with uncertainties for every temp step 
    nom = unp.nominal_values(py)                       # Creates array of temp value at each temp step
    std = unp.std_devs(py)                             # Creates array of uncertainty (1 standard deviation) at each temp step

    ## Calculating residuals
    dif = nom - ydata
    difs.append(dif)

    ## Prepare resulst csv
    result = pd.DataFrame({'Date': [table["Time"][0][:10]], 
                        'Thermistor': [ThermRes.columns.values[i]],
                        'a': a.n, 'b': b.n, 'c': c.n, 'd': d.n,
                        'uncert_a': a.s, 'uncert_b': b.s, 'uncert_c': c.s, 'uncert_d': d.s,
                        'R0': zeros[i]})
    result = result[['Date', 
                     'Thermistor', 'a', 'b', 'c', 'd', 'uncert_a', 'uncert_b', 'uncert_c', 'uncert_d', 'R0']]
    results = results.append(result, ignore_index=True)
    
    ## Ploting
    # Plot Curves and points
    plt.subplot(311)
    plt.plot(nom, res, 'g-')
    plt.ylabel('Rt/R0')
    # Plotting residuals
    plt.subplot(312)
    plt.plot(ydata, dif, 'r.', markersize = 2)
    plt.ylabel('Error (K)') 
    # Plot T uncertainty over T range
    plt.subplot(313)
    plt.plot(ydata, 2 * std)                           # 95 % confidence
    plt.ylabel('Uncertainty (K)')
    plt.xlabel('Temperature (K)')
    
   
# Write results csv
results.to_csv(dir + 'results.csv', index = False) 
    
# Plot data and save file
plt.tight_layout()
plt.savefig(dir + 'Plot.pdf')
plt.show()

# Sources
# https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html
# https://pypi.org/project/uncertainties/
# https://pythonhosted.org/uncertainties/user_guide.html
# https://stackoverflow.com/questions/24633664/confidence-interval-for-exponential-curve-fit/26042460
# https://pythonhosted.org/uncertainties/user_guide.html#index-9
# https://stackoverflow.com/questions/24633664/confidence-interval-for-exponential-curve-fit/26042460
# http://apmonitor.com/che263/index.php/Main/PythonRegressionStatistics