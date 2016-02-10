import math
import time

from Fluke1502A import Fluke1502A

NUM_SAMPLES = 1000
MAX_STD_DEV = 0.0001

def getStd(samples, avg):
    std = 0
    for i in range(len(samples)):
        std += (samples[0] - avg) ** 2
    std /= len(samples)
    return math.sqrt(std)
    
if __name__ == "__main__":

    probe   = Fluke1502A()
    done    = False
    samples = []
    
    if not probe.connect("COM5"):
        print "Failed to connect to probe"
        exit(1)
        
    while len(samples) < NUM_SAMPLES:
        samples.append(float(probe.readTemp()))
        avg = sum(samples) / len(samples)
        std = getStd(samples, avg)
        print chr(8) * 80, "[{}/{}] samples - average: {:.6}, STD: {:.6}        ".format(len(samples), NUM_SAMPLES, avg, std),
        
    print ""
    
    oldestSampleIndex = 0
    std = 1e9
    while std > MAX_STD_DEV:
        samples[oldestSampleIndex] = float(probe.readTemp())
        oldestSampleIndex = (oldestSampleIndex + 1) % NUM_SAMPLES
        
        average = sum(samples) / NUM_SAMPLES
        std     = getStd(samples, average)
        
        print chr(8) * 48, "[{}]Average: {}, STD: {}".format(oldestSampleIndex, average, std),
    
    print "Done"
        
    
    