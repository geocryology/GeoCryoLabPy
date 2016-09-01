import datetime
import math
import sys
import time

from Keysight34972A import Keysight34972A
from Fluke7341  import Fluke7341
from Fluke1502A import Fluke1502A

NUM_PROBES      = 2
PROBE_LIST      = [1, 2]
SAMPLE_INTERVAL = 5
BUFFER_SIZE     = 5000
STD_HOLD_COUNT  = 5000
TEMP_INCREMENT  = 0.0

""" QUICK VALUES FOR TESTING
SAMPLE_INTERVAL = 2
BUFFER_SIZE = 5
STD_HOLD_COUNT = 5
"""

class RingBuffer():
    
    def __init__(self, size):
        self.size    = size
        self.buffer  = [0] * size
        self.pointer = 0
        self.count   = 0
        """
        for i in range(size):
            if i % 2:
                self.buffer[i] = -1e16
            else:
                self.buffer[i] =  1e16
        """

    def update(self, value):
        self.buffer[self.pointer] = value
        self.pointer = (self.pointer + 1) % self.size
        self.count += 1
        
    def reset(self):
        self.count   = 0

    def getAverage(self, silent=True):
        if self.count < self.size:
            if not silent:
                print "[WARNING] Buffer has not been filled completely: [{}/{}]".format(self.count, self.size)
        return sum(self.buffer) / self.size
        
    def getSTD(self):
        std = 0
        avg = self.getAverage()
        for i in range(self.size):
            std += (self.buffer[i] - avg) ** 2
        std /= self.size
        return math.sqrt(std)
        
    

def thermalRamp(start, end, increment, daq, bath, thermalProbe):

    setpoint = start
    bath.setSetpoint(setpoint)
    TEMP_INCREMENT = increment

    timestamp = datetime.datetime.now().isoformat().split('.')[0].replace(':', '-')
    csvFile   = "calibration{}.csv".format(timestamp)
    
    probeTitles = ",".join(["probe {}".format(i) for i in PROBE_LIST])
    averageTitles = ",".join(["average {}".format(i) for i in PROBE_LIST])
    f = open(csvFile, "w")
    f.write("time, elapsed time, setpoint, bath temp, probe temp,{},{}\n".format(probeTitles, averageTitles))
    f.close()
    
    # create ring buffer for each thermistor
    buffers = [RingBuffer(BUFFER_SIZE) for i in range(NUM_PROBES)]
    minSTDs = [1e9 for i in range(NUM_PROBES)]
    maxSTDs = [[0] * STD_HOLD_COUNT for i in range(NUM_PROBES)]
    counts  = [0 for i in range(NUM_PROBES)]
    
    done            = False
    numMeasurements = 0
    t0              = datetime.datetime.now()
    equilibriumTime = time.time()
    while not done:
    
        try:
            t1 = time.time()
            
            bathTemp    = float(bath.readTemp())
            probeTemp   = float(thermalProbe.readTemp())
            resistances = daq.readValues()
            numMeasurements += 1
            
            t = datetime.datetime.now()
            timestamp   = "{}/{}/{} {}:{}:{}".format(t.month, t.day, t.year, t.hour, t.minute, t.second)
            
            # calculate STD for all probes, update count if minimum doesn't change
            for i in range(NUM_PROBES):
                buffers[i].update(resistances[i])
                std = buffers[i].getSTD()
                if std < minSTDs[i]:
                    print "new lowest std"
                    minSTDs[i] = std
                    counts[i]  = 0
                elif int(std) > max(maxSTDs[i]):
                    print "std too high"
                    counts[i]  = 0
                else:
                    if numMeasurements > BUFFER_SIZE:
                        print "stabilizing"
                        counts[i] += 1
                    else:
                        print "need more measurements"
                maxSTDs[i] = maxSTDs[i][1:] + [int(std)]
                
            if abs(bathTemp - setpoint) > 0.01:
                print "bathTemp ({}) != setpoint ({})".format(bathTemp, setpoint)
                bath.setSetpoint(setpoint)
                counts = [0 for count in counts]
                
            # check if any probes are not at equilibrium
            allEqualized = True
            for i in range(NUM_PROBES):
                if counts[i] < STD_HOLD_COUNT:
                    allEqualized = False
                    break
                    
            r = ",".join([str(i) for i in resistances])
            a = ",".join([str(buffer.getAverage()) for buffer in buffers])
            
            t = datetime.datetime.now() - t0
            seconds =  t.seconds %    60
            minutes = (t.seconds /    60) % 60
            hours   = (t.seconds /  3600) % 24
            elapsedTime   = "{}:{}:{}".format(hours, minutes, seconds)
            
            
            f = open(csvFile, "a")
            f.write("{},{},{},{},{},{},{}".format(timestamp, elapsedTime, setpoint, bathTemp, probeTemp, r, a))
            
            # go to next setpoint
            if allEqualized and numMeasurements > BUFFER_SIZE:
                print "equalized"
                
                f.write(",{}".format(",".join([str(buffer.getAverage()) for buffer in buffers])))
                
                if abs(setpoint - end) < 0.001:
                    done = True
                else:    
                    setpoint += TEMP_INCREMENT
                    bath.setSetpoint(setpoint)
                
                for i in range(NUM_PROBES):
                    buffers[i].reset()
                    counts[i] = 0
                    
                numMeasurements = 0
                
                equilibriumTime = time.time() - equilibriumTime
                f.write(",{}".format(equilibriumTime))
                equilibriumTime = time.time()
 
            f.write("\n")
            f.close()
            
            print counts
                
            sampleTime = time.time() - t1
            
            if sampleTime < SAMPLE_INTERVAL:
                print "Elapsed: {}, Sleeping: {}".format(sampleTime, SAMPLE_INTERVAL - sampleTime)
                time.sleep(SAMPLE_INTERVAL - sampleTime)
            
        except KeyboardInterrupt:
            done = True

