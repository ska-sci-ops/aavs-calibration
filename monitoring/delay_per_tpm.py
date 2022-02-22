#!/opt/caastro/ext/anaconda/bin/python

# Author : Marcin Sokolowski
# Links :
# http://matplotlib.org/users/pyplot_tutorial.html
# https://python4mpia.github.io/fitting_data/least-squares-fitting.html

# just info :
from __future__ import print_function
from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div
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
import psycopg2


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

g_connected=False
conn=None

def db_connect( dbname='aavs', db_host_ip="10.0.10.200" ):
   global g_connected
   global conn

   if not g_connected:
      print("testing connection to database")
      # open up database connection
      try:
         conn = psycopg2.connect( database='aavs' , host=db_host_ip, user='aavs' )
      except:
         logger.error("Unable to open connection to database")
         sys.exit(1)

      print("Connected!")
      g_connected=True
   else :
      print("Already connected -> using exisitng connection")
         
   return conn


def get_last_calsolution( station_id=2 ) :
   global conn

   szSQL = "select max(extract(epoch from fit_time)) as max_uxtime, max(fit_time) as max_dtm from calibration_solution where station_id=%d" % (station_id) 
   print("Execurting SQL : %s" % szSQL)

   # conn = db_connect()   
   cur = conn.cursor()
   cur.execute(szSQL)
   records = cur.fetchall()

   max_uxtime = -1
   max_dtm    = None
   print("\tNumber of selected records = %d" % (len(records)))
   for rec in records:
       print("\tTest rec[0] = %s (check if None)" % (rec[0]))
       if rec[0] is not None :
           print("\tTest rec[0] = %.2f" % (rec[0]))
           max_uxtime = float( rec[0] )
           max_dtm    = rec[1]
           
   cur.close()
   print("Maximum unix time of calibration solution in the database = %.2f (dtm = %s)" % (max_uxtime,max_dtm))
   
   return (max_uxtime,max_dtm)


def get_last_delays( station_id=2 ) :
   global conn
   
   (max_uxtime,max_dtm) = get_last_calsolution( station_id=station_id )
   
   if max_uxtime <= 0 :
      print("ERROR : no calibration solutions in the database for station_id = %d" % (station_id))
      return (None,None,None,None)

   # *1000 to have in nanoseconds
   szSQL = "select ant_id,x_delay*1000,y_delay*1000 from calibration_solution where station_id=%d and fit_time='%s'" % (station_id,max_dtm) 
   print("Execurting SQL : %s" % szSQL)

   # conn = db_connect()   
   cur = conn.cursor()
   cur.execute(szSQL)
   records = cur.fetchall()

   ants=[]
   x_delays=[]
   y_delays=[]
   ant_tpm=[]
   tpm=1
   cnt=0
   
   print("\tNumber of selected records = %d" % (len(records)))
   for rec in records:
       if rec[0] is not None :
           print("\tTest rec[0] = %d / %.2f / %.2f" % (int(rec[0]),float(rec[1]),float(rec[2])))
           ant_idx    = int(rec[0])
           delay_x    = float(rec[1])
           delay_y    = float(rec[2])
           
           ants.append( ant_idx )
           x_delays.append( delay_x )
           y_delays.append( delay_y )
           ant_tpm.append ( tpm )
           cnt += 1

           if (cnt % 16) == 0 :
              tpm += 1

           
   cur.close()
   
   print("Returning %d antennas, %d tpms, %d X delays and %d Y delays" % (len(ants),len(ant_tpm),len(x_delays),len(y_delays)))
   n = len(ants)
   for ant in range(0,n) :
      print("%d : TPM-%d , x_delays = %.2f [ns], y_delays = %.2f [ns]" % (ant,ant_tpm[ant],x_delays[ant],y_delays[ant]))

   return (ants, ant_tpm, x_delays, y_delays)


