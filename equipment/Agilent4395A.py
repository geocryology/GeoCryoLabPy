"""
Python class representing the Agilent4395A Frequency Response Analyzer
"""
import cmath
import datetime
import sys
import visa

from draw import draw

# Controller class for the Agilent 4395A Frequency Response Analyzer
#   - operates over GPIB using a National Instruments USB-GPIB cable
#
# GPIB uses two methods for communication:
#   WRITE - Sends a command, doesn't return a response
#   QUERY - Sends a command, followed by a '?', and returns a response


class Agilent4395A:

    # GPIB Address, used to specify connection
    ADDRESS = u'GPIB0::16::INSTR'

    # GPIB ID string, returned by the '*IDN?' query, used to test if connection is successful
    ID = u'HEWLETT-PACKARD,4395A,MY41101925,REV1.12\n'

    def __init__(self):
        self.rm = visa.ResourceManager()
        self.analyzer = None

    # Connect to and initialize the analyzer
    def connect(self):

        self.analyzer = self.rm.open_resource(self.ADDRESS)
        currentID = (self.query("*IDN?"))
        if currentID != self.ID:
            print "ID discrepancy:"
            print "  expected:", self.ID
            print "  actual:  ", currentID
            return False

        self.write("*RST")
        self.write("*CLS")
        return True

    # Close the connection (should be done before script exits)
    def disconnect(self):
        self.analyzer.close()

    # Sends a string to the analyzer, does not return a response
    def write(self, cmd):
        self.analyzer.write(cmd)

    # Sends a string (must end with '?'), returns response
    # If the response is large, it may take several seconds to return
    def query(self, cmd):
        return self.analyzer.query(cmd)

if __name__ == "__main__":

    # Test script, sends some configuration commands and reads the measured data

    import time

    fra = Agilent4395A()


    if not fra.connect():
        print "Failed to connect to Agilent4395A"
        exit(1)

    # dictionaries to store measurements
    results = {"A": {}, "B": {}}
    channels = ["A", "B"]
    filename = sys.argv[1]

    # Setup parameters
    Rs = 50.0 # resistance, ohms
    power = 0.0 # dB
    nPoints = 201
    f1 = 100
    f2 = 100000000

    # overwrite power from command line
    if len(sys.argv) == 3:
        power = eval(sys.argv[2])

    # Validate parameters
    if not (1 <= nPoints <= 801):
        print "nPoints must be in the range [0, 801]"
        exit()

    if not (f1 < f2):
        print "f1 must be less than f2"
        exit()

    if not (10 <= f1 <= 510000000):
        print "start/stop frequencies must be in the range [10, 510M]"
        exit()

    if not (10 <= f2 <= 510000000):
        print "start/stop frequencies must be in the range [10, 510M]"
        exit()

    # BWAUTO 1
    fmts = ["LINM", "PHAS", "REAL", "IMAG", "LOGM"]
    commands = """NA
        CHAN1
        HOLD
        SWPT LOGF
        BWAUTO 1
        POIN {}
        FORM4
        MEAS {{}}
        PHAU DEG
        STAR {} HZ
        STOP {} HZ
        POWE {}
        FMT LINM""".format(nPoints, f1, f2, power)

    for channel in channels:
        #print "press enter to measure channel {}".format(channel), raw_input()

        # Configure analyzer for measurements
        print "Configuring analyzer for measurement of channel {}".format(channel)
        commandList = commands.format(channel).split("\n")
        for cmd in commandList:
            fra.write(cmd.strip())
        time.sleep(15)

        # Get sweep duration
        t = 10
        try:
            duration = fra.query("SWET?").strip()
            t = float(duration)
        except:
            print "failed to convert to float: ", duration
            t = 180
        print "sweep time: {}".format(t)

        # Make measurement
        t0 = time.time()
        fra.write("SING")
        while time.time() < t0 + t + 2:
            print "waiting"
            time.sleep(1)

        # Read data from analyzer
        for fmt in fmts:
            print "Reading Channel {}: {} ...".format(channel, fmt),
            fra.write("FMT {}".format(fmt))

            # results are read as list of x1,y1,x2,y2,x3,y3... where every yn value is 0.
            # this line splits the list at every comma, strips out every second value, and converts to floats
            response = fra.query("OUTPDTRC?")
            print "done - {} bytes".format(len(response))
            results[channel][fmt] = map(float, response.strip().split(",")[::2])

    # Read x-axis values (frequency points)
    freqs = fra.query("OUTPSWPRM?").strip()
    freqs = map(float, freqs.split(","))

    timestamp = datetime.datetime.now().isoformat()

    print "saving file"
    filename = "sweepResults_{}.csv".format(filename)
    output = open(filename, "w")
    output.write("Impedance Measurement Performed with an Agilent 4395A Network Analyzer\n")
    output.write("File generated on: {}\n".format(timestamp))
    output.write("Rs = {} ohms\n".format(Rs))
    output.write("Impedance Calculation: Rs x (Va - Vb) / Vb\n")
    output.write("Start Frequency: {} Hz\n".format(f1))
    output.write("Stop  Frequency: {} Hz\n".format(f2))
    output.write("Number of data points: {}\n".format(nPoints))
    output.write("Source Power (dB): {}\n".format(power))
    output.write("Measurement BW: auto \n")
    output.write("\n") # Store additional info here
    output.write("\n") # Store additional info here
    output.write("Frequency,Va (real),Va (imag),Vb (real),Vb (imag),Va Mag,Va Phase,Vb Mag,Vb Phase,Impedance Mag,Impedance Phase\n")

    for i in range(nPoints):
        freq   = freqs[i]
        VaReal = results["A"]["REAL"][i]
        VaImag = results["A"]["IMAG"][i]
        VbReal = results["B"]["REAL"][i]
        VbImag = results["B"]["IMAG"][i]
        Va     = VaReal + 1j * VaImag
        Vb     = VbReal + 1j * VbImag
        Z      = Rs * (Va - Vb) / Vb
        VaMag, VaPhase = cmath.polar(Va)
        VbMag, VbPhase = cmath.polar(Vb)
        ZMag, ZPhase   = cmath.polar(Z)
        VaPhase        = 180 * VaPhase / cmath.pi
        VbPhase        = 180 * VbPhase / cmath.pi
        ZPhase         = 180 * ZPhase / cmath.pi

        output.write("{},{},{},{},{},{},{},{},{},{},{}\n".format(
            freq, VaReal, VaImag, VbReal, VbImag,
            VaMag, VaPhase, VbMag, VbPhase, ZMag, ZPhase))

    output.close()

    fra.disconnect()

    #time.sleep(1)

    draw(filename)

    exit()