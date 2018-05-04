import argparse
import configparser
import datetime
import time

import numpy as np

from Keysight34972A import Keysight34972A
from Fluke7341      import Fluke7341
from Fluke1502A     import Fluke1502A
from pyEmail        import Emailer

validChannels = range(101, 121) + range(201, 221) + range(301, 321)

def getChannels(channelList):
    channels = set()
    ranges = channelList.split(",")
    for rng in ranges:
        if ":" in rng:
            lo, hi = map(int, rng.split(":"))
            for channel in range(lo, hi+1):
                if channel not in validChannels:
                    print "Invalid channel {}".format(channel)
                    exit(1)
                channels.add(channel)
        else:
            if channel not in validChannels:
                print "Invalid channel {}".format(channel)
                exit(1)
            channels.add(int(rng))
    return channels

def getChannelName(channel):
    slot = channel / 100
    k    = channel % 100 + 20 * (slot - 1)
    cable = 1 + (k-1) / 10
    return "T17-S{}C{}-{}".format(str(slot), str(cable), str(k).zfill(3))

# Default settings
startTemp =  5      # Initial bath temperature
endTemp   = -2      # Final bath temperature
resetTemp = 20      # Reset bath to this temperature after experiment ends
increment = 1       # Temperature increment between setpoints
nReads    = 10      # Number of times to read values from DAQ at each setpoint

tempDelay = 20 * 60 # Time delay between setpoints (in seconds)
readDelay = 15      # Time delay between subsequent DAQ reads (in seconds)
initDelay = 20 * 60 # Additional time delay only for adjusting to initial bath temperature
# DAQ channels to read
# - Sensors are identified by DAQ slot (1-3, first digit)
#   and sensor number (1-20, second and 3rd digits)
# - Channels must be comma separated, i.e. 101,102,103,202,203
# - Channels can be specified as a range, i.e. 101:110 for sensors 1-10
# - Ranges can be comma separated, i.e. 101:105,110:115 for sensors 1-5 and 10-15
# - Ranges can only contain sensors on one slot, so 101:320 will not work
channelList  = "101:120,201:220,301:320"

parser = argparse.ArgumentParser(description="Read DAQ while stepping bath through temperature ramp",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--start',    default=startTemp, type=float, help="Initial bath temperature")
parser.add_argument('--end',      default=endTemp,   type=float, help="Final bath temperature")
parser.add_argument('--reset',    default=resetTemp, type=float, help="Bath will reset to this temperature after experiment")
parser.add_argument('--inc',      default=increment, type=float, help="Temperature increment between setpoints")
parser.add_argument('--nreads',   default=nReads,    type=int,   help="Number of times to read from DAQ at each setpoint")
parser.add_argument('--tdelay',   default=tempDelay, type=int,   help="Time (s) to wait between setpoints")
parser.add_argument('--rdelay',   default=readDelay, type=int,   help="Time (s) to wait between subsequent DAQ reads")
parser.add_argument('--idelay',   default=initDelay, type=int,   help="Time (s) to wait for adjustment to initial setpoint. This delay is only used once at the start of the experiment")

parser.add_argument('--channels', default=channelList,           help="List of DAQ channels to read, see code for detailed documentation on format")
parser.add_argument('--filename', help="Filename of output csv file (.csv extention added automatically)")
parser.add_argument('--eta', action='store_const', default=False, const=True, help="Print estimated time and exit without running experiment")

parser.add_argument('--email',    default="",                    help="Send results to this email")
parser.add_argument('--subject',  default="Experiment Complete", help="Email subject line")
args = parser.parse_args()

startTemp = args.start
endTemp   = args.end
resetTemp = args.reset
increment = args.inc
nReads    = args.nreads

tempDelay = args.tdelay
readDelay = args.rdelay
initDelay = args.idelay

channelList = args.channels

channels     = getChannels(channelList)
channelNames = {}
for channel in sorted(channels):
    channelNames[str(channel)] = getChannelName(channel)

if startTemp > endTemp:
    increment = -abs(increment)
else:
    increment = abs(increment)

setpoints = np.arange(startTemp, endTemp + 0.001 * np.sign(increment), increment)
duration = len(setpoints) * (tempDelay + nReads * readDelay)
print "Estimated completion time: {} hours".format(1.0 * duration / 3600)

if args.eta:
    exit()

daq   = Keysight34972A()
bath  = Fluke7341()
probe = Fluke1502A()

if not daq.connect():
    print "Failed to connect to DAQ"
    exit(1)

if not bath.connect():
    print "Failed to connect to bath"
    daq.disconnect()
    exit(1)

if not probe.connect():
    print "Failed to connect to probe"
    bath.disconnect()
    daq.disconnect()
    exit(1)

filename  = ""
if args.filename:
    filename = "{}".format(args.filename)
else:
    timestamp = datetime.datetime.now().isoformat().split('.')[0].replace(':', '_')
    filename  = "{}".format(timestamp)

for mode in ["res", "avg", "std"]:
    output = open("{}_{}.csv".format(filename, mode), "w")
    output.write("Time,Setpoint,ProbeTemp,BathTemp,{}\n".format(",".join([channelNames[str(channel)] for channel in sorted(channels)])))
    output.close()

bath.setSetpoint(setpoints[0])
time.sleep(initDelay)
for setpoint in setpoints:
    bath.setSetpoint(setpoint)
    time.sleep(tempDelay)

    # lists to hold results of batch of measurements
    probeTemps = []
    bathTemps  = []
    daqResults = []
    measureStartTime = datetime.datetime.now().isoformat() # time that first measurement in a batch is taken

    for i in range(nReads):
        t0 = time.time()
        print "\r  Measuring DAQ [{}/{}]".format(i+1, nReads),
        currentTime = datetime.datetime.now().isoformat()

        probeTemp = float(probe.readTemp())
        probeTemps.append(probeTemp)

        bathTemp  = float(bath.readTemp())
        bathTemps.append(bathTemp)

        daqVals   = daq.readResistances(channelList)
        daqResults.append(daqVals)
        daqVals   = ",".join(map(str, daqVals))
        with open("{}_res.csv".format(filename), "a") as output:
            output.write("{},{},{},{},{}\n".format(currentTime, setpoint, probeTemp, bathTemp, daqVals))

        time.sleep(readDelay - (time.time() - t0))

    # compute mean and std of each column
    probeMean = np.mean(probeTemps)
    probeStd  = np.std(probeTemps)

    bathMean  = np.mean(bathTemps)
    bathStd   = np.std(bathTemps)

    daqMeans  = np.mean(daqResults, axis=0)
    daqStds   = np.std(daqResults, axis=0)



    # convert results to strings
    daqMeans  = ",".join(map(str, daqMeans))
    daqStds   = ",".join(map(str, daqStds))

    with open("{}_avg.csv".format(filename), "a") as output:
        output.write("{},{},{},{},{}\n".format(measureStartTime, setpoint, probeMean, bathMean, daqMeans))

    with open("{}_std.csv".format(filename), "a") as output:
        output.write("{},{},{},{},{}\n".format(measureStartTime, setpoint, probeStd, bathStd, daqStds))

    print ""


bath.setSetpoint(resetTemp)

bath.disconnect()
probe.disconnect()
daq.disconnect()

if args.email:
    cfg  = configparser.ConfigParser()
    cfg.read("lab.cfg")
    fromEmail = cfg["Email"]["address"]
    fromPass  = cfg["Email"]["password"]
    e = Emailer(fromEmail, fromPass)
    e.send(args.email, args.subject, ["{}_{}.csv".format(filename, mode) for mode in ["res", "avg", "std"]])
