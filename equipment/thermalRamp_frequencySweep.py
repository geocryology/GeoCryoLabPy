import subprocess
import time
from Fluke7341      import Fluke7341

if __name__ == "__main__":

    bath = Fluke7341()

    if not bath.connect():
        print "failed to connect to bath"
        exit()

    for setpoint in range(21)[::-1]:
        bath.setSetpoint(20)
        time.sleep(3000)

        print "performing sweep"

        args = ["python",
            "frequencySweep.py",
            "thermalTest_{}C".format(setpoint),
            "50"]
        subprocess.Popen(args).wait()
        print "done"

    bath.setSetpoint(20)





