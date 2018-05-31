from LaudaRP845 import LaudaRP845
from pandas import read_csv
import numpy as np
from time import sleep


delay = 30 ## delay n seconds before starting

# conect to bath
bath = LaudaRP845
if not bath.connect():
    print("Failed to connect to Lauda")
    exit(1)

# define temperature ramp
# temps = read_csv()
time = range(0,180,30)
temps = [20, 19.5, 19, 18.5, 19, 19.2]
t_delta = np.diff(time)

# put it to the starting target temp and wait
bath.setSetpoint(temps[0])
sleep(30)

# start the clock and begin changing temperatures
for i in range(0,len(time)):
    bath.setSetpoint(temps[i + 1])
    cur_set = bath.getSetpoint()
    cur_temp = bath.getBathTemp()
    print('target: {}, current: {}'.format(cur_set, cur_temp))
    sleep(t_delta[i]) # wait until next defined temperature

bath.disconnect()

if __name__ == "__main__":
    pass