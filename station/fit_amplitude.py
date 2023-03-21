# from builtins import str
import logging
import os
import sys
import copy
import math
from optparse import OptionParser,OptionGroup

import numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import interp1d

# DEBUG :
import pdb

channel2freq = (400.00/512.00)
debug=False

def parse_options(idx=0):
   usage="Usage: %prog [options]\n"
   usage+='\tRead calibration amplitudes from text file and fit \n'
   parser = OptionParser(usage=usage,version=1.00)
   parser.add_option('-s','--fit_start_channel',dest="fit_start_channel",default=None, help="Start channel for the fit [default %]. Negative value -> first available channel", type=int )
   parser.add_option('-e','--fit_end_channel',dest="fit_end_channel",default=None, help="End channel for the fit [default %]. Negative value -> highest available channel", type=int )
   parser.add_option('-c','--fit_channel',dest="fit_channel",default=None, help="Frequency channel to be fitted (excluded from the fit) [default %]. None or negative value -> fit all channels", type=int )
   parser.add_option('--delta_channels',dest="delta_channels",default=-1,help="Number of channels around specific channel used to interpolation or fit [default %]", type=int )
   parser.add_option('-i','--n_iterations','--iterations','--n_iter','--iter',dest="n_iterations",default=1,help="Number of fitting iterations [default %]", type=int )
   parser.add_option('-p','--polynomial_order','--poly_order','--pol_order',dest="polynomial_order",default=-1,help="Order of fitted polynomial, negative means use interpolation [default %]", type=int )
   parser.add_option('--do_not_exclude',dest="include_all_channels",action="store_true",default=False,help="Flag if all channels (including fit_channel) are included in the fit [default %s]")
   
   parser.add_option('--fit_in_mhz','--mhz',action="store_true",dest="fit_in_mhz",default=False, help="Convert channel number to MHz [default %]")
   
   # output file :
   parser.add_option('--outfile','--output_file',dest="outfile",default="fitted.txt", help="Name of output file [default %]")

   (options, args) = parser.parse_args(sys.argv[idx:])
   
   if options.delta_channels is not None and options.fit_channel is not None :
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
    phase_x_arr=[]
    phase_y_arr=[]
    count=0

    for line in data : 
        words = line.split(' ')

        if line[0] != "#" :
            freq_ch = int(words[0+0])
            amp_x = float(words[1+0])
            phase_x = float(words[2+0])
            amp_y = float(words[3+0])
            phase_y = float(words[4+0])
            
            # print "DEBUG : Adding %d / %.2f" % (ant_idx,phase_offset)
            
            freq_ch_arr.append( freq_ch )
            amp_x_arr.append( amp_x )
            amp_y_arr.append( amp_y )
            
            phase_x_arr.append( phase_x )
            phase_y_arr.append( phase_y )
            
            count += 1
        else :
           if words[1+0] == "Antenna" :
              antenna_id = int(words[3+0])

    file.close()

    return (antenna_id,freq_ch_arr,amp_x_arr,amp_y_arr,phase_x_arr,phase_y_arr,count)

def interpolate_amplitude( interpol_channel, freq_ch_arr, freq_mhz_arr, amp_arr, fit_in_mhz=False, start_channel=None, end_channel=None, include_all_channels=False,
                           polynomial_order=-1, n_iterations=1, max_chi2=1000000 ) :
   global debug
   x_axis=[] # without a point 
   x_axis_with=[] # with the channel itself 
   y_axis=[]
   
   # re-write, but skip interpol_channel channel and convert from channels to MHz (if required):
   in_count=len(freq_ch_arr) 
      
   for i in range(0,in_count) :
      in_range = True
   
