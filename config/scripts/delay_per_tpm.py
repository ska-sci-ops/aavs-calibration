#!/opt/caastro/ext/anaconda/bin/python

# Author : Marcin Sokolowski
# Links :
# http://matplotlib.org/users/pyplot_tutorial.html
# https://python4mpia.github.io/fitting_data/least-squares-fitting.html

# just info :
import sys,os
import math
import numpy
# examples :
# numpy.mean([1,2,3,4,5,6,7,8])
# scipy.stats is a module within a module scipy and has to separately imported :
# version 1 :
# from scipy.stats import pearsonr,linregress 
# version 2 :
from scipy import stats
from matplotlib import pyplot
from optparse import OptionParser,OptionGroup
from pylab import *
import time

def read_data(filename) :
   file=open(filename,'r')

   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   # print data

   # initialisation of empty lists :
   ant_name=[]
   ant_delay=[]
   ant_tpm=[]
   min_x=1e20
   max_x=-1e20
   cnt=0
   tpm=1
   for line in data : 
      words = line.split(' ')

      if line[0] == '#' or line[0]=='\n' or len(line) <= 0 or len(words)<2 :
         continue

      if line[0] != "#" :
         name  = words[0+0]
         delay = float(words[1+0])

         ant_name.append( name )
         ant_delay.append( delay )
         ant_tpm.append ( tpm )
         cnt += 1
         
         if (cnt % 16) == 0 :
            tpm += 1

#         if x > max_x :
#            max_x = x
#         if x < min_x :
#            min_x = x

#   print "Frequency range = %.4f - %.4f MHz" % (min_x,max_x)
   return (ant_name,ant_delay,ant_tpm)

def calc_mean_delays_per_tpm( ant_name, ant_delay, ant_tpm, outfile="delay_vs_tpm.txt" , outconfig="delays_vs_tpm.conf" , b_save_both_pols=True ) :
   n_ant = len(ant_name)
   n_tpms = n_ant / 16
   print "Calculating mean delays for %d TPMs ( n_ant = %d )" % (n_tpms,n_ant)
   mean_delays = []
   
   out_f = open( outfile , "w" )
   out_conf_f = open( outconfig, "w" )
   out_f.write("# TPM MEDIAN[ns] MEAN[ns]\n")
   out_conf_f.write("# MEDIAN[ns] DELAY_PER_ANT[ns]\n")
#   for ant_idx in ant_name :
   for tpm in range(1,(n_tpms+1)) :
      mean_delay = 0
      count = 0
      all_values = ""
      tpm_delays = []
      tpm_delays_round = []

      for ant_idx in range(0,n_ant):
         if ant_tpm[ant_idx] == tpm :
            if math.fabs( ant_delay[ant_idx] ) > 0.000001 :
               mean_delay += ant_delay[ant_idx]
               count      += 1 
               all_values += ("%.2f " % (ant_delay[ant_idx]))
            else :
               print "WARNING : antenna index = %d skipped in MEDAN/MEDIAN due to 0 delay (probably calibration failed)" % (ant_idx)
               
            tpm_delays.append( ant_delay[ant_idx] )

            # use all delays (even the bad ones = ZERO ) it needs to be 16 in the end :               
            tpm_delays_round.append( int(round(ant_delay[ant_idx])) )

      if len(tpm_delays) != 16 :
          print "ERROR : number of delays for TPM-%d is %d - should be 16 !!!" % (tpm,len(tpm_delays))
          os.exit(-1)
      
      if count > 0 :            
         if b_save_both_pols and len(tpm_delays_round)==16 :
            # print "WARNING : stacking 16 delays to form 32 (both pols)"
            # tpm_delays_round_stack = numpy.hstack( (tpm_delays_round,tpm_delays_round) )
            # tpm_delays_round = tpm_delays_round_stack
            
            # !!! Delays per antenna - FPGAs handle both pols (not one FPGA per polarisation) !!!
            # adding 2 values for X and Y polarisation :
            tpm_delays_round_stack = []
            for d in range(0,len(tpm_delays_round)) :
                tpm_delays_round_stack.append( tpm_delays_round[d] )
                tpm_delays_round_stack.append( tpm_delays_round[d] )
                
            tpm_delays_round = tpm_delays_round_stack    

      
         median_delay = numpy.median( tpm_delays )
         mean_delay = mean_delay / count      
         mean_delays.append( mean_delay )
         print "TPM-%02d -> mean delay = %.4f [nanoseconds] , median = %.4f [ns] ( based on %d values : %s )" % (tpm,mean_delay,median_delay,count,all_values)
         
         line = "%d %.4f %.4f %s\n" % (tpm,median_delay,mean_delay,tpm_delays)
         out_f.write( line )
         
         tpm_delays_round_string=""
         for d in range(0,len(tpm_delays_round)) :
            tpm_delays_round_string += str(int(tpm_delays_round[d]))
            if d < (len(tpm_delays_round)-1) :
               tpm_delays_round_string += ", "
         
         line = "    - %d [%s]\n" % (int(round(median_delay)),tpm_delays_round_string)
         out_conf_f.write( line )
      else :
         print "WARNING : tpm=%d has no delays ????" % (tpm)

   
   out_f.close()         
   out_conf_f.close()

# print "    - "round($2);

   return (mean_delays)
      

def main() :
   filename = "20190812_delays_nanosec.txt"
   if len(sys.argv) >= 2 :
      filename = sys.argv[1]

   outconfig = filename.replace(".txt",".conf")
   outfile="delay_vs_tpm.txt"


   (ant_name,ant_delay,ant_tpm) = read_data( filename )
   (mean_delays) = calc_mean_delays_per_tpm( ant_name , ant_delay , ant_tpm, outfile=outfile, outconfig=outconfig )
   

if __name__ == "__main__":
   main()
