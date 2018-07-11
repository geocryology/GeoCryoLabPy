import matplotlib.pyplot as plt
import numpy as np
import datetime
from scipy import interpolate
from pandas import DataFrame, read_csv, to_datetime

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

    def contourPlot(self):
        """ produces an interpolated depth - time plot """
        df = self.tmp.groupby(['Timestamp', 'depth'], as_index=False).mean() # depth-averages
        df.drop(['column'], axis = 1) # no longer relevant


    def threeD(self):
        """ an interactive surface 3d plot"""
        pass


df = read_csv(r"C:\Users\A139\Documents\2018-07-06_FirstRun\2018-07-06_FirstRun_processed.csv")
df['Timestamp'] = to_datetime(df['Timestamp'])

df = df[df['column'].between(1, 6)]
df['value'][df['value'] < - 100] = np.nan
df = df.groupby(['Timestamp', 'depth'], as_index=False).mean()
df.drop(['column'], axis = 1)

df = df.iloc[::10, :]
X = df['Timestamp']
Y = df['depth']
Z = df['value']

xi = np.linspace(X.min().value, X.max().value, 100)
yi = np.linspace(Y.min(), Y.max(), 100)

xi, yi = np.meshgrid(xi, yi)
rbf = interpolate.Rbf(X, Y, Z, function='linear')
zi = rbf(xi, yi)
xi = [to_datetime(q) for q in xi]
plt.figure()
CS = plt.contour(xi, yi, zi)
plt.show()
plt.clabel(CS, inline=1, fontsize=10)
plt.title('Simplest default with labels')