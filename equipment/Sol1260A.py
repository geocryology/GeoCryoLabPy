"""
Python package to communicate with Solartron 1260A Frequency Analyzer
"""
# refer https://pyvisa.readthedocs.io/
import visa

# Module for the Agilent 4395A Vector Network Analyzer
#   - operates over GPIB using a National Instruments USB-GPIB cable
#
# GPIB uses two methods for communication:
#   WRITE - Sends a command, doesn't return a response
#   QUERY - Sends a command, followed by a '?', and returns a response

# Default GPIB Address, used to specify connection
# refer section 7.2.3 in 1260A analyzer manual
ADDRESS = 'GPIB0::12::INSTR'

# GPIB ID string, returned by the '*IDN?' query, used to test if connection is successful
# refer section 7.2.7 in 1260A analyzer manual
ID = '1260 IMPEDANCE ANALYZER, SOLARTRON, 0, 0'

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
    # Input (from analyzer to computer) command terminator (refer section 7.2.3 in 1260A analyzer manual)
    analyzer.read_termination = ';' # this is for the reference of visa Python package
    # Output (from computer to analyzer) command terminator (refer section 5.8.2 in 1260A analyzer manual)
    analyzer.write_termination = '\r\n' # this is for the reference of visa Python package
    write("*RST") # resets the analyzer to its default values
    write("*CLS") # clears error queues and various registers
    write("TT2") # resets the analyzer (not sure if required after *RST command)
    write("OT 0") # instructs analyzer that output command terminator is \r\n (CRLF or Carriage Return Line Feed)
    # (to input a command with more than one parameter)
    write("OS 0") # instructs analyzer that output command separator is , (comma)
    write("OP 2,1") # instructs analyzer to send (dump all) data in ASCII format over GPIB
    return True

# Sends a string to the analyzer, does not return a response
def write(cmd):
    analyzer.write(cmd)
    time.sleep(0.02) # Min required time between consecutive write commands

# Sends a string (must end with '?'), returns response
# If the response is large, it may take several seconds to return
def query(cmd):
    return analyzer.query(cmd)

# Close the connection (should be done before script exits)
def disconnect():
    analyzer.close()
