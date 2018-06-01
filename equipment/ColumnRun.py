import argparse
import configparser
import datetime
import time

import numpy as np

from LaudaRP845 import LaudaRP845
from ColumnUtils import Thermistor
from logDAQ import getChannels, getChannelName

validChannels = range(101, 121) + range(201, 221) + range(301, 321)


# Default settings
channelList = []
dflt_initDelay = 0

dflt_duration  =  15 # minutes
dflt_port_up   =  12
dflt_port_low  =  9
dflt_ft_up     = '10 + (t/60)' # one degree per hour ramp
dflt_ft_low    = '10'         # 
dflt_up        =  1
dflt_low       =  1
dflt_rep_up    =  1
dflt_rep_up    =  1
dflt_tstop_up  =  15
dflt_tstop_low =  15

dflt_rdelay      =  90 # seconds between DAQ readings

parser = argparse.ArgumentParser(description="Read soil column temperatures from DAQ while cooling baths operate",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# Experiment control
parser.add_argument('--delay',    default=dflt_initDelay, type=int, help="How long to wait (minutes) before starting the experiment")

# Cooling plate control
parser.add_argument('--up',    default=dflt_up, type=int, help="Enable upper cooling plate 0 = off, 1 = on")
parser.add_argument('--low',    default=dflt_low, type=int, help="Enable lower cooling plate 0 = off, 1 = on")
parser.add_argument('--port_up',   default=dflt_port_up, type=int, help="Port for bath controlling upper cooling plate")
parser.add_argument('--port_low',  default=dflt_port_low, type=int, help="Port for bath controlling upper cooling plate")
parser.add_argument('--ft_up',     default=dflt_ft_up, type=str, help="Function defining upper cooling plate temperature as a funtion of 't' (minutes) e.g. '12 + (t/30)' or  '22' (for constant temperature")
parser.add_argument('--ft_low',    default=dflt_ft_low, type=str, help="Function defining lower cooling plate temperature as a funtion of 't' (minutes) e.g. '12 + (t/30)' or  '22' (for constant temperature")
parser.add_argument('--rep_up',    default=dflt_up, type=int, help="Number of repetitions for upper cooling plate program")
parser.add_argument('--rep_low',    default=dflt_up, type=int, help="Number of repetitions for lower cooling plate program")
parser.add_argument('--tstop_up',    default=dflt_tstop_up, type=int, help="Number of minutes to run upper cooling plate function before terminating or repeating")
parser.add_argument('--tstop_low',    default=dflt_tstop_low, type=int, help="Number of minutes to run lower cooling plate function before terminating or repeating")
parser.add_argument('--disc_up',    default=dflt_disc_up, type=int, help="Discretization interval for upper bath function")
parser.add_argument('--disc_low',    default=dflt_disc_low, type=int, help="Discretization interval for lower bath function")

# Thermistor control
parser.add_argument('--rdelay',    default=dflt_rdelay, type=int, help="number of seconds between thermistor measurements (DAQ)")
parser.add_argument('--channels', default=channelList, help="List of DAQ channels to read, see code for detailed documentation on format")
parser.add_argument('--filename', help="Filename of output csv file (.csv extention added automatically)")
parser.add_argument('--calib', help="Filename of thermistor calibration file")

# Email control
parser.add_argument('--email',    default="",                    help="Send results to this email")
parser.add_argument('--subject',  default="Experiment Complete", help="Email subject line")

# Set parameters from command line arguments
args = parser.parse_args()

up = args.up
low = args.low
port_up = args.port_up
port_low = args.port_low
ft_up = args.ft_up
ft_low = args.ft_low
rep_up = args.rep_up
rep_low = args.rep_low
tstop_up = args.tstop_up
tstop_low = args.tstop_low
disc_up = args.disc_up
disc_low = args.disc_low

channels     = getChannels(channelList)
channelNames = {}
for channel in sorted(channels):
    channelNames[str(channel)] = getChannelName(channel)


# Connect to instruments if they're needed
connected = []

if channelList:
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

for mode in ["res", "tmp"]:
    output = open("{}_{}.csv".format(filename, mode), "w")
    output.write("Timestamp,upperBathTemp,upperExtTemp,upperSetpoint,lowerBathTemp,lowerExtTemp,lowerSetpoint,{}\n".format(",".join([channelNames[str(channel)] for channel in sorted(channels)])))
    output.close()

# Wait...
if args.initDelay:
    time.sleep(args.initDelay)

# Start bath programs
if up:
    bathUpper.controlProgram("start")
if low:
    bathLower.controlProgram("start")

duration = np.max()
# Start recording
    for t in __: 
        t0 = time.time()
        
        # read and write DAQ
        print "\r  Measuring DAQ [{}/{}]".format(i+1, nReads),
        currentTime = datetime.datetime.now().isoformat()

        # measure bath temps 
        T_up, T_low, Text_up, Text_low = -999, -999, -999, -999
        if up:
            T_up = bathUpper.getBathTemp()
            print('skipping external temperature for upper bath')
        if low:
            T_low = bathLower.getBathTemp()
            print('skipping external temperature for lower bath')
    
    time.sleep(readDelay - (time.time() - t0))
'''
use nice argparse code from logDAQ
 --lower temperature file for lower plate
 --upper temperature file for upper plate
  every n seconds:
  get and write 


# define upper and lower functions from args with eval
str = '3*np.sin(t*np.pi/30)+15'
f_up = lambda t: eval(str)

kill subprocesses
'''

# disconnect connected devices
map(lambda x: x.disconnect(), connected)
