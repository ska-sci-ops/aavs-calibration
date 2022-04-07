
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

# try to import panda module, but do not crash if it's not available:
g_spreadsheet_csv_file=None
g_use_spreadsheet=False
try:
  import pandas
  
  print("INFO : pandas module imported correctly -> will be able to googldoc spreadsheet information in the reports")
  g_use_spreadsheet=True
except:
  print("WARNING : panda module is not available. It will not be possible to read CSV files (use googldoc spreadsheet information)")
  g_use_spreadsheet=False

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

def init_rfi_bands() :
   if len(global_excluded_freq_ranges) <= 0 :
       global_excluded_freq_ranges.add( ( 240 , 274 ) ) 
       global_excluded_freq_ranges.add( ( 355 , 385 ) )

       print("DEBUG : RFI bands initialised -> %d bad bands" % (len(global_excluded_freq_ranges)))      

def is_channel_ok( ch ) :
  global global_excluded_freq_ranges

  freq_mhz = ch2freq( ch )

  init_rfi_bands()
  
  for excluded_range in global_excluded_freq_ranges :
     if freq_mhz >= excluded_range[0] and freq_mhz <= excluded_range[1] :
        return False

  return True

def mkdir_p(path):
   try:
      os.makedirs(path)
   except OSError as exc: # Python >2.5
      if exc.errno == errno.EEXIST:
         pass
      else: raise

def ch2freq( ch ) :
   return CH2FREQ*ch 

def get_miriad_antenna_index( antenna_names, antname ) :
   for miriad_index in range(0,len(antenna_names)) :
      if antenna_names[miriad_index] == antname :
         return miriad_index
   
   return -1


##########################################################################################################################################
# FUNCTION reads power spectrum from a text file and if there is 3rd column it is treated as an RMS
##########################################################################################################################################
def read_spectrum( file_name ) :

   freq=[]
   power=[]
   rms_power=[]
   
   file=open( file_name,'r')
   
   # reads the entire file into a list of strings variable data :
   data=file.readlines()
   for line in data : 
       if line[0] == '#' :
           continue

       line = line.strip()   
       words = line.split(' ')
       
#       print("DEBUG : len(words) = %d\n" % (len(words)))
#       print("DEBUG : len(words) = %d : |%s|%s|%s|" % (len(words),words[0+0],words[1+0],words[2+0]))
                      

       if line[0] != "#" :
          x=float(words[0+0])
          y=float(words[1+0])
          z=0
          if len(words) >= 3 :
             z = float(words[2+0])   
      
          freq.append(x)
          power.append(y)
          rms_power.append(z)

       file.close()
   
   print "Read %d points from file %s" % (len(freq),file_name)
   return (freq,power,rms_power)    



##########################################################################################################################################
# 
# FUNCTION : checks antennas : calculates number of bad channels and total power 
# 
# INPUT :
#     spectrum - antenna power spectrum in all frequency channels (numpy array or so)
#     median_spectrum - reference median power spectrum of all antennas (calculated in each frequency channel)
#     iqr_spectrum    - standard deviation in each frequency channels calculated over all antennas 
#     threshold_in_sigma - threshold in sigmas to check if power in each channel is within a range (median_spectrum +/- threshold_in_sigma + iqr_spectrum) 
#                          if it is in this range -> channel is ok, if not channel is BAD
#     ant_idx         - antenna index only for debugging purposes 
#     debug = true / false                  
# 
# OUTPUT :
#     n_bad_channels - number of bad channels, which how power outside the range ( median_spectrum[ch] +/- threshold_in_sigma + iqr_spectrum[ch])
#     total_power    - total power (sum over spectrum[ch])
# 
##########################################################################################################################################
def check_antenna( spectrum, median_spectrum, iqr_spectrum, threshold_in_sigma=3, ant_idx=-1, debug=False, max_gap=5 ):
   global global_excluded_freq_ranges
   global CH2FREQ

   total_power = 0
   n_bad_channels = 0
   
   start_bad_final = -1
   end_bad_final   = -1
   
   start_bad = -1
   end_bad   = -1
   
   n_chan = len(spectrum)
   for ch in range(0,n_chan) :
      freq_mhz = ch*CH2FREQ
   
      diff = spectrum[ch] - median_spectrum[ch]
      rms = iqr_spectrum[ch] / 1.35

      if debug :       
         print("DEBUG-DEBUG : %d : diff = %.4f - %.4f = %.4f vs. %.4f * %.4f" % (ch,spectrum[ch],median_spectrum[ch],diff,threshold_in_sigma,rms))

      bad_range_updated = False # flag that current BAD-bandpass has been updated
      if math.fabs(diff) > threshold_in_sigma*rms :
         if debug :
            print("DEBUG : channel = %d is bad ( fabs(%.2f) > %.4f * %.4f )\n" % (ch,diff,threshold_in_sigma,rms))
         n_bad_channels += 1
         
         if start_bad <= 0 :
            start_bad = ch
            bad_range_updated = True
            
         if end_bad < 0 or ch<=(end_bad + max_gap) : # maximum gap 3 channels to still form BAD_BANDPASS
            end_bad = ch
            bad_range_updated = True
            
         if debug :            
            print("DEBUG : bad_range_updated = %s ( %d-%d , max_gap = %d)" % (bad_range_updated,start_bad,end_bad,max_gap))

      if not bad_range_updated and ch>(end_bad + max_gap) : # no update and passed max_gap channels already
         if start_bad >=0 and end_bad >= 0 :         
            if is_channel_ok(ch) :
               if debug :
                  print("!!! UPDATING ??? DEBUG ch=%d : current BAD range is %d-%d , new candidate is %d-%d" % (ch,start_bad_final,end_bad_final,start_bad,end_bad))
               if (start_bad_final<0 and end_bad_final<0) or (end_bad-start_bad) > (end_bad_final-start_bad_final) :
                  # if the first BAD-BAND found or larger bad bandpass found than the previous :
                  # set final bad range (widest)
                  start_bad_final = start_bad
                  end_bad_final   = end_bad
            
               # in any case (if new BAD range is better than old or not) reset temporary bad range (compared with the widest so far):
               start_bad = -1
               end_bad   = -1
            else :
               # if RFI channel extend end_bad 
               if debug :
                  print("DEBUG : ch=%d is RFI channel -> updating end_bad" % (ch))
               end_bad = ch
             
         
      is_ok = True
      
      for excluded_range in global_excluded_freq_ranges :
          if freq_mhz >= excluded_range[0] and freq_mhz <= excluded_range[1] :
             is_ok = False
             break
      
      if is_ok :
         total_power += spectrum[ch]
   
   # end of loop check if bad bandpass range needs an update :
   if start_bad >=0 and end_bad >= 0 :
      if (start_bad_final<0 and end_bad_final<0) or (end_bad-start_bad) > (end_bad_final-start_bad_final) :
         # if the first BAD-BAND found or larger bad bandpass found than the previous :
         # set final bad range (widest)
         start_bad_final = start_bad
         end_bad_final   = end_bad
         

   if debug : 
      print("ANTENNA %d : number of bad channels = %d , total_power = %d" % (ant_idx,n_bad_channels,total_power))
  
   return (n_bad_channels,total_power,start_bad_final,end_bad_final)


