### Tools to facilitate column experiments
import numpy as np
from pandas import read_csv, DataFrame

class Thermistor(object):
    def __init__(self):
        self.calibration = None

    def readCalibration(self, file):
        """
        reads a calibration file and stores parameters as a dictionary
        """
        calib = read_csv(file)
        calib = calib.set_index(calib.columns[0])
        self.calibration = calib.transpose().to_dict()
        return True

    def calculateTemperature(self, res, thermistor):
        """
        Calculates temperature for a particular thermistor provided that a 
        suitable calibration is available
        """
        if self.calibration[thermistor]:
            C = self.calibration[thermistor]
            keys = ['a','b','c','d','R0']
            (a,b,c,d,R0) = [C[x] for x in keys]
            T = self.func(res, a, b, c, d, R0)
            return T
        else:
            raise ValueError('thermistor not in calibration file') 
    
    def calculateUncertainty(self, res, thermistor):
        """
        calculates uncertainty on thermistor given 
        """
        if self.calibration[thermistor]:
            C = self.calibration[thermistor]
            keys = ['a','b','c','d', 'uncert_a', 'uncert_b', 'uncert_c', 'uncert_d', 'R0']
            (a,b,c,d, uncert_a, uncert_b, uncert_c, uncert_d,R0) = [C[x] for x in keys]
            Ts = np.array([
                self.func(res, a + uncert_a, b + uncert_b, c + uncert_c, d + uncert_d, R0), 
                self.func(res, a + uncert_a, b - uncert_b, c + uncert_c, d + uncert_d, R0),   
                self.func(res, a + uncert_a, b + uncert_b, c - uncert_c, d + uncert_d, R0), 
                self.func(res, a + uncert_a, b - uncert_b, c - uncert_c, d + uncert_d, R0), 
                self.func(res, a - uncert_a, b + uncert_b, c + uncert_c, d + uncert_d, R0), 
                self.func(res, a - uncert_a, b - uncert_b, c + uncert_c, d + uncert_d, R0),
                self.func(res, a - uncert_a, b + uncert_b, c - uncert_c, d + uncert_d, R0), 
                self.func(res, a - uncert_a, b - uncert_b, c - uncert_c, d + uncert_d, R0),
                self.func(res, a + uncert_a, b + uncert_b, c + uncert_c, d - uncert_d, R0), 
                self.func(res, a + uncert_a, b - uncert_b, c + uncert_c, d - uncert_d, R0),   
                self.func(res, a + uncert_a, b + uncert_b, c - uncert_c, d - uncert_d, R0), 
                self.func(res, a + uncert_a, b - uncert_b, c - uncert_c, d - uncert_d, R0), 
                self.func(res, a - uncert_a, b + uncert_b, c + uncert_c, d - uncert_d, R0), 
                self.func(res, a - uncert_a, b - uncert_b, c + uncert_c, d - uncert_d, R0),
                self.func(res, a - uncert_a, b + uncert_b, c - uncert_c, d - uncert_d, R0), 
                self.func(res, a - uncert_a, b - uncert_b, c - uncert_c, d - uncert_d, R0)
                ])
            T = [min(Ts), max(Ts)]
            return T
        else:
            raise ValueError('thermistor not in calibration file') 
       

    @staticmethod
    def func(R, a, b, c, d, R0): 
        """
        Args:
            T temperature in 
            a,b,c,d are calibration parameters
        """
        x = R / R0
        T = 1 / (a + b * np.log(x) + c * np.log(x)**2 + d * np.log(x)**3)
        return T

