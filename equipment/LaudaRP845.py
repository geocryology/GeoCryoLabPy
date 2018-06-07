import configparser
import re
import serial
from numpy import diff, concatenate, floor

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
    SETPOINT_MIN        =  2 #[NB] changed to 2 deg for now until there is glycol in the bath

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
    # port must be an integer corresponding to the desired port (e.g. 12 = COM12)
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

        # convert to string
        level = "{:03d}".format(level)
        res = self.sendCmd("out sp 01 {}".format(level))[0]
        if "OK" in res:
            self.info("Pump level changed to {}".format(level))
            return True

        return False

    def setProgram(self, program):
        """Select one of the 5 programmable temperature-time profiles"""
        if not (1 <= program <= 5 and isinstance(program, int)):
            self.warning("Program {:0d} not set. Choose an integer between 1 and 5".format(program))
            return False

        res = self.sendCmd("rmp select {}".format(program))[0].strip()

        if "OK" in res:
            self.info("Program {:0d} has been selected".format(program))
            return True

        return False

    def setProgramSegment(self, temp, time, tol, pump=8, start=False):
        """Append a segment to the currently selected program"""
        if temp > self.SETPOINT_MAX:
            self.warning("Setpoint '{}' too high, max = {}. Segment not added.".format(temp, self.SETPOINT_MAX))
            return False

        if temp < self.SETPOINT_MIN:
            self.warning("Setpoint '{}' too low, min = {}. Segment not added.".format(temp, self.SETPOINT_MIN))
            return False

        # convert values to strings in appropriate format
        temp = "{:3.2f}".format(temp)
        time = "{:05d}".format(time)
        tol = "{:3.2f}".format(tol)
        pump = "{:01d}".format(pump)

        program = int(self.getCurrentProgram())
        res = self.sendCmd("rmp out 00 {} {} {} {}".format(temp, time, tol, pump))[0].strip()

        if "OK" in res:
            self.info("Segment appended to program {:0d}".format(program))
            return True

        return False

    def setProgramRepetitions(self, reps):
        """Set the number of times the program runs (0 - 250) 0 = unlimited"""
        if not 0 <= reps <= 250:
                self.error("Choose between 0 and 250 repetitions")

        n =  "{:03d}".format(reps)
        program = int(self.getCurrentProgram())
        res = self.sendCmd("rmp out 02 {}".format(n))

        if "OK" in res:
            self.info("Program {:0d} will run {} times".format(program, re.sub('^0$', 'infinitely many', n)))
            return True

        return False

    def setProgramProfile(self, program, f_temp, stop, step, reps = 1, f_pump = None, f_tol = None):
        """
        Defines a program (temperature-time profile) based on the values of a function

        Args:
            f_temp (function): a function f(x) defined on the closed interval [0, stop] that
            returns a temperature value for any x in its domain where x is measured in minutes
            stop (int): for how many minutes should the program run
            step (int): time discretization of function in minutes (minimum 1 minute)
            reps (int): how many times should the function repeat
            program (int): Which program slot to save in?
            f_pump (function): Optionally, a function g(x) that defines the pump level on [0, stop]
            If not supplied, pump level will be set to a constant value equal to the current pump level

        If using a sinusoidal function, ensure that the period is a multiple of
        the step size to avoid aliasing problems
        """
        # erase the current program
        self.setProgram(program)
        self.deleteProgram()

        # Use current pumplevel if no function is defined for it
        if f_pump is None:
            p = self.getPumpLevel()
            f_pump = lambda x: p

        # ensure bath achieves target temperature before starting
        if f_tol is None:
            f_tol = lambda x: 0.1 if x == 1 else 0

        # Define each timstep. In the future, these don't have to be evenly spaced
        times = range(0, stop + step, step)
        intervals = concatenate([[0], diff(times)]) # interval for START is always 0
        temps = [f_temp(float(t)) for t in times]
        tols =  [f_tol(float(t))  for t in times]
        pumps = [f_pump(float(t)) for t in times]

        # Write program segment for each timestep
        for (T, I, L, P) in zip(temps, intervals, tols, pumps):
            self.setProgramSegment(T, I, L, P)
        self.setProgramRepetitions(reps)
        self.info("Program written")

    def getProgramSegment(self, seg):
        seg =  "{:03d}".format(seg)
        res = self.sendCmd("rmp in 00 {}".format(seg))[0].strip()

        if not re.match(r"ERR", res):
            res = [float(x) for x in res.split('_')]
            return res

        return False

    def getAllProgramSegments(self, program=None, nmax=150):
        """Return a list of program segments for a specified program
        If no program is specified, the current program is retrieved"""
        if program is not None:
            self.setProgram(program)

        prg = []

        for i in range(0, nmax):
            res = self.getProgramSegment(i)
            if res:
                prg.append(res)
            else:
                break

        return(prg)

    def getBathID(self):
        """
        Gets bath identification number. This is a workaround and uses the digits after the decimal
        in the maximum bath temperature as id
        """
        res = float(self.sendCmd('in sp 04')[0].strip())
        bathID = int(10 * (res - floor(res)))
        return(bathID)

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

    def getCurrentProgram(self):
        res = self.sendCmd("rmp in 04")[0].strip()
        return float(res)

    def deleteProgram(self):
        program = self.getCurrentProgram()
        res = self.sendCmd("rmp reset")

        if "OK" in res:
            self.info("Program {} cleared".format(program))
            return True

        return False

    def controlProgram(self, command):
        """Control program execution ('start','stop','pause', 'cont')"""
        if not command in ['start', 'stop', 'pause', 'cont']:
            self.error("Command must be one of ('start', 'stop','pause', 'cont')")

        program = self.getCurrentProgram()
        res = self.sendCmd("rmp {}".format(command))

        if "OK" in res:
            self.info("Program {}: {}".format(program, command))
            return True

        return False


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

    lauda.setSetpoint(19.5)
    print lauda.getBathTemp()
    #print lauda.getExtTemp()
    print lauda.getBathLevel()
    print lauda.getPumpLevel()
    print lauda.getSetpoint()

    lauda.disconnect()