##########################################################################################################################################
# FUNCTION : write power spectrum to output file 
# 
#  INPUT : 
#       spectrum - numpy array of power in each channel (spectrum[ch])
#       filename - name of output filename
#       iqr      - standard deviation of power calculated over all antennas (as inter-quartile range)
#       flag     - OK or BAD - to save if the antnena is considered OK or BAD
##########################################################################################################################################
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

##########################################################################################################################################
#
#
# WARNING : old function not currently used. Ignore for now, but do not remove
#
# 
##########################################################################################################################################
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
   
   ( median_bad_channels_x , median_total_power_x, median_start_bad_ch_x, median_end_bad_ch_x ) = check_antenna( median_spectrum_x, median_spectrum_x , iqr_spectrum_x )
   ( median_bad_channels_y , median_total_power_y, median_start_bad_ch_y, median_end_bad_ch_y ) = check_antenna( median_spectrum_y, median_spectrum_y , iqr_spectrum_y )
   print("Median : bad_channels_x = %d , total_power_x = %d, bad_channels_y = %d , total_power_y = %d" % (median_bad_channels_x,median_total_power_x,median_bad_channels_y,median_total_power_y))

   comment = ("# max_bad_channels = %d , median total power in X = %d and in Y = %d (total power is expected to be in the range x0.5 to x2 of these values)" % (max_bad_channels,n_total_power_x,n_total_power_y))
   
   # write antenna spectra :
   for ant in range(0,nof_ant_per_tile) :
      spectrum_x = d_test[t_sample,:,ant,0]
      spectrum_y = d_test[t_sample,:,ant,1]
         
      ( n_bad_channels_x , n_total_power_x, start_bad_ch_x, end_bad_ch_x ) = check_antenna( spectrum_x, median_spectrum_x , iqr_spectrum_x )
      ( n_bad_channels_y , n_total_power_y, start_bad_ch_y, end_bad_ch_y ) = check_antenna( spectrum_y, median_spectrum_y , iqr_spectrum_y )
         
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

##########################################################################################################################################
# FUNCTION : read data in all HDF5 files with a filename specified by template hdf_file_template. There are 16 files (one per tile), each HDF5 file contains data from 16 antennas 
# INPUT :
#     hdf_file_template - template file name
#     nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512 : number of tiles in file (16), number of antennas per tile (16), number of polarisations (2), number of frequency channels (512)
# 
# OUTPUT :
#     f_array - hash table of HDF5 files
#     f_data  - data in all HDF5 files (antoher hash table)
#     n_timesteps - number of read timesteps (to be analysed, as specified by parameter --n_timesteps, where -1 means ALL)
#   
##########################################################################################################################################
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

##########################################################################################################################################
# FUNCTION : for each antenna calculate its median power spectrum over all timesteps (as specified by parameter --n_timesteps, where -1 means ALL)
# 
#   INPUT :
#        f_data - data files (see read_all_tiles_data)
#        t_sample_list - list of timestamps to be analysed
#        do_write      - write output file (True/False)
#        out_ant_median_file - name of output file 
#        nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512 : number of tiles in file (16), number of antennas per tile (16), number of polarisations (2), number of frequency channels (512)
#        min_value - minimum acceptable value (default 0, as there should not be values <0 in the power spectrum - it would be an error value)
#        outdir    - name out output directory 
# 
#    OUTPUT : 2 2D arrays indexed by antenna and frequency channel with median power spectra of all antennas as a function of frequncy channel for both polarisations :
#       median_spectrum_per_ant_x - median power spectra for all antennas in X pol.
#       median_spectrum_per_ant_y - median power spectra for all antennas in Y pol.
# 
##########################################################################################################################################
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

##########################################################################################################################################
#
#
# WARNING : old function not currently used. Ignore for now, but do not remove
#
#
##########################################################################################################################################   
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
   
   ( median_bad_channels_x , median_total_power_x, median_start_bad_ch_x, median_end_bad_ch_x ) = check_antenna( median_spectrum_x, median_spectrum_x , iqr_spectrum_x )
   ( median_bad_channels_y , median_total_power_y, median_start_bad_ch_y, median_end_bad_ch_y ) = check_antenna( median_spectrum_y, median_spectrum_y , iqr_spectrum_y )
   print("Median : bad_channels_x = %d , total_power_x = %d, bad_channels_y = %d , total_power_y = %d" % (median_bad_channels_x,median_total_power_x,median_bad_channels_y,median_total_power_y))
   
   # write antenna spectra :
   
   out_bad_f = open( out_bad_list_file , "w" )
   for tile in range(0,nof_tiles) : 
      d_test=f_data[tile] 

      for ant in range(0,nof_ant_per_tile) :
         ant_idx = tile*nof_ant_per_tile + ant
      
         spectrum_x = d_test[t_sample,:,ant,0]
         spectrum_y = d_test[t_sample,:,ant,1]
         
         ( n_bad_channels_x , n_total_power_x, start_bad_ch_x, end_bad_ch_x ) = check_antenna( spectrum_x, median_spectrum_x , iqr_spectrum_x )
         ( n_bad_channels_y , n_total_power_y, start_bad_ch_y, end_bad_ch_y ) = check_antenna( spectrum_y, median_spectrum_y , iqr_spectrum_y )
         
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

