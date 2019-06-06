#!/usr/bin/env python3
# calc RA and DEC of sun given a unix time and add simple model sun to
# an existing FITS image

# command-line args:
#sun_add.py unixtime freq_mhz image.fits 

from astropy.time import Time
from astropy.wcs import WCS
from astropy.io import fits
from astropy.modeling import models
import numpy as np
import astropy.coordinates
import sys,math

unix_time=int(sys.argv[1])
obs=astropy.coordinates.EarthLocation.of_site('MWA')
#print unix_time
t = Time(unix_time,format='unix')
sunpos = astropy.coordinates.get_sun(t)
sunazel=sunpos.transform_to(astropy.coordinates.AltAz(location=obs))
print("RA: %f, DEC: %f, alt: %f, az: %f" % (sunpos.ra.hour,sunpos.dec.degree,sunazel.alt.degree,sunazel.az.degree) )

if sunazel.alt.degree < 1:
  print("It is not daytime. Nothing to do")
  sys.exit(1)

freq_mhz = float(sys.argv[2])

# open the model image and load the WCS
hdulist = fits.open(sys.argv[3])
skyimg=np.squeeze(np.nan_to_num(hdulist[0].data))
wcs = WCS(hdulist[0].header)
wcs2d=wcs.dropaxis(2)   # drop the bogus frequency axis
# find the pixel coord of the sun in 0-based pixel coords
sunpixcrd = wcs2d.wcs_world2pix(sunpos.ra.degree,sunpos.dec.degree, 0)
#print("Sun pixel coords: %f,%f"%(sunpixcrd[0],sunpixcrd[1]))

# make model sun blob
imshape=skyimg.shape
y,x = np.mgrid[0:(imshape[0]),0:(imshape[1])]
sunscale=0.5/np.abs(wcs2d.wcs.cdelt)
modelsun=models.Ellipse2D(1.0,sunpixcrd[0],sunpixcrd[1],sunscale[0],sunscale[1],0)
modelsunimg=modelsun(x,y)

# scale total flux
# output the quiet solar radio flux in Jy at given input frequency in MHz
# based on http://spaceacademy.net.au/env/sol/solradp/solradp.htm
# and extras.springer.com/2009/978-3-540-88054-7/06_vi4b_4116.pdf
# 1 solar flux unit (SFU) = 10000 Jy
# based on the Benz paper, the quiet solar flux can be approximated between 50 and 350 MHz by
# S = 1.94e-4 * f^(1.992) SFU = 1.94 * f^(1.992) Jy, where f is in MHz
s_flux = 1.94*math.pow(freq_mhz,1.992)
modelsunimg *= s_flux/np.sum(modelsunimg)

# add model sun to sky image and write new image
skyimg += modelsunimg
newhdr = wcs2d.to_header()
newhdu = fits.PrimaryHDU(header=newhdr)
fits.writeto('skywt_sun.fits',skyimg,header=newhdr,overwrite=True)

