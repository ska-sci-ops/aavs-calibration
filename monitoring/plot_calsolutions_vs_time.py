#! /usr/bin/env python
"""
Script for certain MWA database queries required for primary beam calibration (based on test_db.py and some other MWA python scripts : sql_find_observations.py )
"""
from __future__ import print_function


from future import standard_library
standard_library.install_aliases()
from builtins import range
import logging, sys, os, glob, string, re, urllib.request, urllib.parse, urllib.error, math, time
import errno
from optparse import OptionParser
import numpy
import psycopg2


from optparse import OptionParser

def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
      else: raise


g_connected=False
conn=None

def db_connect():
   global g_connected
   global conn

   if not g_connected:
      print("testing connection to database")
      # open up database connection
      try:
         conn = psycopg2.connect(database='aavs')
      except:
         logger.error("Unable to open connection to database")
         sys.exit(1)

      print("Connected!")
      g_connected=True
   else :
      print("Already connected -> using exisitng connection")
         
   return conn

def get_mean_stddev_delay_per_ant( outname="eda2_mean_stddev_delay.txt", max_time_stamp_file="last_calibration.txt" , station_id=2, start_date="2019-09-07 00:00:00" ) :
   global conn

   szWhere = ""
#   if station_id == 2 :
#      szWhere += ( " and fit_time >= '%s' " % 
      
#   if start_date is not None :
#      szWhere += " and fit_time >= '%s' " % (start_date)
           
   # excluding some wrong solutions in SQL :
   szSQL = "select (ant_id+1) as ant,COALESCE(avg(x_delay),0) as mean_x_delay_ns,COALESCE(stddev(x_delay),0) as stddev_mean_x_delay_ns,COALESCE(avg(y_delay),0) as mean_y_delay_ns,COALESCE(stddev(y_delay),0) as stddev_mean_y_delay_ns from calibration_solution where fit_time >= '%s' AND station_id=%d group by ant_id order by ant_id" % (start_date,station_id)
   print("Execurting SQL : %s" % szSQL)

   # conn = db_connect()   
   cur = conn.cursor()
   cur.execute(szSQL)
   records = cur.fetchall()

   max_ux_time = -1000

   ants    = []
   avg_x_delays = []
   stddev_x_delays = []
   avg_y_delays = []
   stddev_y_delays = []

#   ux_time = []
#   fit_time = []
   
   out_f = open( outname , "w" )   
   for rec in records:
       ant = float( rec[0] )
       avg_x_delay    = float( rec[1] )
       stddev_x_delay = float( rec[2] )
       avg_y_delay    = float( rec[3] )
       stddev_y_delay = float( rec[4] )

       
       line = "%d %.4f %.4f %.4f %.4f\n" % (ant,avg_x_delay,stddev_x_delay,avg_y_delay,stddev_y_delay)   
       if avg_x_delay > -1000 and avg_y_delay > -1000 :       
           out_f.write( line )
           
           ants.append( ant )
           avg_x_delays.append( avg_x_delay )
           stddev_x_delays.append( stddev_x_delay )
           avg_y_delays.append( avg_y_delay )
           stddev_y_delays.append( stddev_y_delay )
       else :
           print("WARNING : error in calibration ? ant %d (x_delay,y_delay) = (%.2f,%.2f)" % (ant,avg_x_delay,avg_y_delay))


   cur.close()
   out_f.close()
   
   max_file = open( max_time_stamp_file , "w" )
   line = "%.1f\n" % (max_ux_time)
   max_file.write( line )
   max_file.close()
   
   return ( ants, avg_x_delays, stddev_x_delay, avg_y_delays, stddev_y_delay )


def get_calsolution_delay( ant_id=0, outname="calsol_amp_antid0.txt", max_time_stamp_file="last_calibration.txt" , station_id=2, start_date="2000-01-01 00:00:00" ) :
   global conn

   szWhere = ""
   if station_id == 2 :
      szWhere += " and fit_time >= '2019-08-12 11:30:00' "
      
