"""
Python module to communicate with Agilent4395A Vector Network Analyzer
"""
import visa

# Module for the Agilent 4395A Vector Network Analyzer
#   - operates over GPIB using a National Instruments USB-GPIB cable
#
# GPIB uses two methods for communication:
#   WRITE - Sends a command, doesn't return a response
#   QUERY - Sends a command, followed by a '?', and returns a response

# GPIB Address, used to specify connection
ADDRESS = u'GPIB0::16::INSTR'

# GPIB ID string, returned by the '*IDN?' query, used to test if connection is successful
ID = u'HEWLETT-PACKARD,4395A,MY41101925,REV1.12\n'

rm = visa.ResourceManager()

# Connect to and initialize the analyzer
def connect():
    analyzer = rm.open_resource(ADDRESS)
    currentID = (query("*IDN?"))
    if currentID != ID:
        print "ID discrepancy:"
        print "expected: ", ID
        print "actual: ", currentID
        return False

    write("*RST") # resets the analyzer to its default values
    write("*CLS") # clears error queues and various registers
    return True

# Sends a string to the analyzer, does not return a response
def write(cmd):
    analyzer.write(cmd)

# Sends a string (must end with '?'), returns response
# If the response is large, it may take several seconds to return
def query(cmd):
    return analyzer.query(cmd)

# Close the connection (should be done before script exits)
def disconnect():
    analyzer.close()