##########################################################################################################################################
# FUNCTION : calculate median spectrum and standard deviation (as inter-quartile range) over median spectra of all the antennas 
#            this is a reference spectrum to which all the antennas are then compare to asses their health 
# 
#    INPUT :
#        median_spectrum_per_ant_x - median power spectra of all the antennas in X polarisation
#        median_spectrum_per_ant_y - median power spectra of all the antennas in X polarisation
#        out_median_file           - output filename where text file with median power spectrum is written
#        do_write                  - write output file True/False
#        nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512 : number of tiles in file (16), number of antennas per tile (16), number of polarisations (2), number of frequency channels (512)
#        min_value - minimum acceptable value (default 0, as there should not be values <0 in the power spectrum - it would be an error value)
#        outdir    - name out output directory 
# 
##########################################################################################################################################
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

      median_spectrum_x[ch] = 0
      median_spectrum_y[ch] = 0
      iqr_spectrum_x[ch] = 0
      iqr_spectrum_y[ch] = 0
      
      if t_count_x > 0 :
         median_spectrum_x[ch] = x_list[t_count_x/2]
         iqr_spectrum_x[ch] = x_list[int(t_count_x*0.75)] - x_list[int(t_count_x*0.25)]
      else :
         print("WARNING ch=%d : no antenna has power larger then minimum %.2f in X pol." % (ch,min_val))
         
      if t_count_y > 0 :
         median_spectrum_y[ch] = y_list[t_count_y/2]
         iqr_spectrum_y[ch] = y_list[int(t_count_y*0.75)] - y_list[int(t_count_y*0.25)]
      else :
         print("WARNING ch=%d : no antenna has power larger then minimum %.2f in Y pol." % (ch,min_val))

#      ants = len(x_list)      
#      if ants != ant_count :
#         print("WARNING : number of antennas = %d != expected %d * %d = %d" % (nof_ant_per_tile,nof_tiles,ant_count))
#      else :
#         print("Channel %d : calculating median of %d antennas" % (ch,ants))
            
#      median_spectrum_x[ch] = x_val
#      median_spectrum_y[ch] = y_val      
      
   if do_write :    
      out_x_name = "%s/%s_x.txt" % (outdir,out_median_file)      
      out_y_name = "%s/%s_y.txt" % (outdir,out_median_file)      
   
      # write median spectrum :
      print("PROGRESS : writing median spectra to output file")
      write_spectrum( median_spectrum_x, out_x_name, iqr_spectrum_x )
      write_spectrum( median_spectrum_y, out_y_name, iqr_spectrum_y )
      
   return (median_spectrum_x,median_spectrum_y,iqr_spectrum_x,iqr_spectrum_y)

##########################################################################################################################################
#
# FUNCTION : generate images of power spectra of each antenna with reference median spectrum +/- 3 standard deviations 
#   bad channels are marged and information if antenna is considered BAD or OK in the image title and legend 
# 
##########################################################################################################################################
def plot_antenna_with_median( options, antname, median_freq, median_power, median_power_err, ant_freq, ant_power, outdir="images/", y_min=0, y_max=60, label="X pol.", plot_db=False, color='black', pol='x', ux_time=None, median_total_power=-1 ) :
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
   time_str = time_dtm.strftime("%d/%m/%Y %H:%M:%S")
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


##########################################################################################################################################
# write_bad_antenna_csv_header( out_bad_f , options )
# 
# FUNCTION : write header of the generated .csv file 
# 
##########################################################################################################################################
def write_bad_antenna_csv_header( out_bad_csv_f , options ) :
   # /home/msok/Desktop/EDA2/doc/software/Antenna_Health/Dave_Minchin/header2.txt
   header_columns = [ "TILE NUMBER","ANTENNA NUMBER","POP GRID REF.","X-POL LNA","Y-POL LNA","SMART BOX PORT","SMART BOX NUMBER","FIBRE TAIL NUMBER FROM SMART BOX TO FNDH FOBOT","FEM NUMBER","Fibre Cable Length from SMART Box to FNDH","FNDH Fobot Port to CFNDH","CFNDH Fobot MPO Fly Lead","Original Order of SDGI Cable","CFNDH-Bldg Fibre Info","Due to Splice Error"," Appears at Bldg as ","Bldg Fibre Colour","TPM Location","TPM Position & Logical Number","TPM Ser. No","TPM IP Addrs","TPM Port Number/RX position","Webpage PLOT NUMBER","MIRIAD Index","Permanent Comments" ]
   
   header_line = ""
   for key in header_columns :
      header_line += ("\"%s\"," % key )

   out_bad_csv_f.write("%s\n" % (header_line))

