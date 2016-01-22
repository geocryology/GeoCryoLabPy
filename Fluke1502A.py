
import serial

class Fluke1502A:
    
    ENDL                = "\r"
    TIMEOUT_INIT        = 0.25
    TIMEOUT_CONSECUTIVE = 0.05
    CHARS_PER_READ      = 16

    def __init__(self):
    
        self.conn = None
        
    # Connects and opens serial connection to specified port
    # port must be a string in the form COM* where * is one or more digits - ex. COM7 or COM12
    def connect(self, port, baud=9600, timeout=2.0):
        
        try:
            self.conn = serial.Serial(port, baud, timeout=timeout, rtscts=True, write_timeout=timeout)
        except ValueError:
            self.error("Invalid COM port or Baud rate specified")
            return False
        except serial.SerialException:
            self.error("Failed to connect to port {}".format(self.port))
            return False

        return True

    # Closes the serial connection
    def disconnect(self):
        self.conn.close()
        
    # Sends specified command to the Fluke1502A. Paramater cmd should be a string with no newline character
    def sendCmd(self, cmd, nBytes=4096):
        cmd += self.ENDL
        cmd = bytearray(cmd)
        
        self._send(cmd)
        return self._recv(nBytes)
        
    def _send(self, bytes):
        
        try:
            self.conn.write(bytes)
        except serial.SerialTimeoutException:
            self.error("Serial write timed out")
    
    def _recv(self, nBytes):
        bytes = self.conn.read(nBytes)
        res   = str(bytes).splitlines()
        return res
        
    def error(self, msg):
        print "[ERROR] " + format(msg)
        exit(1)
        
if __name__ == "__main__":
    
    fluke = Fluke1502A()
    if not fluke.connect("COM7"):
        print "Failed to connect to Fluke1502A"
        exit(1)
    
    print fluke.sendCmd("t")
    print fluke.sendCmd("h")
    
    
    
    fluke.disconnect()
    
    
    