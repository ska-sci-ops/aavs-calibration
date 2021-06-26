
import h5py
import numpy
import math
import sys
import os
import time
from datetime import datetime
import copy

# option parsing :
from optparse import OptionParser,OptionGroup
import errno
import getopt
import optparse

# plotting :
# Test if X-windows / DISPLAY is not needed :
import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import pylab
import matplotlib.pyplot as plt

# from matplotlib import rc
# rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
# rc('text', usetex=True)
# params = {'legend.fontsize': 'x-large',
#          'figure.figsize': (60, 20),
#          'axes.labelsize': 'x-large',
#          'axes.titlesize':'x-large',
#          'xtick.labelsize':'x-large',
#          'ytick.labelsize':'x-large'}
# pylab.rcParams.update(params)

#
# GLOBAL VARIABLES :
#
# /home/msok/aavs/bitbucket/aavs-calibration/config/eda2$ grep Ant instr_config_eda2.txt | awk '{printf("\"%s\",",$7);}'
# /home/msok/aavs/bitbucket/aavs-calibration/config/aavs2$ grep Ant instr_config_aavs2.txt | awk '{printf("\"%s\",",$7);}'
eda2_aavs2_antenna_names = [ "Ant061","Ant063","Ant064","Ant083","Ant136","Ant124","Ant123","Ant122","Ant084","Ant085","Ant086","Ant097","Ant121","Ant120","Ant099","Ant098","Ant134","Ant135","Ant152","Ant153","Ant201","Ant200","Ant199","Ant188","Ant154","Ant155","Ant156","Ant167","Ant187","Ant186","Ant169","Ant168","Ant118","Ant137","Ant138","Ant147","Ant204","Ant203","Ant185","Ant184","Ant148","Ant149","Ant150","Ant151","Ant183","Ant172","Ant171","Ant170","Ant065","Ant066","Ant079","Ant080","Ant139","Ant119","Ant117","Ant116","Ant081","Ant082","Ant100","Ant101","Ant105","Ant104","Ant103","Ant102","Ant006","Ant007","Ant008","Ant021","Ant062","Ant053","Ant052","Ant051","Ant023","Ant024","Ant025","Ant026","Ant032","Ant031","Ant030","Ant029","Ant027","Ant028","Ant054","Ant055","Ant096","Ant095","Ant091","Ant090","Ant056","Ant057","Ant058","Ant059","Ant089","Ant088","Ant087","Ant060","Ant092","Ant093","Ant094","Ant125","Ant162","Ant161","Ant160","Ant159","Ant126","Ant127","Ant128","Ant129","Ant133","Ant132","Ant131","Ant130","Ant157","Ant158","Ant163","Ant164","Ant223","Ant197","Ant196","Ant195","Ant165","Ant166","Ant189","Ant190","Ant194","Ant193","Ant192","Ant191","Ant198","Ant220","Ant221","Ant222","Ant252","Ant251","Ant250","Ant249","Ant224","Ant225","Ant226","Ant227","Ant248","Ant247","Ant246","Ant228","Ant202","Ant217","Ant218","Ant219","Ant255","Ant254","Ant253","Ant245","Ant229","Ant230","Ant231","Ant240","Ant244","Ant243","Ant242","Ant241","Ant205","Ant206","Ant212","Ant213","Ant256","Ant239","Ant238","Ant237","Ant214","Ant215","Ant216","Ant232","Ant236","Ant235","Ant234","Ant233","Ant140","Ant145","Ant146","Ant173","Ant211","Ant210","Ant209","Ant208","Ant174","Ant175","Ant178","Ant179","Ant207","Ant182","Ant181","Ant180","Ant073","Ant107","Ant108","Ant109","Ant177","Ant176","Ant144","Ant143","Ant110","Ant111","Ant112","Ant113","Ant142","Ant141","Ant115","Ant114","Ant040","Ant041","Ant042","Ant043","Ant106","Ant078","Ant077","Ant076","Ant045","Ant068","Ant069","Ant070","Ant075","Ant074","Ant072","Ant071","Ant001","Ant012","Ant013","Ant014","Ant067","Ant048","Ant047","Ant046","Ant015","Ant016","Ant017","Ant036","Ant044","Ant039","Ant038","Ant037","Ant002","Ant003","Ant004","Ant005","Ant050","Ant049","Ant035","Ant034","Ant009","Ant010","Ant011","Ant018","Ant033","Ant022","Ant020","Ant019" ]

