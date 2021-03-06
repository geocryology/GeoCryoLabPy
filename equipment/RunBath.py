from LaudaRP845 import LaudaRP845
from pandas import read_csv
import numpy as np
from time import sleep


delay = 30 ## delay n seconds before starting

# conect to bath
bath = LaudaRP845()
if not bath.connect(port=9):
    print("Failed to connect to Lauda")
    exit(1)

#print(bath.getBathTemp())
print('this is bath {}'.format(bath.getBathID()))
# print(bath.getCurrentProgram())
# ft = lambda t: 3 * np.sin(2 * t * np.pi / 10) + 15
# fp = lambda x: 8
# fto = lambda x: 0.1 if x == 1 else 0
# bath.setProgramFunction(2, ft, 10, 1, reps = 2, f_pump = fp, f_tol=fto )

# bath.controlProgram('start')

#print(np.array(bath.getAllProgramSegments(program=2)))
#bath.controlProgram('start')
# print('getting programs')
# print(bath.getAllProgramSegments(program=1))

#bath.setProgramSegment(18, 4, 0,3)
#print(bath.getCurrentProgram())
# bath.setPumpLevel(4)
################################################
# # define temperature ramp
# # temps = read_csv()
# time = range(0,180,30)
# temps = [20, 19.5, 19, 18.5, 19, 19.2]
# t_delta = np.diff(time)

# # put it to the starting target temp and wait
# bath.setSetpoint(temps[0])
# sleep(30)

# # start the clock and begin changing temperatures
# for i in range(1, len(time)):
#     bath.setSetpoint(temps[i])
#     cur_set = bath.getSetpoint()
#     cur_temp = bath.getBathTemp()
#     print('target: {}, current: {}'.format(cur_set, cur_temp))
#     sleep(t_delta[i - 1]) # wait until next defined temperature

bath.disconnect()

if __name__ == "__main__":
    pass