##########################################################################################################################################
# write_bad_antenna_html_header( out_bad_f , options )
# 
# FUNCTION : write header of the generated .html file 
# 
##########################################################################################################################################
def write_bad_antenna_html_header( out_bad_html_f , options, median_total_power_x, median_total_power_y, out_put_files ) :
   now = datetime.now()
   now_str = now.strftime("%Y-%m-%d %H:%M:%S")

   out_bad_html_f.write("<html>\n")
   out_bad_html_f.write("<head>\n")
   out_bad_html_f.write("<style>\n")
   out_bad_html_f.write("table, th, td {\n")
   out_bad_html_f.write("   border: 1px solid black;\n")
   out_bad_html_f.write("}\n")
   out_bad_html_f.write("</style>\n")
   out_bad_html_f.write("</head>\n")
   out_bad_html_f.write("<body>\n")
   
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
   
   line = "<li>If number of bad channels is larger than %d (out of 512), where bad channels are counted as those which deviate from the median spectrum by more than %.2f standard deviations.<br> Number of bad channels is specified as values of BAD_CH_X and BAD_CH_Y variables</li>\n" % (options.max_bad_channels,options.threshold_in_sigma)
   out_bad_html_f.write( line )
   
   out_bad_html_f.write( "</ul>\n" )
   
   # fault types :
   line = "<h2>Fault types:</h2>\n<ul>\n"
   out_bad_html_f.write( line )
   line = "<li><font color=\"red\"><strong>flatline</strong> : Total power < 1/4 of total power of median spectrum</font></li>\n"
   out_bad_html_f.write( line )
   line = "<li><font color=\"black\"><strong>low_power</strong>  : 1/4 of total power of median spectrum < Total power < 1/2 of total power of median spectrum</font></li>\n"
   out_bad_html_f.write( line )
   line = "<li><font color=\"black\"><strong>high_power</strong> : Total power > 2 times total power of median spectrum</font></li>\n"
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

         is_csv = False
         try :      
            if outfile.index(".csv") >= 0 :
               is_csv = True
         except ValueError :
            pass

         if is_txt or is_csv :
            line = "<li><a href=\"%s\"><u>%s</u></a></li>\n" % (outfile,outfile)
         else :
            line = "<li><a href=\"%s_x.txt\"><u>Median X pol.</u></a> <a href=\"%s_y.txt\"><u>Median Y pol.</u></a></li>\n" % (outfile,outfile) 
            
         out_bad_html_f.write( line )
            
   out_bad_html_f.write( "</ul>\n" )
      
#   out_bad_html_f.write( "<br>\n" )
#   out_bad_html_f.write( "<body>\n" )
#   out_bad_html_f.write( "<br>\n" )
   out_bad_html_f.write( "<br>\n" )
   out_bad_html_f.write( "<h2>Antenna spectra compared with a median spectrum +/- %.1f x standard deviation (calculated using the interquartile range or IQR) :</h2>\n" % (options.threshold_in_sigma) )
#   out_bad_html_f.write( "<ol>\n" )
   
   # table :
   out_bad_html_f.write( "<table style=\"width:100%\">\n" )   
   out_bad_html_f.write( "<tr>\n" )
   out_bad_html_f.write( "<th>Table Index</th>\n" )
   out_bad_html_f.write( "<th>Tile</th>\n" )
   out_bad_html_f.write( "<th>Antenna</th>\n" )
   out_bad_html_f.write( "<th>Polarisation</th>\n" )
   out_bad_html_f.write( "<th>POP</th>\n" )
   out_bad_html_f.write( "<th>SMARTBOX-PORT</th>\n" )
   out_bad_html_f.write( "<th>SMARTBOX-NUMBER</th>\n" )
   out_bad_html_f.write( "<th>FIBRE_TAIL</th>\n" )
   out_bad_html_f.write( "<th>Status</th>\n" )
   out_bad_html_f.write( "<th> Additional information </th>\n" )
   out_bad_html_f.write( "</tr>\n" )
#   out_bad_html_f.write( "</table>\n" )


##########################################################################################################################################
# 
# FUNCTION : write end of the generated .html file 
# 
##########################################################################################################################################   
def write_bad_antenna_html_end( out_bad_html_f , options ) :
#  out_bad_html_f.write( "</table>\n" )
#  out_bad_html_f.write("</ol>\n\n")
   
#   line = ("<br><h2>Number of antennas with one bad polarisation : %d </h2>\n\n" % (n_bad_ant))
#   print("DEBUG : line with number of bad antennas = |%s|" % (line))
#   out_bad_html_f.write( line )
   
   out_bad_html_f.write("</body>\n")
   out_bad_html_f.write("</html>\n")
   



##########################################################################################################################################
# 
# FUNCTION : write end of the generated .html file 
# 
##########################################################################################################################################   
def write_stat_table( out_bad_html_f , n_bad_ant, flatline_x_count , flatline_y_count, lowpower_x_count, lowpower_y_count, highpower_x_count, highpower_y_count ) :

   line = ("<br><h2>Number of antennas with one bad polarisation : %d </h2>\n\n" % (n_bad_ant))
   print("DEBUG : line with number of bad antennas = |%s|" % (line))
   out_bad_html_f.write( line )

   # table :
   out_bad_html_f.write( "<table style=\"width:100%\">\n" )   
   out_bad_html_f.write( "<tr>\n" )
   out_bad_html_f.write( "<th>Fault type</th>\n" )
   out_bad_html_f.write( "<th>X polarisation</th>\n" )
   out_bad_html_f.write( "<th>Y polarisation</th>\n" )
   out_bad_html_f.write( "</tr>\n" )

   # number of flatline antennas in red :   
   html_line = ("<tr>  <td><font color=\"red\"><strong>flatline</strong></font></td> <td><font color=\"red\"><strong>%d</strong></font></td> <td><font color=\"red\"><strong>%d</strong></font></td> </tr>\n" % (flatline_x_count,flatline_y_count))
   out_bad_html_f.write( html_line )

   # number of low-power antennas in black :   
   html_line = ("<tr>  <td><font color=\"black\"><strong>low power</strong></font></td> <td><font color=\"black\"><strong>%d</strong></font></td> <td><font color=\"black\"><strong>%d</strong></font></td> </tr>\n" % (lowpower_x_count,lowpower_y_count))
   out_bad_html_f.write( html_line )

   # number of high-power antennas in black :   
   html_line = ("<tr>  <td><font color=\"black\"><strong>high power</strong></font></td> <td><font color=\"black\"><strong>%d</strong></font></td> <td><font color=\"black\"><strong>%d</strong></font></td> </tr>\n" % (highpower_x_count,highpower_y_count))
   out_bad_html_f.write( html_line )
   
   out_bad_html_f.write( "</table>\n" )   
   print("DEBUG : End of write_stat_table")
   

