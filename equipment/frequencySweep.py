import cmath
import datetime
import sys
import time

from Agilent4395A import Agilent4395A as Agilent


# Configures the analyzer with the following parameters:
#   fra      an connected instance if Agilent4395A
#   nPoints  number of points for the sweep (max 801)
#   f1       start frequency in Hz
#   f2       stop frequency in Hz
# The static configuration commands will set the following properties:
#   Network Analysis mode
#   Logarithmic sweep
#   Automatic measurement bandwidth
def configure(fra, nPoints, f1, f2):
    print ""
    print "Configuring analyzer:"
    print "  nPoints: {}".format(nPoints)
    print "  f1:      {}".format(f1)
    print "  f2:      {}".format(f2)

    commands = """NA
        CHAN1
        HOLD
        SWPT LOGF
        BW 10
        POIN {}
        FORM4
        MEAS {{}}
        PHAU DEG
        STAR {} HZ
        STOP {} HZ
        POWE 0
        FMT LINM""".format(nPoints, f1, f2)

    # repeat configuration per channel
    for channel in ["A", "B"]:

        commandList = commands.format(channel).split("\n")

        for command in commandList:
            fra.write(command)

        # allow some time for configuration to finish
        print "  Channel {} ...".format(channel),
        time.sleep(15)
        print "Done"


# Makes a measurement, saves data to file
def measure(fra, powerLevel):

    fmts = ["LINM", "PHAS", "REAL", "IMAG", "LOGM"]
    results = {"A": {}, "B": {}}
    channels = ["A", "B"]

    # set power level
    fra.write("POWE {}".format(powerLevel))
    time.sleep(1)

    # Get sweep duration (tells us how long to wait for results)
    t = 60
    try:
        duration = fra.query("SWET?").strip()
        t = float(duration)
        print "Sweep time: {}".format(t)
    except:
        print "failed to convert to float: ", duration

    t0 = time.time()
    # perform sweep, read results
    for channel in channels:

        fra.write("MEAS {}".format(channel))
        time.sleep(1)

        # Make measurement
        t0 = time.time()
        fra.write("SING")
        while (time.time() < t0 + t + 2):
            print "\rReading Channel {}: {}%".format(channel, int(100 * (time.time() - t0) / (t + 2))),
            time.sleep(0.125)
        print "\rReading Channel {}: 100%".format(channel)

        # Read data from analyzer
        for fmt in fmts:
            fra.write("FMT {}".format(fmt))

            # results are read as list of x1,y1,x2,y2,x3,y3... where every yn value is 0.
            response = fra.query("OUTPDTRC?")

            # this line splits the list at every comma, strips out every second value, and converts to floats
            results[channel][fmt] = map(float, response.strip().split(",")[::2])

        # Read x-axis values (frequency points)
        freqs = fra.query("OUTPSWPRM?").strip()
        freqs = map(float, freqs.split(","))

    return (results, freqs)

def generateFile(filename, results, freqs, Rs, nPoints, f1, f2, powerLevel):

    timestamp = datetime.datetime.now().isoformat()

    # write values to file
    filename = "{}_{}dB.csv".format(filename, str(powerLevel).replace(".", "-"))
    output = open("march 21 2019/" + filename, "w")
    output.write("Impedance Measurement Performed with an Agilent 4395A Network Analyzer\n")
    output.write("File generated on: {}\n".format(timestamp))
    output.write("Rs = {} ohms\n".format(Rs))
    output.write("Impedance Calculation: Rs x (Va - Vb) / Vb\n")
    output.write("Start Frequency: {} Hz\n".format(f1))
    output.write("Stop  Frequency: {} Hz\n".format(f2))
    output.write("Number of data points: {}\n".format(nPoints))
    output.write("Source Power (dB): {}\n".format(powerLevel))
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


if __name__ == "__main__":

    # default values
    Rs = 50.0
    nPoints = 201
    f1 = 10
    f2 = 50000000
    filename = "out"

    # power level in dB, as an array
    # use array of size 1 for single measurement (e.g. [0] for 0 dB)
    # range function easily makes a list of evenly spaced integers
    #powerLevels = range(-10, 11, 2)
    powerLevels = [0]

    if len(sys.argv) != 3:
        print "  Usage: python frequencySweep.py filename Rs"
        exit()

    filename = sys.argv[1]

    try:
        Rs = float(sys.argv[2])
    except:
        print "Failed to convert Rs to float"
        exit()

    fra = Agilent()

    if not fra.connect():
        print "Failed to connect to Agilent4395A"
        exit(1)



    # send configuration to analyzer
    configure(fra, nPoints, f1, f2)

    i = 0
    for powerLevel in powerLevels:
        results, freqs = measure(fra, powerLevel)
        generateFile(filename, results, freqs, Rs, nPoints, f1, f2, powerLevel)
        i += 1
        print "{}done {}/{} sweeps".format(chr(8)*32, i, len(powerLevels)),

    fra.disconnect()
