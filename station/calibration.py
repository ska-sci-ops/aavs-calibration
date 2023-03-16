# Based on comments in :
# aavs@aavs-lmc:/opt/aavs/bin$ joe station.py
"""Coefficients is a 3D complex array of the form [antenna, channel, polarization], with each element representing a 
            normalized coefficient, with (1.0, 0.0) the normal, expected response for an ideal antenna. Antenna is the index 
            specifying the antenna within the index (using correlator indexing). Channel is the index specifying the channels 
            at the beamformer output, .e. considering only those channels actually processed and beam assignments. The polarization 
            index ranges from 0 to 3.
            0: X polarization direct element
            1: X->Y polarization cross element
            2: Y->X polarization cross element
            3: Y polarization direct element"""
from __future__ import print_function


import numpy
import sys
import os
import math
import pickle
import copy

import calibration_db
import fit_amplitude

from optparse import OptionParser,OptionGroup

# Defaults based on : ~/Desktop/AAVS1/data/20190320/20190320/phase_vs_antenna_X.txt and phase_vs_antenna_Y.txt see also ~/Desktop/AAVS1/logbook/20190402_eda1-tpm17_realtime_vs_offline_beamformer.odt :
# should correspond to the same as in file : phase_vs_antenna.pkl (in svn : /home/msok/bighorns/software/analysis/scripts/python/eda2/pointing )
default_eda1_tpm17_ant_list = [ 0 ,1 ,2 ,3 ,4 ,5 ,6 ,7 ,8 ,9 ,10 ,11 ,12 ,13 ,14 ,15 ]
default_eda1_tpm17_ant_count = 16
default_eda1_tpm17_phase_offset_x = [ -0.0000 ,-29.8011 ,130.5227 ,6.7357 ,-10.7470 ,-137.0803 ,-124.8536 ,22.9653 ,-116.1612 ,-78.6366 ,74.3674 ,-26.2321 ,53.5002 ,-41.8852 ,-135.7549 ,-139.9859 ] 
default_eda1_tpm17_phase_offset_y = [ -0.0000 ,-17.2882 ,126.0434 ,2.4542 ,-1.8393 ,-116.0005 ,-129.4990 ,25.9765 ,-122.2604 ,-79.4688 ,90.2283 ,-27.6532 ,49.1883 ,-50.0944 ,-139.9135 ,-145.5877 ]

def print_coeff_pol( obj, pol ) :
 
   pol_str = "X"
   if pol == 3 :
      pol_str = "Y"
   elif pol == 1 :
      pol_str = "XY"
   elif pol == 2 :
      pol_str = "YX"

   n_ant  = obj.shape[0]
   n_chan = obj.shape[1]
   n_pols = obj.shape[2]
   middle_chan = int( n_chan / 2 )

   print("------------------------------------------------ %s polarisation ------------------------------------------------" % (pol_str))
   offline_beamformer_opt=""
   print("------------------------------------------------")
   print("%s-polarisation phases of calibration solutions :" % (pol_str))
   print("------------------------------------------------")
   print("Ant     Phase[deg]")
   print("------------------------------------------------")
   for ant in range(0,n_ant) :
      complex_coeff = obj[ant,middle_chan,pol]
      phase_deg     = numpy.angle( complex_coeff ) * (180.00/math.pi)
      print("%d     %.4f" % (ant,phase_deg))
      
      phase_str = "%.4f" % (phase_deg)
      offline_beamformer_opt += phase_str
      if ant < (n_ant-1) :
         offline_beamformer_opt += ","
      
   print("------------------------------------------------")
   print("-%s %s" % (pol_str,offline_beamformer_opt))      
   print("------------------------------------------------")       


def print_coeff( obj, filename=None ) :
   if filename is not None :
      print("Calibration coefficients from file %s" % (filename))   
   
   print_coeff_pol( obj , 0 ) # 0 is X pol
   print_coeff_pol( obj , 3 ) # 3 is Y pol
   
