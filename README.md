# GeoCryoLabPy
Python code for automating geocryology laboratory
Files located in C:\git\GeoCryoLabPy\equipment

# Class files for various lab instruments

Many pieces of lab equipment have a Python class designed to easily facilitate connection and communication. They should be straightforward to use and all follow a similar protocol:
1. Connect to the device using the connect() function which will automatically detect port numbers
2. Send any required configuration commands (for example LaudaRP845.setControlMode(2) to enable external thermometer control)
3. Read any data and log to file (for example Fluke1502A.readTemp() to get the temperature of the calibration bath, measured externally)

There are several pre-built logging scripts described in the next section, but in case of designing your own, a typical script will behave something like this:
1. Connect to all needed devices
2. Send configuration data if necessary
3. In a loop, continuously read data and if necessary update configurations (like bath temperature)
4. At the end of the script, disconnect from all devices. This will usually happen automatically, but it is a good habit to call disconnect() when finished with a device.

## Agilent4395A.py - Frequency Response Analyzer

Supports writing configuration commands (see list of useful commands in analyzerCommands.txt) and reading measured data. Connects via USB and uses pyvisa library for communication. The included code in this module can be used to read impedance measurements and record them in a csv file. This code was written mainly for debugging and testing, and should not be used for making proper measurements.

## Fluke1502A.py - Thermometer Readout

The thermometer readout uses a Serial connection (9600 BAUD, RTS/CTS enabled). It contains methods for reading and writing configuration data and reading temperature measurements. If a function is not listed below, it is only meant for internal use.
    
    connect(): Scans all COM ports and requests identifier to find and connect to Fluke1502A.
    disconnect(): To be called when all communications are finished, typically at the end of a script.
    sendCmd(): Send command as a string, for example "t" to read the temperature. The devices response is returned. 
               Most common commands have dedicated functions, so this should only be used if there is no 
               function implemented for the command you need.
    readTemp(): Read temperature of thermometer, returned as a string.
    setUnits(): Change measurement units (C (default), F, or K)
    getValue(): Get a specific value, such as probe type or calibration parameters
    printCalibrationData(): Retrieve and print all calibration parameters
    printModelInfo(): Print model number and ID string

## Fluke7341.py - Calibration Bath

The calibration bath also uses a Serial connection (2400 BAUD, RTS/CTS enabled). It has a very similar set of methods as the thermometer readout. The functions for this are nearly identical to the Fluke1502, so refer to the above list.

## LaudaRP845.py - Recirculating Bath

Again, this uses a Serial connection (9600 BAUD), but it has the following additional commands compared to the previous devices.
    
    setCoolingMode(): 0 - No cooling
                      1 - Forced cooling
                      2 - Automatic (default, used for maintaining a setpoint)
    setControlMode(): 0 - Internal thermometer control
                      1 - External thermometer control (for use with external pt100 sensor)
                      2 - External analogue controller
                      3 - External serial controller
    setSetpoint(): Set bath setpoint
    setPumpLevel(): Strength of circulating pump (from 1-8, default 4)
    getBathTemp(): Read bath temperature, returned as float
    getExtTemp(): Read temperature of external pt100 probe
    getBathLevel(): Get fill level of bath
    getSetpoint(): Read current setpoint
    getPumpLevel(): Read pump level    
    setProgram(): Select one of the 5 programmable temperature/time profiles
    setProgramSegment(): Add one segment to the currently selected program
    setProgramRepetitions(): Set how many times the program temperature cycle is to repeat
    getProgramSegment(): Read the details of a specific programmed segment
    getAllProgramSegments(): Read the details of an entire program
    deleteProgram(): Clear all segments of currently selected program
    getCurrentProgram(): Return the number (index) of the currenly selected program
    controlProgram(): Control program behaviour (start, pause, resume, stop)
    setProgramProfile(): Define a temperature-time profile for the bath to follow using a python function F(t) where t is measured in minutes
    
## Keysight34972A.py - Data Acquisition Unit

The DAQ uses a USB connecion, and follows the SCPI convention for communication. This is generally used for measuring thermistors, and contains several configuration parameters depending on the type of thermistors you wish to measure.