##########################################################################################################################################
#
# FUNCTION : main function 
#     - reading the data from HDF5 files
#     - calculating median spectra for each antnena
#     - calculating median spectrum of X and Y polarisation over all antennas 
#     - checking health of each antenna by comparison with median spectrum and standard deviation
#     - writing output text and html files
# 
#  all these steps are performed by calling earlier described functions 
# 
# all tiles :
# t_sample_list=[0] - to just use a single timestamp
#
##########################################################################################################################################
def check_antenna_health( hdf_file_template, options, 
                          nof_tiles=16, nof_ant_per_tile=16, nof_pols=2, nof_channels=512,
                          antenna_names=None ):
   
   ux_time = time.time()
   out_bad_list_file = options.station_name + "_bad_antennas.txt"
   out_bad_list_html_file = options.station_name + "_bad_antennas.html"
   out_bad_list_csv_file = options.station_name + "_bad_antennas.csv"
   out_health_report = options.station_name + "_health_report.txt"
   out_median_file   = options.station_name + "_median"
   out_ant_median_file = options.station_name + "_median_spectrum_ant"
   out_instr_config_file = options.station_name + "_instr_config.txt"
   
   out_put_files = [ out_bad_list_file, out_bad_list_html_file, out_health_report, out_median_file, out_ant_median_file, out_bad_list_csv_file , out_instr_config_file ]
   
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
   ( median_bad_channels_x , median_total_power_x, median_start_bad_ch_x, median_end_bad_ch_x ) = check_antenna( median_spectrum_x, median_spectrum_x , iqr_spectrum_x )
   ( median_bad_channels_y , median_total_power_y, median_start_bad_ch_y, median_end_bad_ch_y ) = check_antenna( median_spectrum_y, median_spectrum_y , iqr_spectrum_y )
   print("\tMedian : bad_channels_x = %d , total_power_x = %d, bad_channels_y = %d , total_power_y = %d" % (median_bad_channels_x,median_total_power_x,median_bad_channels_y,median_total_power_y))
   
   # Find bad antennas and save to file :   
   out_bad_f = open( options.outdir + "/" + out_bad_list_file , "w" )
   out_bad_html_f = open( options.outdir + "/" + out_bad_list_html_file , "w" )
   out_bad_csv_f = open( options.outdir + "/" + out_bad_list_csv_file , "w" )
   out_instr_config_f = open( options.outdir + "/" + out_instr_config_file , "w" )
   comment = ("# max_bad_channels = %d , median total power in X = %d and in Y = %d (total power is expected to be in the range x0.5 to x2 of these values)\n" % (options.max_bad_channels,median_total_power_x,median_total_power_y))
   out_bad_f.write( comment )
   out_bad_f.write( ("# UNIXTIME = %.4f\n" % (ux_time)) )
   out_bad_f.write( "# ANTNAME  ANT_INDEX  TILE  ANT   REASON\n" )
   out_instr_config_f.write("# INPUT ANTENNA POL     DELTA   FLAG\n")
   
   # html file :
   write_bad_antenna_html_header( out_bad_html_f , options, median_total_power_x, median_total_power_y, out_put_files )

   # csv file 
   write_bad_antenna_csv_header( out_bad_csv_f , options )   
   
   out_report_f = open( options.outdir + "/" + out_health_report , "w" )
   out_report_f.write( ("# MAXIMUM NUMBER OF BAD CHANNELS ALLOWED = %d\n" % (options.max_bad_channels)) )
   out_report_f.write( ("# UNIXTIME = %.4f\n" % (ux_time)) )
   comment = ("#  ANT_NAME TILE_ID  ANT_ID  TOTAL_POWER_X  NUM_BAD_CHANNELS_X  TOTAL_POWER_Y  NUM_BAD_CHANNELS_Y  STATUS  DETAILS\n" )   
   out_report_f.write( comment )
   comment = ("#   MED    MED      MED      %06d            %03d                %06d             %03d        REFERENCE\n" % (median_total_power_x,median_bad_channels_x,median_total_power_y,median_bad_channels_y))
   out_report_f.write( comment )

   n_bad_ant_count = 0
   flatline_x_count = 0
   flatline_y_count = 0
   lowpower_x_count = 0
   lowpower_y_count = 0
   highpower_x_count = 0
   highpower_y_count = 0
   
   print("\tComparing antenna spectra with median spectrum ...")   
   for tile in range(0,nof_tiles) : 
      d_test=f_data[tile] 

      for ant in range(0,nof_ant_per_tile) :
         ant_idx = tile*nof_ant_per_tile + ant
      
         # spectrum_x = d_test[t_sample,:,ant,0]
         # spectrum_y = d_test[t_sample,:,ant,1]
         ant_median_spectrum_x = median_spectrum_per_ant_x[ant_idx]
         ant_median_spectrum_y = median_spectrum_per_ant_y[ant_idx]
         
         ( n_bad_channels_x , n_total_power_x, start_bad_ch_x, end_bad_ch_x ) = check_antenna( ant_median_spectrum_x, median_spectrum_x , iqr_spectrum_x, ant_idx=ant_idx, threshold_in_sigma=options.threshold_in_sigma )
         ( n_bad_channels_y , n_total_power_y, start_bad_ch_y, end_bad_ch_y ) = check_antenna( ant_median_spectrum_y, median_spectrum_y , iqr_spectrum_y, ant_idx=ant_idx, threshold_in_sigma=options.threshold_in_sigma )
         
         # TODO : html_line_x = generate_html_line( ... , pol='X' )
         # TODO : html_line_y = generate_html_line( ... , pol='Y' )
         flag_x = ""
         flag_y = ""
         bad_power_x = False
         bad_power_y = False
         flatline_x  = False
         flatline_y  = False
         
         fault_type_x = ""
         fault_type_y = ""
         
         if n_total_power_x < (median_total_power_x/2) or n_total_power_x > (median_total_power_x*2):
            flag_x += (",BAD_POWER_X=%d" % n_total_power_x)
            bad_power_x = True
            if n_total_power_x < (median_total_power_x/4) :
               flatline_x = True
               fault_type_x = "flatline_x"
               flatline_x_count += 1
            elif n_total_power_x < (median_total_power_x/2) :
               fault_type_x = "low_power_x"
               lowpower_x_count += 1
            elif n_total_power_x > (median_total_power_x*2) :
               fault_type_x = "high_power_x"
               highpower_x_count += 1
            # print("DEBUG : %d vs. %d or %d vs %d" % (n_total_power_x,median_total_power_x,n_total_power_x,median_total_power_x))
         else :
            if n_bad_channels_x > options.max_bad_channels :
               flag_x += ("BAD_CH_X=%d" % n_bad_channels_x)
               fault_type_x += ("Bandpass %.1f - %.1f MHz" % (ch2freq(start_bad_ch_x),ch2freq(end_bad_ch_x)) )
            
         if n_total_power_y < (median_total_power_y/2) or n_total_power_y > (median_total_power_y*2):
            flag_y += (",BAD_POWER_Y=%d" % n_total_power_y)
            bad_power_y = True
            if n_total_power_y < (median_total_power_y/4) :
               flatline_y = True
               fault_type_y = "flatline_y"
               flatline_y_count += 1
            elif n_total_power_y < (median_total_power_y/2) :
               fault_type_y = "low_power_y"
               lowpower_y_count += 1
            elif n_total_power_y > (median_total_power_y*2) :
               fault_type_y = "high_power_y"
               highpower_y_count += 1
         else :
            if n_bad_channels_y > options.max_bad_channels :
               flag_y += ("BAD_CH_Y=%d" % n_bad_channels_y)
               fault_type_y += ("Bandpass %.1f - %.1f MHz" % (ch2freq(start_bad_ch_y),ch2freq(end_bad_ch_y)) )


         # get antenna name if mapping hash table is provided :
         antname = " ?? " 
         if antenna_names is not None :
            antname = antenna_names[ant_idx]         
      
         pop = "?"
         smartbox_port = "?"
         smartbox_number = "?"
         fibre_tail = "?"
         if g_spreadsheet_csv_file is not None :
            print("INFO : will try to use information from the spreadsheet")
            # TODO 
            # antname, tile+1
            (spreadsheet_idx,pop,smartbox_port,smartbox_number,fibre_tail) = get_details_from_spreadsheet( tile+1 , antname )

         status = "OK"      
         flag = ""

         is_ok = True
         is_x_ok = True
         is_y_ok = True
         flag_x_value = 0
         flag_y_value = 0
         if len(flag_x) <= 0 :
            flag_x = "OK"
         else :
            is_ok = False
            is_x_ok = False
            if "flatline_x" in fault_type_x :
               flag_x_value = 1
            
         if len(flag_y) <= 0 :
            flag_y = "OK"
         else :
            is_ok = False
            is_y_ok = False
            flag_y_value = 1
            if "flatline_y" in fault_type_y :
               flag_y_value = 1


         if is_ok :
            flag   = "OK"
         else :
            status = "BAD"
            n_bad_ant_count += 1
            
            flag = flag_x + "," + flag_y
            line = "%s : %05d  %05d , %05d %s\n" % (antname,ant_idx,tile,ant,flag)
            out_bad_f.write( line )
            font_color_x = "black"
            font_color_y = "black"
            font_color   = "black"
            font_type_start = ""
            font_type_end   = ""
            
            if flatline_x :
               font_color_x = "red"
               font_color   = "red"
               font_type_start = "<strong>"
               font_type_end   = "</strong>"
               
                        
            if flatline_y :
               font_color_y = "red"
               font_color   = "red"
               font_type_start = "<strong>"
               font_type_end   = "</strong>"
                        
                        
            html_line = ""            
            # HTML line for polarisation X :
            if not is_x_ok or options.show_both_pols :
               html_line += "<tr>\n"
               # Antname and tile :
               # remove strong