CH2FREQ = ( 400.00/512.00 )

# excluded frequency ranges in MHz :
global_excluded_freq_ranges = set()

def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
      else: raise

def check_antenna( spectrum, median_spectrum, iqr_spectrum, threshold_in_sigma=3, ant_idx=-1, debug=False ):
   global global_excluded_freq_ranges
   global CH2FREQ

   total_power = 0
   n_bad_channels = 0
   
   n_chan = len(spectrum)
   for ch in range(0,n_chan) :
      freq_mhz = ch*CH2FREQ
   
      diff = spectrum[ch] - median_spectrum[ch]
      rms = iqr_spectrum[ch] / 1.35
      
      if math.fabs(diff) > threshold_in_sigma*rms :
         n_bad_channels += 1
         
      is_ok = True
      
      for excluded_range in global_excluded_freq_ranges :
          if freq_mhz >= excluded_range[0] and freq_mhz <= excluded_range[1] :
             is_ok = False
             break
      
      if is_ok :
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

def plot_antenna_with_median( options, antname, median_freq, median_power, median_power_err, ant_freq, ant_power, outdir="images/", y_min=1, y_max=60, label="X pol.", plot_db=False, color='black', pol='x', ux_time=None, median_total_power=-1 ) :
   # CH2FREQ = ( 400.00/512.00 )
   global CH2FREQ
   
   count_median = len(median_power)
   if ux_time is None :
      ux_time = time.time()
   
   bad_freq=[]
   bad_power=[]
   
   for i in range(0,len(median_power)) :
      if ant_power[i] > median_power[i] + options.threshold_in_sigma*median_power_err[i] :
         bad_freq.append( median_freq[i] )
         bad_power.append( ant_power[i] )
   
   if options.plot_db :
      for i in range(0,len(median_power)) :
         value = median_power[i] # save value before going to DB (needed in error re-calc)
         if median_power[i] > 0 :
            median_power[i] = 10.00*math.log10(median_power[i])
         else : 
            median_power[i] = 0.00
            value = 1.00
         # (10.00/TMath::Log(10.00))*(1.00/y_val)*y_val;
         median_power_err[i] = (10.00/math.log(10.00))*(1.00/value)*median_power_err[i]
         
      for i in range(0,len(ant_power)) :
         if ant_power[i] > 0 :
            ant_power[i] = 10.00*math.log10(ant_power[i])   
         else :
            ant_power[i] = 0.00
      
      if len(bad_power) > 0 :
         for i in range(0,len(bad_power)) :
            if bad_power[i] > 0 :
               bad_power[i] = 10.00*math.log10(bad_power[i])
            else :
               bad_power[i] = 0.00

   median_freq = numpy.array( median_freq ) * CH2FREQ
   ant_freq    = numpy.array( ant_freq ) * CH2FREQ
   if len(bad_freq) > 0 :
      bad_freq    = numpy.array( bad_freq ) * CH2FREQ
   
   if y_max is None :
      y_max = max(median_power)*1.2

   fig = plt.figure(figsize=(60,20)) 
   ax = fig.add_subplot(1,1,1) # create axes within the figure : we have 1 plot in X direction, 1 plot in Y direction and we select plot 1
   for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
      item.set_fontsize(30)

   
   plt.ylim([y_min,y_max])
