import matplotlib.pyplot as plt
import numpy as np
import datetime
import matplotlib.dates as mdates
from scipy import interpolate
from pandas import DataFrame, read_csv, to_datetime, concat, Timedelta, to_numeric
from sys import version_info

class ColumnPlotter:
    """ plotting various  """

    def __init__(self, columnFile):
        self.loadData(columnFile)

    def loadData(self, columnFile):
        """ reads processed data and saves it as a pandas dataframe """
        df = read_csv(columnFile)
        df['Timestamp'] = to_datetime(df['Timestamp'])
        self.data = df
        self.__splitData()

    def __splitData(self):
        """ splits data into different parts of soil column """
        self.tmp = self.data[self.data['column'].between(1, 6)]   # main column thermistors
        self.ctr = self.data[self.data['column'] == 7]    # centreline thermistors
        self.out = self.data[self.data['column'] == 8]    # exterior (jacket) theristors
        self.aux = self.data[self.data['column'] == -999] # auxiliary temperatures

    def __autoclean(self, df, cutoff = -40):
        """ remove any depths with ANY sensor dropouts (temperature below cutoff)"""
         # find positions with dropouts
        self.dropouts = set(df.loc[df['value'] < cutoff, 'position'])

        # get rid of 'em
        out = df.drop(df[df.position.isin(self.dropouts)].index, inplace =  False)
        return(out)

    def linearPlot(self, column=1):
        """ produces a plot with temperature over time for a single column """
        # make copy of data so it doesn't interfere, and remove any dropouts
        df = self.__autoclean(self.data)

        # Prepare data
        df = df[df['column'] == column]
        df['depth'] = to_numeric(df['depth'])

        # Prepare list of depths
        depths = df.depth.unique()
        depths.sort()

        # Plot a line for every depth
        for i in depths:
            dep = df[df['depth'] == i]
            plt.plot(dep['Timestamp'], dep['value'], label = i)
            plt.ylabel('Temperature (C)')
            plt.xlabel('Time')
            plt.legend(title = 'Depth (mm)')

        plt.show()

    def contourPlot(self, label=True, contour=True):
        """ produces an interpolated depth - time plot """
        # make copy of data so it doesn't interfere, and remove any dropouts
        df = self.__autoclean(self.tmp)

        # remove unnecessary columns
        df.drop(['column'], axis = 1, inplace = True)
        df.drop(['uncertainty'], axis = 1, inplace = True)
        df.drop(['position'], axis = 1, inplace = True)
        df.drop(['name'], axis = 1, inplace = True)

        # get depth-averaged values
        #df = self.tmp.groupby(['Timestamp', 'depth'], as_index=False).mean() # depth-averages
        df = df.groupby(['Timestamp', 'depth'], as_index=False).agg(np.nanmean)

        # reshape data into "wide" format
        d = df.set_index(['depth', 'Timestamp'])
        d = d.unstack()

        # extract x,y and z (array) values
        X = to_datetime(list(d.columns.levels[1]))
        Y = d.index
        Z = np.array(d)

        # set up plot
        fig = plt.figure(figsize=(10, 6))
        ax1 = fig.add_subplot(111)
        clev = np.arange(np.nanmin(Z), np.nanmax(Z), 1)

        # add data
        cs = ax1.contourf(X, Y, Z,  levels=clev, cmap=plt.cm.coolwarm)
        fig.colorbar(cs, ticks = np.arange(-25,25,5))

        if contour:
            cs2 = ax1.contour(X, Y, Z, levels = np.arange(-50, 50, 5), colors='k', linewidths = 1)
            if label:
                plt.clabel(cs2, fontsize=8, inline=1, fmt="%1.0f")

        # set up x and y axis ticks
        ax1.xaxis.set_major_locator(mdates.DayLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d           "))
        ax1.xaxis.set_minor_locator(mdates.HourLocator(interval = 6))
        ax1.xaxis.set_minor_formatter(mdates.DateFormatter("%H:%M"))
        plt.setp(ax1.xaxis.get_minorticklabels(), rotation=70)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=70)
        plt.ylim(max(Y), min(Y))

        # axis labels
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Depth (cm)')
        plt.subplots_adjust(bottom = 0.2, top = 0.95, left = 0.08, right = 0.95)

        plt.show()

    def meanPlot(self, st_hr = 40, end_hr = 64, trumpet=True, use_set_bndry=False):
         # get thermistor and plate data.  remove any droupouts

        if use_set_bndry:
            # force upper and lower boundaries to be set temperature (e.g. if external probes have become unseated)
            self.aux.loc[(self.aux['name'] == 'upperExtTemp'), 'value'] = self.aux.loc[(self.aux['name'] == 'upperTarget'), 'value'].values
            self.aux.loc[(self.aux['name'] == 'lowerExtTemp'), 'value'] = self.aux.loc[(self.aux['name'] == 'lowerTarget'), 'value'].values
        bndry = self.aux[(self.aux['name'] == 'upperExtTemp') | (self.aux['name'] == 'lowerExtTemp')]
        df = concat([self.tmp, bndry], axis=0)
        df = self.__autoclean(df)

        # remove unnecessary columns
        df.drop(['column'], axis = 1, inplace = True)
        df.drop(['uncertainty'], axis = 1, inplace = True)
        df.drop(['position'], axis = 1, inplace = True)
        df.drop(['name'], axis = 1, inplace = True)

        # take time subset of data then drop timestamp column
        st = df['Timestamp'][0] + Timedelta(hours = st_hr)
        en = df['Timestamp'][0] + Timedelta(hours = end_hr)
        df = df[df['Timestamp'].between(st, en)]
        df.drop(['Timestamp'], axis = 1, inplace = True)

        # get depth averages
        if version_info[0] > 3: # don't know why this doesn't work with v 2.x
            Tmax = df.groupby(['depth'], as_index = False).agg(np.nanmax)
            Tmin = df.groupby(['depth'], as_index = False).agg(np.nanmin)
            df = df.groupby(['depth'], as_index = False).agg(np.nanmean)
        else:
            Tmax = df.groupby(['depth'], as_index = False)['value'].max()
            Tmin = df.groupby(['depth'], as_index = False)['value'].min()
            df = df.groupby(['depth'], as_index = False)['value'].mean()

        # set up plot
        fig = plt.figure(figsize = (10, 6))
        ax1 = fig.add_subplot(111)

         # add data
        X = df['value']
        Y = df['depth']
        ax1.plot(X, Y, color='k')
        if trumpet:
            ax1.fill_betweenx(Tmax['depth'], Tmin['value'], Tmax['value'], color = (.8, .8, .8, 0.5))
            ax1.plot(Tmax['value'], Tmax['depth'], color = 'r')
            ax1.plot(Tmin['value'], Tmin['depth'], color = 'b')

        if version_info[0] > 3:
            ax1.plot([float(X[Y == 0]), float(X[Y == Y.max()])], [0, Y.max()], 'k--', lw=0.5)
        else:
            ax1.plot([np.float(X[Y == 0]), np.float(X[Y == Y.max()])], [0, Y.max()], 'k--', lw=0.5)
        plt.ylim(max(Y), min(Y))

        # axis labels
        ax1.set_ylabel('Depth (mm)')
        ax1.set_xlabel('Temperature (C)')

        plt.show()

    def threeD(self):
        """ an interactive 3d plot"""
        pass



