import configparser
import re
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

    ERRORS              = {
        "2":  "Wrong input",
        "3":  "Wrong command",
        "5":  "Syntax error in value",
        "6":  "Illegal value",
        "8":  "Module not available",
        "30": "Programmer - all segments occupied",
        "31": "Setpoint not possible",
        "32": "TiH <= TiL",
        "33": "External sensor missing",
        "34": "Analogue value not available",
        "35": "Automatic is selected",
        "36": "No setpoint input possible, programmer is running or paused",
        "37": "No start from programmer possible, analogue setpoint input is switched on",
    }

    def __init__(self):
        self.conn = None
        self.err  = False

    # Connects and opens serial connection to specified port
    # port must be a string in the form COM* where * is one or more digits - ex. "COM7" or "COM12"
    def connect(self, port=0, baud=9600, timeout=2.0):
        """Scan serial ports for device and attempt connection."""
        cfg  = configparser.ConfigParser()
        cfg.read("lab.cfg")

        if port == 0: # default, no port specified
            port = cfg["LaudaRP845"].getint("Port")
            portList = [port] + range(1, 13)
        else:
            portList = [port]

        for p in portList:
            print "Attempting to connect to port {} ...".format(p),
            if self.tryPort(p, baud, timeout):
                print "Connected"

                # we connected to something, now request identifier to verify it is the RP845
                res = self.sendCmd("TYPE")
                if len(res) > 0:
                    if "RP  845" in res[0]:
                        print "  Correctly identified as Lauda RP 845"
                        cfg["LaudaRP845"]["Port"] = str(p)
                        with open("lab.cfg", "w") as cfgFile:
                            cfg.write(cfgFile)
                        return True
                    else:
                        print "  Failed to identify as Lauda RP 845"
                else:
                    print "  No response"
            else:
                print "Failed"

        return False

    def tryPort(self, port, baud, timeout):
        """Attempt to connect to a specific port."""
        port = "COM{}".format(port)
        try:
            self.conn = serial.Serial(port=port, baudrate=baud, timeout=timeout, rtscts=True, write_timeout=timeout)
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
        """Close serial connection."""
        self.conn.close()

    # Sends specified command to the LaudaRP845. Paramater cmd should be a string with no newline character
    def sendCmd(self, cmd, nBytes=4096, raw=False):
        """Send string over serial connection and return response."""
        cmd += self.ENDL
        cmd = bytearray(cmd)

        self._send(cmd)
        res = self._recv_all()

        # check for errors
        error = re.search(r"ERR_(\d+)", res[0])
        if error:
            self.err = True
            code = error.groups()[0]
            self.warning(self.ERRORS[code])

        # if no errors, return result
        self.err = False
        return res

    # Raw serial write - use method sendCmd unless you want to send an exact set of bytes
    def _send(self, bytes):
        """Send array of bytes over serial connection."""
        self.conn.write(bytes)

    # Receive response from device
    # Waits up to TIMEOUT_INIT for first byte of response, and then
    # waits TIMEOUT_CONSECUTIVE between each remaining byte of response.
    # This method returns faster than using a single timeout to wait for the full response
    def _recv_all(self, asLines=True):
        """Return the entirety of the read buffer."""
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
        if asLines:
            res = res.splitlines()
        return res

    # Reads temperature of bath
    # This is an alias for getBathTemp which is consistent with other classes
    def readTemp(self):
        """Return current bath temperature."""
        return self.getBathTemp()

    def setCoolingMode(self, mode):
        """Set cooling mode."""
        if level not in range(3):
            self.warning("Cooling mode must be in range [0, 2]")
            return False

        # convert to
        level = "{:03d}".format(level)
        res = self.sendCmd("out sp 02 {}".format(level))[0]
        if "OK" in res:
            self.info("Cooling mode changed to {} C".format(level))
            return True

        return False

    # Control mode 0 for internal thermometer control
    # Control mode 1 for external pt100 control
    # Control mode 2 and 3 for external analog/serial control
    def setControlMode(self, mode):
        """Set control mode."""
        if level not in range(3):
            self.warning("Control mode must be in range [0, 3]")
            return False

        # convert to
        level = "{:03d}".format(level)
        res = self.sendCmd("out mode 01 {}".format(level))[0]
        if "OK" in res:
            self.info("Control mode mode changed to {} C".format(level))
            return True

        return False

    # set the setpoint of the bath in the same units as set wih setUnits()
    def setSetpoint(self, setpoint):
        """Set bath setpoint."""
        if setpoint > self.SETPOINT_MAX:
            self.warning("Setpoint '{}' too high, max = {}. Setpoint unchanged.".format(setpoint, self.SETPOINT_MAX))
            return False

        if setpoint < self.SETPOINT_MIN:
            self.warning("Setpoint '{}' too low, min = {}. Setpoint unchanged.".format(setpoint, self.SETPOINT_MIN))
            return False

        # convert setpoint to string with format xxx.xx (lauda desired format)
        setpoint = "{:3.2f}".format(setpoint)

        res = self.sendCmd("out sp 00 {}".format(setpoint))[0]
        if "OK" in res:
            self.info("Setpoint changed to {} C".format(setpoint))
            return True

        return False

    def setPumpLevel(self, level):
        """Set pump level."""
        if level not in range(1, 9):
            self.warning("Pump level must be in range [1, 8]")
            return False

        # convert to
        level = "{:03d}".format(level)
        res = self.sendCmd("out sp 01 {}".format(level))[0]
        if "OK" in res:
            self.info("Pump level changed to {} C".format(level))
            return True

        return False

    def getBathTemp(self):
        """Get temperature measured by internal sensor."""
        res = self.sendCmd("in pv 10")[0].strip()
        return float(res)

    def getExtTemp(self):
        """Get temperature measured by external sensor."""
        res = self.sendCmd("in pv 13")[0].strip()
        return float(res)

    def getBathLevel(self):
        """Get current bath level."""
        res = self.sendCmd("in pv 05")[0].strip()
        return int(float(res))

    def getSetpoint(self):
        """Get current setpoint."""
        res = self.sendCmd("in sp 00")[0].strip()
        return float(res)

    def getPumpLevel(self):
        """Get current pump level."""
        res = self.sendCmd("in sp 01")[0].strip()
        return int(float(res))

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

# Simple test code
if __name__ == "__main__":

    lauda = LaudaRP845()
    if not lauda.connect():
        print "Failed to connect to LaudaRP845"
        exit(1)

    lauda.setSetpoint(12.34)
    print lauda.getBathTemp()
    #print lauda.getExtTemp()
    print lauda.getBathLevel()
    print lauda.getPumpLevel()
    print lauda.getSetpoint()

    lauda.disconnect()