#   if start_date is not None :
#      szWhere += " and fit_time >= '%s' " % (start_date)
           
   # excluding some wrong solutions in SQL :
   szSQL = "select extract(epoch from fit_time) as uxtime,COALESCE(x_delay,-1000),COALESCE(y_delay,-1000),fit_time from calibration_solution where ant_id=%d and (fit_time<'2018-12-20 00:00:00' or fit_time>'2018-12-31 23:59:59') and fit_time not in ('2019-08-13 11:39:00+08','2019-08-14 11:44:00+08') and station_id=%d and fit_time>='%s' %s order by fit_time ASC" % (ant_id,station_id,start_date,szWhere) 
   print("Execurting SQL : %s" % szSQL)

   # conn = db_connect()   
   cur = conn.cursor()
   cur.execute(szSQL)
   records = cur.fetchall()

   max_ux_time = -1000

   x_delay = []
   y_delay = []   
   ux_time = []
   fit_time = []
   
   out_f = open( outname , "w" )   
   for rec in records:
       ux = float( rec[0] )
       x_del = rec[1] 
       y_del = rec[2]
       ft    = rec[3]
       if ux > max_ux_time :
           max_ux_time = ux

       line = "%.2f %.12f %.12f %s\n" % (ux,x_del,y_del,ft)   
       if x_del > -1000 and y_del > -1000 :       
           out_f.write( line )
           
           ux_time.append( ux )
           x_delay.append( x_del )
           y_delay.append( y_del )
           fit_time.append( ft )
       else :
           print("WARNING : error in calibration ? %s (x_delay,y_delay) = (%.2f,%.2f)" % (ft,x_del,y_del))


   cur.close()
   out_f.close()
   
   max_file = open( max_time_stamp_file , "w" )
   line = "%.1f\n" % (max_ux_time)
   max_file.write( line )
   max_file.close()
   
   return ( x_delay , y_delay, ux_time, fit_time )

def read_last_calibration_dtm( max_time_stamp_file="last_calibration.txt" ) :
   if os.path.exists( max_time_stamp_file ) :
       file=open( max_time_stamp_file , 'r' )
       data=file.readlines()
       file.close()
   
       for line in data : 
           words = line.split(' ')
           return float(words[0])
       
   return -1000
    
def is_there_new_calibration( last_calibration_date=-1000, station_id=2 ) :
   global conn

   if last_calibration_date is None or last_calibration_date<0 :
       # if no last calibration date is provided -> return TRUE 
       return True
   else :
       szSQL = "select max(extract(epoch from fit_time)) as max_uxtime from calibration_solution where extract(epoch from fit_time) > '%s' and station_id=%d" % (last_calibration_date,station_id) 

   print("Execurting SQL : %s" % szSQL)

   # conn = db_connect()   
   cur = conn.cursor()
   cur.execute(szSQL)
   records = cur.fetchall()

   max_uxtime = -1
   print("\tNumber of selected records = %d" % (len(records)))
   for rec in records:
       print("\tTest rec[0] = %s (check if None)" % (rec[0]))
       if rec[0] is not None :
           print("\tTest rec[0] = %.2f" % (rec[0]))
           max_uxtime = float( rec[0] )

   cur.close()
   print("Maximum unix time of calibration solution in the database = %.2f" % (max_uxtime))
   
   if max_uxtime > 0 :
       return True
   
   return False
               

def read_delays( filename ) : 
   print("read_data(%s) ..." % (filename))

   if not os.path.exists( filename ) :
      print("ERROR : could not read satellite info file %s" % (filename))
      return (None,0.00,None,None,None,None)

   file=open(filename,'r')

   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   # print data

   delays_x = []
   delays_y = []

   for line in data : 
      line=line.rstrip()
      words = line.split(' ')

      if line[0] == '#' or line[0]=='\n' or len(line) <= 0 or len(words)<4 :
         continue

#      print "line = %s , words = %d" % (line,len(words))

      if line[0] != "#" :
         ux       = float( words[0+0] )
         delay_x  = float ( words[1+0] )
         delay_y  = float ( words[2+0] )
         dt       = words[3+0]
         t        = words[4+0]
         
         delays_x.append( delay_x )
         delays_y.append( delay_y )
         
   
   delays_x = numpy.array( delays_x )
   delays_y = numpy.array( delays_y )
   
   return ( delays_x , delays_y )


