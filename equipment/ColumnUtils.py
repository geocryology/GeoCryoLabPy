### Tools to facilitate column experiments
import os
import shutil
import re
from os import path, listdir
import numpy as np
import uncertainties as unc
from uncertainties.umath import log as ulog

from pandas import read_csv, DataFrame, melt


class Thermistor(object):
    """
    Provides tools to deal with thermistors based on external calibration
    and name files
    """
    def __init__(self):
        self.calibration = None

    def readNames(self, file):
        """
        Read a csv that gives the name of the thermistor in each channel
        """
        names = read_csv(file)
        self.channelNames = {x:y for (x, y) in zip(names.ix[:, 0], names.ix[:, 1])}


    def getChannelName(self, channel):
        """
        Get name of thermistor in channel.  Uses a csv to store names which allows for
        the replacement of thermistors over time if any burn out
        """
        if self.channelNames[channel]:
            name = self.channelNames[channel]
            return(name)

        else:
            raise LookupError('Channel not valid')

    def readCalibration(self, file):
        """
        reads a calibration file and stores parameters as a dictionary
        """
        calib = read_csv(file)
        calib = calib.set_index(calib.columns[1])
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
            raise LookupError('thermistor not in calibration file')

    def calculateUncertainty(self, res, thermistor):
        """
        calculates uncertainty on thermistor given a resistance and the thermistor name
        """

        if self.calibration[thermistor]:
            C = self.calibration[thermistor]
            keys = ['a','b','c','d', 'uncert_a', 'uncert_b', 'uncert_c', 'uncert_d', 'R0']
            (a,b,c,d, uncert_a, uncert_b, uncert_c, uncert_d,R0) = [C[x] for x in keys]

            # add uncertainty to resistance measurements
            R0 = unc.ufloat(R0, 0.12)
            res = unc.ufloat(res, 0.12)

            Tu = self.func(res, unc.ufloat(a, uncert_a*2), unc.ufloat(b, uncert_b*2),
                         unc.ufloat(c, uncert_c*2), unc.ufloat(d, uncert_d*2), R0)
            return unc.std_dev(Tu)
        else:
            raise LookupError('thermistor not in calibration file')

    @staticmethod
    def func(R, a, b, c, d, R0):
        """
        Args:
            T temperature in
            a,b,c,d are calibration parameters
        """
        x = R / R0
        T = 1 / (a + b * ulog(x) + c * ulog(x)**2 + d * ulog(x)**3)
        return T

    def hasCalibration(self, thermistors):
        """ checks if a list of thermistors (names) have calibration data """
        if not self.calibration:
            print("Missing calibration file")
            return False

        missing = []
        for name in thermistors:
            if not self.calibration[name]:
                missing.append(name)

        if len(missing) == 0:
            return True

        print('\n'.join(map(str, missing)))
        return False

def getChannels(channelList):
    """get a set of channels from a text string"""
    validChannels = range(101, 121) + range(201, 221) + range(301, 321)
    channels = set()
    ranges = channelList.split(",")

    for rng in ranges:
        # For 'true' ranges
        if ":" in rng:
            lo, hi = map(int, rng.split(":"))
            for channel in range(lo, hi+1):
                if channel not in validChannels:
                    print("Invalid channel {}".format(channel))
                    exit(1)
                channels.add(channel)

       # For singletons
        else:
            if int(rng) not in validChannels:
                print("Invalid channel {}".format(channel))
                exit(1)
            channels.add(int(rng))

    return channels

def getChannelName(channel):
    """Get the name of a thermistor based on its channel"""
    slot = channel / 100
    k    = channel % 100 + 20 * (slot - 1)
    cable = 1 + (k-1) / 10
    return "T17-S{}C{}-{}".format(str(slot), str(cable), str(k).zfill(3))


