"""
communicate with Solartron 1255B Frequency Response Analyzer and record V1/V2
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

# Default GPIB address of analyzer (refer section 7.2.3 in 1260A/1255B analyzer manual)
ADDRESS = u'GPIB0::12::INSTR'
rm = visa.ResourceManager()
analyzer = rm.open_resource(ADDRESS) # Connect to analyzer
# Input (from analyzer to computer) command terminator (refer section 7.2.3 in 1260A/1255B analyzer manual)
analyzer.read_termination = '\r\n' #';' # this is for the reference of visa Python package
# Output (from computer to analyzer) command terminator (refer section 5.8.2 in 1260A/1255B analyzer manual)
analyzer.write_termination = '\r\n' # this is for the reference of visa Python package

# GPIB uses two methods for communication:
# WRITE: sends an instruction to analyzer without expecting a response
def write(cmd):
    analyzer.write(cmd)
    time.sleep(1) # Minimum time in seconds between consecutive write commands
# QUERY: Sends an instruction to analyzer expecting a response
def query(cmd):
    return analyzer.query(cmd)
# responses may take upto several seconds to return
analyzer.timeout = int(10000) # time in seconds for GPIB timeout

def disconnect(): # To close the connection before script ends
    analyzer.close()

# GPIB ID string returned by the '*IDN?' query (refer section 7.2.7 in 1260A/1255B analyzer manual)
print 'Expected GPIB ID of analyzer: 1255B FREQUENCY RESPONSE ANALYZER, SOLARTRON,0,0d'
print 'Actual GPIB ID of analyzer: ' query('*IDN?')

write('*RST') # resets the analyzer to its default values
write('*CLS') # clears error queues and various registers
write('TT 2') # resets the analyzer (may be not required after *RST command)
write('OS 0') # instructs analyzer that output command separator is a comma (to input a command with more than one parameter)
write('OT 0') # instructs analyzer that output command terminator is \r\n (CRLF or Carriage Return Line Feed)
write('OP 2,1') # instructs analyzer to send (dump all) data in ASCII format over GPIB

# Setup parameters
cell = '100 kohm resistor' # '1 microfarad capacitor' # 'cell with shield (d=5mm)' # d is electrode spacing
Rr = 10 # 1294 current measurement switch setting (Rr is range resistor value in ohms)
Vampl = 1.0 # Generator (AC voltage source mode) RMS amplitude in volts
Vbias = 0.0 # Generator DC bias in volts
int_time = 1.0 # Analyzer integration time in seconds
f1 = 1.0 # start frequency (10microHz < f1 < f2 < 32MHz)
f2 = 1e6 # stop frequency
nPoints = 7 # 201 # number of measurement points between f1 and f2

# triple quotes for multi-line strings
# configuration commands (refer 1260A/1255B manual)
# FV 1 (these commands not required for 1255B)
# GT 0
# RA 3,0
# DC 3,0
# configuration commands in 3 stages:
# stage 1 commands (section 3.6.3 of 1260A/1255B manual): Setting the analyzer
# IS ; RA ; DC ; IP ; OU ;
# stage 2 commands (section 3.6.4 of 1260A/1255B manual): Setting the Generator
# VA ; VB ; FR
# stage 3 command (section 3.6.5 of 1260A/1255B manual): Commanding a Measurement
# SI
# stage 4 command (section 3.6.6 of 1260A/1255B manual): Setting the Display
# SO 1,2
commands = '''IS {}
    RA 1,0
    RA 2,0
    DC 1,0
    DC 2,0
    IP 1,1
    IP 2,1
    OU 1,0
    OU 2,0
    VA {}
    VB {}
    CV 1
    UW 0'''.format(int_time,Vampl,Vbias)
# CV 1 (for result in polar coordinates)
# UW 0 (for angle between -180 and 180 degrees)
print 'Configuring analyzer for V1/V2 measurement(s)'
commandList = commands.split('\n')
for cmd in commandList:
    write(cmd.strip())

print 'Varying generator frequency and recording V1/V2'
freq = []
V12_mag = []
V12_ang = []
for f in np.geomspace(f1,f2,num=nPoints):
    write('FR ' + str(f)) # frequency
    query('SI') # Commanding a Measurement
    write('SO 1,2') # Setting the Display to show V12=V1/V2
    result = query('DO') # retrieve measurement as: f, V12mag, V12ang, ...
    result = result.encode('utf-8')
    result = map(float, result.split(','))
    # store results separately in freq, V12_mag, V12_ang
    freq.append(result[0])
    V12_mag.append(result[1])
    V12_ang.append(result[2])
disconnect()

print 'Saving impedance data in specified file'
timestamp = datetime.datetime.now().isoformat()
filenametemp = '{}\{}.csv'.format(pathname,filename)
output = open(filenametemp, 'w')
output.write('Impedance measurement of {} using Solartron 1255A frequency response analyzer with 1294 impednace interface\n'.format(cell))
output.write('File generated on: {}\n'.format(timestamp))
output.write('1294 current measurement switch setting: range resistor: Rr = {} ohms\n'.format(Rr))
output.write('Start Frequency: {} Hz\n'.format(f1))
output.write('Stop  Frequency: {} Hz\n'.format(f2))
output.write('Number of data points per frequency sweep: {}\n'.format(nPoints))
output.write('Generator (AC voltage source mode) RMS amplitude: {} V\n'.format(Vampl))
output.write('Generator DC bias: {} V\n'.format(Vbias))
output.write('Analyzer integration time: {} s\n'.format(int_time))
output.write('Frequency, Impedance magnitude, Impedance angle (degrees)\n')
for i in range(len(freq)):
    output.write('{},{},{}\n'.format(freq[i],Rr*V12_mag[i],V12_ang[i]))

output.close()
exit()
