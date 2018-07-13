import matplotlib.pyplot as plt
from pandas import read_csv, DataFrame, datetime
import numpy as np
from drawnow import drawnow
import time
from Fluke1502A import Fluke1502A


class monitorFile():
    """ make real-time plots of data files as they are written from instruments to a file """
    def __init__(self):
        self.fig = plt.figure() # make a figure
        self.col_x = 0
        self.col_y = 1
        self.max_x = 15

    def setFile(self, file):
        self.file = file

    def set_xcol(self, x):
        self.col_x = x

    def set_ycol(self, y):
        self.col_y = y

    def set_xmax(self, xmax):
        self.max_x = xmax

    def readdata(self, file=None):
        if file is None:
            file = self.file
        self.data = pd.read_csv(file)

        # take only last rows
        if self.data.shape[0] > self.max_x:
            self.data = self.data[-self.max.x:]

    def simpleXY(self):
        X = self.data[self.data.columns[self.col_x]]
        Y = self.data[self.data.columns[self.col_y]]
        plt.scatter(X, Y)

    def execute(self, refresh = 5, runfor=15):
        """ monitor and plot data"""
        for i in range(1, runfor):
            self.readdata()
            drawnow(self.simpleXY)
            plt.pause(0.001)
            time.sleep(refresh)

class monitorFluke1502:
    def __init__(self):
        self.probe = Fluke1502A()
        self.probe.connect()
        self.max_x = 50
        self.fig = plt.figure() # make a figure
        self.X = list()
        self.Y = list()

    def set_xmax(self, xmax):
        self.max_x = xmax

    def read(self, init=False):
        t = datetime.now()
        T = float(self.probe.readTemp())
        self.X.append(t)
        self.Y.append(T)

    def plotsetup(self, ax):
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=70)
        ax.set_xlabel('Time')
        ax.set_ylabel('Temperature (C)')
        plt.subplots_adjust(bottom = 0.2, top = 0.95, left = 0.15, right = 0.95)

    def plot(self):
        X = self.X
        Y = self.Y
        if len(X) > self.max_x:
            X = X[-self.max_x:]
            Y = Y[-self.max_x:]
        plt.plot(X, Y)
        axes = plt.gca()
        self.plotsetup(axes)

    def watch(self, refresh = 1, runfor = 60):
        t_end = time.time() + runfor
        self.run = True
        while self.run:
            self.read()
            drawnow(self.plot)
            plt.pause(refresh)
            if time.time() > t_end:
                self.run = False

# M = monitorFile()
# M.setFile("E:/Users/Nick/Desktop/text.csv")
# M.execute()

M = monitorFluke1502()
M.set_xmax(10)
M.watch()