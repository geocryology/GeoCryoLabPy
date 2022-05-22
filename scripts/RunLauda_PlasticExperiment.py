#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from LaudaRP845 import LaudaRP845
from pandas import DataFrame
from datetime import datetime, timedelta
from time import sleep
from math import sin, pi
import toml

def square_wave(time_now, time_start, time_step_measure, temp_min, temp_max):
    # function to generate square temperature ramps
    # time:       time for which temperature is desired [datetime object]
    # timeStart:  start time of experiment
    # timeStep:   time step for each period [s]
    # tempMin:    minimum temperature [C]
    # tempMax:    maximum temperature [C]
    sin_now = sin((time_now - time_start).total_seconds() * pi * 2 / time_step_measure)
    if sin_now > 0:
        return temp_min
    return temp_max

def main(args):
    # read parameters from TOML file
    par = toml.load(args.tomlFile)
    print(par)

    # set parameters, bath1 does cycle, bath 2 does steady
    time_start = datetime.fromisoformat(par['start'])
    time_step_measure = par['time_step_measure_m'] * 60 # [s]
    time_step_cycle = par['time_step_cycle_h'] * 3600  # [s]
    time_step_steady = par['time_step_steady_d'] * 3600 * 24  # [s]
    time_duration = par['duration_d'] * 3600 * 24  # [s]



    bath1 = LaudaRP845()
    if not bath1.connect(port=9):
        print("Failed to connect to Lauda")
        exit(1)

    bath2 = LaudaRP845()
    if not bath2.connect(port=12):
        print("Failed to connect to Lauda")
        exit(1)

    print('INITIALIZING EXPERIMENT: baths')
    print('bath {} has {} C'.format(bath1.getBathID(), bath1.getBathTemp()))
    print('bath {} has {} C \n'.format(bath2.getBathID(), bath2.getBathTemp()))

    # Control mode 0 for internal thermometer control
    bath1.setControlMode(0)
    bath2.setControlMode(0)

    bath1.controlProgram('stop')
    bath2.controlProgram('stop')

    # wait if experiment has not yet started
    time_wait = time_start - datetime.utcnow()
    if time_wait.total_seconds() > 0:
        print("Waiting for start time")
        sleep(time_wait.total_seconds())

    # time loop with changing temperature and logging
    time_stop = time_start + timedelta(seconds=time_duration)
    while time_stop > datetime.utcnow():
        time_now = datetime.utcnow()
        # query baths and measure
        df = DataFrame(
            {
                "time_UTC": [time_now],
                "bath1_Tset": [bath1.getSetpoint()],
                "bath1_Tobs": [bath1.getBathTemp()],
                "bath2_Tset": [bath2.getSetpoint()],
                "bath2_Tobs": [bath2.getBathTemp()]
            }
        )
        # feedback
        print('{}, '
              'B1 set: {}, B1 obs: {}, '
              'B2 set: {}, B2 obs: {}'.format(time_now.strftime("%d/%m/%Y at %H:%M"),
                                              df.bath1_Tset[0],
                                              df.bath1_Tobs[0],
                                              df.bath2_Tset[0],
                                              df.bath2_Tobs[0]))
        # append to csv file, write header on first time, date parses in Excel
        with open(par['outfile'], 'a') as f:
            df.to_csv(f, header=f.tell() == 0,
                      float_format='%.2f', index=False)
        # set new temperatures, wait
        bath1.setSetpoint(square_wave(time_now, time_start,
                                      time_step_cycle,
                                      par['temp_min_C'], par['temp_max_C']))
        bath2.setSetpoint(square_wave(time_now, time_start,
                                      time_step_steady,
                                      par['temp_min_C'], par['temp_max_C']))
        sleep(time_step_measure)

    # finish
    bath1.disconnect()
    bath2.disconnect()
    print('FINISHED EXPERIMENT')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("tomlFile", type=str)
    args = parser.parse_args()
    main(args)

#    pass