def save_coeff( obj , name ):
    pickle_file = name
    if name.find(".pkl") < 0 :
        pickle_file = name + '.pkl'

    with open( pickle_file, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
        
    print("Saved coefficients to file %s" % (pickle_file))    

def load_coeff( pickle_file, show=True, swap_pols=False, sign_value=1 ) :
   obj = None
 
   with open( pickle_file, 'rb') as f:
       obj = pickle.load(f)

   if swap_pols :
      print("WARNING : polarisation swap is required -> swapping now")
      n_ants=obj.shape[0]
      n_ch=obj.shape[1]
      
      for ant in range(0,n_ants):
         for ch in range(0,n_ch):
            xx=obj[ant,ch,0]
            yy=obj[ant,ch,3]
       
            # swap :
            obj[ant,ch,0]=yy
            obj[ant,ch,3]=xx

       
   if sign_value < 1 :
      if sign_value < 0 :
         print("DEBUG : load_coeff -> conjugate calibration coefficients")
         obj = numpy.conjugate( obj )
         show = True
      else :
         obj = 0.00*obj
         print("DEBUG : load_coeff -> setting calibration coefficients to ZERO")
         show = True

   if show :
      print_coeff( obj, pickle_file )

   return obj


def read_phase_offsets( filename ) :
    print("Reading phase offsets from file %s" % (filename))

    file=open( filename , 'r' )
    data=file.readlines()

    antenna_arr=[]
    phase_offset_arr=[]
    count=0

    for line in data : 
        words = line.split(' ')

        if line[0] == '#' :
            continue

        if line[0] != "#" :
            ant_idx = int(words[0+0])
            phase_offset = float(words[1+0])
            
            # print "DEBUG : Adding %d / %.2f" % (ant_idx,phase_offset)
            
            antenna_arr.append( ant_idx )
            phase_offset_arr.append( phase_offset )
            
            count += 1
            
    file.close()
            
    return (antenna_arr,phase_offset_arr,count)


def read_calibration_phase_offsets( phase_offset_file_X=None, phase_offset_file_Y=None, n_channels=8, n_pols=4, debug=False ) :
    
    calibration_coef = None 

    antenna_arr_x = copy.copy( default_eda1_tpm17_ant_list )
    antenna_arr_y = copy.copy( default_eda1_tpm17_ant_list )
    count_x       = default_eda1_tpm17_ant_count
    count_y       = default_eda1_tpm17_ant_count
    phase_offset_arr_x = copy.copy( default_eda1_tpm17_phase_offset_x )
    phase_offset_arr_y = copy.copy( default_eda1_tpm17_phase_offset_y )

    if phase_offset_file_X is not None and phase_offset_file_Y is not None :
        (antenna_arr_x,phase_offset_arr_x,count_x) = read_phase_offsets( phase_offset_file_X )
        (antenna_arr_y,phase_offset_arr_y,count_y) = read_phase_offsets( phase_offset_file_Y )
    
    coeff_arr_x = phase_offset_arr_x[:] # apparently .copy is not in python 2.7 so using copy with slicing
    coeff_arr_y = phase_offset_arr_y[:] # apparently .copy is not in python 2.7 so using copy with slicing
    
    if count_x == count_y :
       calibration_coef = numpy.zeros( (count_x, n_channels, n_pols ) , dtype=numpy.complex128)
       
       if debug : 
          print("calibration_coef.shape = %d x %d x %d" % (calibration_coef.shape[0],calibration_coef.shape[1],calibration_coef.shape[2]))   
          print("Number of phase offsets agree between X and Y and is %d" % (count_x))
                                   
          print("# ANT   |     X[deg]      |     Y[deg]       |    X_complex    |    Y_complex    |")
          
       for i in range(0,count_x) :       
          phase_x_rad = phase_offset_arr_x[i]*(math.pi / 180.00)
          phase_y_rad = phase_offset_arr_y[i]*(math.pi / 180.00)

          coeff_arr_x[i] = complex( math.cos(phase_x_rad) , math.sin(phase_x_rad) )
          coeff_arr_y[i] = complex( math.cos(phase_y_rad) , math.sin(phase_y_rad) )
          
          # initialising all channels with the same coefficients and leaving cross-pols XY and YX (2,3) = ZERO :
          calibration_coef[i,:,0] = coeff_arr_x[i] 
          calibration_coef[i,:,3] = coeff_arr_y[i]
       
          if debug : 
             print(" %03d    |    %09.4f    |    %09.4f     |  %s  |  %s  |" % (i,phase_offset_arr_x[i],phase_offset_arr_y[i],coeff_arr_x[i],coeff_arr_y[i]))
          
          
          
    else :
       print("ERROR : different number of coefficients read from files %s and %s , %d and %d respectively -> cannot continue" % (phase_offset_file_X,phase_offset_file_Y,count_x,count_y))
       


    return calibration_coef

# TODO : frequency_channel - should be central channel and 8 channels should start from -4 channels :
def get_calibration_coeff_from_db( start_frequency_channel, station_id, swap_pols=False, nof_antennas=256, n_channels=8, n_pols=4 , debug=True, apply_amplitudes=False, 
                                   x_amp_par=None, y_amp_par=None, flag_antennas_list=None , sign_value=1 , invert_amplitudes=False, fittime=None, db_field_postfix="_amp" ) : # use database 

    if sign_value < 1 :
       if sign_value < 0 :
          print("DEBUG : get_calibration_coeff_from_db -> conjugate calibration coefficients")
          debug = True
       else :
          print("DEBUG : get_calibration_coeff_from_db -> setting calibration coefficients to ZERO")
          debug = True

    # not yet implemented 
    (x_delays,y_delays) = calibration_db.get_latest_delays( station_id=station_id, nof_antennas=nof_antennas, fittime=fittime )

    print("get_calibration_coeff_from_db( start_frequency_channel=%d , station_id=%d )" % (start_frequency_channel,station_id))
    if debug : 
       print("DEBUG - calibration solutions from the MCCS database (swap_pols = %s)" % (swap_pols))   
       print("# ANT   |     X[deg]      |     Y[deg]       |    X_complex    |    Y_complex    |")

    calibration_coef = numpy.zeros( (nof_antennas, n_channels, n_pols ) , dtype=numpy.complex128)

    for frequency_channel in range(start_frequency_channel,(start_frequency_channel+n_channels)):
       freq_channel_idx = frequency_channel - start_frequency_channel
       frequency_mhz = frequency_channel * (400.00/512.00)
       
       if apply_amplitudes :
          x_amp = x_amp_par
          y_amp = y_amp_par
       
          if x_amp is None or y_amp is None :
             print("DEBUG : reading amplitudes from MCCS database ...")
             (x_amp,y_amp) = calibration_db.get_latest_amps( station_id=station_id, freq_channel=frequency_channel, fittime=fittime, db_field_postfix=db_field_postfix )
          
          if x_amp is not None and y_amp is not None :
             if len(x_amp) != len(x_delays) or len(y_amp) != len(y_delays) :
                print("ERROR : cannot apply calibration amplitudes, dimenssions of arrays are different")
                apply_amplitudes = False
          
       
       print("--------------------------- channel = %d , %.4f [MHz] ---------------------------" % (frequency_channel,frequency_mhz))
       flagged = 0 
       for ant_idx in range(0,nof_antennas) :    
          # X pol : 
          x_delay_us = x_delays[ant_idx][0] # delay in micro-seconds 
          x_slope_rad = 2.00*math.pi*x_delay_us; # 10^6 from MHz * 10^-6 from uses = 10^0
          x_phase0_rad = x_delays[ant_idx][1]
          phase_x_rad =  x_phase0_rad +  x_slope_rad*frequency_mhz
          amplitude_x = 1.00
    
          # Y pol : 
          y_delay_us = y_delays[ant_idx][0] # delay in micro-seconds
          y_slope_rad = 2.00*math.pi*y_delay_us; # 10^6 from MHz * 10^-6 from uses = 10^0
          y_phase0_rad = y_delays[ant_idx][1]
          phase_y_rad =  y_phase0_rad +  y_slope_rad*frequency_mhz
          amplitude_y = 1.00
          
          if apply_amplitudes :
             amplitude_x = x_amp[ant_idx]
             amplitude_y = y_amp[ant_idx]
             
             if invert_amplitudes :
                print("DEBUG : inverting amplitudes (%.6f,%.6f) -> (%.6f,%.6f)" % (amplitude_x,amplitude_y,(1.00 / amplitude_x),(1.00 / amplitude_y)))

                if amplitude_x != 0 :
                   amplitude_x = 1.00 / amplitude_x

                if amplitude_y != 0 :
                   amplitude_y = 1.00 / amplitude_y
          
          # initialising all channels with the same coefficients and leaving cross-pols XY and YX (2,3) = ZERO :
          if swap_pols : 
             calibration_coef[ant_idx,freq_channel_idx,0] = complex( math.cos(phase_y_rad) , sign_value*math.sin(phase_y_rad) ) * amplitude_y
             calibration_coef[ant_idx,freq_channel_idx,3] = complex( math.cos(phase_x_rad) , sign_value*math.sin(phase_x_rad) ) * amplitude_x             
          else :
             calibration_coef[ant_idx,freq_channel_idx,0] = complex( math.cos(phase_x_rad) , sign_value*math.sin(phase_x_rad) ) * amplitude_x
             calibration_coef[ant_idx,freq_channel_idx,3] = complex( math.cos(phase_y_rad) , sign_value*math.sin(phase_y_rad) ) * amplitude_y
             
       
          if flag_antennas_list is not None :
             if ant_idx in flag_antennas_list :
                print("WARNING : flagging antenna %d" % (ant_idx))
                calibration_coef[ant_idx] = calibration_coef[ant_idx]*0
                flagged = flagged + 1

          if sign_value == 0 :
             print("WARING : setting all calibration solutions to ZERO !")
             calibration_coef[ant_idx,freq_channel_idx] = calibration_coef[ant_idx,freq_channel_idx]*0
             
          
          if debug : 
             phase_x_debug = numpy.angle( calibration_coef[ant_idx,freq_channel_idx,0] )*(180.00/math.pi)
             phase_y_debug = numpy.angle( calibration_coef[ant_idx,freq_channel_idx,3] )*(180.00/math.pi)
             print(" %03d    |    %09.4f    |    %09.4f     |  %s  |  %s  |" % (ant_idx,phase_x_debug,phase_y_debug,calibration_coef[ant_idx,freq_channel_idx,0],calibration_coef[ant_idx,freq_channel_idx,3]))
   
       print("DEBUG : flagged %d antennas" % (flagged))

    
    return calibration_coef

def get_calibration_coeff( calibration_file = None , swap_pols=False , sign_value=1 ) : # Pickle file with calibration coefficients or phase_vs_antenna.pkl can be used 

    calib_coeff = None
    
    if calibration_file is not None :
        # if pickle file is provided load it and return :
        calib_coeff = load_coeff( calibration_file , swap_pols=swap_pols , sign_value=sign_value )
    else :
        # if pickle file is not provided use hardcoded defaults (see description above )
        calib_coeff = read_calibration_phase_offsets()

    return calib_coeff        

def calc_pointing_coeff( pointing_coeff,          # pointing coefficients (not file ready array)
                         calibration_file = None  # Pickle file with calibration coefficients or phase_vs_antenna.pkl can be used
                      ) :

    calib_coeff = get_calibration_coeff( calibration_file )
    # pointing_coeff = load_coeff( pointing_file )
    
    final_coeff = calib_coeff * pointing_coeff 
    
    # numpy.angle( final_coeff[1,0,:] )*(180.00/math.pi)
    # 
    # Loading can be implemtned when station object is imported too :
    # ipython -i /opt/aavs/bin/station.py -- -t tpm-17
    # station.calibrate_station(final_coeff)
    # 2019-04-02 12:47:55,607 - INFO - Station - Downloaded coefficients to tiles in 0.044s
    # 2019-04-02 12:47:55,610 - INFO - Station - Switched calibration banks
    # see page 5 of eda2_pointing.odt
    
    return ( final_coeff , pointing_coeff , calib_coeff )


def get_pointing_coeff( pointing_file,           # pointing coefficients based on saved by eda1 pointing script eda1_tpm17_pointing.py
                        calibration_file = None  # Pickle file with calibration coefficients or phase_vs_antenna.pkl can be used
                      ) :

    calib_coeff = get_calibration_coeff( calibration_file )
    pointing_coeff = load_coeff( pointing_file )
    
    final_coeff = calib_coeff * pointing_coeff 
    
    # numpy.angle( final_coeff[1,0,:] )*(180.00/math.pi)
    # 
    # Loading can be implemtned when station object is imported too :
    # ipython -i /opt/aavs/bin/station.py -- -t tpm-17
    # station.calibrate_station(final_coeff)
    # 2019-04-02 12:47:55,607 - INFO - Station - Downloaded coefficients to tiles in 0.044s
    # 2019-04-02 12:47:55,610 - INFO - Station - Switched calibration banks
    # see page 5 of eda2_pointing.odt
    
    return ( final_coeff , pointing_coeff , calib_coeff )
                        

def parse_options(idx=0):
   usage="Usage: %prog [options]\n"
   usage+='\tRead calibration coefficients and prepare then into a format required by aavs@aavs-lmc:/opt/aavs/bin$ joe station.py \n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-f','--filebase',dest="filebase",default="phase_vs_antenna", help="Base file name , just _X.txt and _Y.txt are added to load [default %]")
   parser.add_option('-o','--outfile','--out_file','--pklfile','--out_pklfile','--out_pkl',dest="outfile",default=None, help="Output .pkl filename [default same as filebase]")
   parser.add_option('-t','--test_pickle_file',"--test_pickle",dest="test_pickle_file",default=None, help="Read pickle file and compare to text files (phase_vs_antenna_X.txt and phase_vs_antenna_Y.txt) [default %]")
   parser.add_option('-d','--debug','--verbose','--verb',action="store_true",dest="debug",default=False, help="More debugging information [default %]")
   parser.add_option('--pol_swap','--polarisation_swap','--swap_pols',action="store_true",dest="polarisation_swap",default=False, help="Swap polarisations as done in EDA2 [default %]")

   parser.add_option('-s','--sign','--sign_value',dest="sign_value",default=1, help="Sign value [default %]",type="int")

   # options of saving calibration solutions to text file :
   parser.add_option('--start_freq_channel','--start_freq_ch',dest="start_freq_channel",default=204, help="Start frequency channel [default %]",type="int")
   parser.add_option('--get_cal_from_db','--get_db_cal','--save_db_cal','--save_db_cal_file',dest="out_db_calfile",default=None, help="Save MCCS calibration to text file [default %]")
   parser.add_option('--save_n_channels_per_ant','--save_cal_per_ant','--save_n_channels',dest="save_channels_per_ant", default=1, help="Works with --save_db_cal_file and saves calibration solutions in specified number of channels per antenna [default %]", type=int)
   parser.add_option("--station_id", '--station', dest="station_id", default=2, help="Station ID (as in the station configuratio file) [default: %]", type=int )
   parser.add_option('--invamp','--ampinv',action="store_true",dest="invamp",default=False, help="Invert amplitudes [default %]")
   
   # DATABASE :
   parser.add_option('--fittime','--calsol_fittime','--fittime_db',dest='fittime',default=None, help="Fittime of calibration solutions to be used [default None]. Default None means that the latest set of calibration solutions in DB will be used")
   parser.add_option('--db_field_postfix','--amp_field_postfix',dest='db_field_postfix',default="_amp", help="Postfix in amplitude field in the database [default %s]")
      
   # fitting :
   parser.add_option('--fit_start_channel',dest="fit_start_channel",default=None, help="Start channel for the fit [default %]. Negative value -> first available channel", type=int )
   parser.add_option('--fit_end_channel',dest="fit_end_channel",default=None, help="End channel for the fit [default %]. Negative value -> highest available channel", type=int )
   parser.add_option('--fit_channel',dest="fit_channel",default=-1, help="Frequency channel to be fitted (excluded from the fit) [default %]. Negative value -> center channel", type=int )
   parser.add_option('--delta_channels',dest="delta_channels",default=-1,help="Number of channels around specific channel used to interpolat [default %]", type=int )

   parser.add_option('--fit_in_mhz','--mhz',action="store_true",dest="fit_in_mhz",default=False, help="Convert channel number to MHz [default %]")