#   print("plt.ylim([%.4f,%.4f])" % (y_min,y_max))

   # plot median :
   a,b,c = plt.errorbar( median_freq, median_power, yerr=median_power_err, xerr=None, linestyle='None', marker='o', color='blue' , markersize=5, label="Median spectrum +/- 1sigma" + label)
   # just for Legend - as otherwise does not want to work ...
   label_str = "Median spectrum +/- 1sigma (total power = %d)" % (median_total_power)
   line_median, = plt.plot( median_freq, median_power, linestyle='None', marker='o', color='blue' , markersize=5, label=label_str )

   # plot ant_power 
   line_antenna, = plt.plot( ant_freq, ant_power, linestyle='None', marker='+', color=color  , markersize=5, label=antname + " spectrum " + label)
   
   line_bads = None
   if len(bad_power) > 0 :
      # highlight bad channels in red : 
      line_bads, = plt.plot( bad_freq, bad_power, linestyle='None', marker='x', color='red', markersize=20, label="Bad channels"  )
   
   ax.set_xlabel( "Frequency [MHz]" , fontsize=30 )
   if options.plot_db : 
      ax.set_ylabel( "Power [dB]" , fontsize=30 ) 
   else : 
      ax.set_ylabel( "Power [?]" , fontsize=30 ) # r to treat it as raw string 

   # legend :
   plt.legend(fontsize=50)
   if line_bads is not None :
      # bbox_to_anchor=(0.68, 0.82)
      plt.legend(loc=1,handles=[line_antenna,line_median,line_bads],fontsize=50)      
   else :
      plt.legend(loc=1,handles=[line_antenna,line_median],fontsize=50)

   # date time :
   time_dtm = datetime.utcfromtimestamp( ux_time )
   time_str = time_dtm.strftime("%m/%d/%Y %H:%M:%S")
   x_center = ant_freq[len(ant_freq)/2] 
   plt.text( x_center*0.7, y_max*1.00, time_str + " UTC", fontsize=50, color='black')

   title = antname
   if label is not None :
      title = title + " , "
      title = title + label

#   ax.set_title( title )
   fig.suptitle( title, fontsize=40 )
   plt.grid(True,which='both')
   
   pngfile=outdir + "/" + antname + "_" + pol + ".png"
   plt.savefig( pngfile , dpi=80 )   
   
   # close :
   plt.close(fig) # close first figure although second one is active   


# write_bad_antenna_html_header( out_bad_f , options )
def write_bad_antenna_html_header( out_bad_html_f , options, median_total_power_x, median_total_power_y, out_put_files ) :
   now = datetime.now()
   now_str = now.strftime("%Y-%m-%d %H:%M:%S")

   out_bad_html_f.write("<html>\n")
   line = "<title>List of bad antennas in the SKA-Low station %s</title>\n" % (options.station_name)
   out_bad_html_f.write( line )
   
   line = "<center><h1>List of bad antennas in the SKA-Low station %s</h1></center>\n" % (options.station_name)
   out_bad_html_f.write( line )
   
   line = "<center>( generated at %s AWST )</center>" % (now_str)
   out_bad_html_f.write( line )
   
   line = "<h2>Criteria for flagging bad antennas:</h2>\n<ul>\n"   
   out_bad_html_f.write( line )
   
   line = "<li>Total power is flagged as bad if it's lower than 1/2 of total power of median spectrum or larger than 2 times total power of median spectrum (= %.2f and %.2f for X and Y polarisations respectively)</li>\n" % (median_total_power_x,median_total_power_y)
   out_bad_html_f.write( line )
   
   line = "<li>If number of bad channels is larger than %d, where bad channels are counted as those which deviate from the median spectrum by more than %.2f sigma.<br> Number of bad channels is specified as values of BAD_CH_X and BAD_CH_Y variables</li>\n" % (options.max_bad_channels,options.threshold_in_sigma)
   out_bad_html_f.write( line )
   
   out_bad_html_f.write( "</ul>\n" )
   
   line = "<h2>Other output files:</h2>\n<ul>\n"
   out_bad_html_f.write( line )
   
   for outfile in out_put_files :
      is_html = False
            
      try :      
         if outfile.index(".html") >= 0 :
            is_html = True
      except ValueError :
         pass
      
      if not is_html :
         is_txt = False
         try :      
            if outfile.index(".txt") >= 0 :
               is_txt = True
         except ValueError :
            pass

         if is_txt :
            line = "<li><a href=\"%s\"><u>%s</u></a></li>\n" % (outfile,outfile)
         else :
            line = "<li><a href=\"%s_x.txt\"><u>Median X pol.</u></a> <a href=\"%s_y.txt\"><u>Median Y pol.</u></a></li>\n" % (outfile,outfile) 
            
         out_bad_html_f.write( line )
            
   out_bad_html_f.write( "</ul>\n" )
      
