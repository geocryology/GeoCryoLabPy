import datetime
import math
import sys
import time

from Keysight34972A import Keysight34972A
from Fluke7341  import Fluke7341
from Fluke1502A import Fluke1502A

class RingBuffer():

    def __init__(self, size):
        self.size    = size
        self.buffer  = [0] * size
        self.pointer = 0
        self.count   = 0

    def update(self, value):
        self.buffer[self.pointer] = value
        self.pointer = (self.pointer + 1) % self.size
        self.count  += 1

    def reset(self):
        self.count   = 0

    def getAverage(self, silent=True):
        if self.count < self.size:
            if not silent:
                print "[WARNING] Buffer has not been filled completely: [{}/{}]".format(self.count, self.size)
        return sum(self.buffer) / self.size

    def getSTD(self):
        std = 0
        avg = self.getAverage()
        for i in range(self.size):
            std += (self.buffer[i] - avg) ** 2
        std /= self.size
        return math.sqrt(std)

class EquilibriumMonitor():

    def __init__(self, size, name=""):

        self.size     = size
        self.readings = RingBuffer(size)
        self.STDs     = [0] * size
        self.count    = 0
        self.name     = name

    def update(self, value):
        self.readings.update(value)
        std = self.readings.getSTD()

        self.count += 1

        if std < min(self.STDs):
            self._print("converging")
            self.minSTD = std
            self.count  = 0

        elif std > max(self.STDs) * 1.025:
            self._print("diverging")
            self.count  = 0

        else self.count < self.size:
            self._print("stabilizing")

        self.STDs = self.STDs[1:] + [std]

    def isEqualized(self):
        return self.count >= self.size

    def reset(self):
        self.count = 0

    def _print(self, msg):
        print "{} {} [{}/{}]".format(self.name.rjust(8), msg, self.count, self.size)