def read_all_delays( outfile="eda2_mean_stddev_delay.txt") :
   out_f = open( outfile, "w" )

   for ant in range(0,256):
      filename = ('calsol_delay_antid%03d.txt' % (ant))
      (x_delays,y_delays) = read_delays( filename )
      
      rms_x = x_delays.std()
      mean_x = x_delays.mean()
      rms_y = y_delays.std()
      mean_y = y_delays.mean()      
      
      line = ("%d %.8f %.8f %8f %.8f %.8f %.8f\n" % ((ant+1),mean_x,rms_x,(rms_x/mean_x),mean_y,rms_y,(rms_y/mean_y)))
      out_f.write( line )
      
      
   out_f.close()

if __name__ == "__main__":
   # OLD TEST :
   # gridpoint=gridpoint(1117271016)
   # (az,elev,za)=get_beam_pointing(1117271016) 
   # print "Beam pointing for obsID=%d is (az,el,za)=(%.8f,%.8f,%.8f)" % (1117271016,az,elev,za)

   usage="Usage: %prog [options]\n"
   usage+="\tPlots calibration solutions amplitude vs. time\n"
   
   parser = OptionParser(usage=usage)
   parser.add_option('-o','--outdir','--dir',dest='outdir',default="caldb/",help='Output directory [default %default]')
   parser.add_option('-f','--outfile','--outfname',dest='outfile',default="eda2_mean_stddev_delay.txt",help='Output filename [default %default]')
   parser.add_option('-t','--lastcal_stamp','--last_calibration_file',dest='last_calibration_file',default="last_calibration.txt",help='Last calibration file [default %default]')
   parser.add_option("--station_id", '--station', dest="station_id", default=2, help="Station ID (as in the station configuratio file) [default: %]", type=int )
   parser.add_option("--station_name", dest="station_name", default="EDA2", help="Station ID (as in the station configuratio file) [default: %]" )
   parser.add_option("--start_date", dest="start_date", default=None, help="Start date to select data [default %]" )
   parser.add_option("--get_mean_stddev_delay","--mean_stddev",action="store_true",dest="get_mean_stddev_delay", default=False, help="Get mean/stddev from the database [default %]" )
   parser.add_option("--no_db","--nodb",action="store_true",dest="no_db", default=False, help="Do not use database [default %]" )
   

#   parser.add_option('-s','--short_dipole_obsids',dest='short_dipole_obsid',default=None,help='Find obsIDs of short dipole tests for a given obsID [default %default]',type="int")
#   parser.add_option('-f','--output_filename','--outfname',dest='output_filename',default=None,help='Name of output filename [default %default]')
#   parser.add_option('-m','--max_time_distance',dest='max_time_distance',default=86400,help='Maximum time separation between gpstime and short dipole test [default %default]')
   (options, args) = parser.parse_args()
#   mkdir_p( options.outdir )
       

   if options.no_db :
      print("No using database - just plotting using text files")
      

   conn = db_connect()   
   
   do_plots = True
   if os.path.exists( options.last_calibration_file ) :
       last_calib_date = read_last_calibration_dtm( options.last_calibration_file )
   
       if is_there_new_calibration( last_calib_date, station_id=options.station_id ) : 
          print("INFO : there are new calibration solutions in the database")
       else :
          print("WARNING : no new calibration solutions to plot found in the database after %s" % (last_calib_date))
          do_plots = False

   if do_plots :   
       mkdir_p( options.outdir )
       
       if options.get_mean_stddev_delay :
           # def get_mean_stddev_delay_per_ant( outname="eda2_mean_stddev_delay.txt", max_time_stamp_file="last_calibration.txt" , station_id=2, start_date="2019-09-07 00:00:00" ) 
           outfile = '%s/%s' % (options.outdir,options.outfile)
           get_mean_stddev_delay_per_ant( outfile, start_date=options.start_date, station_id=options.station_id )
       else :
           for ant_id in range(0,256) :
               outfile = '%s/calsol_delay_antid%03d.txt' % (options.outdir,ant_id)
               get_calsolution_delay( ant_id, outfile, start_date=options.start_date, station_id=options.station_id )
   else :
       print("WARNING : no new calibration solutions to plot found in the database")
       
      
   conn.close()
   
   