#   out_bad_html_f.write( "<br>\n" )
   out_bad_html_f.write( "<body>\n" )
#   out_bad_html_f.write( "<br>\n" )
   out_bad_html_f.write( "<br>\n" )
   out_bad_html_f.write( "<h2>Antenna spectra compared with a median spectrum +/- %.1f x sigma_iqr :</h2>\n" % (options.threshold_in_sigma) )
   out_bad_html_f.write( "<ul>\n" )
   
def write_bad_antenna_html_end( out_bad_html_f , options, n_bad_ant=0 ) :
   out_bad_html_f.write("</ul>\n\n")
   
   line = ("<br><h2>Number of antennas with one bad polarisation : %d </h2>\n\n" % (n_bad_ant))
   print("DEBUG : line with number of bad antennas = |%s|" % (line))
   out_bad_html_f.write( line )
   
   out_bad_html_f.write("</body>\n")
   out_bad_html_f.write("</html>\n")
   



  
   


# all tiles :
# t_sample_list=[0] - to just use a single timestamp
def check_antenna_health( hdf_file_template, options, 
                          nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512,
                          antenna_names=None ):
   
   ux_time = time.time()
   out_bad_list_file = options.station_name + "_bad_antennas.txt"
   out_bad_list_html_file = options.station_name + "_bad_antennas.html"
   out_health_report = options.station_name + "_health_report.txt"
   out_median_file   = options.station_name + "_median"
   out_ant_median_file = options.station_name + "_median_spectrum_ant"
   
   out_put_files = [ out_bad_list_file, out_bad_list_html_file, out_health_report, out_median_file, out_ant_median_file ]
   
   ant_count = nof_tiles*nof_ant_per_tile
   
   # TODO : at the moment just one timetamp is used here:
   # t_sample = t_sample_list[0]
   # if t_sample_list is None : 
      
   # frequency table :
   freq = numpy.arange(512)
   
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
   out_bad_html_f = open( options.outdir + "/" + out_bad_list_html_file , "w" )
   comment = ("# max_bad_channels = %d , median total power in X = %d and in Y = %d (total power is expected to be in the range x0.5 to x2 of these values)\n" % (options.max_bad_channels,median_total_power_x,median_total_power_y))
   out_bad_f.write( comment )
   out_bad_f.write( ("# UNIXTIME = %.4f\n" % (ux_time)) )
   out_bad_f.write( "# ANTNAME  ANT_INDEX  TILE  ANT   REASON\n" )
   
   # html file :
   write_bad_antenna_html_header( out_bad_html_f , options, median_total_power_x, median_total_power_y, out_put_files )
   
   
   out_report_f = open( options.outdir + "/" + out_health_report , "w" )
   out_report_f.write( ("# MAXIMUM NUMBER OF BAD CHANNELS ALLOWED = %d\n" % (options.max_bad_channels)) )
   out_report_f.write( ("# UNIXTIME = %.4f\n" % (ux_time)) )
   comment = ("#  ANT_NAME TILE_ID  ANT_ID  TOTAL_POWER_X  NUM_BAD_CHANNELS_X  TOTAL_POWER_Y  NUM_BAD_CHANNELS_Y  STATUS  DETAILS\n" )   
   out_report_f.write( comment )
   comment = ("#   MED    MED      MED      %06d            %03d                %06d             %03d        REFERENCE\n" % (median_total_power_x,median_bad_channels_x,median_total_power_y,median_bad_channels_y))
   out_report_f.write( comment )

   n_bad_ant_count = 0
   print("\tComparing antenna spectra with median spectrum ...")   
   for tile in range(0,nof_tiles) : 
      d_test=f_data[tile] 

      for ant in range(0,nof_ant_per_tile) :
         ant_idx = tile*nof_ant_per_tile + ant
      
         # spectrum_x = d_test[t_sample,:,ant,0]
         # spectrum_y = d_test[t_sample,:,ant,1]
         ant_median_spectrum_x = median_spectrum_per_ant_x[ant_idx]
         ant_median_spectrum_y = median_spectrum_per_ant_y[ant_idx]
         
         ( n_bad_channels_x , n_total_power_x ) = check_antenna( ant_median_spectrum_x, median_spectrum_x , iqr_spectrum_x, ant_idx=ant_idx, threshold_in_sigma=options.threshold_in_sigma )
         ( n_bad_channels_y , n_total_power_y ) = check_antenna( ant_median_spectrum_y, median_spectrum_y , iqr_spectrum_y, ant_idx=ant_idx, threshold_in_sigma=options.threshold_in_sigma )
         
         flag_x = ""
         flag_y = ""
         bad_power_x = False
         bad_power_y = False
         if n_bad_channels_x > options.max_bad_channels :
            flag_x += ("BAD_CH_X=%d" % n_bad_channels_x)
         if n_total_power_x < (median_total_power_x/2) or n_total_power_x > (median_total_power_x*2):
            flag_x += (",BAD_POWER_X=%d" % n_total_power_x)
            bad_power_x = True
            # print("DEBUG : %d vs. %d or %d vs %d" % (n_total_power_x,median_total_power_x,n_total_power_x,median_total_power_x))
            
         if n_bad_channels_y > options.max_bad_channels :
            flag_y += (",BAD_CH_Y=%d" % n_bad_channels_y)
         if n_total_power_y < (median_total_power_y/2) or n_total_power_y > (median_total_power_y*2):
            flag_y += (",BAD_POWER_Y=%d" % n_total_power_y)
            bad_power_y = True

         # get antenna name if mapping hash table is provided :
         antname = " ?? " 
         if antenna_names is not None :
            antname = antenna_names[ant_idx]         

         status = "OK"      
         flag = ""

         is_ok = True
         if len(flag_x) <= 0 :
            flag_x = "OK"
         else :
            is_ok = False
            
         if len(flag_y) <= 0 :
            flag_y = "OK"
         else :
            is_ok = False

         if is_ok :
            flag   = "OK"
         else :
            status = "BAD"
            n_bad_ant_count += 1
            
            flag = flag_x + "," + flag_y
            line = "%s : %05d  %05d , %05d %s\n" % (antname,ant_idx,tile,ant,flag)
            out_bad_f.write( line )
            
            html_line = "   <li> <strong>%s / Tile%s</strong> (config file index = %05d  , in tile index = %05d) : " % (antname,tile,ant_idx,ant)
            if len(flag_x) > 0 :
               # TODO : create description for X in html 
               html_line += ("<a href=\"images/%s_x.png\"><u>%s</u></a>" % (antname,flag_x))
            if len(flag_y) > 0 :
               # TODO : create description for Y in html
               html_line += (", <a href=\"images/%s_y.png\"><u>%s</u></a>" % (antname,flag_y))
            html_line += "</a>\n"               
            out_bad_html_f.write( html_line )

         # out_x_name = "ant_%05d_%05d_x.txt" % (tile,ant)
         # out_y_name = "ant_%05d_%05d_y.txt" % (tile,ant)
         # write_spectrum( spectrum_x, out_x_name, None, flag )
         # write_spectrum( spectrum_y, out_y_name, None, flag )

         print("TILE %d , ANTENNA %d : bad_channels_x = %d , total_power_x = %d , bad_channels_y = %d , total_power_y = %d -> %s" % (tile,ant,n_bad_channels_x,n_total_power_x,n_bad_channels_y,n_total_power_y,flag))
         #          #  TILE_ID  ANT_ID  TOTAL_POWER_X  NUM_BAD_CHANNELS_X  TOTAL_POWER_Y  NUM_BAD_CHANNELS_Y
         comment = ("#  %s  %02d       %02d       %06d            %03d                %06d             %03d          %s : %s\n" % (antname,tile,ant,n_total_power_x,n_bad_channels_x,n_total_power_y,n_bad_channels_y,status,flag) )   
         out_report_f.write( comment )
         
         if options.do_images :
            # def plot_antenna_with_median( median_freq, median_power, median_power_err, ant_freq, ant_power, outdir="images/", y_min=1, y_max=None, label="X pol." ) :
            label = "X pol. (%s)" % (flag_x)            
            color = 'black'
            if bad_power_x :
               color = 'red'
            plot_antenna_with_median( options, antname, freq, copy.copy(median_spectrum_x), copy.copy(iqr_spectrum_x), freq, copy.copy(ant_median_spectrum_x), label=label, outdir=options.outdir + "/images/", color=color, pol='x', ux_time=ux_time, median_total_power=median_total_power_x )

            label = "Y pol. (%s)" % (flag_y)            
            color = 'black'
            if bad_power_y :
               color = 'red'
            plot_antenna_with_median( options, antname, freq, copy.copy(median_spectrum_y), copy.copy(iqr_spectrum_y), freq, copy.copy(ant_median_spectrum_y), label=label, outdir=options.outdir + "/images/", color=color, pol='y', ux_time=ux_time, median_total_power=median_total_power_y )
   
   out_bad_f.close()         
   
   # write end of the file and close :   
   write_bad_antenna_html_end( out_bad_html_f , options, n_bad_ant=n_bad_ant_count )
   out_bad_html_f.close()
      