#              html_line += ("   <td><font color=\"%s\">%s%d%s</font></td> <td><font color=\"%s\">%s%s%s</font></td> <td><font color=\"%s\">%sTile%d%s</font></td>\n" % (font_color,font_type_start,n_bad_ant_count,font_type_end,font_color,font_type_start,antname,font_type_end,font_color,font_type_start,tile+1,font_type_end))
               html_line += ("   <td><font color=\"%s\">%s%d%s</font></td> <td><font color=\"%s\">%sTile%d%s</font></td> <td><font color=\"%s\">%s%s%s</font></td><td><font color=\"%s\">%s%s%s</font></td>\n" % (font_color,font_type_start,n_bad_ant_count,font_type_end,font_color,font_type_start,tile+1,font_type_end,font_color,font_type_start,antname,font_type_end,font_color,font_type_start,"X",font_type_end))
               # details from the spreadsheet :
               html_line += ("   <td><font color=\"%s\">%s%s%s</font></td> <td><font color=\"%s\">%s%s%s</font></td> <td><font color=\"%s\">%s%s%s</font></td> <td><font color=\"%s\">%s%s%s</font></td>\n" % \
                            (font_color,font_type_start,pop,font_type_end, \
                             font_color,font_type_start,smartbox_port,font_type_end, \
                             font_color,font_type_start,smartbox_number,font_type_end, \
                             font_color,font_type_start,fibre_tail,font_type_end))
               # X polarisation :
               html_line += ("   <td> <font color=\"%s\">%s%s%s</s></font> <a href=\"images/%s_x.png\"><u>%s</u></a></td>\n" % (font_color_x,font_type_start,fault_type_x,font_type_end,antname,flag_x))
               # Y polarisation :
               # html_line += ("   <td> <font color=\"%s\">%s%s%s</s></font> <a href=\"images/%s_y.png\"><u>%s</u></a></td>\n" % (font_color_y,font_type_start,fault_type_y,font_type_end,antname,flag_y))
               # extra information 
               html_line += ("   <td> <font color=\"%s\">%s config file index = %05d  , in tile index = %05d %s</font></td>\n" % (font_color,font_type_start,ant_idx,ant,font_type_end) )
               html_line += "</tr>\n"
               
            if not is_y_ok or options.show_both_pols :               
               # HTML line for polarisation Y :
               html_line += "<tr>\n"
               # Antname and tile :
               # remove strong
               html_line += ("   <td><font color=\"%s\">%s%d%s</font></td> <td><font color=\"%s\">%sTile%d%s</font></td> <td><font color=\"%s\">%s%s%s</font></td><td><font color=\"%s\">%s%s%s</font></td>\n" % (font_color,font_type_start,n_bad_ant_count,font_type_end,font_color,font_type_start,tile+1,font_type_end,font_color,font_type_start,antname,font_type_end,font_color,font_type_start,"Y",font_type_end))
               # details from the spreadsheet :
               html_line += ("   <td><font color=\"%s\">%s%s%s</font></td> <td><font color=\"%s\">%s%s%s</font></td> <td><font color=\"%s\">%s%s%s</font></td> <td><font color=\"%s\">%s%s%s</font></td>\n" % \
                               (font_color,font_type_start,pop,font_type_end, \
                               font_color,font_type_start,smartbox_port,font_type_end, \
                               font_color,font_type_start,smartbox_number,font_type_end, \
                               font_color,font_type_start,fibre_tail,font_type_end))
               # X polarisation :
               # html_line += ("   <td> <font color=\"%s\">%s%s%s</s></font> <a href=\"images/%s_x.png\"><u>%s</u></a></td>\n" % (font_color_x,font_type_start,fault_type_x,font_type_end,antname,flag_x))
               # Y polarisation :
               html_line += ("   <td> <font color=\"%s\">%s%s%s</s></font> <a href=\"images/%s_y.png\"><u>%s</u></a></td>\n" % (font_color_y,font_type_start,fault_type_y,font_type_end,antname,flag_y))
               # extra information 
               html_line += ("   <td> <font color=\"%s\">%s config file index = %05d  , in tile index = %05d %s</font></td>\n" % (font_color,font_type_start,ant_idx,ant,font_type_end) )
               html_line += "</tr>\n"
                        
            
