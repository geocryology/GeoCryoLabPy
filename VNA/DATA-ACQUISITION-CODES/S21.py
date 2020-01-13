import datetime
import sys
import time
import numpy as np

from agilent4395a import agilent4395a as agilent4395a # agilent4395a is controller class for the Agilent 4395A Vector Network Analyzer operating over GPIB
fra = agilent4395a()

# GPIB uses two methods for communication:
#   WRITE - Sends a command, doesn't return a response
#   QUERY - Sends a command, followed by a '?', and returns a response

# script sends configuration commands and reads the measured data

if not fra.connect():
    print "Failed to connect to Agilent4395A"
    exit(1)

pathname = sys.argv[1]
filename = sys.argv[2]
counttotal = sys.argv[3]
counts = range(1,int(counttotal)+1,1)
#dictionary to store measurements
results = {count: {} for count in counts}

# Setup parameters
Z0 = 50 #VNA port impedance in ohms
power = 0.0 # <15dBm
nPoints = 201 # 1 <= nPoints <= 801
f1 = 500 # f1 < f2 and 10 <= f1,f2 <= 510000000
f2 = 500000
ifbw = 100 # IF bandwidth
avgfct = 1 # Averaging Factor

fmts = ["REAL", "IMAG"]

# BWAUTO 1
# MEAS {{}}
# configuration commands (refer Agilent-4395A-programming-manual):
commands = """NA
    STODMEMO
    RECD "S21E_CAL.STA"
    CHAN1
    HOLD
    SWPT LOGF
    BW {}
    AVER 1
    AVERFACT {}
    POIN {}
    FORM4
    MEAS BR
    STAR {} HZ
    STOP {} HZ
    POWE {}
    FMT LINM""".format(ifbw,avgfct,nPoints, f1, f2, power)
# Configure analyzer for measurements
print "Configuring analyzer for S21 measurement(s)"
commandList = commands.split("\n")
for cmd in commandList:
    fra.write(cmd.strip())

time.sleep(10)

for count in counts:
    # Get sweep duration
    t = 10
    try:
        duration = fra.query("SWET?").strip()
        t = float(duration)*avgfct
    except:
        print "failed to convert to float: ", duration
        t = 180

    print "total sweep time for S21 measurement {} is: {}".format(count,t)

    # Make measurements
    t0 = time.time()
    fra.write("NUMG {}".format(avgfct))
    print "waiting"
    while time.time() < t0 + t + 2:
        time.sleep(1)

    # Read measurement data from analyzer
    for fmt in fmts:
        print "Reading S21 measurement {}: {} ...".format(count, fmt),
        fra.write("FMT {}".format(fmt))
        # results are read as list of x1,y1,x2,y2,x3,y3... where every yn value is 0.
        # this line splits the list at every comma, strips out every second value, and converts to floats
        response = fra.query("OUTPDTRC?")
        print "done - {} bytes".format(len(response))
        results[count][fmt] = map(float, response.strip().split(",")[::2])

# Read x-axis values (frequency points)
freqs = fra.query("OUTPSWPRM?").strip()
freqs = map(float, freqs.split(","))

#timestamp = datetime.datetime.now().isoformat()
print "saving file"
filenametemp = "{}\{}.csv".format(pathname,filename)
output = open(filenametemp, "w")
output.write("series method - lossy splitter - S21 data (active-probe-0ohm) \n")
output.write("port impedance (Z0): {} ohm\n".format(Z0))
output.write("\n")
output.write("Source Power: {} dBm\n".format(power))
output.write("Start Frequency: {} Hz\n".format(f1))
output.write("Stop  Frequency: {} Hz\n".format(f2))
output.write("IF BandWidth: {} Hz \n".format(ifbw))
output.write("Number of data points per sweep: {}\n".format(nPoints))
output.write("Averaging Factor (number of sweeps per trial): {}\n".format(avgfct))
output.write("Number of trials: {}\n".format(counttotal))
output.write("Frequency, S21-precision, S21-average, S21 (raw data)\n")
# definition for S21-precision=stdev(S21)/abs(S21-average)
for i in range(nPoints):
    S21Real=[results[count]["REAL"][i] for count in counts]
    S21Imag=[results[count]["IMAG"][i] for count in counts]
    S21=np.array(S21Real)+1j*np.array(S21Imag)
    output.write("{},{},{},{}\n".format(freqs[i], np.std(S21)/np.absolute(np.mean(S21)), str(np.mean(S21))[1:-1], ", ".join(str(dummy)[1:-1] for dummy in S21)))

output.close()
fra.disconnect()
exit()