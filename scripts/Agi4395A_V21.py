"""
communicate with Agilent4395A Vector Network Analyzer and record V2/V1
operate using a National Instruments USB-GPIB cable
"""
import visa # refer https://pyvisa.readthedocs.io/
import datetime
import sys
import time
import numpy as np

# user specified pathname (expected as 1st argument while running code) for creating a file for storing analyzer data
pathname = sys.argv[1]
# user specified filename (expected as 2nd argument while running code) into which analyzer data is stored
filename = sys.argv[2]
# user specified number of times to repeat each V2/V1 measurement for estimating precision
counttotal = sys.argv[3]

# Default GPIB address of analyzer (refer section C-21 of 4395A manual or section 9-2 of 4395A programming manual)
ADDRESS = u'GPIB1::16::INSTR' # u'GPIB0::16::INSTR'
rm = visa.ResourceManager()
analyzer = rm.open_resource(ADDRESS) # Connect to analyzer

# GPIB uses two methods for communication:
# WRITE: sends an instruction to analyzer without expecting a response
def write(cmd):
    analyzer.write(cmd)
# QUERY: Sends an instruction to analyzer expecting a response (some may take several seconds to return)
def query(cmd):
    return analyzer.query(cmd)

def disconnect(): # To close the connection before script ends
    analyzer.close()

# GPIB ID string returned by the '*IDN?' query (refer section I-1 in 4395A programming manual)
print 'Expected GPIB ID of analyzer: HEWLETT-PACKARD,4395A,MY41101925,REV1.12'
print 'Actual GPIB ID of analyzer: ' query('*IDN?')

write('*RST') # resets the analyzer to its default values
write('*CLS') # clears error queues and various registers

counts = range(1,int(counttotal)+1,1)
results = {count: {} for count in counts} # dictionary to store measurements

# Setup parameters
cell = 'cell with shield (d=5mm)' # d is electrode spacing
Z0 = 50 # VNA port impedance in ohms
Rs = 1e3 # current measurment resistor value in ohms connected to cell's terminal-2
power = 15.0 # 0.0 # <15dBm # power input to cell's terminal-1
AttR = 30 # Attenuation in dB at receiver R (terminal-1 of cell)
AttB = 20 # Attenuation in dB at receiver B (terminal-2 of cell)
f1 = 100 # start frequency (f1 < f2 and 10 <= f1,f2 <= 510000000)
f2 = 10000000 # stop frequency
nPoints = 201 # number of measurement points between f1 and f2 (1 <= nPoints <= 801)
ifbw = 10 # IF bandwidth #"AUTO" #100 (refer 4395A manual for definition)
avgfct = 1 # Averaging Factor (refer 4395A manual for definition)
fmts = ['REAL', 'IMAG']

# triple quotes for multi-line strings
# configuration commands (refer 4395A programming manual):
# BWAUTO 1
# MEAS {{}}
# STODMEMO
# RECD "SHORT.STA"
commands = '''NA
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
    FMT LINM'''.format(ifbw, avgfct, nPoints, AttR, AttB, f1, f2, power)
print 'Configuring analyzer for V2/V1 measurement(s)'
commandList = commands.split('\n')
for cmd in commandList:
    write(cmd.strip())
time.sleep(10)

for count in counts:
    # Get sweep duration
    t = 10
    try:
        duration = query("SWET?").strip()
        t = float(duration)*avgfct
    except:
        print "Failed to convert to float: ", duration
        t = 180
    print "Total sweep time for V21 measurement {} is: {}".format(count,t)

    # Make measurement(s)
    t0 = time.time()
    write("NUMG {}".format(avgfct))
    print "waiting"
    while time.time() < t0 + t + 2:
        time.sleep(1)

    # Read measurement data from analyzer
    for fmt in fmts:
        print "Reading V21 measurement {}: {} ...".format(count, fmt),
        write("FMT {}".format(fmt))
        response = query("OUTPDTRC?") # response obtained as x1,y1,x2,y2,x3,y3... where every yn value is 0
        print "done - {} bytes".format(len(response))
        results[count][fmt] = map(float, response.strip().split(",")[::2]) # response split at every comma, strip out every second value, and convert to float
freq = query("OUTPSWPRM?").strip() # obtain frequency points
freq = map(float, freq.split(","))
disconnect()

print "Saving V2/V1 data in specified file"
timestamp = datetime.datetime.now().isoformat()
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
for i in range(nPoints):
    V21Real=[results[count]["REAL"][i] for count in counts]
    V21Imag=[results[count]["IMAG"][i] for count in counts]
    V21=np.array(V21Real)+1j*np.array(V21Imag)
    output.write("{},{},{},{},{}\n".format(freq[i], np.std(np.real(V21))/np.mean(np.abs(np.real(V21))), np.std(np.imag(V21))/np.mean(np.abs(np.imag(V21))), str(np.mean(V21))[1:-1], ", ".join(str(dummy)[1:-1] for dummy in V21)))

output.close()
exit()
