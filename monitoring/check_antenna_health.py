
import h5py
import numpy
import math
import sys
import os

# option parsing :
from optparse import OptionParser,OptionGroup
import errno
import getopt
import optparse

def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
      else: raise

def check_antenna( spectrum, median_spectrum, iqr_spectrum, thereshold_in_sigma=3, ant_idx=-1, debug=False ):

   total_power = 0
   n_bad_channels = 0
   
   n_chan = len(spectrum)
   for ch in range(0,n_chan) :
      diff = spectrum[ch] - median_spectrum[ch]
      rms = iqr_spectrum[ch] / 1.35
      
      if math.fabs(diff) > thereshold_in_sigma*rms :
         n_bad_channels += 1
         
      total_power += spectrum[ch]
         

   if debug : 
      print("ANTENNA %d : number of bad channels = %d , total_power = %d" % (ant_idx,n_bad_channels,total_power))
  
   return (n_bad_channels,total_power)


def write_spectrum( spectrum , filename, iqr=None, flag="OK" ) :
   out_f = open( filename , "w" )

   n_chan = len(spectrum)
   for ch in range(0,n_chan) :
      if iqr is not None :
         rmsiqr = iqr[ch]/1.35
         line = "%d %d %.4f %.4f %s\n" % (ch,spectrum[ch],rmsiqr,iqr[ch],flag)
      else :
         line = "%d %d %s\n" % (ch,spectrum[ch],flag)
      out_f.write( line )
      
   out_f.close()


# Check antenna health in comparison to other antennas within the same tile for only a single timestamp (default t_sample=0 - using sample 0)
# so it will be median spectrum calculated using 16 spectra from other antennas 
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# TODO : extend to use 16 HDF5 files and calculate median spectrum using 256 spectra from all antennas within a station !!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def check_antenna_health_single_tile( hdf_file, t_sample=0, out_median_file="median",
                          nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512, nof_samples=64,
                          max_bad_channels=100 ):
   f = h5py.File( hdf_file )
   data = f['chan_']['data'][:]
   nof_samples = data.shape[0]
   
   d_test=data.reshape((nof_samples, nof_channels, nof_ant_per_tile, nof_pols))

   median_spectrum_x = numpy.zeros( nof_channels )
   median_spectrum_y = numpy.zeros( nof_channels )
   iqr_spectrum_x = numpy.zeros( nof_channels )
   iqr_spectrum_y = numpy.zeros( nof_channels )
   
   for ch in range(0,nof_channels) :
   
      x_list=[]
      y_list=[]
         
      for ant in range(0,nof_ant_per_tile) :
         x_list.append( d_test[t_sample,ch,ant,0] )
         y_list.append( d_test[t_sample,ch,ant,1] )
            
      x_list.sort()
      y_list.sort()
      ants = len(x_list)
      
      if ants != (nof_ant_per_tile) :
         print("WARNING : number of antennas = %d != expected %d" % (nof_ant_per_tile))
      else :
         print("Channel %d : calculating median of %d antennas" % (ch,ants))
      
      
      median_spectrum_x[ch] = x_list[ants/2]
      median_spectrum_y[ch] = y_list[ants/2]   

      q75= int(ants*0.75);
      q25= int(ants*0.25);

      iqr_spectrum_x[ch] = x_list[q75] - x_list[q25]
      iqr_spectrum_y[ch] = y_list[q75] - y_list[q25]
      
      
   out_x_name = "%s_x.txt" % (out_median_file)      
   out_y_name = "%s_y.txt" % (out_median_file)      
   
   # write median spectrum :
   write_spectrum( median_spectrum_x, out_x_name, iqr_spectrum_x )
   write_spectrum( median_spectrum_y, out_y_name, iqr_spectrum_y )
   
   print("\n\n")
   print("CHECKING ANTNENA HEALTH:")
   
   ( median_bad_channels_x , median_total_power_x ) = check_antenna( median_spectrum_x, median_spectrum_x , iqr_spectrum_x )
   ( median_bad_channels_y , median_total_power_y ) = check_antenna( median_spectrum_y, median_spectrum_y , iqr_spectrum_y )
   print("Median : bad_channels_x = %d , total_power_x = %d, bad_channels_y = %d , total_power_y = %d" % (median_bad_channels_x,median_total_power_x,median_bad_channels_y,median_total_power_y))

   comment = ("# max_bad_channels = %d , median total power in X = %d and in Y = %d (total power is expected to be in the range x0.5 to x2 of these values)" % (max_bad_channels,n_total_power_x,n_total_power_y))
   
   # write antenna spectra :
   for ant in range(0,nof_ant_per_tile) :
      spectrum_x = d_test[t_sample,:,ant,0]
      spectrum_y = d_test[t_sample,:,ant,1]
         
      ( n_bad_channels_x , n_total_power_x ) = check_antenna( spectrum_x, median_spectrum_x , iqr_spectrum_x )
      ( n_bad_channels_y , n_total_power_y ) = check_antenna( spectrum_y, median_spectrum_y , iqr_spectrum_y )
         
      flag = ""
      if n_bad_channels_x > max_bad_channels :
         flag += ("BAD_CH_X=%d" % n_bad_channels_x)
      if n_total_power_x < (median_total_power_x/2) or n_total_power_x > (median_total_power_x*2):
         flag += (",BAD_POWER_X=%d" % n_total_power_x)
         # print("DEBUG : %d vs. %d or %d vs %d" % (n_total_power_x,median_total_power_x,n_total_power_x,median_total_power_x))
            
      if n_bad_channels_y > max_bad_channels :
         flag += (",BAD_CH_Y=%d" % n_bad_channels_y)
      if n_total_power_y < (median_total_power_y/2) or n_total_power_y > (median_total_power_y*2):
         flag += (",BAD_POWER_Y=%d" % n_total_power_y)
      
      if len(flag) <= 0 :
         flag = "OK"

      out_x_name = "ant_%05d_%05d_x.txt" % (tile,ant)
      out_y_name = "ant_%05d_%05d_y.txt" % (tile,ant)
      write_spectrum( spectrum_x, out_x_name, None, flag )
      write_spectrum( spectrum_y, out_y_name, None, flag )
         
      print("TILE %d , ANTENNA %d : bad_channels_x = %d , total_power_x = %d , bad_channels_y = %d , total_power_y = %d -> %s" % (tile,ant,n_bad_channels_x,n_total_power_x,n_bad_channels_y,n_total_power_y,flag))
            
      
   f.close()

