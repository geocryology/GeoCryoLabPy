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

The DAQ uses a USB connecion, and follows the SCPI convention for communication. This is generally used for measuring thermistors, and contains several configuration parameters depending on the type of thermistors you wish to measure.

# Measurement Scripts

## Controller.py

Controller.py uses a feedback loop to make measurements and automatically determine when the temperature has reached thermal equilibrium. It operates based on a sequence of text commands to define a 'program'. The controller will log temperature readings at specified intervals until the supplied program terminates. The valid commands are as follows:

    SET x
Set calibration bath setpoint to x

    WAIT
Wait until thermal equilibrium. Measurements will continue during the wait.

    RAMP start stop increment
RAMP will set the initial setpoint to 'start', and then issue a WAIT command. Once reaching thermal equilibrium, it will add 'increment' to the setpoint and then WAIT again. This process repeats until 'stop' setpoint has been reached.

    HOLD t
This is like WAIT, but waits for an explicit time interval, t, rather than waiting for equilibrium. The program will move to the next command after t seconds, regardless of whether the temperatures have stabilized or not.
    
    STOP
This command will terminate the program. All measurements will cease and results will be logged.

This module works well, but is not very user-friendly yet. Configuration requires editing the python file. Parameters of interest are as follows:

#### in Controller.__init__()
* sampleInterval

Number of seconds between consecutive measurements.
* sensorList

A python list of thermistor numbers, eg [1, 3, 7] would measure thermistors on channels 1, 3, and 7. This script only supports the first of three slots in the DAQ, but can handle all 20 channels on that slot. Set to empty list if not using the DAQ.

#### in Controller.connect()
* COM ports

The COM ports must be set correctly for both the calibration bath and the thermometer readout. It can be difficult to tell which CO port is which without trying them all, although MATLABs instrument toolbox can tell you which ports have devices connected. Using this, it will usually list ports 1-12, and the proper ports are always in the 4-12 range.

## frequencySweep.py

Uses the Frequency Response Analyzer to measure impedance and phase values over a specified frequency range. It also has the option to measure at multiple specified power levels. It requires two command line arguments, the first being the desired name of the csv output file, and the second being the value of the sensing resistor (Rs) in ohms. Changing the start/stop frequencies, number of datapoints to measured, or the range of power levels must be done in the python script, just after the 'if __name__ == "__main__":' line.

## thermistorCalibrate.py

This is the first version of Controller.py and should not be used. It will likely be removed in the future.
