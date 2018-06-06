import argparse
import configparser
import datetime
import time

import numpy as np

from LaudaRP845     import LaudaRP845
from Keysight34972A import Keysight34972A
from ColumnUtils    import Thermistor
from logDAQ         import getChannels, getChannelName
from itertools      import izip
from pyEmail        import Emailer



# Default settings
validChannels = range(101, 121) + range(201, 221) + range(301, 321)
channelList = []
dflt_initDelay = 0

dflt_duration  =  15           # minutes
dflt_port_up   =  12           # Which port to connect to for upper bath
dflt_port_low  =  9            # Which port to connect to for lower bath
dflt_ft_up     = '10 + (t/60)' # One degree per hour ramp
dflt_ft_low    = '10'          # Constant temperature 
dflt_up        =  1            # Use upper temperature control? 0: no, 1: yes
dflt_low       =  1            # Use lower temperature control? 0: no, 1: yes
dflt_rep_up    =  1            # Number of repetitions upper cooling plate program
dflt_rep_low   =  1            # Number of repetitions lower cooling plate program
dflt_tstop_up  =  15           # Duration in minutes of a single loop of the upper program
dflt_tstop_low =  15           # Duration in minutes of a single loop of the lower program
dflt_disc_up   =  5            # How often should the temperature control function be 'sampled' to set bath setpoint
dflt_disc_low  =  5            # How often should the temperature control function be 'sampled' to set bath setpoint

dflt_rdelay    =  90           # seconds between DAQ readings (thermistor sampling frequency)

