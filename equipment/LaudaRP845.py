import serial

# Class for LAUDA RP 845 Recirculating Bath with Serial Interface
#   - Temperatures are read in Celsius
#   - Serial interface should be configured to 9600 BAUD, 1 stop bit, no parity, 8 data bits

class LaudaRP845:

    ENDL                = "\r"          # character to send after a command
    TIMEOUT_INIT        = 2.00          # time to wait for first character of response
    TIMEOUT_CONSECUTIVE = 0.25          # max time to wait for each subsequent character
    CHARS_PER_READ      = 16            # reads response 16 bytes at a time

    # Setpoint Min/Max values are in Celsius
    # These values are safety constraints, they can be changed as necessary
    SETPOINT_MAX        =  50
    SETPOINT_MIN        = -25

    def __init__(self, units="c"):
        self.units = units
        self.conn = None

    # Connects and opens serial connection to specified port
    # port must be a string in the form COM* where * is one or more digits - ex. "COM7" or "COM12"
    def connect(self, port=0, baud=9600, timeout=2.0):

        if port == 0: # default, no port specified
            portList = range(1, 12)
        else:
            portList = [port]

        for p in portList:
            print "Attempting to connect to port {} ...".format(p),
            if self.tryPort(p, baud, timeout):
                print "Connected"

                # we connected to something, now request identifier to verify it is the 1502A
                res = self.sendCmd("")
                if len(res) > 0:
                    if "ver.7341,1.08" in res[0]:
                        print "  Correctly identified as Fluke 7431"
                        return True
                    else:
                        print "  Failed to identify as Fluke 7431"
                else:
                    print "  No response"
            else:
                print "Failed"

        return False

    def tryPort(self, port, baud, timeout):
        port = "COM{}".format(port)
        try:
            self.conn = serial.Serial(port=port, baudrate=baud, timeout=timeout, rtscts=True, write_timeout=timeout)
            self.setUnits("c")
            self.sendCmd("sa=0")        # disable automatic data readout
            self._recv_all()            # clears read buffer
        except ValueError:
            self.error("Invalid COM port or Baud rate specified")
            return False
        except serial.SerialException:
            return False
        except serial.SerialTimeoutException:
            return False

        return True

    # Closes the serial connection
    def disconnect(self):
        self.conn.close()

    # Sends specified command to the Fluke7341. Paramater cmd should be a string with no newline character
    def sendCmd(self, cmd, nBytes=4096):
        cmd += self.ENDL
        cmd = bytearray(cmd)

        self._send(cmd)
        return self._recv_all()

    # Raw serial write - use method sendCmd unless you want to send an exact set of bytes
    def _send(self, bytes):

        self.conn.write(bytes)

    # Receive response from device
    # Waits up to TIMEOUT_INIT for first byte of response, and then
    # waits TIMEOUT_CONSECUTIVE between each remaining byte of response.
    # This method returns faster than using a single timeout to wait for the full response
    def _recv_all(self):
        res = ""
        originalTimeout   = self.conn.timeout
        self.conn.timeout = self.TIMEOUT_INIT

        # check for response
        byte = self.conn.read()
        if not byte: # tests if response is empty
            return ""
        else:
            res += str(byte)

        self.conn.timeout = self.TIMEOUT_CONSECUTIVE

        # continuously read bytes until buffer is empty
        while byte:
            byte = self.conn.read()
            res += str(byte)

        self.conn.timeout = originalTimeout
        return res.splitlines()[1:]

    # Reads temperature of bath, returned as string
    def readTemp(self):
        res  = self.sendCmd("t")
        #print res
        temp = res[0][2:10].strip()
        return temp

    # set units of measurements for the device
    # valid options for units are as follows (case insensitive):
    #   Celsius   - "c", "celsius"
    #   Farenheit - "f", "farenheit"
    def setUnits(self, units):
        units = units.lower()
        if   units in ["c", "celsius"]:
            self.sendCmd("u=c")
            self.units = "c"
        elif units in ["f", "farenheit"]:
            self.sendCmd("u=f")
            self.units = "f"
        else:
            self.warning("Invalid units: {}".format(units))
            return False

        return True

    # set the setpoint of the bath in the same units as set wih setUnits()
    def setSetpoint(self, setpoint, units="c"):

        if units != self.units:
            if not self.setUnits(units):
                self.warning("Invalid units '{}', setpoint unchanged".format(units))
                return False

        if setpoint > self.SETPOINT_MAX:
            self.warning("Setpoint '{}' too high, max = {}. Setpoint unchanged.".format(setpoint, self.SETPOINT_MAX))
            return False

        if setpoint < self.SETPOINT_MIN:
            self.warning("Setpoint '{}' too low, min = {}. Setpoint unchanged.".format(setpoint, self.SETPOINT_MIN))
            return False

        self.sendCmd("s={}".format(setpoint))
        self.info("Setpoint changed to {} {}".format(setpoint, units))
        return True

    """
    def calibrate(self, low, high, waitTime):
        r0    = self.getR0()
        alpha = self.getAlpha()
    """

    # Prints info message
    def info(self, msg):
        print "[INFO] " + format(msg)

    # Prints warning message but does not exit
    def warning(self, msg):
        print "[WARNING] " + format(msg)

    # Prints error message and exits
    def error(self, msg):
        print "[ERROR] " + format(msg)
        exit(1)

# Simple test code, logs 10 readings to a csv file
if __name__ == "__main__":

    import csv
    import datetime
    import time

    fluke = Fluke7341()
    if not fluke.connect():
        print "Failed to connect to Fluke7341"
        exit(1)

    print "temp: {}".format(fluke.sendCmd("t"))

    fluke.setSetpoint(-40)
    fluke.setSetpoint(100)
    fluke.setSetpoint(0)

    with open("out.csv", "wb") as csvFile:
        csvFile.write("time,{}".format(fluke.units))

        for i in range(10):
            timestamp = datetime.datetime.now().isoformat().split(".")[0]
            csvFile.write("{},".format(timestamp))
            csvFile.write(fluke.readTemp())
            csvFile.write("\r\n")

    #print fluke.readTemp()

    fluke.disconnect()


