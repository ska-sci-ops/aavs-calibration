#! /usr/bin/env python

# sends send_channelised_data_continous command for range of channels , default is to send the command every 10 seconds which allows to collect 3 correlation matrices per channel
# send to separate HDF5 files (see suggested daq_receiver.py command below )
# to be used in conjunction with script :
# python /opt/aavs/bin/daq_receiver.py -i eth3:1 -K -d . -t 16 --correlator_samples=1835008 --nof_channels=1 --max-filesize_gb=0
# to collected correlated data 
# 

from __future__ import print_function
from pyaavs.tile import Tile
from pyfabil import Device

from pyaavs import station
# import pyaavs.logger


from multiprocessing import Pool
from threading import Thread
import threading
import logging
import yaml
import time
import math
import sys
import os
import numpy

if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %station [options]")
    parser.add_option("--config", action="store", dest="config",
                      type="str", default=None, help="Configuration file [default: None]")
    parser.add_option("--port", action="store", dest="port",
                      type="int", default=None, help="Port [default: None]")
    parser.add_option("--lmc_ip", action="store", dest="lmc_ip",
                      default=None, help="IP [default: None]")
    parser.add_option("--lmc_port", action="store", dest="lmc_port",
                      type="int", default=None, help="Port [default: None]")
    parser.add_option("--lmc-mac", action="store", dest="lmc_mac",
                      type="int", default=None, help="LMC MAC address [default: None]")
    parser.add_option("-f", "--bitfile", action="store", dest="bitfile",
                      default=None, help="Bitfile to use (-P still required) [default: None]")
    parser.add_option("-t", "--tiles", action="store", dest="tiles",
                      default=None, help="Tiles to add to station [default: None]")
    parser.add_option("-P", "--program", action="store_true", dest="program",
                      default=False, help="Program FPGAs [default: False]")
    parser.add_option("-I", "--initialise", action="store_true", dest="initialise",
                      default=False, help="Initialise TPM [default: False]")
    parser.add_option("-C", "--program_cpld", action="store_true", dest="program_cpld",
                      default=False, help="Update CPLD firmware (requires -f option)")
    parser.add_option("-T", "--enable-test", action="store_true", dest="enable_test",
                      default=False, help="Enable test pattern (default: False)")
    parser.add_option("--use_teng", action="store_true", dest="use_teng",
                      default=None, help="Use 10G for LMC (default: None)")
    parser.add_option("--chan-trunc", action="store", dest="chan_trunc",
                      default=None, type="int", help="Channeliser truncation [default: None]")
    parser.add_option("-B", "--beamf_start", action="store_true", dest="beamf_start",
                      default=False, help="Start network beamformer")
    parser.add_option("--channel-integration-time", action="store", dest="channel_integ",
                      type="float", default=None, help="Integrated channel integration time [default: None]")
    parser.add_option("--beam-integration-time", action="store", dest="beam_integ",
                      type="float", default=None, help="Integrated beam integration time [default: None]")
    parser.add_option("--beamformer-scaling", action="store", dest="beam_scaling",
                      type="int", default=None, help="Beamformer scaling [default: None]")
    parser.add_option("--beam-start_frequency", action="store", dest="start_frequency_channel",
                      type="float", default=None, help="Beamformer scaling [default: None]")
    parser.add_option("--beam-bandwidth", action="store", dest="beam_bandwidth",
                      type="float", default=None, help="Beamformer scaling [default: None]")
                      
                      
    # specify channels to sweep and how long to stay on a single channel :
    parser.add_option("--start-channel", "--start_channel", action="store", dest="start_channel",
                      type="int", default=51, help="Start channel [default: %default]")
    parser.add_option("--end-channel", "--end_channel", "--stop_channel", "--stop-channel", action="store", dest="stop_channel",
                      type="int", default=155, help="Stop channel [default: %default]")
    parser.add_option("--step-channel", "--step_channel", '--step', action="store", dest="step_channel",
                      type="int", default=13, help="Step channel [default: %default] , 13 channels x (400/512) corresponds to ~10 MHz step")
    parser.add_option("--time_per_channel", "--inttime", "--dwell-time", action="store", dest="time_per_channel",
                      type="int", default=15, help="Time on channel in seconds [default: %default seconds]")

    parser.add_option("--start_ux", "--start_unixtime", action="store", dest="start_unixtime",
                      type="int", default=-1, help="Start unixtime [default: %default]")                      

    parser.add_option("--max_time_sec", "--total_time_sec", action="store", dest="total_time_seconds",
                      type="int", default=-1, help="Total time in seconds, <=0 means inifite until killed [default: %default]")
                      
                                            
    parser.add_option("--add_uav_channels", "--include_uav_channels", action="store_true", dest="add_uav_channels", default=False, help="Include UAV channels at the very end")
    parser.add_option("--channel_filename", "--channel_file", action="store", dest="channel_file", default="current_channel.txt", help="Channel ID [default %default]")    

    parser.add_option("--n_iterations", "--n_iter", "--iterations", action="store", dest="n_iterations", default=1, help="Number of iterations over channels, <=0 means infinite loop [default %default]",type="int")
    parser.add_option("--daq_exit_file","--exit_file",action="store", dest="daq_exit_file", default="daqExit.txt", help="Daq exit filename causes script to stop and quit [default %default]")
                                            
                                                      
    (conf, args) = parser.parse_args(argv[1:])

    # Connect to station
    station.load_configuration_file(conf.config)
    aavs_station = station.Station(station.configuration)
    aavs_station.connect()

    # Set current thread name
    threading.currentThread().name = "Station"

    
