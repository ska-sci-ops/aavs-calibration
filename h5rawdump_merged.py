#!/usr/bin/python
# code to dump the raw data from a Marcin merged hdf5 voltage file. This is just the same as
# h5dump -d "/chan_/data" -b -o outfilename
# but about 1000 times faster

from __future__ import print_function
import h5py,sys,getopt

def printUsage():
  print("Usage\n")
  print("\t-o\toutputfilename. No default")
  print("\t-i\tinputfilename. No default")
  sys.exit(1)

if len(sys.argv)<1:
  printUsage()

try:
  opts, args = getopt.getopt(sys.argv[1:], "i:o:")
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

f=h5py.File(infilename,mode='r')
# output output file
outfp=open(outfilename,'w')

d=f[u'chan_'][u'data']
s = d.shape
for t in range(s[0]):
  dchunk=d[t,:]
  dchunk.tofile(outfp)

