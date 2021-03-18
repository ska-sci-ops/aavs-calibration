#!/usr/bin/python3
# print RA and DEC of sun given a unix time
from __future__ import print_function
from astropy.time import Time
import astropy.coordinates
import sys

unix_time = int(sys.argv[1])
t = Time(unix_time,format='unix')
sunpos = astropy.coordinates.get_sun(t)
print(sunpos.ra.hour, sunpos.dec.degree)
