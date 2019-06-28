#!/usr/bin/env python
# calculate the LST at the MRO given the unix time as a command-line argument
from astropy.time import Time
import sys

#print "Arg: "+sys.argv[1]
t=Time(long(sys.argv[1]),format='unix')
lst = t.sidereal_time(kind='apparent',longitude=116.67082)
#print lst.to_string(decimal=True)
print lst.hour
