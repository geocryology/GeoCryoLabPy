import serial

class Fluke1502A:
    
    ENDL                = "\r"
    TIMEOUT_INIT        = 0.25
    TIMEOUT_CONSECUTIVE = 0.05
    CHARS_PER_READ      = 16

    def __init__(self, units="c"):
        self.units = units
        self.conn = None
        
    # Connects and opens serial connection to specified port
    # port must be a string in the form COM* where * is one or more digits - ex. "COM7" or "COM12"
    def connect(self, port, baud=9600, timeout=2.0):
        
        try:
            self.conn = serial.Serial(port, baud, timeout=timeout, rtscts=True, write_timeout=timeout)
        except ValueError:
            self.error("Invalid COM port or Baud rate specified")
            return False
        except serial.SerialException:
            self.error("Failed to connect to port {}".format(port))
            return False
            
        self.sendCmd("u={}".format(self.units))
        self.sendCmd("sa=0")

        return True

    # Closes the serial connection
    def disconnect(self):
        self.conn.close()
        
    # Sends specified command to the Fluke1502A. Paramater cmd should be a string with no newline character
    def sendCmd(self, cmd, nBytes=4096):
        cmd += self.ENDL
        cmd = bytearray(cmd)
        
        self._send(cmd)
        return self._recv_all()
        #return self._recv(nBytes)
        
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
        temp = res[0][2:12].strip()
        return temp
        
    # set units of measurements for the device
    # valid options for units are as follows (case insensitive):
    #   Celsius   - "c", "celsius"
    #   Farenheit - "f", "farenheit"
    #   Kelvin    - "k", "kelvin"
    #   Ohms      - "o", "ohms"
    def setUnits(self, units):
        units = units.lower()
        if   units in ["c", "celsius"]:
            self.sendCmd("u=c")
            self.units = "c"
        elif units in ["f", "farenheit"]:
            self.sendCmd("u=f")
            self.units = "f"
        elif units in ["k", "kelvin"]:
            self.sendCmd("u=k")
            self.units = "k"
        elif units in ["o", "ohms"]:
            self.sendCmd("u=o")
            self.units = "o"
        else:
            self.error("Invalid units: {}".format(units))

    # Prints error message and exits
    def error(self, msg):
        print "[ERROR] " + format(msg)
        exit(1)
        
# Simple test code, logs 10 readings to a csv file
if __name__ == "__main__":
    
    import csv
    import datetime
    import time

    fluke = Fluke1502A()
    if not fluke.connect("COM7"):
        print "Failed to connect to Fluke1502A"
        exit(1)

    print fluke.sendCmd("t")
    print fluke.sendCmd("h")
    
    with open("out.csv", "wb") as csvFile:
        csvFile.write("time,{}".format(fluke.units))
        
        for i in range(10):
            timestamp = datetime.datetime.now().isoformat().split(".")[0]
            csvFile.write("{},".format(timestamp))
            csvFile.write(fluke.readTemp())
            csvFile.write("\r\n")
            
    #print fluke.readTemp()
    
    fluke.disconnect()
    
    
    