if __name__ == "__main__":

    # Connect to and initialize DAQ
    daq = Keysight34972A()
    if not daq.connect():
        print "Failed to connect to Keysight34972A".format()
        exit(1)
    daq.initialize(Keysight34972A.MODE_RESISTANCE, PROBE_LIST)
     
    # Connect to and initialize bath
    bath = Fluke7341()
    if not bath.connect("COM5"):
        print "Failed to connect to Fluke7341"
        exit(1)
        
    thermalProbe = Fluke1502A()
    if not thermalProbe.connect("COM7"):
        print "Failed to connect to Fluke1502A"
        exit(1)

    changeSetpoint = False
    setpoint       = 21.0
    if len(sys.argv) > 1:
        try:
            setpoint = float(sys.argv[1])
            changeSetpoint = True
        except ValueError:
            print "parameter must be a float"
            bath.disconnect()
            daq.disconnect()
            exit()
        
    if changeSetpoint:
        bath.setSetpoint(setpoint)

    # thermalRamp(1, -10, -0.1, daq, bath, thermalProbe)
    # thermalRamp(-10, 1, 0.1, daq, bath, thermalProbe)
    
    # thermalRamp(0, -4, -0.02, daq, bath, thermalProbe)
    # thermalRamp(-4, -6, -0.1, daq, bath, thermalProbe)
    # thermalRamp(-6, -10, -1.0, daq, bath, thermalProbe)
    
    # thermalRamp(-10, -6, 1.0, daq, bath, thermalProbe)
    # thermalRamp(-6, -4, 0.1, daq, bath, thermalProbe)
    # thermalRamp(-4, 0, 0.02, daq, bath, thermalProbe)
    
    thermalRamp(0.0, 1.0, 0.0, daq, bath, thermalProbe)
    
    bath.disconnect()
    daq.disconnect()
    thermalProbe.disconnect()