#   parser.add_option('-c','--cal','--calibrator',dest="calibrator",default="HerA", help="Calibrator name [default %]")
#   parser.add_option('--meta_fits','--metafits',dest="metafits",default=None, help="Metafits file [default %]")

   (options, args) = parser.parse_args(sys.argv[idx:])
   
   if options.delta_channels is not None :
      if options.fit_start_channel is None :
         options.fit_start_channel = options.fit_channel - options.delta_channels

      if options.fit_end_channel is None :
         options.fit_end_channel = options.fit_channel + options.delta_channels


   return (options, args)


def test_calibration( pickle_file , sign_value=1 ) :
    coeff1 = read_calibration_phase_offsets("phase_vs_antenna_X.txt","phase_vs_antenna_Y.txt")
    
    out_f_x = open("test_X.tmp", "w")        
    out_f_y = open("test_Y.tmp", "w")
    for ant in range(0,coeff1.shape[0]):
        line = ( "%d %.2f\n" % (ant,numpy.angle( coeff1[ant,0,0] )*(180.00/math.pi)))
        out_f_x.write( line )        
        
        line = ( "%d %.2f\n" % (ant,numpy.angle( coeff1[ant,0,3] )*(180.00/math.pi)) )
        out_f_y.write( line )
        
    out_f_x.close()
    out_f_y.close()
    
    cmd = "diff phase_vs_antenna_X.txt test_X.tmp"
    print("%s" % (cmd))
    os.system( cmd )
    print("ANY DIFFERENCE ???")

    cmd = "diff phase_vs_antenna_Y.txt test_Y.tmp"
    print("%s" % (cmd))
    os.system( cmd )
    print("ANY DIFFERENCE ???")

    # check picke file :    
    coeff2 = get_calibration_coeff( calibration_file=pickle_file, sign_value=sign_value )
    out_f_x = open("test_X_pickle.tmp", "w")        
    out_f_y = open("test_Y_pickle.tmp", "w")
    for ant in range(0,coeff2.shape[0]):
        line = ( "%d %.2f\n" % (ant,numpy.angle( coeff2[ant,0,0] )*(180.00/math.pi)))
        out_f_x.write( line )        

        line = ( "%d %.2f\n" % (ant,numpy.angle( coeff2[ant,0,3] )*(180.00/math.pi)) )
        out_f_y.write( line )

    out_f_x.close()
    out_f_y.close()

    cmd = "diff phase_vs_antenna_X.txt test_X_pickle.tmp"
    print("%s" % (cmd))
    os.system( cmd )
    print("ANY DIFFERENCE ???")

    cmd = "diff phase_vs_antenna_Y.txt test_Y_pickle.tmp"
    print("%s" % (cmd))
    os.system( cmd )
    print("ANY DIFFERENCE ???")

    
    print() 
    print("Compare pickle to text files - any differences ???")
    for ant in range(0,coeff1.shape[0]) :
       for ch in range(0,coeff1.shape[1]) :
           for pol in range(0,coeff1.shape[2]) :
              if coeff1[ant,ch,pol] != coeff2[ant,ch,pol] :
                 print("DIFFERENCE !!!")
                 
    print("No difference ???")             

