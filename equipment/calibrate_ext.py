import argparse
import configparser
import datetime
import time

import numpy as np

from LaudaRP845     import LaudaRP845
from Keysight34972A import Keysight34972A
from Fluke7341      import Fluke7341
from Fluke1502A     import Fluke1502A
from pyEmail        import Emailer
from ColumnUtils    import getChannels, getChannelName

port_up   =  9            # Which port to connect to for upper bath
port_low  =  12 # Which port to connect to for lower bath

parser = argparse.ArgumentParser(description="Read soil column temperatures from DAQ while cooling baths operate",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('--nreads',     default=5, type=int, help="how many reads")
parser.add_argument('--idelay',     default=0, type=int, help="Time (s) to wait for adjustment to initial setpoint corresponding to f(0) of the temperature control function. This delay is only used once at the start of the experiment (default: 0)")
parser.add_argument('--rdelay',    default=5,    type=int, help="Wait time (s) between thermistor (DAQ) and cooling bath measurements")
parser.add_argument('--filename',   type=str, help="calibration file")
args = parser.parse_args()
nreads = args.nreads
filename   = args.filename
readDelay   = args.rdelay
initDelay = args.idelay

# Connect to instruments if they're needed
connected = []

bath  = Fluke7341()
probe = Fluke1502A()
bathUpper = LaudaRP845()
bathLower = LaudaRP845()

if not bath.connect():
    print "Failed to connect to bath"
    daq.disconnect()
    exit(1)
connected.append(bath)

if not probe.connect():
    print "Failed to connect to probe"
    map(lambda x: x.disconnect(), connected)
    exit(1)
connected.append(probe)

if not bathUpper.connect(port=port_up):
    print("Failed to connect to upper bath")
    map(lambda x: x.disconnect(), connected)
    exit(1)
connected.append(bathUpper)

if not bathLower.connect(port=port_low):
    print("Failed to connect to lower bath")
    map(lambda x: x.disconnect(), connected)
    exit(1)
connected.append(bathLower)

# Prepare files for writing
commonHdrs = 'Timestamp,upperExtTemp,lowerExtTemp,probeTemp,bathTemp'

# Write resistances file
output = open(filename, "w")
output.write("{}\n".format(commonHdrs))
output.close()

print('delaying {} seconds'.format(initDelay))
time.sleep(initDelay)

# Start recording
print('start recording')
for t in range(0, nreads*readDelay, readDelay):
    t0 = time.time()
    currentTime = datetime.datetime.now().isoformat()


    # read external monitors
    Text_up = bathUpper.getExtTemp()
    Text_low = bathLower.getExtTemp()

    # read probe
    probeTemp = float(probe.readTemp())

    # read fluke bath
    bathTemp  = float(bath.readTemp())

    # write data (resistances)
    print('Ext1: {}, Ext2: {}, Probe: {},Bath: {}'.format(Text_up, Text_low, probeTemp, bathTemp))
    with open("{}".format(filename), "a") as output:
        output.write("{},{},{},{},{}\n".format(currentTime, Text_up, Text_low, probeTemp, bathTemp))

    # wait until next measurement instant
    time.sleep(readDelay - (time.time() - t0))

# disconnect connected devices
map(lambda x: x.disconnect(), connected)
