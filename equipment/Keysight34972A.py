import visa
import time


class Keysight34972A():
    
    PROMPT = "34972A>"
    ENDL   = "\n"
    ID     = u'Agilent Technologies,34972A,MY49021266,1.16-1.12-02-02\n'
    
    def __init__(self):
        self.rm = visa.ResourceManager()
        self.instance = None
        
    def connect(self):
        
        self.instance = self.rm.open_resource(u'USB0::2391::8199::my49021266::0::INSTR')
        id = (self.query("*IDN?"))
        if id != self.ID:
            print "ID discrepancy:"
            print "expected:", self.ID
            print "actual:  ", id
            return False
            
        keysight.timeout = None
        self.write("*RST")
        self.write("*CLS")
        return True
        
    def disconnect(self):
        self.instance.close()
        
    def write(self, cmd):
        return self.instance.write(cmd)
        
    def query(self, cmd):
        return self.instance.query(cmd)
 
if __name__ == "__main__":
    
    keysight = Keysight34972A()

    if not keysight.connect():
        print "Failed to connect to Keysight34972A".format()
        exit(1)
        
    keysight.write("format:reading:channel 1;alarm 1;unit 1;time:type rel")
    keysight.write("configure:temperature auto,max,(@101)")
    keysight.write("trigger:count 3")
    keysight.write("initiate")
    
    print keysight.query("fetch?")
        
    keysight.disconnect()