"""
Python class representing the Agilent4395A Vector Network Analyzer
"""
import visa

# Controller class for the Agilent 4395A Vector Network Analyzer
#   - operates over GPIB using a National Instruments USB-GPIB cable
#
# GPIB uses two methods for communication:
#   WRITE - Sends a command, doesn't return a response
#   QUERY - Sends a command, followed by a '?', and returns a response

class agilent4395a:

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
        currentID = (self.query("*IDN?"))
        if currentID != self.ID:
            print "ID discrepancy:"
            print "  expected:", self.ID
            print "  actual:  ", currentID
            return False

        self.write("*RST")
        self.write("*CLS")
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