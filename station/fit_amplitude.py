# from builtins import str
import logging
import os
import sys
from optparse import OptionParser,OptionGroup

import numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import interp1d

channel2freq = (400.00/512.00)

def parse_options(idx=0):
   usage="Usage: %prog [options]\n"
   usage+='\tRead calibration amplitudes from text file and fit \n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-s','--fit_start_channel',dest="fit_start_channel",default=None, help="Start channel for the fit [default %]. Negative value -> first available channel", type=int )
   parser.add_option('-e','--fit_end_channel',dest="fit_end_channel",default=None, help="End channel for the fit [default %]. Negative value -> highest available channel", type=int )
   parser.add_option('-c','--fit_channel',dest="fit_channel",default=-1, help="Frequency channel to be fitted (excluded from the fit) [default %]. Negative value -> center channel", type=int )
   parser.add_option('--delta_channels',dest="delta_channels",default=-1,help="Number of channels around specific channel used to interpolat [default %]", type=int )
   
   parser.add_option('--fit_in_mhz','--mhz',action="store_true",dest="fit_in_mhz",default=False, help="Convert channel number to MHz [default %]")
   
   # output file :
   parser.add_option('--outfile','--output_file',dest="outfile",default="fitted.txt", help="Name of output file [default %]")

   (options, args) = parser.parse_args(sys.argv[idx:])
   
   if options.delta_channels is not None :
      if options.fit_start_channel is None :
         options.fit_start_channel = options.fit_channel - options.delta_channels

      if options.fit_end_channel is None :
         options.fit_end_channel = options.fit_channel + options.delta_channels

   return (options, args)


def read_amplitudes( filename="calsol_ant000.txt" ) :
    print("DEBUG : reading calibration solution file %s" % (filename))

    file=open( filename , 'r' )
    data=file.readlines()

    antenna_id=-1
    freq_ch_arr=[]
    amp_x_arr=[]
    amp_y_arr=[]
    count=0

    for line in data : 
        words = line.split(' ')

        if line[0] != "#" :
            freq_ch = int(words[0+0])
            amp_x = float(words[1+0])
            amp_y = float(words[3+0])
            
            # print "DEBUG : Adding %d / %.2f" % (ant_idx,phase_offset)
            
            freq_ch_arr.append( freq_ch )
            amp_x_arr.append( amp_x )
            amp_y_arr.append( amp_y )
            
            count += 1
        else :
           if words[1+0] == "Antenna" :
              antenna_id = int(words[3+0])

    file.close()

    return (antenna_id,freq_ch_arr,amp_x_arr,amp_y_arr,count)

def interpolate_amplitude( interpol_channel, freq_ch_arr, freq_mhz_arr, amp_arr, fit_in_mhz=False, start_channel=None, end_channel=None ) :
   x_axis=[]
   y_axis=[]
   
   # re-write, but skip interpol_channel channel and convert from channels to MHz (if required):
   in_count=len(freq_ch_arr) 
      
   for i in range(0,in_count) :
      in_range = True
   
      if freq_ch_arr[i] != interpol_channel :               
         if start_channel is not None and freq_ch_arr[i] < start_channel :
            in_range = False

         if end_channel is not None and freq_ch_arr[i] > end_channel :
            in_range = False
      
         if in_range :
            y_axis.append( amp_arr[i] )
            if fit_in_mhz :
               x_axis.append( freq_mhz_arr[i] )
            else :
               x_axis.append( freq_ch_arr[i] )
   
   
   interpol_function = interp1d( x_axis, y_axis, kind='cubic')   

   # calculate interpolated values 
   count = len(x_axis)   
   out_amp_arr=[]
   for i in range(0,count) :
      y_val = interpol_function( x_axis[i] )
      out_amp_arr.append( y_val )

   # calculate return value - i.e. interpolated for a specified channel :
   interpol_freq_mhz = interpol_channel*channel2freq      
   ret = None
   if fit_in_mhz :
      ret = interpol_function( interpol_freq_mhz )
   else :
      ret = interpol_function( interpol_channel )
      

   return ( ret , x_axis , out_amp_arr , fit_in_mhz, interpol_function )
  
     

# main program
if __name__ == "__main__":
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    start_idx=0
    input_file="calsol_ant000.txt"
    if len(sys.argv) > 1:
       input_file = sys.argv[1]
       start_idx=1

    (options, args) = parse_options( start_idx ) 
    print("####################################")
    print("PARAMETERS:")
    print("####################################")
    print("Fit channel                : %d" % (options.fit_channel))
    print("Channel range used for fit : %d - %d" % (options.fit_start_channel,options.fit_end_channel))    
    print("####################################")
    
    (antenna_id,freq_ch_arr,amp_x_arr,amp_y_arr,count) = read_amplitudes( input_file ) 
    print("INFO : antenna %d - read %d points from the input file %s" % (antenna_id,len(freq_ch_arr),input_file))
    
    freq_mhz_arr=[]
    for channel in freq_ch_arr :
       freq_mhz = channel*channel2freq
       freq_mhz_arr.append( freq_mhz )
   
    # interpolate value at specified channel :    
    ( channel_value_x , x_axis_x , out_amp_arr_x , fit_in_mhz_x , interpol_function_x ) = interpolate_amplitude( options.fit_channel, freq_ch_arr, freq_mhz_arr, amp_x_arr, fit_in_mhz=False, start_channel=options.fit_start_channel, end_channel=options.fit_end_channel )
    ( channel_value_y , x_axis_y , out_amp_arr_y , fit_in_mhz_y , interpol_function_y ) = interpolate_amplitude( options.fit_channel, freq_ch_arr, freq_mhz_arr, amp_y_arr, fit_in_mhz=False, start_channel=options.fit_start_channel, end_channel=options.fit_end_channel )
    print("DEBUG : fitted value for channel %d is AMP_X = %.6f , AMP_Y = %.6f vs. recalculated %.6f / %.6f" % (options.fit_channel,channel_value_x,channel_value_y,interpol_function_x(options.fit_channel),interpol_function_y(options.fit_channel)))
    

    out_f = open( options.outfile, "w" )
    line = "# Freq_channel AMP_X AMP_Y\n" 
    line2 = ("# Fitted in channels\n")
    if fit_in_mhz_x :
       line = "# Freq[MHz] AMP_X AMP_Y\n"       
       line2 = ("# Fitted in frequency [MHz]\n")

    out_f.write( line2 )
    out_f.write( line )    
    
    for i in range(0,len( freq_ch_arr )) :
       channel = freq_ch_arr[i]
       x_value = freq_ch_arr[i]
       if fit_in_mhz_x :
          x_value = freq_mhz_arr[i]

       y_value_x = None
       y_value_y = None
       
       if channel >= options.fit_start_channel and channel <= options.fit_end_channel :              
          y_value_x = interpol_function_x(x_value)
          y_value_y = interpol_function_y(x_value)
       else :
          y_value_x = amp_x_arr[i]
          y_value_y = amp_y_arr[i]
         
          
       line = ("%.3f %.6f %.6f\n" % (x_value,y_value_x,y_value_y))   
       out_f.write( line )   

    out_f.close()    
    