import time
import datetime

from Fluke7341 import Fluke7341
from Fluke1502A import Fluke1502A
from Keysight34972A import Keysight34972A

if __name__ == "__main__":

    bath = Fluke7341()
    probe = Fluke1502A()
    daq = Keysight34972A()


    if not bath.connect():
        print "failed to connect to bath"
        exit()

    if not probe.connect():
        print "failed to connect to probe"
        exit()

    if not daq.connect():
        print "failed to connect to bath"
        exit()

    """
    datetime.datetime.now().isoformat().replace(":", "_").split(".")[0] # timestamp for file name
    datetime.datetime.now().isoformat() # timestamp for logging
    """

    probeList = "103:105,201:203"
    interval = 5
    duration = 25
    # equivalent to temperatures = [0, 5, 10, 15, 20]
    bath_temps = []
    probe_temps = []
    daq_resistances = []

    bath.setSetpoint(15)

    start_time = time.time()
    last_measurement_time = start_time
    while time.time() < start_time + duration:
        print datetime.datetime.now().isoformat()
        bath_temp = bath.readTemp()
        probe_temp = probe.readTemp()
        resistances_string = daq._query("measure:resistance? (@{})".format(probeList))
        resistances_floats = map(float, [t for t in resistances_string.split(',')]) # convert strings to floats, not strictly necessary for logging directly

        bath_temps.append(bath_temp)
        probe_temps.append(probe_temp)
        daq_resistances.append(resistances_string)

        print bath_temp, probe_temp, resistances_string

        while time.time() < last_measurement_time + interval:
            time.sleep(0.01)

        last_measurement_time += interval

    print "done"
    print bath_temps
    print probe_temps
    print daq_resistances

    f = open("out.csv", "w")
    f.write("bath temp, probe temp\n")
    for i in range(len(bath_temps)):
        f.write("{},{},{}\n".format(bath_temps[i], probe_temps[i], daq_resistances[i].strip()))

    f.close()

    probe.disconnect()
    bath.disconnect()
    daq.disconnect()


