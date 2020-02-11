
import h5py
import sys
import os
import getopt
import numpy

def print_usage():
  print("Usage\n")
  print("python count_zeros.py INFILE OUTFILE")
  sys.exit(1)
  
  
if __name__ == "__main__":
   infile="test.hdf5"
   outfile="test.txt"
   
   if len(sys.argv) > 1:   
       infile = sys.argv[1]
  
   if len(sys.argv) > 2:   
       outfile = sys.argv[2]
       
   
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
         header_line += ( "T%dX T%dY " % (t,t))
         
      out_f.write( header_line + "\n" )   
   
   for time in range(s[0]):
      for input in range(n_inputs) :
         if data[time,input][0] == 0 and data[time,input][1] == 0 :
            zero_counter[input] += 1 

     
   line = "" 
   for input in range(n_inputs) :
     line += ("%d " % (zero_counter[input]))                
   out_f.write( line + "\n" ) 
     
   out_f.close()
   
   