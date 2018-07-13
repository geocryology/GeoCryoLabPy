import matplotlib.pyplot as plt
import pandas as pd
from drawnow import drawnow
import time

class Monitor():
    """ make real-time plots of data files as they are written from instruments """
    def __init__(self):
        #plt.ion() # enable interactivity
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

#    plt.show(block=False)
#    plt.draw()

M = Monitor()
M.setFile("E:/Users/Nick/Desktop/text.csv")
M.execute()

