import sys
from os import path


if __name__ == '__main__':

    fp = path.dirname(path.realpath(__file__))
    eqp = path.join(path.dirname(fp), "equipment")
    sys.path.append(eqp)

    from ColumnUtils import ColumnExperiment
    import argparse
    import configparser

    parser = argparse.ArgumentParser(description="Process raw data from column experiment",
                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--sh',  type=float, help="soil height in cm")
    parser.add_argument('--rd',  type=str,   help="path to raw temperature data file")
    parser.add_argument('--cfg', type=str,   help="path to columnconfig directory")
    parser.add_argument('-f',    action='store_true',   help="overwrite existing directory")

    args = parser.parse_args()

    C = ColumnExperiment(raw_data = args.rd, cfg_dir = args.cfg, soil_height = args.sh)
    C.setOverwrite(args.f)
    C.processColumn()