#  CLOSE HDF5 files :
   for tile in range(0,nof_tiles) :   
      f_array[tile].close()




def parse_options(idx):
   parser=optparse.OptionParser()
   parser.set_usage("""parse_pulsars.py""")
   parser.add_option("--n_timesteps","--timesteps",dest="n_timesteps",default=-1,help="Number of timesteps used for calculations (<0 -> all) [default: %default]",type="int")
   parser.add_option("--outdir","--out_dir","--dir","-o",dest="outdir",default="./",help="Output directory [default: %default]")
   parser.add_option("--station","--station_name",dest="station_name",default="eda2",help="Prefix for output files [default: %default]")
   parser.add_option('--latest','--newest','--last',action="store_true",dest="latest",default=False, help="Use the most recent timestamps [default %default]")
   parser.add_option('--threshold','--threshold_in_sigma',dest="threshold_in_sigma",default=3,help="Threshold in sigma [default %default]")
   parser.add_option('--max_bad_channels','--max_bad_ch',dest="max_bad_channels",default=100,help="Maximum number of bad channels [default %default]",type="int")
   
   # plotting :
   parser.add_option('--images','--plot',action="store_true",dest="do_images",default=False, help="Do images [default %default]")
   parser.add_option('--plot_db',action="store_true",dest="plot_db",default=False, help="Do images in dB scale [default %default]")
   
   (options,args)=parser.parse_args(sys.argv[idx:])

   return (options, args)
   
   
