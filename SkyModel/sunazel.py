#!/usr/bin/env python3
# print RA and DEC of sun given a unix time
from astropy.time import Time
import astropy.coordinates
import sys

unix_time=int(sys.argv[1])
obs=astropy.coordinates.EarthLocation.of_site('MWA')
#print unix_time
t = Time(unix_time,format='unix')
sunpos = astropy.coordinates.get_sun(t)
sunelaz = sunpos.transform_to(astropy.coordinates.AltAz(obstime=t,location=obs))
print(sunelaz.alt.degree,sunelaz.az.degree)