def save_calcoeff_to_text_files_per_ant( calibration_coef, out_text_file, start_freq_channel, n_channels, options ) :
   # print("ERROR : saving multiple channel to separate per-antenna text files is not yet implemented !")   
   ant_count = calibration_coef.shape[0]
   print("Saving calibration coefficients to output file %s , number of antennas = %d, channel range %d - %d" % (out_text_file,ant_count,start_freq_channel,start_freq_channel+n_channels))

   for ant in range(0,ant_count) :
      out_text_file_final = ( out_text_file % ant )
      out_f = open( out_text_file_final , "w" )
      out_f.write("# Antenna = %d\n" % (ant))
      line = "# FREQ_CH AMP_X PHASE_X AMP_Y PHASE_Y AMP_XY PHASE_XY AMP_YX PHASE_YX\n"
      out_f.write( line )
      
      for freq_channel in range(start_freq_channel,start_freq_channel+n_channels) :
         channel_index = freq_channel - start_freq_channel

         amp_x = numpy.abs( calibration_coef[ant,channel_index,0] ) 
         phase_x = numpy.angle( calibration_coef[ant,channel_index,0] )*(180.00/numpy.pi)

         amp_xy = numpy.abs( calibration_coef[ant,channel_index,1] ) 
         phase_xy = numpy.angle( calibration_coef[ant,channel_index,1] )*(180.00/numpy.pi)

         amp_yx = numpy.abs( calibration_coef[ant,channel_index,2] ) 
         phase_yx = numpy.angle( calibration_coef[ant,channel_index,2] )*(180.00/numpy.pi)

         amp_y = numpy.abs( calibration_coef[ant,channel_index,3] ) 
         phase_y = numpy.angle( calibration_coef[ant,channel_index,3] )*(180.00/numpy.pi)

         line = "%d %.8f %.4f %.8f %.4f %.8f %.4f %.8f %.4f\n" % (freq_channel,amp_x,phase_x,amp_y,phase_y,amp_xy,phase_xy,amp_yx,phase_yx)
         out_f.write( line )

      out_f.close()
      
      if options.fit_channel >= 0 :
         print("DEBUG : fitting amplitude around channel %d" % (options.fit_channel))
         
         out_fitted_file=out_text_file_final.replace(".txt","_fitted.txt")
         fit_amplitude.interpolate_and_save( out_text_file_final, fit_channel=options.fit_channel , fit_start_channel=options.fit_start_channel, fit_end_channel=options.fit_end_channel, outfile=out_fitted_file, fit_in_mhz=False  )
         print("DEBUG : saved fitted bandpass to output file %s" % (out_text_file_final))
   
   return    