#      if freq_ch_arr[i] != interpol_channel or include_all_channels :               
      if start_channel is not None and freq_ch_arr[i] < start_channel :
         in_range = False

      if end_channel is not None and freq_ch_arr[i] > end_channel :
         in_range = False
      
      if in_range :
         if freq_ch_arr[i] != interpol_channel or include_all_channels :
            y_axis.append( amp_arr[i] )
            
         if fit_in_mhz :
            if freq_ch_arr[i] != interpol_channel or include_all_channels :
               x_axis.append( freq_mhz_arr[i] )
            x_axis_with.append( freq_mhz_arr[i] )
         else :
            if debug :
               print("DEBUG : interpolate_amplitude - added channel %d (compared to %d - %d)" % (freq_ch_arr[i],start_channel,end_channel))
            if freq_ch_arr[i] != interpol_channel or include_all_channels :               
               x_axis.append( freq_ch_arr[i] )
               x_axis_with.append( freq_ch_arr[i] )
   
   # calculate return value - i.e. interpolated for a specified channel :
   interpol_freq_mhz = interpol_channel*channel2freq
   ret = None
   poly_coeffs = None
   interpol_function = None

   if polynomial_order > 0 :   
      iter=0
      # fitting polynomial :
      
      poly_coeffs=None
      x_axis_fit=copy.copy( x_axis )
      y_axis_fit=copy.copy( y_axis )
      
      if interpol_channel == 227 :
         print("TEST\n")
      
      while iter < n_iterations and len(x_axis_fit) > polynomial_order :
         poly_coeffs = np.polyfit( x_axis_fit, y_axis_fit, polynomial_order )
         out_amp_arr = np.poly1d(poly_coeffs)(x_axis_fit)
         if fit_in_mhz :
            ret = np.poly1d(poly_coeffs)( interpol_freq_mhz )
         else :
            ret = np.poly1d(poly_coeffs)( interpol_channel )

         max_resid=-10000000
         max_resid_i=-1         
         for i in range(0,len(x_axis_fit)) :
            resid = y_axis_fit[i] - out_amp_arr[i];
            if math.fabs(resid) > max_resid :
               max_resid = math.fabs(resid)
               max_resid_i = i
            
            print("RESIDUALS (iter=%d) : %.3f %.6f" % (iter,x_axis_fit[i],resid))


         if max_resid_i >= 0 :
            print("DEBUG : iteration = %d -> excluding value %.6f at %d" % (iter,y_axis_fit[max_resid_i],max_resid_i))
            x_axis_fit_new = []
            y_axis_fit_new = []   
            for i in range(0,len(x_axis_fit)) :
               if i != max_resid_i :
                  x_axis_fit_new.append(x_axis_fit[i])
                  y_axis_fit_new.append(y_axis_fit[i])
         
            x_axis_fit=copy.copy( x_axis_fit_new )
            y_axis_fit=copy.copy( y_axis_fit_new )
         else :
            # no outlier found -> exit the loop
            print("DEBUG : iteration = %d no outlier found -> existing the loop" % (iter));
            break
               
            
         iter += 1

      # output calculated for all the points         
      out_amp_arr = np.poly1d(poly_coeffs)(x_axis)   
         
      return ( ret , x_axis , out_amp_arr , fit_in_mhz, poly_coeffs, poly_coeffs )       
   else :
      # interpolation :
      interpol_function = interp1d( x_axis, y_axis, kind='cubic')   

      # calculate interpolated values (including the excluded channel or interest) - so that there are all channels :
      count = len(x_axis_with)   
      out_amp_arr=[]
      for i in range(0,count) :
         y_val = interpol_function( x_axis_with[i] )
         out_amp_arr.append( y_val )

      if fit_in_mhz :
         ret = interpol_function( interpol_freq_mhz )
      else :
         if debug :
            print("DEBUG : interpolation range : %.3f - %.3f , vs. channel = %d" % (min(x_axis),max(x_axis),interpol_channel))
         ret = interpol_function( interpol_channel )
      

      return ( ret , x_axis , out_amp_arr , fit_in_mhz, interpol_function, poly_coeffs )
  
def interpolate_and_save( input_file, fit_channel , fit_start_channel, fit_end_channel, outfile, fit_in_mhz=False, n_iterations=1, max_chi2=1000000  ) :     
    (antenna_id,freq_ch_arr,amp_x_arr,amp_y_arr,phase_x_arr,phase_y_arr,count) = read_amplitudes( input_file ) 
    print("INFO : antenna %d - read %d points from the input file %s. Interpolating channel %.3f in range %.3f - %.3f," % (antenna_id,len(freq_ch_arr),input_file,fit_channel,fit_start_channel,fit_end_channel))
    
    freq_mhz_arr=[]
    for channel in freq_ch_arr :
       freq_mhz = channel*channel2freq
       freq_mhz_arr.append( freq_mhz )
   
    # interpolate value at specified channel :    
    ( channel_value_x , x_axis_x , out_amp_arr_x , fit_in_mhz_x , interpol_function_x, poly_coeffs_x ) = interpolate_amplitude( fit_channel, freq_ch_arr, freq_mhz_arr, amp_x_arr, fit_in_mhz=fit_in_mhz, start_channel=fit_start_channel, end_channel=fit_end_channel, n_iterations=n_iterations, max_chi2=max_chi2 )
    ( channel_value_y , x_axis_y , out_amp_arr_y , fit_in_mhz_y , interpol_function_y, poly_coeffs_y ) = interpolate_amplitude( fit_channel, freq_ch_arr, freq_mhz_arr, amp_y_arr, fit_in_mhz=fit_in_mhz, start_channel=fit_start_channel, end_channel=fit_end_channel, n_iterations=n_iterations, max_chi2=max_chi2 )
    print("DEBUG : fitted value for channel %d is AMP_X = %.6f , AMP_Y = %.6f vs. recalculated %.6f / %.6f" % (fit_channel,channel_value_x,channel_value_y,interpol_function_x(fit_channel),interpol_function_y(fit_channel)))
    

    out_f = open( outfile, "w" )
    line = "# FREQ_CH AMP_X PHASE_X AMP_Y PHASE_Y\n" 
    line2 = ("# Fitted in channels\n")
    if fit_in_mhz_x :
       line = "# Freq[MHz] AMP_X PHASE_X AMP_Y PHASE_Y\n"
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
       
       if channel >= fit_start_channel and channel <= fit_end_channel :              
          y_value_x = interpol_function_x(x_value)
          y_value_y = interpol_function_y(x_value)
       else :
          y_value_x = amp_x_arr[i]
          y_value_y = amp_y_arr[i]
         
          
       line = ("%.3f %.6f %.6f %.6f %.6f\n" % (x_value,y_value_x,phase_x_arr[i],y_value_y,phase_y_arr[i]))   
       out_f.write( line )   

    out_f.close()    

