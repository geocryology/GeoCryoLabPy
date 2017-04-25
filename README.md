# GeoCryoLabPy
Python code for automating geocryology laboratory 

# Class files for various lab instruments

You generally won't have to use these class files directly unless you are building your own script which uses them. There are already a few scripts built which take care of configuration/measurement which are described in the next section.

## Agilent4395A.py - Frequency Response Analyzer

Supports writing configuration commands (see list of useful commands in analyzerCommands.txt) and reading measured data. Connects via USB and uses pyvisa library for communication. The included code in this module can be used to read impedance measurements and record them in a csv file. This code was written mainly for debugging and testing, and should not be used for making proper measurements.

## Fluke1502A.py - Thermometer Readout

The thermometer readout uses a Serial connection (9600 BAUD, RTS/CTS enabled). It contains methods for reading and writing configuration data and reading temperature measurements.

## Fluke7341.py - Calibration Bath

The calibration bath also uses a Serial connection (2400 BAUD, RTS/CTS enabled). It has a very similar set of methods as the thermometer readout.

## Keysight34972A.py - Data Acquisition Unit

The DAC uses a USB connecion, and follows the SCPI convention for communication. This is generally used for measuring thermistors, and contains several configuration parameters depending on the type of thermistors you wish to measure.

# Measurement Scripts
