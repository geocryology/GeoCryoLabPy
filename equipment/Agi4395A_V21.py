# script uses Agi4395A.py module to measure and store V2/V1 of a cell connected to Agilent 4395A
# script sends configuration commands and reads the measured data

import datetime
import sys
import time
import numpy as np
import Agi4395A as vna # Agi4395A is a module to establish GPIB connection with Agilent 4395A Vector Network Analyzer

if not vna.connect():
    print "Failed to connect to Agilent4395A"
    exit(1)

pathname = sys.argv[1]
filename = sys.argv[2]
counttotal = sys.argv[3]
counts = range(1,int(counttotal)+1,1)
#dictionary to store measurements
results = {count: {} for count in counts}

# Setup parameters
cell = "cell with shield (d=5mm)" # d is electrode spacing
Z0 = 50 # VNA port impedance in ohms
Rs = 1e3 # current measurment resistor value in ohms connected to cell's terminal-2
power = 15.0 # 0.0 # <15dBm # power input to cell's terminal-1
AttR = 30 # Attenuation in dB at receiver R (terminal-1 of cell)
AttB = 20 # Attenuation in dB at receiver B (terminal-2 of cell)
# f1 < f2 and 10 <= f1,f2 <= 510000000
f1 = 100 # start frequency
f2 = 10000000 # stop frequency
 # 1 <= nPoints <= 801
nPoints = 201 # number of measurement points between f1 and f2
ifbw = 10 # IF bandwidth #"AUTO" #100 (refer 4395A manual for details)
avgfct = 1 # Averaging Factor (refer 4395A manual for details)

fmts = ["REAL", "IMAG"]

# BWAUTO 1
# BW {}
# MEAS {{}}
# configuration commands (refer Agilent-4395A-programming-manual):
#    STODMEMO
#    RECD "SHORT.STA"
# triple quotes for multi-line strings
commands = """NA
    CHAN1
    HOLD
    SWPT LOGF
    BW {}
    AVER 1
    AVERFACT {}
    POIN {}
    FORM4
    MEAS BR
    ATTR {}DB
    ATTB {}DB
    STAR {} HZ
    STOP {} HZ
    POWE {}
    FMT LINM""".format(ifbw, avgfct, nPoints, AttR, AttB, f1, f2, power)
# Configure analyzer for measurements
print "Configuring analyzer for V21 measurement(s)"
commandList = commands.split("\n")
for cmd in commandList:
    vna.write(cmd.strip())

time.sleep(10)

for count in counts:
    # Get sweep duration
    t = 10
    try:
        duration = vna.query("SWET?").strip()
        t = float(duration)*avgfct
    except:
        print "failed to convert to float: ", duration
        t = 180

    print "total sweep time for V21 measurement {} is: {}".format(count,t)

    # Make measurements
    t0 = time.time()
    vna.write("NUMG {}".format(avgfct))
    print "waiting"
    while time.time() < t0 + t + 2:
        time.sleep(1)

    # Read measurement data from analyzer
    for fmt in fmts:
        print "Reading V21 measurement {}: {} ...".format(count, fmt),
        vna.write("FMT {}".format(fmt))
        # results are read as list of x1,y1,x2,y2,x3,y3... where every yn value is 0.
        # this line splits the list at every comma, strips out every second value, and converts to floats
        response = vna.query("OUTPDTRC?")
        print "done - {} bytes".format(len(response))
        results[count][fmt] = map(float, response.strip().split(",")[::2])

# Read x-axis values (frequency points)
freqs = vna.query("OUTPSWPRM?").strip()
freqs = map(float, freqs.split(","))

vna.disconnect()

timestamp = datetime.datetime.now().isoformat()
print "saving file"
filenametemp = "{}\{}.csv".format(pathname,filename)
output = open(filenametemp, "w")
output.write("V21 measurement of {} using Agilent 4395A vector network analyzer\n".format(cell))
output.write("File generated on: {}\n".format(timestamp))
output.write("Port impedance (Z0): {} ohm\n".format(Z0))
output.write("Current measurement resistor (Rs) connected at terminal-2 of cell: {} ohm\n".format(Rs))
output.write("Source Power to terminal-1 of cell: {} dBm\n".format(power))
output.write("Attenuation at receiver R (terminal-1 of cell): {} dB\n".format(AttR))
output.write("Attenuation at receiver B (terminal-2 of cell): {} dB\n".format(AttB))
output.write("Start Frequency: {} Hz\n".format(f1))
output.write("Stop  Frequency: {} Hz\n".format(f2))
output.write("Number of data points per frequency sweep: {}\n".format(nPoints))
output.write("IF BandWidth: {} Hz \n".format(ifbw))
output.write("Averaging Factor (number of sweeps per trial): {}\n".format(avgfct))
output.write("Number of trials: {}\n".format(counttotal))
output.write("Frequency, V21_real (precision), V21_imag (precision), V21 (average), V21 (raw data)\n")
# definition for V21_precision=stdev(V21)/abs(V21_average)
for i in range(nPoints):
    S21Real=[results[count]["REAL"][i] for count in counts]
    S21Imag=[results[count]["IMAG"][i] for count in counts]
    S21=np.array(S21Real)+1j*np.array(S21Imag)
    output.write("{},{},{},{},{}\n".format(freqs[i], np.std(np.real(S21))/np.mean(np.abs(np.real(S21))), np.std(np.imag(S21))/np.mean(np.abs(np.imag(S21))), str(np.mean(S21))[1:-1], ", ".join(str(dummy)[1:-1] for dummy in S21)))

output.close()

exit()