def save_calcoeff_to_text_file( calibration_coef, out_text_file, start_freq_channel, n_channels=1 ) :
   for freq_channel in range(start_freq_channel,start_freq_channel+n_channels) :
      channel_index = freq_channel - start_freq_channel
      out_text_file_final = ( out_text_file % freq_channel )
      out_f = open( out_text_file_final , "w" )

      ant_count = calibration_coef.shape[0]
      print("Saving calibration coefficients for frequency channel %d to output file %s , number of antennas = %d" % (freq_channel,out_text_file_final,ant_count))

      out_f.write("# frequency channel %d = %.4f MHz\n" % (freq_channel,freq_channel*(400.00/512.00)))

      line = "# ANT AMP_X PHASE_X AMP_Y PHASE_Y AMP_XY PHASE_XY AMP_YX PHASE_YX\n"
      out_f.write( line )
   
      for ant in range(0,ant_count) :
         amp_x = numpy.abs( calibration_coef[ant,channel_index,0] ) 
         phase_x = numpy.angle( calibration_coef[ant,channel_index,0] )*(180.00/numpy.pi)
      
         amp_xy = numpy.abs( calibration_coef[ant,channel_index,1] ) 
         phase_xy = numpy.angle( calibration_coef[ant,channel_index,1] )*(180.00/numpy.pi)
      
         amp_yx = numpy.abs( calibration_coef[ant,channel_index,2] ) 
         phase_yx = numpy.angle( calibration_coef[ant,channel_index,2] )*(180.00/numpy.pi)
      
         amp_y = numpy.abs( calibration_coef[ant,channel_index,3] ) 
         phase_y = numpy.angle( calibration_coef[ant,channel_index,3] )*(180.00/numpy.pi)
           
         line = "%d %.8f %.4f %.8f %.4f %.8f %.4f %.8f %.4f\n" % (ant,amp_x,phase_x,amp_y,phase_y,amp_xy,phase_xy,amp_yx,phase_yx)
         out_f.write( line )
   
      out_f.close()
                 