class Controller():

    COMMANDS  = ["wait", "hold", "ramp", "set", "stop"]
    DEBUG     = True

    TEMP_MAX  = 50
    TEMP_MIN  = -25

    RAMP  = 0
    HOLD  = 1
    WAIT  = 2
    SET   = 3
    STOP  = 4
    GO    = 5

    STATES = ["RAMP", "HOLD", "WAIT", "SET", "STOP", "GO"]

    def __init__(self):

        self.sampleInterval = 5
        self.bufferSize     = 30
        self.stdHoldCount   = 30

        self.daq   = None
        self.bath  = None
        self.probe = None

        self.sensorList    = [1, 2]
        self.sensorBuffers = []
        self.probeBuffer   = None
        self.bathBuffer    = None
        self.numSensors    = 0

        self.file      = ""
        self.commands  = []             # command queue
        self.command   = 0              # index of current command within self.commands
        self.state     = self.GO

        # state variables
        self.rampStart = 0.0
        self.rampEnd   = 0.0
        self.rampInc   = 0.0
        self.holdTime  = 0.0
        self.setpoint  = 0.0
        self.t0        = 0

    def connect(self):

        self.daq   = Keysight34972A()
        self.bath  = Fluke7341()
        self.probe = Fluke1502A()

        if self.numSensors > 0:
            if not self.daq.connect():
                print "Failed to connect to Keysight34972A (DAQ)".format()
                return False
            self.daq.initialize(Keysight34972A.MODE_RESISTANCE, self.sensorList)

        if not self.bath.connect("COM5"):
            print "Failed to connect to Fluke7341 (Calibration Bath)"
            return False

        if not self.probe.connect("COM7"):
            print "Failed to connect to Fluke1502A (Probe Reader)"
            return False

        return True

    def disconnect(self):
        self.daq.disconnect()
        self.bath.disconnect()
        self.probe.disconnect()

    def init(self):

        self.numSensors    =  len(self.sensorList)
        self.sensorBuffers = [EquilibriumMonitor(self.bufferSize, name="sensor{}".format(i)) for i in range(self.numSensors)]
        self.probeBuffer   =  EquilibriumMonitor(self.bufferSize, name="probe")
        self.bathBuffer    =  EquilibriumMonitor(self.bufferSize, name="bath")

        timestamp = datetime.datetime.now().isoformat().split('.')[0].replace(':', '-')
        self.file = "{}.csv".format(timestamp)

        self.t0 = time.time()

    def validateCommand(self, command):

        command = command.strip()
        command = command.replace(",", " ")
        if command == "":
            return True

        command = command.split()
        com     = command[0].lower()
        args    = command[1:]

        if com.startswith("#"):
            return True

        elif com == "wait":
            if len(args) > 0:
                self.error("WAIT requires 0 arguments")
                return False

        elif com == "hold":
            if len(args) != 1:
                self.error("HOLD requires 1 argument")
                return False
            else:
                try:
                    i = int(args[0])
                    if i < 0:
                        self.error("HOLD requires positive integer argument")
                        return False
                    return True
                except ValueError:
                    self.error("HOLD requires integer argument")
                    return False

        elif com == "ramp":
            if len(args) != 3:
                self.error("RAMP requires 3 arguments")
                return False
            else:
                try:
                    for i in range(3):
                        args[i] = float(args[i])
                except ValueError:
                    self.error("RAMP requires 3 numeric values")
                    return False

                start = args[0]
                end   = args[1]
                inc   = args[2]
                direction = end - start
                if direction * inc < 0:
                    self.error("RAMP increment has incorrect sign")
                    return False

                if start < self.TEMP_MIN:
                    self.error("RAMP start must be greater than or equal to {}".format(self.TEMP_MIN))
                    return False
                elif start > self.TEMP_MAX:
                    self.error("RAMP start must be less than or equal to {}".format(self.TEMP_MAX))
                    return False

                if end < self.TEMP_MIN:
                    self.error("RAMP end must be greater than or equal to {}".format(self.TEMP_MIN))
                    return False
                elif end > self.TEMP_MAX:
                    self.error("RAMP end must be less than or equal to {}".format(self.TEMP_MAX))
                    return False

        elif com == "set":
            if len(args) != 1:
                self.error("SET requires 1 argument")
                return False
            else:
                setpoint = 0
                try:
                    setpoint = float(args[0])
                except ValueError:
                    self.error("SET requires a numeric value")
                    return False

                if setpoint < self.TEMP_MIN:
                    self.error("SET setpoint must be greater than or equal to {}".format(self.TEMP_MIN))
                    return False
                elif setpoint > self.TEMP_MAX:
                    self.error("SET setpoint must be less than or equal to {}".format(self.TEMP_MAX))
                    return False

        else:
            self.error("Invalid command {}.".format(command))
            return False

        return True

    def validateProgram(self, program):
        lines = program.splitlines()
        lineCount = 1
        for line in lines:
            if self.validateCommand(line):
                action = self.getAction(line)
                if action in self.COMMANDS:
                    self.commands.append(line)
            else:
                self.error("Error at line {}".format(lineCount))
                return False

            lineCount += 1
        return True

    def getAction(self, command):
        if len(command.split()) == 0:
            return []
        return command.split()[0].strip().lower()

    def getArgs(self, command):
        args = command.split()[1:]
        args = [float(arg) for arg in args]
        return args

    def nextState(self):

        if self.command >= len(self.commands):
            self.state = self.STOP
            return

        action = self.getAction(self.commands[self.command])
        args = self.getArgs(self.commands[self.command])
        self.command += 1

        if action == "wait":
            self.state = self.WAIT
        elif action == "hold":
            self.holdTime = self.t0 + args[0]
            self.state = self.HOLD
        elif action == "ramp":
            self.setpoint = args[0]
            self.rampEnd  = args[1]
            self.rampInc  = args[2]
            self.bath.setSetpoint(self.setpoint)
            self.state = self.RAMP
        elif action == "set":
            self.setpoint = args[0]
            self.state    = self.SET
        elif action == "stop":
            self.state = self.STOP
        else:
            self.error("UNKOWN COMMAND: {}".format(action))
            self.state = self.STOP

        self.resetBuffers()
        self.info("state: {}".format(self.STATES[self.state]))


    def isEqualized(self):
        return self.probeBuffer.isEqualized()

    def resetBuffers(self):
        self.bathBuffer.reset()
        self.probeBuffer.reset()
        for i in range(self.numSensors):
            self.sensorBuffers[i].reset()

    def runProgram(self, program):

        if not self.validateProgram(program):
            print "Invalid program."
            return False

        self.init()

        if not self.connect():
            return False

        self.program = program.splitlines()
        self.command = 0

        self.nextState()

        while self.state != self.STOP:
            self.step()

            if   self.state == self.GO:
                self.nextState()

            elif self.state == self.HOLD:
                if self.t0 > self.holdTime:
                    self.nextState()

            elif self.state == self.WAIT:
                if self.isEqualized():
                    self.nextState()

            elif self.state == self.SET:
                self.bath.setSetpoint(self.setpoint)
                self.nextState()

            elif self.state == self.RAMP:
                if abs(self.setpoint - self.rampEnd) < 0.001:
                    if self.isEqualized():
                        self.nextState()
                if self.isEqualized():
                    self.setpoint += self.rampInc
                    self.bath.setSetpoint(self.setpoint)
                    self.resetBuffers()

            elif self.state == self.STOP:
                pass

            else:
                self.error("Unknown state: {}".format(self.state))

        self.disconnect()

    def step(self):

        # make new readings and update appropriate buffers
        bathTemp    = float(self.bath.readTemp())
        probeTemp   = float(self.probe.readTemp())
        resistances = self.daq.readValues()

        self.bathBuffer.update(bathTemp)
        self.probeBuffer.update(probeTemp)
        for i in range(self.numSensors):
            self.sensorBuffers[i].update(resistances[i])

        # log results
        t = datetime.datetime.now()
        timestamp   = "{}/{}/{} {}:{}:{}".format(t.month, t.day, t.year, t.hour, t.minute, t.second)

        t = datetime.datetime.now() - datetime.datetime.fromtimestamp(self.t0)
        seconds =  t.seconds %    60
        minutes = (t.seconds /    60) % 60
        hours   = (t.seconds /  3600) % 24
        elapsedTime   = "{}:{}:{}".format(hours, minutes, seconds)

        output = open(self.file, "a")
        resistances = ",".join([str(r) for r in resistances])
        output.write(",".join([timestamp, elapsedTime, str(self.setpoint),
                                  str(bathTemp), str(probeTemp), resistances]))
        output.write("\n")
        output.close()

        # wait until next measurement interval
        while time.time() < self.t0 + self.sampleInterval:
            time.sleep(0.01)

        self.t0 = self.t0 + self.sampleInterval

    def info(self, msg):
        if self.DEBUG: print "[INFO]", msg

    def warning(self, msg):
        if self.DEBUG: print "[WARNING]", msg

    def error(self, msg):
        if self.DEBUG: print "[ERROR]", msg

