### Tools to facilitate column experiments
import numpy as np
from pandas import read_csv, DataFrame

class Thermistor(object):
    """
    Provides tools to deal with thermistors based on external calibration
    and name files
    """
    def __init__(self):
        self.calibration = None

    def readNames(self, file):
        """
        Read a csv that gives the name of the thermistor in each channel
        """
        names = read_csv(file)
        self.channelNames = {x:y for (x,y) in zip(names.ix[:,0], names.ix[:,0])}
        mes = {x:y for (x,y) in zip(a.ix[:,0], a.ix[:,1])}

    def channelName(self, channel):
        """
        Get name of thermistor in channel.  Uses a csv to store names which allows for
        the replacement of thermistors over time if any burn out
        """
        if self.channelNames[channel]:
            name = self.channelNames[channel]
            return(name)

        else:
            raise LookupError('Channel not valid')

    def readCalibration(self, file):
        """
        reads a calibration file and stores parameters as a dictionary
        """
        calib = read_csv(file)
        calib = calib.set_index(calib.columns[0])
        self.calibration = calib.transpose().to_dict()
        return True

    def calculateTemperature(self, res, thermistor):
        """
        Calculates temperature for a particular thermistor provided that a
        suitable calibration is available
        """
        if self.calibration[thermistor]:
            C = self.calibration[thermistor]
            keys = ['a','b','c','d','R0']
            (a,b,c,d,R0) = [C[x] for x in keys]
            T = self.func(res, a, b, c, d, R0)
            return T
        else:
            raise LookupError('thermistor not in calibration file')

    def calculateUncertainty(self, res, thermistor):
        """
        calculates uncertainty on thermistor given
        """
        if self.calibration[thermistor]:
            C = self.calibration[thermistor]
            keys = ['a','b','c','d', 'uncert_a', 'uncert_b', 'uncert_c', 'uncert_d', 'R0']
            (a,b,c,d, uncert_a, uncert_b, uncert_c, uncert_d,R0) = [C[x] for x in keys]
            Ts = np.array([
                self.func(res, a + uncert_a, b + uncert_b, c + uncert_c, d + uncert_d, R0),
                self.func(res, a + uncert_a, b - uncert_b, c + uncert_c, d + uncert_d, R0),
                self.func(res, a + uncert_a, b + uncert_b, c - uncert_c, d + uncert_d, R0),
                self.func(res, a + uncert_a, b - uncert_b, c - uncert_c, d + uncert_d, R0),
                self.func(res, a - uncert_a, b + uncert_b, c + uncert_c, d + uncert_d, R0),
                self.func(res, a - uncert_a, b - uncert_b, c + uncert_c, d + uncert_d, R0),
                self.func(res, a - uncert_a, b + uncert_b, c - uncert_c, d + uncert_d, R0),
                self.func(res, a - uncert_a, b - uncert_b, c - uncert_c, d + uncert_d, R0),
                self.func(res, a + uncert_a, b + uncert_b, c + uncert_c, d - uncert_d, R0),
                self.func(res, a + uncert_a, b - uncert_b, c + uncert_c, d - uncert_d, R0),
                self.func(res, a + uncert_a, b + uncert_b, c - uncert_c, d - uncert_d, R0),
                self.func(res, a + uncert_a, b - uncert_b, c - uncert_c, d - uncert_d, R0),
                self.func(res, a - uncert_a, b + uncert_b, c + uncert_c, d - uncert_d, R0),
                self.func(res, a - uncert_a, b - uncert_b, c + uncert_c, d - uncert_d, R0),
                self.func(res, a - uncert_a, b + uncert_b, c - uncert_c, d - uncert_d, R0),
                self.func(res, a - uncert_a, b - uncert_b, c - uncert_c, d - uncert_d, R0)
                ])
            T = [min(Ts), max(Ts)]
            return T
        else:
            raise LookupError('thermistor not in calibration file')

    @staticmethod
    def func(R, a, b, c, d, R0):
        """
        Args:
            T temperature in
            a,b,c,d are calibration parameters
        """
        x = R / R0
        T = 1 / (a + b * np.log(x) + c * np.log(x)**2 + d * np.log(x)**3)
        return T

    def hasCalibration(self, thermistors):
        """ checks if a list of thermistors (names) have calibration data """
        if not self.calibration:
            print("Missing calibration file")
            return False

        missing = []
        for name in thermistors:
            if not self.calibration[name]:
                missing.append(name)

        if len(missing) == 0:
            return True

        print('\n'.join(map(str, missing)))
        return False

def getChannels(channelList):
    """get a set of channels from a text string"""
    validChannels = range(101, 121) + range(201, 221) + range(301, 321)
    channels = set()
    ranges = channelList.split(",")

    for rng in ranges:
        # For 'true' ranges
        if ":" in rng:
            lo, hi = map(int, rng.split(":"))
            for channel in range(lo, hi+1):
                if channel not in validChannels:
                    print "Invalid channel {}".format(channel)
                    exit(1)
                channels.add(channel)

       # For singletons
        else:
            if int(rng) not in validChannels:
                print "Invalid channel {}".format(channel)
                exit(1)
            channels.add(int(rng))

    return channels

def getChannelName(channel):
    """Get the name of a thermistor based on its channel"""
    slot = channel / 100
    k    = channel % 100 + 20 * (slot - 1)
    cable = 1 + (k-1) / 10
    return "T17-S{}C{}-{}".format(str(slot), str(cable), str(k).zfill(3))