if __name__ == '__main__':

    (options, args) = parse_options() 

    phase_offset_file_X = options.filebase + "_X.txt"
    phase_offset_file_Y = options.filebase + "_Y.txt"
    
    if options.polarisation_swap :
       phase_offset_file_tmp = phase_offset_file_X
       phase_offset_file_X = phase_offset_file_Y
       phase_offset_file_Y = phase_offset_file_tmp

    if options.outfile is None :
        options.outfile = options.filebase

    print("####################################################")
    print("PARAMTERS :")
    print("####################################################")
    print("File base       = %s -> files %s / %s" % (options.filebase,phase_offset_file_X,phase_offset_file_Y))
    print("Output pkl file = %s" % (options.outfile))
    print("polarisation_swap = %s" % (options.polarisation_swap))
    print("Sign_value        = %d" % (options.sign_value))
    print("Save MCCS DB calfile = %s" % (options.out_db_calfile))
    print("\tinvamp = %s" % (options.invamp))
    print("DB Amplitude field postfix = %s" % (options.db_field_postfix))
    print("####################################################")
    
    if options.out_db_calfile is not None :
       print("INFO : getting calibration from MCCS DB and saving to text file")
       
       # def get_calibration_coeff_from_db( start_frequency_channel, station_id, swap_pols=False, nof_antennas=256, n_channels=8, n_pols=4 , debug=True, apply_amplitudes=False, 
       #                            x_amp_par=None, y_amp_par=None, flag_antennas_list=None , sign_value=1 , invert_amplitudes=False ) : # use database    
       ( calibration_coef ) = get_calibration_coeff_from_db( options.start_freq_channel, options.station_id, swap_pols=False, n_channels=options.save_channels_per_ant, apply_amplitudes=True, 
                                                             invert_amplitudes=options.invamp, fittime=options.fittime, db_field_postfix=options.db_field_postfix )
       
       if options.save_channels_per_ant <= 1 :
          save_calcoeff_to_text_file( calibration_coef , options.out_db_calfile, start_freq_channel=options.start_freq_channel, n_channels=1 )
       else :
          save_calcoeff_to_text_files_per_ant( calibration_coef , options.out_db_calfile, start_freq_channel=options.start_freq_channel, n_channels=options.save_channels_per_ant, options=options )
    else :    
       if options.test_pickle_file is not None :
           test_calibration( options.test_pickle_file , sign_value=options.sign_value )
       else :
           (calibration_coef) = read_calibration_phase_offsets( phase_offset_file_X , phase_offset_file_Y, debug=options.debug )
           ant_count = calibration_coef.shape[0]
        
           if options.debug :
              print("Complex EDA-1 calibration coefficients:")
              for ant in range(0,ant_count) :
                  print("X  pol antenna%02d : %s" % (ant,calibration_coef[ant,:,0]))    
                  print("XY pol antenna%02d : %s" % (ant,calibration_coef[ant,:,1]))
                  print("YX pol antenna%02d : %s" % (ant,calibration_coef[ant,:,2]))
                  print("Y  pol antenna%02d : %s" % (ant,calibration_coef[ant,:,3]))
                  print()
                  print()

           save_coeff( calibration_coef, options.outfile )
    