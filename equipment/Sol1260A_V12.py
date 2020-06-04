# script uses Sol1260A.py module to measure and store V1/V2 of a cell connected to Solatron 1260A through 1294 interface
# script sends configuration commands and reads the measured data

import datetime
import sys
# import time
import numpy as np
import Sol1260A as ia # Sol1260A is a module to establish GPIB connection with Solatron 1260A Impedance Analyzer

if not ia.connect():
    print "Failed to connect to Agilent4395A"
    exit(1)

pathname = sys.argv[1]
filename = sys.argv[2]

# Setup parameters
cell = "cell with shield (d=5mm)" # d is electrode spacing
Rr = 10 # 1294 current measurement switch setting (Rr is range resistor value in ohms)
Vampl = 1 # Generator (AC voltage source mode) RMS amplitude in volts
Vbias = 0 # Generator DC bias in volts
int_time = 1 # Analyzer integration time in seconds
# 10microHz < f1 < f2 < 32MHz
f1 = 10 # start frequency
f2 = 32000000 # stop frequency
nPoints = 201 # number of measurement points between f1 and f2


# configuration commands (refer 1260A manual)
# triple quotes for multi-line strings
commands = """GT 0
    VA {}
    VB {}
    IS {}
    IP 1,1
    OU 1,0
    IP 2,1
    OU 2,0
    DC 1,0
    DC 2,0
    DC 3,0
    RA 1,0
    RA 2,0
    RA 3,0
    FV 1
    UW 0""".format(Vampl,Vbias,int_time)
# Configure analyzer for measurements
print "Configuring analyzer for V12 measurement(s)"
commandList = commands.split("\n")
for cmd in commandList:
    ia.write(cmd.strip())

freq = []
V12_mag = []
V12_ang = []
# Begin sweep. Set frequency for each sample point, run a single measurement, retrieve result
for f in np.logspace(f1,f2,num=nPoints):
  ia.write("FR " + str(f)) # Set generator frequency
  start_measure = ia.query("SI") # Start measurement and  wait for it to finish (when query returns)
  ia.write("SO 1,2") # Set Display Source to 'V1/V2' to convert last measurment to r, theta
  result = ia.query("DO").split(',') # Request last measurement again. It is now in the form "freq , r, theta"

# Store the received data in freq, V12_mag, V12_ang arrays
  freq.append(result[0])
  V12_mag.append(result[1])
  V12_ang.append(result[2])

ia.disconnect()

timestamp = datetime.datetime.now().isoformat()
print "saving file"
filenametemp = "{}\{}.csv".format(pathname,filename)
output = open(filenametemp, "w")
output.write("V12 measurement of {} using Solartron 1260A impedance analyzer\n".format(cell))
output.write("File generated on: {}\n".format(timestamp))
output.write("1294 current measurement switch setting (range resistor, Rr = {} ohms)\n".format(Rr))
output.write("Start Frequency: {} Hz\n".format(f1))
output.write("Stop  Frequency: {} Hz\n".format(f2))
output.write("Number of data points per frequency sweep: {}\n".format(nPoints))
output.write("Generator (AC voltage source mode) RMS amplitude: {} V\n".format(Vampl))
output.write("Generator DC bias: {} V\n".format(Vbias))
output.write("Analyzer integration time: {} s\n".format(int_time))
output.write("Frequency, V12_magnitude, V12_angle\n")
output.write("{},{},{}\n".format(freq,V12_mag,V12_ang))

output.close()

exit()
