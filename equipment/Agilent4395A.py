import visa

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
        id = (self.query("*IDN?"))
        if id != self.ID:
            print "ID discrepancy:"
            print "  expected:", self.ID
            print "  actual:  ", id
            return False

        self._write("*RST")
        self._write("*CLS")
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

    commands = """CHAN1
        SWPT LOGF
        BWAUTO 1
        POIN 801
        FORM4
        MEAS A
        PHAU DEG
        STAR 1000 HZ
        STOP 500000000 HZ
        FMT LINM
        SING
        AUTO""".split("\n")
        
    for cmd in commands:
        print cmd.strip(),
        raw_input()
        fra.write(cmd.strip())
        
    data = fra.query("OUTPDTRC?")
    
    fra.disconnect()