"""
command syntax
ramp 0, -1, -0.1
ramp -1, 0, 0.1
hold 600
wait

"""
if __name__ == "__main__":

    c = Controller()

    c.runProgram("""
    SET 0
    HOLD 1800
    """)

    c.disconnect()

    exit()

    #test code
    c = Controller()

    assert c.validateCommand("WAIT") == True
    assert c.validateCommand("wait") == True
    assert c.validateCommand("wAIt") == True
    assert c.validateCommand("  WAIT") == True
    assert c.validateCommand("  WAIT  ") == True
    assert c.validateCommand("  WAIT  asdf") == False
    assert c.validateCommand("#  WAIT  asdf") == True
    assert c.validateCommand(" #  WAIT  asdf") == True

    assert c.validateCommand("HOLD") == False
    assert c.validateCommand("HOLD 1") == True
    assert c.validateCommand("HOLD a") == False
    assert c.validateCommand("HOLD -1") == False
    assert c.validateCommand("HOLD 1.0") == False
    assert c.validateCommand("HOLD -1.0") == False
    assert c.validateCommand("HOLD 12 1") == False

    assert c.validateCommand("RAMP") == False
    assert c.validateCommand("RAMP a") == False
    assert c.validateCommand("RAMP a b") == False
    assert c.validateCommand("RAMP 1 2 3") == True
    assert c.validateCommand("RAMP a b c") == False
    assert c.validateCommand("RAMP 1 2.0 3") == True
    assert c.validateCommand("RAMP 1 2.0 3") == True
    assert c.validateCommand("RAMP 1 2.0 -3") == False
    assert c.validateCommand("RAMP 1 -2.0 -3") == True
    assert c.validateCommand("RAMP -25 50 1.0") == True
    assert c.validateCommand("RAMP -26 50 1.0") == False
    assert c.validateCommand("RAMP -25 51 1.0") == False
    assert c.validateCommand("RAMP -25 -2.0 1.0") == True
    assert c.validateCommand("RAMP 1 -2.0 -3 32") == False

    assert c.validateCommand("SET") == False
    assert c.validateCommand("SET 2") == True
    assert c.validateCommand("SET a") == False
    assert c.validateCommand("SET 50") == True
    assert c.validateCommand("SET 51") == False
    assert c.validateCommand("SET 2.0") == True
    assert c.validateCommand("SET -25") == True
    assert c.validateCommand("SET a a") == False
    assert c.validateCommand("SET -26") == False
    assert c.validateCommand("SET -2.0") == True

    assert c.validateCommand("INVALID COMMAND") == False

    assert c.validateProgram("""
    # TEST PROGRAM
    SET 0.0
    WAIT
    SET -10
    WAIT
    RAMP -10, 0, 1.0

    # COMMENT

    RAMP 0.0 -10 -2.0

    HOLD 1800
    """) == True

    assert c.validateProgram("""
    TEST PROGRAM
    SET 0.0
    WAIT
    SET -10
    WAIT
    RAMP -10, 0, 1.0

    # COMMENT

    RAMP 0.0 -10 -2.0

    HOLD 1800
    """) == False
