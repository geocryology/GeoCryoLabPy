import serial

# Class for Fluke 7341 Calibration Bath with Serial Interface
#   - Reads and writes are slow on this device (max 2400 BAUD)
#   - Only supports Celsius and Farenheit internally (Kelvin must be calculated)
#   - Serial interface should be configured to 2400 BAUD, Full Duplex
#   - 

class Fluke7341:
    
    ENDL                = "\r"
    TIMEOUT_INIT        = 2.00
    TIMEOUT_CONSECUTIVE = 0.25
    CHARS_PER_READ      = 16
    
    # Setpoint Min/Max values are in Celsius
    SETPOINT_MAX        =  90
    SETPOINT_MIN        = -30

    def __init__(self, units="c"):
        self.units = units
        self.conn = None
        
    # Connects and opens serial connection to specified port
    # port must be a string in the form COM* where * is one or more digits - ex. "COM7" or "COM12"
    def connect(self, port, baud=2400, timeout=2.0):
        
        try:
            self.conn = serial.Serial(port, baud, timeout=timeout, rtscts=True, write_timeout=timeout)
        except ValueError:
            self.error("Invalid COM port or Baud rate specified")
            return False
        except serial.SerialException:
            self.error("Failed to connect to port {}".format(port))
            return False
            
        self.setUnits("c")
        self.sendCmd("sa=0")
        self._recv_all()

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

    # Raw serial write
    def _send(self, bytes):
        
        try:
            self.conn.write(bytes)
        except serial.SerialTimeoutException:
            self.error("Serial write timed out")
    
    # Raw serial read, up to nBytes
    def _recv(self, nBytes):
        bytes = self.conn.read(nBytes)
        res   = str(bytes).splitlines()
        return res[1:]
       
    # Faster implementation of _recv
    # Waits up to TIMEOUT_INIT for first byte of response, and then
    # waits TIMEOUT_CONSECUTIVE between each remaining byte of response.
    # This method returns faster than using a single timeout to wait for the full response
    def _recv_all(self):
        res = ""
        originalTimeout   = self.conn.timeout
        self.conn.timeout = self.TIMEOUT_INIT
        
        byte = self.conn.read()
        if not byte:
            return ""
        else:
            res += str(byte)
            
        self.conn.timeout = self.TIMEOUT_CONSECUTIVE
        
        while byte:
            byte = self.conn.read()
            res += str(byte)

        self.conn.timeout = originalTimeout
        return res.splitlines()[1:]
        
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
            
    # set the setpoint of in the same units as set wih setUnits()
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
        self.info("Setpoint changed to {} {}".format(setpoint, units)
        return True
    
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
    if not fluke.connect("COM7"):
        print "Failed to connect to Fluke7341"
        exit(1)

    print "temp: {}".format(fluke.sendCmd("t"))
    print "help: {}".format(fluke.sendCmd("h"))
    
    fluke.setSetpoint(-40)
    fluke.setSetpoint(100)
    fluke.setSetpoint(10)
    
    with open("out.csv", "wb") as csvFile:
        csvFile.write("time,{}".format(fluke.units))
        
        for i in range(10):
            timestamp = datetime.datetime.now().isoformat().split(".")[0]
            csvFile.write("{},".format(timestamp))
            csvFile.write(fluke.readTemp())
            csvFile.write("\r\n")
            
    #print fluke.readTemp()
    
    fluke.disconnect()
    
    
    