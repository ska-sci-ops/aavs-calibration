from __future__ import print_function

import h5py
import sys
import os
import getopt
import numpy
from optparse import OptionParser,OptionGroup


def print_usage():
  print("Usage\n")
  print("python count_zeros.py INFILE OUTFILE")
  sys.exit(1)


def parse_options():
   usage="Usage: %prog [options]\n"
   usage+='\tcount zero values in hdf5 file with real and imag (both have to be zero to be counted)'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-s','--start','--start_time',dest="start_time",default=0, help="Start time index [default %default]",type="int")
   parser.add_option('-e','--end','--end_time',dest="end_time",default=1e20, help="End time index [default %default]",type="int") # default = INFINITY 
   (options, args) = parser.parse_args()

   return (options, args)
  
  
if __name__ == "__main__":
   infile="test.hdf5"
   outfile="test.txt"
   
   if len(sys.argv) > 1:   
       infile = sys.argv[1]
  
   if len(sys.argv) > 2:   
       outfile = sys.argv[2]

   (options, args) = parse_options()


   print("######################################################")
   print("PARAMETERS :")       
   print("######################################################")
   print("Infile = %s" % (infile))
   print("Outfile = %s" % (outfile))
   print("Start time index = %d" % (options.start_time))
   print("End time index   = %d" % (options.end_time))
   print("######################################################")
   
   f = h5py.File( infile )
   
   data = f['chan_']['data']
   s = data.shape
   n_inputs = s[1]
   n_ants = n_inputs / 2 
   
   zero_counter = numpy.zeros( n_inputs, dtype=numpy.int64 )
   
   header = False
   if not os.path.exists(outfile) :
      header = True 
   
   out_f = open( outfile , "a+" )
   if header :      
      header_line = "# "
      for t in range(0,n_ants):
         header_line += ( "T%dX T%dY " % ((t+1),(t+1)))
         
      out_f.write( header_line + "\n" )   
   
   for time in range(s[0]):
      if options.start_time<=time and time<=options.end_time :   
         for input in range(n_inputs) :
            if data[time,input][0] == 0 and data[time,input][1] == 0 :
               zero_counter[input] += 1 

     
   line = "" 
   for input in range(n_inputs) :
     line += ("%d " % (zero_counter[input]))                
   out_f.write( line + "\n" ) 
     
   out_f.close()
   
   