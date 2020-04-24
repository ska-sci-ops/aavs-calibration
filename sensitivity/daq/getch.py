#!/usr/bin/python

from __future__ import print_function
import h5py
import sys
import os

from optparse import OptionParser
from sys import argv, stdout

parser = OptionParser(usage="usage: %station [options]")
parser.add_option("--mv", action="store_true", dest="mv",default=False, help="mv to proper subdirectory [default: %default]")
parser.add_option("--cp", action="store_true", dest="cp",default=False, help="cp to proper subdirectory [default: %default]")
parser.add_option("--ln", action="store_true", dest="ln",default=False, help="link to proper subdirectory [default: %default]")

(conf, args) = parser.parse_args(argv[1:])

hdf5_file=""
if len(sys.argv) > 1:
   hdf5_file = sys.argv[1]

f = h5py.File( hdf5_file , "r" )
channel_id = int( f['root'].attrs['channel_id'] )
print("File %s is channel %d" % (hdf5_file,channel_id))

if channel_id >= 0 :
   if conf.cp or conf.mv :
      # create subdirectory only if move or copy required 
      cmd_str = "mkdir -p %d/" % (channel_id)
      os.system( cmd_str )

   if conf.cp :
      cmd_str = "cp %s %d/" % (hdf5_file,channel_id)
      os.system( cmd_str )

   if conf.mv :
      cmd_str = "mv %s %d/" % (hdf5_file,channel_id)
      os.system( cmd_str )
else :
   print("ERROR : channel_id = %d < 0 -> wrong channel value -> ignored" % (channel_id))      
   
