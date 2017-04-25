import math
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

def draw(csvFile):

    csv = None

    try:
        csv = open(csvFile, 'r').readlines()
    except IOError:
        print "Failed to open file {}".format(csvFile)
        exit()

    while not csv[0].lower().startswith("frequency"):
        csv = csv[1:]
    csv = csv[1:]

    numPoints = len(csv)

    frequencies = []
    impedances  = []
    phases      = []

    for i in range(numPoints):
        freq      = float(csv[i].split(',')[0])
        impedance = float(csv[i].split(',')[9])
        phase     = float(csv[i].split(',')[10])
        frequencies.append(freq)
        impedances.append(impedance)
        phases.append(phase)

    x  = frequencies
    y  = impedances
    y2 = phases
    maxImpedance = int(max(impedances))
    minImpedance = int(min(impedances))

    # create two subplots, sharing x axis (frequency)
    fig, (ax1, ax2, ax3) = plt.subplots(3, sharex=True)
    ax1.set_title("Impedance and Phase")

    ax1.plot(frequencies, impedances)
    ax1.set_yscale("linear")
    ax1.set_xscale("log")
    ax1.grid(True)
    ax1.set_ylabel("Impedance [Ohms]")
    ax1.yaxis.set_label_position("right")

    ax2.plot(frequencies, impedances)
    ax2.set_yscale("log")
    ax2.set_xscale("log")
    ax2.grid(True)
    ax2.set_ylabel("Impedance [Ohms]")
    ax2.yaxis.set_label_position("right")

    #ticks =  map(int, list(ax1.get_yticks()))
    #ticks.append([minImpedance, maxImpedance])
    #ticks = sorted(ticks)
    #ax1.set_yticks(ticks)

    ax3.plot(frequencies, phases)
    ax3.set_xscale("log")
    ax3.grid(True)
    ax3.set_ylabel("Phase [Degrees]")
    ax3.set_xlabel("Frequency [Hz]")
    ax3.yaxis.set_label_position("right")

    #ax = axs
    #ax.plot(x, y)
    #ax.set_yscale('log')
    #ax.set_xscale('log')
    #ax.grid(True)

   # plt.show()
    #exit()

    plt.savefig(csvFile.split('.')[0] + ".png")
    plt.close()

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print "  Usage: draw.py file.csv"
        exit(1)

    filename = sys.argv[1]

    draw(filename)


    #for f in os.listdir("power sweep\\1k"):
    #    draw.draw("power sweep\\1k\\{}".format(f))