# <li> version (not table):            
#            html_line += "   <li> <font color=\"%s\"><strong>%s / Tile%s</strong> (config file index = %05d  , in tile index = %05d) : </font>" % (font_color,antname,tile+1,ant_idx,ant) # tile+1 for to be easier matched with other pages etc
#            if len(flag_x) > 0 :
               # TODO : create description for X in html 
#               html_line += ("<a href=\"images/%s_x.png\"><u>%s</u></a>" % (antname,flag_x))
#            if len(flag_y) > 0 :
               # TODO : create description for Y in html
#               html_line += (", <a href=\"images/%s_y.png\"><u>%s</u></a>" % (antname,flag_y))
            
            # end of line + fault in X and Y :   
#            html_line += ( "</a> <strong>X:<font color=\"%s\">%s</s></strong> , Y:<strong><font color=\"%s\">%s</s></strong>\n" % (font_color_x,fault_type_x,font_color_y,fault_type_y))
            
            out_bad_html_f.write( html_line )
            

            # CSV file :
            csv_line = ""
            # Warning : MIRIAD INDEX in Dave's script has indexes starting from 1 too (in the config file they are from ZERO !)
            csv_line += ( "%d,%s,%s,,,%s,%s,%s,,,,,,,,,,,,,,,,%d,,%s,%s,,\n" % ((tile+1),antname,pop,smartbox_port,smartbox_number,fibre_tail,(ant_idx+1),fault_type_x,fault_type_y))
            out_bad_csv_f.write( csv_line )

         instr_config_line_x = "%d\t%d\tX\t0\t%d\t\t# %s\n" % (ant_idx*2,ant_idx,flag_x_value,antname)
         out_instr_config_f.write(instr_config_line_x)

         instr_config_line_y = "%d\t%d\tY\t0\t%d\t\t\n" % (ant_idx*2+1,ant_idx,flag_y_value)
         out_instr_config_f.write(instr_config_line_y)

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
   out_bad_html_f.write( "</table>\n" )
   
   # close instr_config.txt file for given station
   out_instr_config_f.close()
   
   # write stat table
   write_stat_table( out_bad_html_f , n_bad_ant_count, flatline_x_count , flatline_y_count, lowpower_x_count, lowpower_y_count, highpower_x_count, highpower_y_count) 
   
   write_bad_antenna_html_end( out_bad_html_f , options )
   out_bad_html_f.close()
      
#  CLOSE HDF5 files :
   for tile in range(0,nof_tiles) :   
      f_array[tile].close()

# >>> s['POP_GRID_REF'][idx]
# >>> s['SMART_BOX_PORT'][idx]
# >>> s['FIBRE_TAIL_NO'][idx]
# tile    - integer expected
# antenna - integer expected for example 63 for Ant063 
def find_anttile( spreadsheet, tile, antenna ) :
   len_tile = len( spreadsheet['TILE_NO'] ) 
   len_ant  = len( spreadsheet['ANT_NO'] )
   
   len_common = len_tile
   if len_tile == len_ant :
      print("DEBUG : lengths of TILE_NO and ANT_NO columns are the same = |%d|" % (len_common))
   else :
      print("WARNING : number of entries in TILE_NO column = %d != number of entries in ANT_NO column = %d -> using smaller" % (len_tile,len_ant))
      len_common = min(len_tile,len_ant)
      
   for idx in range(0,len_common):
      try : 
         spreadsheet_tile = int( spreadsheet['TILE_NO'][idx] )
         spreadsheet_ant  = int( spreadsheet['ANT_NO'][idx] )
         if tile == spreadsheet_tile and antenna == spreadsheet_ant :
            print("DEBUG : found tile = %d and antenna = %d in the spreadsheet at position %d" % (tile,antenna,idx))
            return (idx)
      except :
         pass

   print("WARNING : could not find tile = %d and antenna = %d in the spreadsheet -> spreadsheet information will not be used" % (tile,antenna))
   return (None)