def read_all_tiles_data( hdf_file_template, nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512 ) :

   print("PROGRESS : reading HDF5 files using file template %s" % (hdf_file_template))
   f_array = {}
   f_data  = {}
   n_timesteps = 0 

   for tile in range(0,nof_tiles) :   
      hdf_file = (hdf_file_template % (tile))
      print("\treading file %s" % (hdf_file))
      f = h5py.File( hdf_file )
      f_array[tile] = f
      data = f['chan_']['data'][:]
      nof_samples = data.shape[0]
      d_test=data.reshape((nof_samples, nof_channels, nof_ant_per_tile, nof_pols))
      f_data[tile] = d_test
      
      if n_timesteps <= 0 :
         n_timesteps = f['sample_timestamps']['data'].shape[0]
         while n_timesteps >= 0 and f['sample_timestamps']['data'][n_timesteps-1] <= 0 :
           n_timesteps = n_timesteps - 1
         
         print("\tdetected number of timestamps = %d (total including zeros is = %d)" % (n_timesteps,f['sample_timestamps']['data'].shape[0]))

   return (f_array,f_data,n_timesteps)

def calc_median_spectra( f_data, t_sample_list, do_write=True, out_ant_median_file="median_spectrum_ant", nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512, min_value=0, outdir="./" ) :
   print("PROGRESS : calculating median spectrum of all antennas ...")
   median_spectrum_per_ant_x = {}
   median_spectrum_per_ant_y = {}
   for tile in range(0,nof_tiles) : 
      d_test=f_data[tile] 

      for ant in range(0,nof_ant_per_tile) :      
          ant_idx = tile*nof_ant_per_tile + ant
          print("\tTILE%05d ANT%05d (ant_idx = %d)" % (tile,ant,ant_idx))
          
          median_spectrum_per_ant_x[ant_idx] = numpy.zeros( nof_channels )
          median_spectrum_per_ant_y[ant_idx] = numpy.zeros( nof_channels )
      
          for ch in range(0,nof_channels) :         
             x_list=[]
             y_list=[]
              
             for t_idx in range(0,len(t_sample_list)) :
                t = t_sample_list[t_idx]
            
                if d_test[t,ch,ant,0] > min_value :
                   x_list.append( d_test[t,ch,ant,0] )
                   
                if d_test[t,ch,ant,1] > min_value :                   
                   y_list.append( d_test[t,ch,ant,1] )
                
             x_list.sort()
             y_list.sort()
             t_count_x = len(x_list)
             t_count_y = len(y_list)
             
             x_val = 0
             y_val = 0
             if t_count_x > 0 :
                x_val = x_list[t_count_x/2]
             if t_count_y > 0 :
                y_val = y_list[t_count_y/2]
                
             median_spectrum_per_ant_x[ant_idx][ch] = x_val
             median_spectrum_per_ant_y[ant_idx][ch] = y_val
             

          if do_write : 
             out_file_name_x = "%s/%s%05d_x.txt" % (outdir,out_ant_median_file,ant_idx)
             out_file_name_y = "%s/%s%05d_y.txt" % (outdir,out_ant_median_file,ant_idx)
             # def write_spectrum( spectrum , filename, iqr=None, flag="OK" ) :
             write_spectrum( median_spectrum_per_ant_x[ant_idx] , out_file_name_x, flag="" )
             write_spectrum( median_spectrum_per_ant_y[ant_idx] , out_file_name_y, flag="" )
   
   return (median_spectrum_per_ant_x,median_spectrum_per_ant_y)
   