parser = argparse.ArgumentParser(description="Read soil column temperatures from DAQ while cooling baths operate",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# Experiment control
parser.add_argument('--delay',    default=dflt_initDelay, type=int, help="How long to wait (minutes) before starting the experiment")

# Cooling plate control
parser.add_argument('--up',        default=dflt_up,        type=int, help="Enable upper cooling plate 0 = off, 1 = on")
parser.add_argument('--low',       default=dflt_low,       type=int, help="Enable lower cooling plate 0 = off, 1 = on")
parser.add_argument('--port_up',   default=dflt_port_up,   type=int, help="Port for bath controlling upper cooling plate")
parser.add_argument('--port_low',  default=dflt_port_low,  type=int, help="Port for bath controlling upper cooling plate")
parser.add_argument('--ft_up',     default=dflt_ft_up,     type=str, help="Function defining upper cooling plate temperature as a funtion of 't' (minutes) e.g. '12 + (t/30)' or  '22' (for constant temperature")
parser.add_argument('--ft_low',    default=dflt_ft_low,    type=str, help="Function defining lower cooling plate temperature as a funtion of 't' (minutes) e.g. '12 + (t/30)' or  '22' (for constant temperature")
parser.add_argument('--rep_up',    default=dflt_up,        type=int, help="Number of repetitions for upper cooling plate program")
parser.add_argument('--rep_low',   default=dflt_low,       type=int, help="Number of repetitions for lower cooling plate program")
parser.add_argument('--tstop_up',  default=dflt_tstop_up,  type=int, help="Number of minutes to run upper cooling plate function before terminating or repeating")
parser.add_argument('--tstop_low', default=dflt_tstop_low, type=int, help="Number of minutes to run lower cooling plate function before terminating or repeating")
parser.add_argument('--disc_up',   default=dflt_disc_up,   type=int, help="Discretization interval for upper bath function")
parser.add_argument('--disc_low',  default=dflt_disc_low,  type=int, help="Discretization interval for lower bath function")

# Thermistor control
parser.add_argument('--rdelay',    default=dflt_rdelay,    type=int, help="number of seconds between thermistor measurements (DAQ)")
parser.add_argument('--channels',  default=channelList,    help="List of DAQ channels to read, see code for detailed documentation on format")
parser.add_argument('--filename',  help="Filename of output csv file (.csv extention added automatically)")
parser.add_argument('--calib',     help="Filename of thermistor calibration file")

# Email control
parser.add_argument('--email',     default="",                        help="Send results to this email")
parser.add_argument('--subject',   default="Experiment Complete",     help="Email subject line")

# Set parameters from command line arguments
args = parser.parse_args()

up        = args.up
low       = args.low
port_up   = args.port_up
port_low  = args.port_low
ft_up     = args.ft_up
ft_low    = args.ft_low
rep_up    = args.rep_up
rep_low   = args.rep_low
tstop_up  = args.tstop_up
tstop_low = args.tstop_low
disc_up   = args.disc_up
disc_low  = args.disc_low

readDelay = args.rdelay

if channelList:
    channels     = getChannels(channelList)
    channelNames = {}
    for channel in sorted(channels):
        channelNames[str(channel)] = getChannelName(channel)
    thermistorNames = [channelNames[str(channel)] for channel in sorted(channels)]

# Connect to instruments if they're needed
connected = []

if channelList:
    daq = Keysight34972A()
    if not daq.connect():
        print("Failed to connect to DAQ")
        exit(1)
    
    connected.append(daq)

if up:
    bathUpper = LaudaRP845()
    if not bathUpper.connect(port=port_up):
        print("Failed to connect to upper bath")
        map(lambda x: x.disconnect(), connected)   
        exit(1)
    
    connected.append(bathUpper)

if low:
    bathLower = LaudaRP845()
    if not bathLower.connect(port=port_low):
        print("Failed to connect to lower bath")
        map(lambda x: x.disconnect(), connected)   
        exit(1)
    
    connected.append(bathLower)  

# Prepare bath programs
if up:
    ft_up = lambda t: eval(ft_up)
    bathUpper.setSetpoint(ft_up(0))
    bathUpper.setProgramProfile(4, ft_up, tstop_up, disc_up, reps = rep_up)

if low:
    ft_low = lambda t: eval(ft_low)
    bathLower.setSetpoint(ft_low(0))
    bathLower.setProgramProfile(4, ft_low, tstop_low, disc_up, reps = rep_low)

# Get calibration data for converstion of resistances
Therm = Thermistor()
Therm.readCalibration(args.calib) 
if not Therm.hasCalibration(channelNames.values()):
    print("Missing calibration data for thermistors!")
    exit(1)

# Prepare files for writing
filename  = ""
if args.filename:
    filename = "{}".format(args.filename)
else:
    timestamp = datetime.datetime.now().isoformat().split('.')[0].replace(':', '_')
    filename  = "{}_ColumnRun".format(timestamp)

commonHdrs = 'Timestamp,upperBathTemp,upperExtTemp,lowerBathTemp,lowerExtTemp'

# Write resistances file
output = open("{}_res.csv".format(filename), "w")
output.write("{},{}\n".format(commonHdrs,",".join(thermistorNames)))
output.close()

# Write temperatures file
upperLim = ['{}_upperlimit'.format(x) for x in thermistorNames]
lowerLim = ['{}_lowerlimit'.format(x) for x in thermistorNames]
headers = [val for triplet in izip(thermistorNames, upperLim, lowerLim) for val in triplet]
output = open("{}_tmp.csv".format(filename), "w")
output.write("{},{}\n".format(commonHdrs, ",".join(headers)))
output.close()

# Wait...
if args.initDelay:
    time.sleep(args.initDelay)

# Start bath programs
if up:
    bathUpper.controlProgram("start")
if low:
    bathLower.controlProgram("start")

duration = np.max(tstop_up * rep_up, tstop_low * rep_low) * 60

# Start recording
for t in range(0, duration + readDelay, readDelay): 
    t0 = time.time()
    currentTime = datetime.datetime.now().isoformat()
    
    # read DAQ
    if channelList:
        print("Measuring DAQ")
        daqVals   = daq.readResistances(channelList)
        
        daqValsTmp = [Therm.calculateTemperature(res, name) for (res, name) in izip(daqVals, thermistorNames)]
        errMinus, errPlus = [Therm.calculateUncertainty(res, name) for (res, name) in izip(daqVals, thermistorNames)]
        daqValsTmp = [val for triplet in izip(daqValsTmp, errMinus, errPlus) for val in triplet]
        daqVals      = ",".join(map(str, daqVals))
        daqValsTmp   = ",".join(map(str, daqValsTmp))
    
    # read bath temps 
    T_up, T_low, Text_up, Text_low = -999, -999, -999, -999
    
    if up:
        T_up = bathUpper.getBathTemp()
        print('skipping external temperature for upper bath')
    if low:
        T_low = bathLower.getBathTemp()
        print('skipping external temperature for lower bath')

    # write data (resistances)
    with open("{}_res.csv".format(filename), "a") as output:
        output.write("{},{},{},{},{},{}\n".format(currentTime, T_up, Text_up, T_low, Text_low, daqVals))

     # write data (temperatures + uncertainties) 
    with open("{}_tmp.csv".format(filename), "a") as output:
        output.write("{},{},{},{},{},{}\n".format(currentTime, T_up, Text_up, T_low, Text_low, daqValsTmp))
    
    # wait until next measurement instant
    time.sleep(readDelay - (time.time() - t0))

# disconnect connected devices
map(lambda x: x.disconnect(), connected)

if args.email:
    cfg  = configparser.ConfigParser()
    cfg.read("lab.cfg")
    fromEmail = cfg["Email"]["address"]
    fromPass  = cfg["Email"]["password"]
    e = Emailer(fromEmail, fromPass)
    e.send(args.email, args.subject, ["{}_{}.csv".format(filename, mode) for mode in ["res", "tmp"]])