class ColumnExperiment(object):
    # 275mm from top of ring to midpoint of lowest thermistor.
    # 230mm from top of ring to top of lower brass plate
    # 2 cm thermistor spacing (offset)

    ROW_HEIGHTS = dict(zip(range(1, 24), np.arange(44. + 2.75, -2. + 2.75, -2)))

    def __init__(self, raw_data, cfg_dir, soil_height):
        self.soil_height = soil_height # height of top of soil in column
        self.cfg_dir = cfg_dir
        self.raw_data = raw_data
        self.experiment = re.sub("_[tr][me][ps]\\..*$", "", path.basename(self.raw_data))
        self.output_dir = path.join(path.dirname(self.raw_data), self.experiment)
        self.overwrite  = False

        # Define height of each row index
        self._read_config_dir(cfg_dir)

    def _read_config_dir(self, cfg_dir):
        """
        Looks for the following configuration files and reads them into dictionaries:
        thermistorNames.csv
        thermistorPosition.csv
        """
        f = listdir(cfg_dir)

        # find calibration files in configuration directory
        f_names    = self.__find_in_list(f, "thermistorNames")
        f_position = self.__find_in_list(f, "thermistorPosition")

        # create dictionaries from csv's
        names_data = read_csv(path.join(cfg_dir, f_names[0]))
        self.names = dict(zip(names_data.ix[:, 0], names_data.ix[:, 1]))
        pos_data = read_csv(path.join(cfg_dir, f_position[0]))
        self.position = dict(zip(pos_data.ix[:, 1], pos_data.ix[:, 0])) # 'reversed' column index order

    def getThermistorDepth(self, thermistor_name):
        ''' get thermistor depth relative to soil surface'''
        therm_pos    = self.position[thermistor_name]
        therm_row    = int(str(therm_pos)[1:3])
        therm_height = self.ROW_HEIGHTS[therm_row]
        therm_depth  = self.soil_height - therm_height

        return(therm_depth)

    def getThermistorColumn(self, thermistor_name):
        ''' get column index of thermistor in tube'''
        therm_pos    = self.position[thermistor_name]
        therm_col    = int(str(therm_pos)[0])

        return(therm_col)

    @staticmethod
    def __find_in_list(lst, pattern):
        '''get an item in a list by regex matching '''
        r = re.compile(pattern)
        found = list(filter(r.match, lst))
        return(found)

    def __create_output_dir(self):
        if os.path.exists(self.output_dir):
            if self.overwrite:
                shutil.rmtree(self.output_dir)
            else:
                print("output directory already exists!  Exiting")
                exit(1)
        os.makedirs(self.output_dir)


    def setOverwrite(self, permission):
        self.overwrite = permission

    def __copy_config(self):
        dest = path.join(self.output_dir, "cfg")
        shutil.copytree(self.cfg_dir, dest)

    def __copy_rawdata(self):
        # copy raw resistance data
        res = re.sub("tmp", "res", self.raw_data)
        shutil.copyfile(res, path.join(self.output_dir, path.basename(res)))

        # copy raw temperature data
        tmp = self.raw_data
        shutil.copyfile(tmp, path.join(self.output_dir, path.basename(tmp)))

    def __zip_output_dir(self):
        print('not implemented yet')
        pass

    def _rename_column(self, column_name):
        if (re.match("Time", column_name) or
            re.match("upper", column_name) or
            re.match("lower", column_name)):
            return(column_name)

        stdev = None
        if (re.match(".*_stdev$", column_name)):
            column_name = re.sub("_stdev$", "", column_name)
            stdev = 1

        D = self.getThermistorDepth(column_name) * 10 # convert to mm
        C = self.getThermistorColumn(column_name)

        newname = "C{:.0f}D{:.0f}".format(C, D)
        if stdev:
            newname = newname + "_stdev"
        return(newname)


    def processFile(self, output_file = None):
        # read data
        df = read_csv(self.raw_data)

        # reshape data
        df = melt(df, id_vars=['Timestamp'])

        # create new columns
        df['position'] = [self._rename_column(x) for x in df['variable']]
        df['depth'] = [re.sub("C\dD([^\_]*)[^0-9]*", "\\1", x) if re.match("C.*D.*", x) else -999 for x in df['position']]
        df['column'] = [re.sub("C(\d).*", "\\1", x) if re.match("C.*D.*", x) else -999 for x in df['position']]
        df['meas_type'] = ["uncertainty" if re.match(".*stdev", x) else "measurement" for x in df['position']]

        # homogenize position and variable columns in preparation for unstacking
        df['position'] = [re.sub('_stdev', "", x) for x in df['position']]
        df['variable'] = [re.sub('_stdev', "", x) for x in df['variable']]

        # reshape (unstack) data
        df = df.set_index(['Timestamp','position', 'variable', 'depth', 'column', 'meas_type'])
        df = df.unstack(5)  # 5 corresponds to the last ('meas_type') column

        # define output column names
        df = DataFrame(df.to_records()) # flatten column names
        df.columns = ['Timestamp', 'position', 'name', 'depth', 'column', 'value', 'uncertainty']

        # input depths for upper and lower plate temperatures
        df.loc[df['name'] == 'upperExtTemp', 'depth'] = 0
        df.loc[df['name'] == 'lowerExtTemp', 'depth'] = self.soil_height * 10 - 23

        # save file
        if output_file is None:
            output_file = re.sub("[tr][em][ps]\\.", "processed.", path.basename(self.raw_data))
            output_file = path.join(self.output_dir, output_file)

        df.to_csv(output_file, index=False)

    def processColumn(self, copycfg = True, copyraw = True, zip = False):
        self.__create_output_dir()
        if copyraw:
            self.__copy_rawdata()
        if copycfg:
            self.__copy_config()
        self.processFile()

        if zip:
            self.__zip_output_dir()

        return(True)