# all tiles :
# t_sample_list=[0] - to just use a single timestamp
def check_antenna_health_OLD( hdf_file_template, t_sample_list=None, out_median_file="median", out_bad_list_file="bad_antennas.txt", out_ant_median_file="median_spectrum_ant",
                          nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512,
                          max_bad_channels=100 ):
   
   # TODO : at the moment just one timetamp is used here:
   # t_sample = t_sample_list[0]
   # if t_sample_list is None : 
      
   
   median_spectrum_x = numpy.zeros( nof_channels )
   median_spectrum_y = numpy.zeros( nof_channels )
   iqr_spectrum_x = numpy.zeros( nof_channels )
   iqr_spectrum_y = numpy.zeros( nof_channels )

   # read all HDF5 file matching the template :
   (f_array,f_data,n_timesteps) = read_all_tiles_data( hdf_file_template )
   
   if t_sample_list is None :
      # if not specified -> use all the timetamps :
      t_sample_list = numpy.arange( f_data[0].shape[0] )

   # initialise median spectrum for all antennas :
   # not yet done    
   # for each antenna calculate median spectrum (using all the specified timestamps) :
   (median_spectrum_per_ant_x,median_spectrum_per_ant_y) = calc_median_spectra( f_data, t_sample_list, out_ant_median_file=out_ant_median_file ) 

   # for now juse use the first, but really should use medians calculated in the earlier step 
   # TODO : at the moment just one timetamp is used here:
   t_sample = t_sample_list[0]

   # calculate median value for each frequency channel    
   print("PROGRESS : calculating median value for every frequency channel ...")
   for ch in range(0,nof_channels) :   
      x_list=[]
      y_list=[]
         
      for tile in range(0,nof_tiles) : 
         d_test=f_data[tile] 
      
         for ant in range(0,nof_ant_per_tile) :
            x_list.append( d_test[t_sample,ch,ant,0] )
            y_list.append( d_test[t_sample,ch,ant,1] )
            
      x_list.sort()
      y_list.sort()
      ants = len(x_list)
      
      if ants != (nof_ant_per_tile*nof_tiles) :
         print("WARNING : number of antennas = %d != expected %d * %d = %d" % (nof_ant_per_tile,nof_tiles,(nof_ant_per_tile*nof_tiles)))
      else :
         print("Channel %d : calculating median of %d antennas" % (ch,ants))
      
      
      median_spectrum_x[ch] = x_list[ants/2]
      median_spectrum_y[ch] = y_list[ants/2]   

      q75= int(ants*0.75);
      q25= int(ants*0.25);

      iqr_spectrum_x[ch] = x_list[q75] - x_list[q25]
      iqr_spectrum_y[ch] = y_list[q75] - y_list[q25]
      
      
   out_x_name = "%s_x.txt" % (out_median_file)      
   out_y_name = "%s_y.txt" % (out_median_file)      
   
   # write median spectrum :
   print("PROGRESS : writing median spectra to output file")
   write_spectrum( median_spectrum_x, out_x_name, iqr_spectrum_x )
   write_spectrum( median_spectrum_y, out_y_name, iqr_spectrum_y )
   
   print("\n\n")
   print("CHECKING ANTNENA HEALTH:")
   
   ( median_bad_channels_x , median_total_power_x ) = check_antenna( median_spectrum_x, median_spectrum_x , iqr_spectrum_x )
   ( median_bad_channels_y , median_total_power_y ) = check_antenna( median_spectrum_y, median_spectrum_y , iqr_spectrum_y )
   print("Median : bad_channels_x = %d , total_power_x = %d, bad_channels_y = %d , total_power_y = %d" % (median_bad_channels_x,median_total_power_x,median_bad_channels_y,median_total_power_y))
   
   # write antenna spectra :
   
   out_bad_f = open( out_bad_list_file , "w" )
   for tile in range(0,nof_tiles) : 
      d_test=f_data[tile] 

      for ant in range(0,nof_ant_per_tile) :
         ant_idx = tile*nof_ant_per_tile + ant
      
         spectrum_x = d_test[t_sample,:,ant,0]
         spectrum_y = d_test[t_sample,:,ant,1]
         
         ( n_bad_channels_x , n_total_power_x ) = check_antenna( spectrum_x, median_spectrum_x , iqr_spectrum_x )
         ( n_bad_channels_y , n_total_power_y ) = check_antenna( spectrum_y, median_spectrum_y , iqr_spectrum_y )
         
         flag = ""
         if n_bad_channels_x > max_bad_channels :
            flag += "BAD_CH_X"
         if n_total_power_x < (median_total_power_x/2) or n_total_power_x > (median_total_power_x*2):
            flag += ",BAD_POWER_X"
            # print("DEBUG : %d vs. %d or %d vs %d" % (n_total_power_x,median_total_power_x,n_total_power_x,median_total_power_x))
            
         if n_bad_channels_y > max_bad_channels :
            flag += "BAD_CH_Y"
         if n_total_power_y < (median_total_power_y/2) or n_total_power_y > (median_total_power_y*2):
            flag += ",BAD_POWER_Y"
      
         if len(flag) <= 0 :
            flag = "OK"
         else :
            line = "%05d : TILE %05d , ANT %05d %s\n" % (ant_idx,tile,ant,flag)
            out_bad_f.write( line )

         out_x_name = "ant_%05d_%05d_x.txt" % (tile,ant)
         out_y_name = "ant_%05d_%05d_y.txt" % (tile,ant)
         write_spectrum( spectrum_x, out_x_name, None, flag )
         write_spectrum( spectrum_y, out_y_name, None, flag )
         
         print("TILE %d , ANTENNA %d : bad_channels_x = %d , total_power_x = %d , bad_channels_y = %d , total_power_y = %d -> %s" % (tile,ant,n_bad_channels_x,n_total_power_x,n_bad_channels_y,n_total_power_y,flag))
   
   out_bad_f.close()         
      
