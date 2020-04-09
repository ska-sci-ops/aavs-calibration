#!/usr/bin/python

from __future__ import print_function
import datetime
import glob
import os
import sys
import time
import warnings

from astropy.io import fits

import numpy

warnings.simplefilter(action='ignore')
import Pyro4


import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

# import mwaconfig
import pointing


"""
  Tests all EDA dipoles by stepping through all 256 dipoles one by one.
"""

# DIPOLE_FILE = "/usr/local/etc/locations.txt"
DIPOLE_FILE = "locations.txt"

TILEID = 0

MAXAGE = 60
HEXD = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']

KURL = 'PYRO:Kaelus@10.128.2.51:19987'
BURLS = {'eda1com':'PYRO:eda1com@10.128.2.63:19987', 'eda2com':'PYRO:eda2com@10.128.2.65:19987'}

XTICKS = [5000, 10000, 15000, 20000, 25000, 30000]
XLABELS = ['50', '100', '150', '200', '250', '300']

YTICKS = [10, 20, 30, 40, 50, 60]
YLABELS = ['10', '20', '30', '40', '50', '60']


def getdata():
  """Returns a numpy array containing the most recently written EDA spectrum.
     Return None if the most recent file is older than MAXAGE seconds.
  """
  flist = glob.glob('/tmp/livespec_??.fits')
  fdict = {}
  for fname in flist:
    fdict[os.path.getmtime(fname)] = fname
  tlist = fdict.keys()
  tlist.sort()
  dtime = tlist[-2]       # Pick the second last one, in case the latest one is still being written.
  fname = fdict[dtime]
  if (time.time() - dtime) > MAXAGE:
    return None   # All files are too old

  f = fits.open(fname)
  return f[0].data, dtime


def freqbin(indat=None):
  """Takes a numpy array (shape=(32768,)) and sums groups of 128 channels to
     produce an output array of shape (256,)
  """
  odat = numpy.zeros(shape=(256,), dtype=numpy.float32)
  for i in range(256):
    odat[i] = indat[(i * 128):(i * 128 + 128)].sum()
  odat.shape = (256, 1, 1)
  return odat


def set_onlybfs(onlybfs):
  print("Setting onlybfs global to %s" % onlybfs)
  kproxy.onlybfs(bfids=onlybfs)
  for proxy in bfproxies.values():
    proxy.onlybfs(bfids=onlybfs)


def point_azel( az=0.00, el=90.00 ) :
 offsets = pointing.getOffsets(dipolefile=DIPOLE_FILE)
 idelays, errors, pointing_coeff, meandelays = pointing.calc_delays(offsets=offsets, az=az, el=el, strict=False, verbose=True, clipdelays=True, optimise=False, cpos=(0.0, 0.0, 0.0))
                                           
 for b in HEXD:
    print("%s : %s" % (b,idelays[b]))
#    print "idelays = %s" % (idelays)                                           
    
#  kproxy = Pyro4.Proxy(KURL)
 bfproxies = {}
 for clientid, url in BURLS.items():
    bfproxies[clientid] = Pyro4.Proxy(url)

 xarray = numpy.zeros(shape=(16, 16, 32768))
 yarray = numpy.zeros(shape=(16, 16, 32768))
 starttime = time.time()

 stime = int(time.time() + 2)
 values = {TILEID:{'X':(None, None, az, el, idelays),
                    'Y':(None, None, az, el, idelays)
                   }
           }
#      kproxy.notify(obsid=0, starttime=stime, stoptime=stime + 8, clientid='Kaelus', rclass='pointing', values=values)
 for clientid, proxy in bfproxies.items():
     proxy.notify(obsid=0, starttime=stime, stoptime=stime + 8, clientid=clientid, rclass='pointing', values=values)

 print("Test finished, EDA-1 / TPM-17 pointed at (az,el) = (%.2f,%.2f) [deg]" % (az,el))
#  time.sleep(8)
  # data, dtime = getdata()

  # We've finished the test, so point the EDA back at the zenith
#  delays = {}
#  for b in HEXD:  # An extra beamformer 'K' to hold Kaelus delays
#    delays[b] = {}
#    for d in HEXD:
#      delays[b][d] = 0  # An offset of 16 is added to all delays, so this will become 16
#  for d in HEXD:
#    delays['K'][d] = 0   # An offset of 128 is added to all delays, so this will become 128
#
#  stime = int(time.time() + 1)
#  values = {TILEID: {'X': (None, None, 0.0, 0.0, delays),
#                     'Y': (None, None, 0.0, 0.0, delays)
#                 }
#            }
#  kproxy.notify(obsid=0, starttime=stime, clientid='Kaelus', rclass='pointing', values=values)
#  for clientid, proxy in bfproxies.items():
#    proxy.notify(obsid=0, starttime=stime, clientid=clientid, rclass='pointing', values=values)

#  print "Test finished, EDA-1 / TPM-17 pointed to zenith."

 return pointing_coeff, meandelays
 
  