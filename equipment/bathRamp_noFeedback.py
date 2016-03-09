# This script will ramp the temperature in the bath from TEMP_MIN to TEMP_MAX degrees 
# Celsius. The temperature will be incremented in steps of INCREMENT degrees, and remain
# at each step for HOLD_TIME seconds. 

import time

from Fluke1502A import Fluke1502A
from Fluke7341  import Fluke7341

TEMP_MIN  = -5.00
TEMP_MAX  = 5.00
INCREMENT = 0.5
HOLD_TIME = 180
TOLERANCE = 0.05

def waitStable(targetTemp, probe):
    t0 = time.time()
    done = False
    currentTemp = float(probe.readTemp())
    
    while not done:
        if not (targetTemp - TOLERANCE < currentTemp < targetTemp + TOLERANCE):
            print "temp not stable: {}".format(currentTemp)
            t0 = time.time()
        else:
            print "temp stable: {}, waiting {} s".format(currentTemp, HOLD_TIME - (time.time() - t0))
            if (time.time() - t0) >= HOLD_TIME:
                done = True
        time.sleep(5)
        currentTemp = float(probe.readTemp())
        
    return True
    
if __name__ == "__main__":
    
    if TEMP_MAX < TEMP_MIN:
        print "TEMP_MAX < TEMP_MIN"
        exit(1)
    
    bath  = Fluke7341()
    probe = Fluke1502A()
    temp  = TEMP_MIN
    done  = False
    
    
    if not bath.connect("COM7"):
        print "Failed to connect to bath"
        exit(1)
        
    if not probe.connect("COM5"):
        print "Failed to connect to probe"
        exit(1)
        
    while not done:
        #print "Changing setpoint to {}".format(temp)
        bath.setSetpoint(temp)
        waitStable(temp, probe)
        
        if temp < TEMP_MAX:
            temp += INCREMENT
        else:
            done = True        
        
    bath.disconnect()
    probe.disconnect()