if __name__ == '__main__' :
#   global global_excluded_freq_ranges
   
   # init global ranges see : /home/msok/Desktop/EDA2/logbook/20210507_eda2_ppd_plots_AUTO.odt
   # ranges in MHz 
   global_excluded_freq_ranges.add( ( 240 , 274 ) ) 
   global_excluded_freq_ranges.add( ( 355 , 385 ) )
   

   hdf_file_template="channel_integ_%d_20210222_09517_0.hdf5"
   if len(sys.argv) > 1:
      hdf_file_template = sys.argv[1]

   (options, args) = parse_options(1)
   
   print("######################################################################################")
   print("PARAMETERS:")
   print("######################################################################################")
   print("hdf_file_template = %s" % (hdf_file_template))
   print("N timesteps       = %d (latest = %s)" % (options.n_timesteps,options.latest))   
   print("Output directory  = %s" % (options.outdir))
   print("Station           = %s" % (options.station_name))
   print("Do images         = %s (dB = %s)" % (options.do_images,options.plot_db))
   print("threshold_in_sigma = %.2f" % (options.threshold_in_sigma))
   print("######################################################################################")
   
   if len(options.outdir) and options.outdir != "./" :
      print("Creating output directory %s ..." % (options.outdir))
      mkdir_p( options.outdir )      
      print("DONE")

      if options.do_images :
         print("Creating images directory %s ..." % (options.outdir + "/images/"))
         mkdir_p( options.outdir + "/images/" )

#   t_sample_list=None
#   if options.n_timesteps > 0 :
#      t_sample_list = numpy.arange( options.n_timesteps )
   
   # at the moment the antenna names are the same for EDA2 and AAVS2 :
   antenna_names = eda2_aavs2_antenna_names
   # if options.station_name == "eda2" :
   #   antenna_names = eda2_antennas

   # check_antenna_health("channel_integ_14_20200205_41704_0.hdf5")
   check_antenna_health( hdf_file_template , options, antenna_names=antenna_names )
      