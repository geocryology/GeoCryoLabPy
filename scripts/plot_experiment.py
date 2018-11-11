import sys
from os import path


if __name__ == '__main__':

    fp = path.dirname(path.realpath(__file__))
    eqp = path.join(path.dirname(fp), "equipment")
    sys.path.append(eqp)

    from ColumnPlot import ColumnPlotter
    import argparse
    import configparser

    parser = argparse.ArgumentParser(description="Process raw data from column experiment",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--data',    type=str,   help="path to processed data file")
    parser.add_argument('--dir',    type=str,   help="directory to save plots")
    parser.add_argument('--mean',    action='store_true',   help="make a mean plot")
    parser.add_argument('--cont',    action='store_true',   help="make a contour plot")
    parser.add_argument('--set_bnds',action='store_true',   help="use target temperatures for mean plot boundaries", default=False)
    args = parser.parse_args()

    P = ColumnPlotter(args.data)

    if args.mean:
        P.meanPlot(use_set_bndry=args.set_bnds)

    if args.cont:
        P.contourPlot()