def fit_all_channels( input_file, fit_in_mhz, polynomial_order, delta_channels, include_all_channels=False, n_iterations=1, max_chi2=1000000 ):
    (antenna_id,freq_ch_arr,amp_x_arr,amp_y_arr,phase_x_arr,phase_y_arr,count) = read_amplitudes( input_file ) 
    print("INFO : fitting all channels for antenna %d - read %d points from the input file %s." % (antenna_id,len(freq_ch_arr),input_file))
    
    freq_mhz_arr=[]
    for channel in freq_ch_arr :
       freq_mhz = channel*channel2freq
       freq_mhz_arr.append( freq_mhz )

    fitted_ch_values=[]   
    fitted_x_values=[]   
    fitted_y_values=[]   

    for i in range(0,len(freq_ch_arr)) :    
       fit_channel = freq_ch_arr[i]
       print("DEBUG : fitting channel %d" % (fit_channel))
       fit_start_channel = fit_channel - delta_channels
       fit_end_channel = fit_channel + delta_channels
    
       # interpolate value at specified channel :    
       ( channel_value_x , x_axis_x , out_amp_arr_x , fit_in_mhz_x , interpol_function_x, poly_coeffs_x ) = interpolate_amplitude( fit_channel, freq_ch_arr, freq_mhz_arr, amp_x_arr, fit_in_mhz=fit_in_mhz, start_channel=fit_start_channel, end_channel=fit_end_channel, include_all_channels=include_all_channels, polynomial_order=polynomial_order, n_iterations=n_iterations, max_chi2=max_chi2 )
       ( channel_value_y , x_axis_y , out_amp_arr_y , fit_in_mhz_y , interpol_function_y, poly_coeffs_y ) = interpolate_amplitude( fit_channel, freq_ch_arr, freq_mhz_arr, amp_y_arr, fit_in_mhz=fit_in_mhz, start_channel=fit_start_channel, end_channel=fit_end_channel, include_all_channels=include_all_channels, polynomial_order=polynomial_order, n_iterations=n_iterations, max_chi2=max_chi2 )
       print("DEBUG : interpolated value for channel %d is AMP_X = %.6f , AMP_Y = %.6f vs. recalculated %.6f / %.6f" % (fit_channel,channel_value_x,channel_value_y,channel_value_x,channel_value_y))
       
       fitted_ch_values.append( fit_channel )
       fitted_x_values.append( channel_value_x )
       fitted_y_values.append( channel_value_y )

    outfile=input_file.replace(".txt","_fitted.txt")
    out_f = open( outfile, "w" )
    line = "# FREQ_CH AMP_X PHASE_X AMP_Y PHASE_Y\n" 
    line2 = ("# Fitted in channels\n")
    if fit_in_mhz_x :
       line = "# Freq[MHz] AMP_X PHASE_X AMP_Y PHASE_Y\n"
       line2 = ("# Fitted in frequency [MHz]\n")

    out_f.write( line2 )
    out_f.write( line )
    
    for i in range(0,len( fitted_ch_values )) :
       x_value = fitted_ch_values[i]
       if fit_in_mhz :
          x_value = x_vale*channel2freq
       
       y_value_x = fitted_x_values[i]
       y_value_y = fitted_y_values[i]

       line = ("%.3f %.6f %.6f %.6f %.6f\n" % (x_value,y_value_x,phase_x_arr[i],y_value_y,phase_y_arr[i]))   
       out_f.write( line )   

    out_f.close()



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
    if options.fit_channel is not None :
       print("Fit channel                : %d" % (options.fit_channel))
    else :
       print("Fit channel                : ALL")
    if options.fit_start_channel is not None and options.fit_end_channel is not None :
       print("Channel range used for fit : %d - %d" % (options.fit_start_channel,options.fit_end_channel))    
    print("####################################")
    
    if options.fit_channel is not None :
       interpolate_and_save( input_file, fit_channel=options.fit_channel , fit_start_channel=options.fit_start_channel, fit_end_channel=options.fit_end_channel, 
                             outfile=options.outfile, fit_in_mhz=options.fit_in_mhz,  n_iterations=options.n_iterations  ) 
    else :
       # TODO : interpolate or fit all channels 
       fit_all_channels( input_file, fit_in_mhz=options.fit_in_mhz, polynomial_order=options.polynomial_order, delta_channels=options.delta_channels, include_all_channels=options.include_all_channels, n_iterations=options.n_iterations ) 
              