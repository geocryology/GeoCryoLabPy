import telnetlib
import time


class Keysight34972A():
    
    PROMPT = "34972A>"
    ENDL   = "\n"
    
    def __init__(self, ip, port=5024):
        self.ip   = ip
        self.port = port
        self.conn = None
        
    def connect(self):
        
        try:
            self.conn = telnetlib.Telnet(self.ip, self.port, timeout=10)
        except KeyboardInterrupt:
            system.exit(1)
        except:
            return False
        
        self.sendCmd("*RST")
        
        return True
        
    def disconnect(self):
        self.conn.close()
        
    def sendCmd(self, cmd):
        self._send(cmd)
        return self._recv()
 
    def _send(self, cmd):
        self.conn.write(cmd + self.ENDL)
        
    def _recv(self, timeout=2):
        res = self.conn.read_until(self.PROMPT, timeout).splitlines()
        return res
    
    
if __name__ == "__main__":
    
    ip   = "134.117.231.204"
    port = 5024
    
    keysight = Keysight34972A(ip, port)

    if not keysight.connect():
        print "Failed to connect to Keysight34972A at {}:{}".format(ip, port)
        exit(1)
        
    keysight.sendCmd("DISP:TEXT \"HELLO\"")
    keysight.sendCmd("DISP:TEXT:CLEAR")
    keysight.sendCmd("CONFIGURE:TEMPERATURE TC,J,(@101)")
    keysight.sendCmd("ROUT:SCAN (@101)")
    keysight.sendCmd("READ?")
    keysight.sendCmd("READ?")
    keysight.sendCmd("READ?")
    keysight.disconnect()