#    if conf.start_unixtime <= 0 :
#       print "ERROR : start unixtime = %d (not specified) -> cannot continue"
#       exit()
       
#    print("Running channels_sweep for station %s" % (configuration['station']['name']))
    
#    if conf.initialise :
#       if configuration['station']['name'].upper() == "EDA2" :
#          print("Initialisation required calling set_preadu_attenuation(0) (as for EDA2) :")
#          aavs_station.set_preadu_attenuation(0)
#          print("set_preadu_attenuation(0) executed")
#       elif configuration['station']['name'].upper() == "AAVS2":
#          print("Initialisation required calling set_preadu_attenuation(0) (as for AAVS2) :")
#          aavs_station.set_preadu_attenuation(10)
#          print("set_preadu_attenuation(10) executed")
#          
#          aavs_station.equalize_preadu_gain(16)
#          print("aavs_station.equalize_preadu_gain(16) executed")
#       else :
#          print("WARNING : unknown station name = %s -> dont know how to optimally initialise" % (configuration['station']['name']))
          
    
    # first wait until specified time 
    if conf.start_unixtime > 0 :
       wait_time = int( conf.start_unixtime - time.time() )
       print("Waiting %d seconds to start data acuisition ..." % (wait_time))
       time.sleep( wait_time )   

    # just to collect some initial data which is bad before collecting proper data later in the loop        
    if True :
       # probably not needed anymore :
       aavs_station.send_channelised_data_continuous( 30 )
       time.sleep( 20 )
    
    
    # running a loop over specified channel range :
    channel_list = []
    if conf.start_channel > 0 and conf.stop_channel > 0 :
       print("Running a loop over channels %d - %d" % (conf.start_channel,conf.stop_channel))
       channel_list = numpy.arange( conf.start_channel,conf.stop_channel,conf.step_channel )
    else :
       print("WARNING : no channel range specified")
    
    if conf.add_uav_channels :
       channel_list = numpy.append( channel_list, [ 64, 90, 141, 204, 294, 410 ] )

    last_channel = -1
    # check if last channel file exists (means that script has crashed and should possibly be continued rather than re-started from first channel as this may cause - de-synchronisation with a 
    # daq loop script in ( ~/aavs-calibration/sensitivity/daq/daq_sensitivity.sh )
    if os.path.exists( conf.channel_file ) :
       channel_file = open( conf.channel_file , 'r' )
       data = channel_file.readlines()
       channel_file.close()
       
       last_channel = int( data[0] ) 
       print("Detected %s file and read last channel = %d -> starting from next channel" % (conf.channel_file,last_channel))
    
    iterations = 0
    start_time = time.time()
    end_time   = start_time + 1000*86400 # 1000 days ~= infinity 
    if conf.total_time_seconds > 0 :
       end_time   = start_time + conf.total_time_seconds
    curr_time = start_time

    print("Start time ux = %d , end_time = %d , curr_time = %d" % (start_time,end_time,curr_time))
    
    continue_loop = True
    while continue_loop and ( iterations < conf.n_iterations or conf.n_iterations <= 0 ) and curr_time < end_time :
        print("%d - iteration over channels" % (iterations))
    
        for channel in channel_list :
            print("Stopping previous and starting channel %d" % (channel))
            aavs_station.send_channelised_data_continuous( channel )
            
            if channel > last_channel :            
               print("%.4f : Staying on channel %d for %d seconds ..." % (time.time(),channel,conf.time_per_channel))
        
               # saving current channel to file :
               channel_f = open( conf.channel_file , "w")
               channel_f.write( ("%d" % (channel)) )
               channel_f.close()
        
               time.sleep( conf.time_per_channel )
        
               # stop transimission is commented out because it stops and then aavs_station.send_channelised_data_continuous does not wake it up again (see e-mails with Alessio starting on Thu 8/29/2019 3:20 PM )
               # aavs_station.stop_data_transmission()
               # print "Waiting 5 seconds for things to settle down ..."
               # time.sleep( 5 )
            else :
               print("Channel %d skipped because smaller than last_channel = %d (continuation of the interrupted loop)" % (last_channel))
                
        # reseting last_channel - it is only for the first iteration in case continuing "broken" iteration
        last_channel = -1

        iterations += 1
        curr_time = time.time()
        print("current ux time = %d vs. end time = %d" % (curr_time,end_time))
        
        # checking for existance of a "STOP_FILE"
        if os.path.exists( conf.daq_exit_file ) :
           print("File %s found -> exiting loop now" % (conf.daq_exit_file))
           continue_loop = False

    
    # stop transimissions before exit   
    aavs_station.stop_data_transmission()
    
    print("Loop over channels executed -> exiting script now")
    exit()
    