#  CLOSE HDF5 files :
   for tile in range(0,nof_tiles) :   
      f_array[tile].close()

def calc_median_spectrum( median_spectrum_per_ant_x , median_spectrum_per_ant_y, out_median_file="median", do_write=True, nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512, min_val=0, outdir="./" ) :
   print("PROGRESS : calculating median value for every frequency channel ...")
   
   ant_count = len(median_spectrum_per_ant_x)

   median_spectrum_x = numpy.zeros( nof_channels )
   median_spectrum_y = numpy.zeros( nof_channels )
   iqr_spectrum_x = numpy.zeros( nof_channels )
   iqr_spectrum_y = numpy.zeros( nof_channels )
   
   for ch in range(0,nof_channels) :   
      x_list=[]
      y_list=[]

      for ant_idx in range(0,ant_count) :         
         
         if median_spectrum_per_ant_x[ant_idx][ch] > min_val :
            x_list.append( median_spectrum_per_ant_x[ant_idx][ch] )
            
         if median_spectrum_per_ant_y[ant_idx][ch] > min_val : 
            y_list.append( median_spectrum_per_ant_y[ant_idx][ch] )
            
      x_list.sort()
      y_list.sort()
      t_count_x = len(x_list)
      t_count_y = len(y_list)

      x_val = 0
      y_val = 0
      if t_count_x > 0 :
         x_val = x_list[t_count_x/2]
      if t_count_y > 0 :
         y_val = y_list[t_count_y/2]

