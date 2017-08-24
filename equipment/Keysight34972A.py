import visa
import time

# Controller class for Keysight 34972A Data Acquisition Unit

class Keysight34972A():

    PROMPT  = "34972A>"     # Expected text after every command is sent
    ENDL    = "\n"          # Character to end each command with

    # Address is USB device address, used for connecting to the device
    # ID is the expected string returned by '*IDN?' query, used to test for successful connection
    ADDRESS = u'USB::2391::8199::MY49021266::0::INSTR'
    ID      = u'Agilent Technologies,34972A,MY49021266,1.16-1.12-02-02\n'

    # ENUM for different operation modes
    # Temperature mode is not tested, but should work
    MODE_RESISTANCE  = 0
    MODE_TEMPERATURE = 1

    def __init__(self):
        self.rm = visa.ResourceManager()
        self.instance = None

        # list of sensors to scan, should be in the form of a list of integers, ex: [1, 2, 4, 5, 12, 17]
        # valid sensors are 1 through 22
        self.scanList = []

    def connect(self):

        self.instance = self.rm.open_resource(self.ADDRESS)
        id = (self._query("*IDN?"))
        if id != self.ID:
            print "ID discrepancy:"
            print "expected:", self.ID
            print "actual:  ", id
            return False

        #self.instance.timeout = None
        self._write("*RST")
        self._write("*CLS")
        return True

    # close the connection
    def disconnect(self):
        self.instance.close()

    # raw
    def _write(self, cmd):
        return self.instance.write(cmd)

    def _query(self, cmd):
        return self.instance.query(cmd)

    # initializes J-type thermocouples to be read in degrees Celsius
    # scanList is a list of probe IDs (can be 1 to 22)
    # ex: initialize([1]), initialize(range(1, 5)), initialize([1, 4, 6])
    def initialize(self, mode, scanList):

        for probe in scanList:
            if not (1 <= probe <= 22):
                print "probe must be an integer between 1 and 22 (inclusive)"
                exit(1)

        self.scanList = scanList

        # add 100 to each probe value (makes the probe ID attached to channel 1)
        scanList = [str(probe + 100) for probe in scanList]

        # convert list of probes to a scan list string
        probeString = ",".join(scanList)
        print probeString

        self._write("format:reading:channel 1;alarm 1;unit 1;time:type rel")
        if mode == self.MODE_TEMPERATURE:
            self._write("configure:temperature tc,j,DEF,(@{})".format(probeString))
        elif mode == self.MODE_RESISTANCE:
            self._write("configure:resistance (@{})".format(probeString))
        self._write("trigger:count 1")

    # read a float value from each sensor in scanList, returned as a list
    def readValues(self):
        self._write("initiate")
        temps = self._query("fetch?").split(',')
        return [float(temp) for temp in temps]

    # read float values for each sensor, but return it in a dict format, ex:
    # {"1": 20.1, "2": 32.5, "4": 30.6}
    def readValuesDict(self):
        tempDict = {}
        self._write("initiate")
        readings = self._query("fetch?").split(',')
        i = 0
        for probe in self.scanList:
            tempDict[str(probe)] = float(readings[i])
            i += 1

        return tempDict

# test code to read resistances from sensors 1 and 2, and return it in both list and dict formats
if __name__ == "__main__":

    keysight = Keysight34972A()

    if not keysight.connect():
        print "Failed to connect to Keysight34972A".format()
        exit(1)

    keysight.initialize(keysight.MODE_RESISTANCE, [1, 2])

    print keysight.readValues()

    print keysight.readValuesDict()


    keysight.disconnect()