# Measurement Scripts

## logDAQ.py

logDAQ.py is used for measuring thermistors while controlling the calibration bath. The 1502A is used as a more precise reference thermometer for said logging. This script supports a large host of command line arguments for tweaking behavior.

    -h, --help           show this help message and exit
    --start START        Initial bath temperature (default: 5)
    --end END            Final bath temperature (default: -2)
    --reset RESET        Bath will reset to this temperature after experiment(default: 20)
    --inc INC            Temperature increment between setpoints (default: 1)
    --nreads NREADS      Number of times to read from DAQ at each setpoint (default: 10)
    --tdelay TDELAY      Time (s) to wait between setpoints (default: 1200)
    --rdelay RDELAY      Time (s) to wait between subsequent DAQ reads (default:15)
    --idelay IDELAY      Time (s) to wait for adjustment to initial setpoint. This delay is only used once at the start of the experiment (default: 1200)
    --channels CHANNELS  List of DAQ channels to read, see code for detailed documentation on format (default: 101:120,201:220,301:320)
    --filename FILENAME  Filename of output csv file (.csv extention added automatically) (default: None)
    --eta                Print estimated time and exit without running experiment (default: False)
    --email EMAIL        Send results to this email (default: )
    --subject SUBJECT    Email subject line (default: Experiment Complete)

## ColumnRun.py

ColumnRun.py is used to launch soil column experiments by controlling the cooling baths as well as the recording interval of thermistors connected to the DAQ. In the script, temperature-time profiles (programs) are written to the cooling baths according to a user-defined function. Then, the programs are set to run, and periodically, the DAQ and the temperature baths are polled for their resistance and temperature values. The strucuture of the script follows that of logDAQ.py and much of the code is very similar. As with logDAQ, the behaviour of the experiment is controlled by command line arguments:


    -h, --help       show this help message and exit
    --idelay         Time (s) to wait for adjustment to initial setpoint corresponding to f(0) of the temperature control function. This delay is only used once at the start of the experiment (default: 0)
    --up             Enable upper cooling plate 0 = off, 1 = on
    --low            Enable lower cooling plate 0 = off, 1 = on
    --port_up        Communication port for the bath controlling the upper cooling plate
    --port_low       Communication port for the bath controlling the lower cooling plate
    --ft_up          Function defining upper cooling plate temperature as a funtion of 't' (minutes).  prefix numpy functions with 'np.' and do not use spaces in the function e.g. '12+(t/30)' or  '22' or 'np.sin(np.radians(t*np.pi/180))
    --ft_low         Function defining lower cooling plate temperature as a funtion of 't' (minutes).  prefix numpy functions with 'np.' and do not use spaces in the function e.g. '12+(t/30)' or  '22' or 'np.sin(np.radians(t*np.pi/180))
    --rep_up         Number of times to repeat upper cooling plate function
    --rep_low        Number of times to repeat upper cooling plate function
    --tstop_up       Length of time (m) to run upper cooling plate function before terminating or repeating
    --tstop_low      Length of time (m) to run lower cooling plate function before terminating or repeating
    --disc_up        Sampling interval (m) for upper bath function. A larger value gives a coarser discretization. E.g. a value of 2 samples the function every two minutes and writes two-minute intervals to the bath
    --disc_low        Sampling interval (m) for lower bath function. A larger value gives a coarser discretization. E.g. a value of 2 samples the function every two minutes and writes two-minute intervals to the bath
    
    --rdelay      Time (s) to wait between subsequent DAQ reads (default:15)

    --start        Initial bath temperature (default: 5)
    --channels   List of DAQ channels to read (e.g. '101:112,205:220'), see code for detailed documentation on format.  Omitting the channels argument will run the cooling baths and record their temperatures but will not connect to or read the DAQ. This can be helpful if the DAQ is being used by another process.
    --filename   Filename of output csv file (.csv extention added automatically) (default: None)
    --email         Send results to this email (default: )
    --subject     Email subject line (default: Experiment Complete)

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