#      ants = len(x_list)      
#      if ants != ant_count :
#         print("WARNING : number of antennas = %d != expected %d * %d = %d" % (nof_ant_per_tile,nof_tiles,ant_count))
#      else :
#         print("Channel %d : calculating median of %d antennas" % (ch,ants))
            
      median_spectrum_x[ch] = x_val
      median_spectrum_y[ch] = y_val      

      iqr_spectrum_x[ch] = x_list[int(t_count_x*0.75)] - x_list[int(t_count_x*0.25)]
      iqr_spectrum_y[ch] = y_list[int(t_count_y*0.75)] - y_list[int(t_count_y*0.25)]
      
   if do_write :    
      out_x_name = "%s/%s_x.txt" % (outdir,out_median_file)      
      out_y_name = "%s/%s_y.txt" % (outdir,out_median_file)      
   
      # write median spectrum :
      print("PROGRESS : writing median spectra to output file")
      write_spectrum( median_spectrum_x, out_x_name, iqr_spectrum_x )
      write_spectrum( median_spectrum_y, out_y_name, iqr_spectrum_y )
      
   return (median_spectrum_x,median_spectrum_y,iqr_spectrum_x,iqr_spectrum_y)


# all tiles :
# t_sample_list=[0] - to just use a single timestamp
def check_antenna_health( hdf_file_template, options, out_median_file="median", out_bad_list_file="bad_antennas.txt", out_ant_median_file="median_spectrum_ant",
                          nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512,
                          max_bad_channels=100 ):
   
   ant_count = nof_tiles*nof_ant_per_tile
   
   # TODO : at the moment just one timetamp is used here:
   # t_sample = t_sample_list[0]
   # if t_sample_list is None : 
      
   
   # read all HDF5 file matching the template :
   (f_array,f_data,n_timesteps) = read_all_tiles_data( hdf_file_template )
   
   t_sample_list=None
   min_timesteps = n_timesteps
   if options.n_timesteps > 0 :      
      min_timesteps = min( options.n_timesteps, n_timesteps )
      
      if options.latest :
         t_sample_list = numpy.arange( n_timesteps-1, n_timesteps-1-min_timesteps , -1 )
         print("DEBUG : created list of the most recent  %d timetemps" % (min_timesteps))
      else :
         t_sample_list = numpy.arange( min_timesteps )         
         print("DEBUG : created list of first %d timetemps" % (min_timesteps))

   
   if t_sample_list is None :
      # if not specified -> use all the timetamps :
      t_sample_list = numpy.arange( n_timesteps )

   # initialise median spectrum for all antennas :
   # not yet done    
   # for each antenna calculate median spectrum (using all the specified timestamps) :
   (median_spectrum_per_ant_x,median_spectrum_per_ant_y) = calc_median_spectra( f_data , t_sample_list, out_ant_median_file=out_ant_median_file, outdir=options.outdir ) 

   # calculate median value for each frequency channel using median spectra 
   (median_spectrum_x,median_spectrum_y,iqr_spectrum_x,iqr_spectrum_y) = calc_median_spectrum( median_spectrum_per_ant_x , median_spectrum_per_ant_y, out_median_file=out_median_file, outdir=options.outdir )
      
   
   print("\n\n")
   print("CHECKING ANTNENA HEALTH:")   
   print("\tCalculating total power of median spectrum ...")
   ( median_bad_channels_x , median_total_power_x ) = check_antenna( median_spectrum_x, median_spectrum_x , iqr_spectrum_x )
   ( median_bad_channels_y , median_total_power_y ) = check_antenna( median_spectrum_y, median_spectrum_y , iqr_spectrum_y )
   print("\tMedian : bad_channels_x = %d , total_power_x = %d, bad_channels_y = %d , total_power_y = %d" % (median_bad_channels_x,median_total_power_x,median_bad_channels_y,median_total_power_y))
   
   # Find bad antennas and save to file :   
   out_bad_f = open( options.outdir + "/" + out_bad_list_file , "w" )
   comment = ("# max_bad_channels = %d , median total power in X = %d and in Y = %d (total power is expected to be in the range x0.5 to x2 of these values)\n" % (max_bad_channels,median_total_power_x,median_total_power_y))
   out_bad_f.write( comment )

   print("\tComparing antenna spectra with median spectrum ...")   
   for tile in range(0,nof_tiles) : 
      d_test=f_data[tile] 

      for ant in range(0,nof_ant_per_tile) :
         ant_idx = tile*nof_ant_per_tile + ant
      
         # spectrum_x = d_test[t_sample,:,ant,0]
         # spectrum_y = d_test[t_sample,:,ant,1]
         ant_median_spectrum_x = median_spectrum_per_ant_x[ant_idx]
         ant_median_spectrum_y = median_spectrum_per_ant_y[ant_idx]
         
         ( n_bad_channels_x , n_total_power_x ) = check_antenna( ant_median_spectrum_x, median_spectrum_x , iqr_spectrum_x, ant_idx=ant_idx )
         ( n_bad_channels_y , n_total_power_y ) = check_antenna( ant_median_spectrum_y, median_spectrum_y , iqr_spectrum_y, ant_idx=ant_idx )
         
         flag = ""
         if n_bad_channels_x > max_bad_channels :
            flag += ("BAD_CH_X=%d" % n_bad_channels_x)
         if n_total_power_x < (median_total_power_x/2) or n_total_power_x > (median_total_power_x*2):
            flag += (",BAD_POWER_X=%d" % n_total_power_x)
            # print("DEBUG : %d vs. %d or %d vs %d" % (n_total_power_x,median_total_power_x,n_total_power_x,median_total_power_x))
            
         if n_bad_channels_y > max_bad_channels :
            flag += (",BAD_CH_Y=%d" % n_bad_channels_y)
         if n_total_power_y < (median_total_power_y/2) or n_total_power_y > (median_total_power_y*2):
            flag += (",BAD_POWER_Y=%d" % n_total_power_y)
      
         if len(flag) <= 0 :
            flag = "OK"
         else :
            line = "%05d : TILE %05d , ANT %05d %s\n" % (ant_idx,tile,ant,flag)
            out_bad_f.write( line )

         # out_x_name = "ant_%05d_%05d_x.txt" % (tile,ant)
         # out_y_name = "ant_%05d_%05d_y.txt" % (tile,ant)
         # write_spectrum( spectrum_x, out_x_name, None, flag )
         # write_spectrum( spectrum_y, out_y_name, None, flag )
         
         print("TILE %d , ANTENNA %d : bad_channels_x = %d , total_power_x = %d , bad_channels_y = %d , total_power_y = %d -> %s" % (tile,ant,n_bad_channels_x,n_total_power_x,n_bad_channels_y,n_total_power_y,flag))
   
   out_bad_f.close()         
      
