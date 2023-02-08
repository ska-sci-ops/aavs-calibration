#!/opt/caastro/ext/anaconda/bin/python

import astropy.io.fits as pyfits
import pylab
import math 
from array import *
import matplotlib.pyplot as plt
import numpy as np
import string
import sys
import os
import errno
import getopt
import optparse


# global parameters :
debug=0
fitsname="file.fits"
out_fitsname="scaled.fits"
do_show_plots=0
do_gif=0

center_x=1025
center_y=1025
radius=600

def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
      else: raise
                                            
def usage():
   print "set_phase_centre.py FITS/UVFITS_FILE RA[deg] DEC[deg]" % out_fitsname
   print "\n"
   print "-d : increases verbose level"
   print "-h : prints help and exists"
   print "-g : produce gif of (channel-avg) for all integrations"

# functions :
def parse_command_line():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvdg", ["help", "verb", "debug", "gif"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-d","--debug"):
            debug += 1
        if o in ("-v","--verb"):
            debug += 1
        if o in ("-g","--gif"):
            do_gif = 1
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"
    # ...

# 
if len(sys.argv) > 1:
   fitsname = sys.argv[1]

ra=0.000
if len(sys.argv) > 2:
   ra = float( sys.argv[2] )

dec=0.000
if len(sys.argv) > 3:
   dec = float( sys.argv[3] )

parser=optparse.OptionParser()
parser.set_usage("""setkey.py""")
parser.add_option('-i','--int','--integer',action="store_true",dest="integer",default=False, help="Integer ?")
parser.add_option('-f','--float','--float',action="store_true",dest="float",default=False, help="Float ?")
# parser.add_option("--ap_radius","-a","--aperture","--aperture_radius",dest="aperture_radius",default=0,help="Sum pixels in aperture radius [default: %default]",type="int")
# parser.add_option("--verbose","-v","--verb",dest="verbose",default=0,help="Verbosity level [default: %default]",type="int")
# parser.add_option("--outfile","-o",dest="outfile",default=None,help="Output file name [default:]",type="string")
# parser.add_option('--use_max_flux','--use_max_peak_flux','--max_flux',dest="use_max_peak_flux",action="store_true",default=False, help="Use maximum flux value around the source center [default %]")
(options,args)=parser.parse_args(sys.argv[4:])


print "####################################################"
print "PARAMTERS :"
print "####################################################"
print "fitsname       = %s"   % fitsname
print "(RA,DEC)       = (%.6f,%.6f) [deg]" % (ra,dec)
print "####################################################"

fits = pyfits.open(fitsname)
x_size = fits[0].header['NAXIS1']
y_size = fits[0].header['NAXIS2']

# 318.226,-16.1081104054
# fits[0].header[keyword] = value
# was : 318.1984911 , -16.116421371
fits[0].header['OBSRA'] = ra
fits[0].header['OBSDEC'] = dec
fits[0].header['CRVAL5'] = ra
fits[0].header['CRVAL6'] = dec

print "Writing fits  %s , setting (RA,DEC)       = (%.6f,%.6f) [deg]" % (fitsname,ra,dec)
fits.writeto( fitsname, clobber=True ) 