# tile    - integer expected
# antname - string for example Ant063 
def get_details_from_spreadsheet( tile, antname ) :
   global g_spreadsheet_csv_file

   if g_spreadsheet_csv_file is not None :
      ant_number = antname[3:] # get antenna number from string like Ant063
      idx = find_anttile( g_spreadsheet_csv_file, int(tile), int(ant_number) )
      
      if idx is not None :
         pop             = g_spreadsheet_csv_file['POP_GRID_REF'][idx]
         smartbox_port   = g_spreadsheet_csv_file['SMART_BOX_PORT'][idx]
         smartbox_number = g_spreadsheet_csv_file['SMART_BOX_NUMBER'][idx]
         fibre_tail      = g_spreadsheet_csv_file['FIBRE_TAIL_NO'][idx]
         
         return (idx,pop,smartbox_port,smartbox_number,fibre_tail)

   return (None,"?","?","?","?")

def read_spreadsheet_file( spreadsheet_csvfile, use_spreadsheet ) :
   global g_use_spreadsheet
   global g_spreadsheet_csv_file
   
   if use_spreadsheet and spreadsheet_csvfile is not None and g_use_spreadsheet :
      print("INFO : trying to read spreadsheet file %s using pandas ..." % (spreadsheet_csvfile))
      try :
         g_spreadsheet_csv_file = pandas.read_csv( spreadsheet_csvfile )
         print("INFO : spreadsheet file read OK !")
         
         return g_spreadsheet_csv_file
      except :
         print("WARNING : could not read spreadsheet information from CSV file %s -> some report fields will not be populated" % (g_spreadsheet_csv_file))
   else :
      print("WARNING : using spreadsheet information is not required or not possible (no pandas module or csv file not specified)")
    

   g_spreadsheet_csv_file = None
   return None

def parse_options(idx):
   parser=optparse.OptionParser()
   parser.set_usage("""parse_pulsars.py""")
   parser.add_option("--n_timesteps","--timesteps",dest="n_timesteps",default=-1,help="Number of timesteps used for calculations (<0 -> all) [default: %default]",type="int")
   parser.add_option("--outdir","--out_dir","--dir","-o",dest="outdir",default="./",help="Output directory [default: %default]")
   parser.add_option("--station","--station_name",dest="station_name",default="eda2",help="Prefix for output files [default: %default]")
   parser.add_option('--latest','--newest','--last',action="store_true",dest="latest",default=False, help="Use the most recent timestamps [default %default]")
   parser.add_option('--threshold','--threshold_in_sigma',dest="threshold_in_sigma",default=3,help="Threshold in sigma [default %default]")
   parser.add_option('--max_bad_channels','--max_bad_ch',dest="max_bad_channels",default=100,help="Maximum number of bad channels [default %default]",type="int")
   
   # presentation of bad antennas :
   parser.add_option('--show_both_pols','--show_both_pols',action="store_true",dest="show_both_pols",default=False, help="Show both polarisations in a bad antenna (also the one which is OK) [default %default]")
   
   # plotting :
   parser.add_option('--images','--plot',action="store_true",dest="do_images",default=False, help="Do images [default %default]")
   parser.add_option('--plot_db',action="store_true",dest="plot_db",default=False, help="Do images in dB scale [default %default]")
   
   # using external spreadsheets
   parser.add_option("--use_spreadsheet","--use_googledoc",action="store_true",dest="use_spreadsheet", default=False, help="Use spreadsheet with information about signal chains to generate more detailed report [default %default]")
   parser.add_option("--spreadsheet_csvfile","--spreadsheet_file",dest="spreadsheet_csvfile",default=None,help="File name of the spreadsheet CSV file [default %default]")
   
   (options,args)=parser.parse_args(sys.argv[idx:])

   return (options, args)
   
   
if __name__ == '__main__' :
#   global global_excluded_freq_ranges
   
   # init global ranges see : /home/msok/Desktop/EDA2/logbook/20210507_eda2_ppd_plots_AUTO.odt
   # ranges in MHz 
   init_rfi_bands()
   

   hdf_file_template="channel_integ_%d_20210222_09517_0.hdf5"
   if len(sys.argv) > 1:
      hdf_file_template = sys.argv[1]

   (options, args) = parse_options(1)
   if options.spreadsheet_csvfile is None :
      options.spreadsheet_csvfile = ("%s.csv" % options.station_name)
   
   print("######################################################################################")
   print("PARAMETERS:")
   print("######################################################################################")
   print("hdf_file_template = %s" % (hdf_file_template))
   print("N timesteps       = %d (latest = %s)" % (options.n_timesteps,options.latest))   
   print("Output directory  = %s" % (options.outdir))
   print("Station           = %s" % (options.station_name))
   print("Do images         = %s (dB = %s)" % (options.do_images,options.plot_db))
   print("threshold_in_sigma = %.2f" % (options.threshold_in_sigma))
   print("Use spreadsheet   = %s (csvfile = %s)" % (options.use_spreadsheet,options.spreadsheet_csvfile))
   print("Show both pols (the OK one) = %s" % (options.show_both_pols))
   print("######################################################################################")
   
   if len(options.outdir) and options.outdir != "./" :
      print("Creating output directory %s ..." % (options.outdir))
      mkdir_p( options.outdir )      
      print("DONE")

      if options.do_images :
         print("Creating images directory %s ..." % (options.outdir + "/images/"))
         mkdir_p( options.outdir + "/images/" )

   print("INFO : reading spreadsheet file %s" % (options.spreadsheet_csvfile))
   read_spreadsheet_file( options.spreadsheet_csvfile, options.use_spreadsheet )

#   t_sample_list=None
#   if options.n_timesteps > 0 :
#      t_sample_list = numpy.arange( options.n_timesteps )
   
   # at the moment the antenna names are the same for EDA2 and AAVS2 :
   antenna_names = eda2_aavs2_antenna_names
   # if options.station_name == "eda2" :
   #   antenna_names = eda2_antennas

   # check_antenna_health("channel_integ_14_20200205_41704_0.hdf5")
   check_antenna_health( hdf_file_template , options, antenna_names=antenna_names )
      