#  CLOSE HDF5 files :
   for tile in range(0,nof_tiles) :   
      f_array[tile].close()




def parse_options(idx):
   parser=optparse.OptionParser()
   parser.set_usage("""parse_pulsars.py""")
   parser.add_option("--n_timesteps","--timesteps",dest="n_timesteps",default=-1,help="Number of timesteps used for calculations (<0 -> all) [default: %default]",type="int")
   parser.add_option("--outdir","--out_dir","--dir","-o",dest="outdir",default="./",help="Output directory [default: %default]")
   parser.add_option('--latest','--newest','--last',action="store_true",dest="latest",default=False, help="Use the most recent timestamps [default %default]")
   (options,args)=parser.parse_args(sys.argv[idx:])

   return (options, args)
   
   
if __name__ == '__main__' :
   hdf_file_template="channel_integ_%d_20210222_09517_0.hdf5"
   if len(sys.argv) > 1:
      hdf_file_template = sys.argv[1]

   (options, args) = parse_options(1)
   
   print("######################################################################################")
   print("PARAMETERS:")
   print("######################################################################################")
   print("hdf_file_template = %s" % (hdf_file_template))
   print("N timesteps       = %d (latest = %s)" % (options.n_timesteps,options.latest))   
   print("######################################################################################")
   
   if len(options.outdir) and options.outdir != "./" :
      print("Creating output directory %s ..." % (options.outdir))
      mkdir_p( options.outdir )      
      print("DONE")

#   t_sample_list=None
#   if options.n_timesteps > 0 :
#      t_sample_list = numpy.arange( options.n_timesteps )
   

   # check_antenna_health("channel_integ_14_20200205_41704_0.hdf5")
   check_antenna_health( hdf_file_template , options )
      