##############################################################################################################################
# 
# Script created by Jishnu Thekkeppattu (2023-03) for caltxt2uv.sh to convert text files with calibration solutions dumped 
# from the database to MIRIAD .uv files with calibration tables 
# 
##############################################################################################################################
import numpy as np
import argparse

parser = argparse.ArgumentParser(description='Read list of gains and phase, perform a median analysis and replace outliers with 0')
parser.add_argument('-x', metavar='xfilename', help='X pol filename with PATH')
parser.add_argument('-y', metavar='yfilename', help='Y pol filename with PATH')
args = parser.parse_args()

xfile = args.x
yfile = args.y

PATHx = "/".join(xfile.split("/")[:-1])+"/"
PATHy = "/".join(yfile.split("/")[:-1])+"/"

gain_x  = np.loadtxt(xfile, delimiter=",")[:,0].astype(np.float64)
phase_x = np.loadtxt(xfile, delimiter=",")[:,1].astype(np.float64)

gain_y  = np.loadtxt(yfile, delimiter=",")[:,0].astype(np.float64)
phase_y = np.loadtxt(yfile, delimiter=",")[:,1].astype(np.float64)

median_gainx = np.median(gain_x)
gain_x[np.where(gain_x > 2*median_gainx)[0]] = 0

median_gainy = np.median(gain_y)
gain_y[np.where(gain_y > 2*median_gainy)[0]] = 0

np.savetxt(PATHx+"filtered_db_gainsx.csv", np.column_stack([gain_x, phase_x]), fmt="%4.4f, %4.4f")
np.savetxt(PATHy+"filtered_db_gainsy.csv", np.column_stack([gain_y, phase_y]), fmt="%4.4f, %4.4f")