def calc_mean_delays_per_tpm( ant_name, ant_delay, ant_tpm, outfile="delay_vs_tpm.txt" , outconfig="delays_vs_tpm.conf" , b_save_both_pols=True ) :
   out_python=outfile.replace("txt","py")
   
   n_ant = len(ant_name)
   n_tpms = old_div(n_ant, 16)
   print("Calculating mean delays for %d TPMs ( n_ant = %d )" % (n_tpms,n_ant))
   mean_delays = []

   out_f_python = open( out_python , "w" )
   out_f_python.write( "\n\n\ndelays = {}\n" )
   
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
               print("WARNING : antenna index = %d skipped in MEDAN/MEDIAN due to 0 delay (probably calibration failed)" % (ant_idx))
               
            tpm_delays.append( ant_delay[ant_idx] )

            # use all delays (even the bad ones = ZERO ) it needs to be 16 in the end :               
            tpm_delays_round.append( int(round(ant_delay[ant_idx])) )

      if len(tpm_delays) != 16 :
          print("ERROR : number of delays for TPM-%d is %d - should be 16 !!!" % (tpm,len(tpm_delays)))
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
         mean_delay = old_div(mean_delay, count)      
         mean_delays.append( mean_delay )
         print("TPM-%02d -> mean delay = %.4f [nanoseconds] , median = %.4f [ns] ( based on %d values : %s )" % (tpm,mean_delay,median_delay,count,all_values))
         
         line = "%d %.4f %.4f %s\n" % (tpm,median_delay,mean_delay,tpm_delays)
         out_f.write( line )
         
         tpm_delays_round_string=""
         for d in range(0,len(tpm_delays_round)) :
            tpm_delays_round_string += str(int(tpm_delays_round[d]))
            if d < (len(tpm_delays_round)-1) :
               tpm_delays_round_string += ", "
               
         tpm_delays_float_string=""
         for d in range(0,len(tpm_delays)) :
            tpm_delays_float_string += ("%.4f " % tpm_delays[d])
            if d < (len(tpm_delays)-1) :
               tpm_delays_float_string += ", "

         
         line = "    - %d [%s]\n" % (int(round(median_delay)),tpm_delays_round_string)
         out_conf_f.write( line )

         full_line = (" delays[%d] = %s\n" % (tpm-1,tpm_delays_float_string))
         out_f_python.write( full_line )
      else :
         print("WARNING : tpm=%d has no delays ????" % (tpm))

   
   out_f.close()         
   out_conf_f.close()

# print "    - "round($2);

   return (mean_delays)
      
def parse_options( idx ):
   usage="Usage: %prog [options]\n"
   usage+='\tPrepares list of delays to be inserted into .yml station config file\n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('--db','--dbname',dest="dbname",default=None, help="Database name, default is None, which means reading from input text file" )
   parser.add_option("--station_id", '--station', dest="station_id", default=0, help="Station ID (as in the station configuratio file) [default: %]", type=int )


   (options, args) = parser.parse_args(sys.argv[idx:])

   return (options, args)


def main() :
   filename = "20190812_delays_nanosec.txt"
   if len(sys.argv) >= 2 :
      filename = sys.argv[1]

   (options, args) = parse_options(1)
   
      
   print("##################################################")
   print("PARAMETERS :")
   print("##################################################")
   print("database   = %s" % (options.dbname))
   print("station ID = %d" % (options.station_id))
   print("##################################################")


   if options.dbname is not None :
      global conn
      conn = db_connect()
    
      outfile = "delay_vs_tpm_lastdb.txt"
      outconfig = "delay_vs_tpm_lastdb.conf"
      (ant_name, ant_tpm, x_delays, y_delays) = get_last_delays( station_id = options.station_id )       
      (mean_delays) = calc_mean_delays_per_tpm( ant_name , x_delays , ant_tpm, outfile=outfile, outconfig=outconfig )           
   else :
      outconfig = filename.replace(".txt",".conf")
      outfile="delay_vs_tpm.txt"

      (ant_name,ant_delay,ant_tpm) = read_data( filename )
      
      (mean_delays) = calc_mean_delays_per_tpm( ant_name , ant_delay , ant_tpm, outfile=outfile, outconfig=outconfig )
   

if __name__ == "__main__":
   main()
