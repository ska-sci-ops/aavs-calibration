#!/usr/bin/env python3
# make a pixel scaling image for an all-sky SIN projection to correct for
# the changing sky area per pixel in this projection. This is used to correct
# for the total flux seen in each pixel when a brightness-like image is
# reprojected/represented in the SIN orthographic projection.

# command-line args: make_pixscalefits.py img_size LST_hours
# 
import sys
import numpy
from astropy.io import fits
from astropy import wcs

imgsize=1024
lst_hours=0
dec_degs=-26.7033
freq_MHz=150.0

def make_azza_arrays(gsize):
  '''Make 2D arrays of azimuth and zenith angle for an orthographic (sine) projection of the entire sky
  '''
  c = (numpy.mod(numpy.reshape(numpy.arange(gsize*gsize),(gsize,gsize)) , gsize) - gsize/2.0)/(gsize/2)
  r = ((numpy.reshape(numpy.arange(gsize*gsize),(gsize,gsize)) // gsize) - gsize/2.0)/(gsize/2)
  fov=180.0 # degrees
  myfov = numpy.sin(fov/2*numpy.pi/180.)
  dsqu = (c*c+r*r)*(myfov*myfov)
  p = numpy.nonzero(dsqu < 1)
  za = dsqu * 0.0 + numpy.pi/2
  za[p] = numpy.arcsin(numpy.sqrt(dsqu[p]))
  az = numpy.arctan2(c,r)
  return az.astype(numpy.float32),za.astype(numpy.float32)

if (len(sys.argv)>1):
    imgsize = int(sys.argv[1])
    #print("Specified image size: %d" % (imgsize))

if (len(sys.argv)>2):
    lst_hours = float(sys.argv[2])

(az,za) = make_azza_arrays(imgsize)

a = az*0.0 + 1.0
p = numpy.nonzero(za < numpy.pi/2*0.97)
a[p] = 1./numpy.cos(za[p])

# make a simple zenith-oriented orthographic projection
w = wcs.WCS(naxis=2)
pixscale=180.0/(imgsize/2)/numpy.pi

w.wcs.crpix = [imgsize/2, imgsize/2]
w.wcs.cdelt = numpy.array([-pixscale, pixscale])
w.wcs.crval = [lst_hours*15, dec_degs]
w.wcs.ctype = ["RA---SIN", "DEC--SIN"]

header = w.to_header()
#header['FREQENCY'] = freq_MHz*1e6  # possibly not needed
hdu = fits.PrimaryHDU(a,header=header)
fname="pixsacle_SIN_%dx%d.fits" % (imgsize,imgsize)
hdu.writeto(fname)


