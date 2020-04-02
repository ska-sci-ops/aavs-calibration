#!/usr/bin/python
# code to dump a single coarse channel out of AAVS raw voltage dump from TPMs

from __future__ import print_function
import h5py
import sys
import getopt

def printUsage():
  print("Usage\n")
  print("\t-o\toutputfilename. No default")
  print("\t-i\tinputfilename. No default")
  sys.exit(1)

if len(sys.argv)<1:
  printUsage()

chan=-1

try:
  opts, args = getopt.getopt(sys.argv[1:], "i:o:c:")
except getopt.GetoptError as err:
  printUsage()

for o, a in opts:
  if o == "-c":
    chan = int(a)
  elif o in ("-o", "--output"):
    outfilename = a
  elif o in ("-i", "--output"):
    infilename = a
  else:
    assert False, "unhandled option"

assert chan >0

hf=h5py.File(infilename,'r')
outfp=open(outfilename,'w')

g=hf[u'chan_']
dat=g['data'].value.reshape(16384,512,32)
dat[:,chan,:].tofile(outfp)


