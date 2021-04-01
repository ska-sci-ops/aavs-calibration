#! /usr/bin/env python

# sends send_channelised_data_continous command for range of channels , default is to send the command every 10 seconds which allows to collect 3 correlation matrices per channel
# send to separate HDF5 files (see suggested daq_receiver.py command below )
# to be used in conjunction with script :
# python /opt/aavs/bin/daq_receiver.py -i eth3:1 -K -d . -t 16 --correlator_samples=1835008 --nof_channels=1 --max-filesize_gb=0
# to collected correlated data 
# 

from pyaavs import station
import pyaavs.logger

import logging
import time

import eda1_tpm_pointing
import calibration
import numpy


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %station [options]")
    parser.add_option("--config", action="store", dest="config",
                      type="str", default=None, help="Configuration file [default: None]")

     # pointing parameters :
    parser.add_option("--az",'--azimuth','--azim',   action="store", dest="azimuth",   type="float", default=0.00,  help="Azimuth [deg] [default: %]")
    parser.add_option("--el",'--elevation','--elev', action="store", dest="elevation", type="float", default=90.00, help="Elevation [deg] [default: %]")

    # station calibration :
    parser.add_option('--calibrate_station','--cal_station','--calst', action="store_true", dest="calibrate_station",   default=False,  help="Calibrate station [default: %]")
    parser.add_option('--calibrate_file','--cal_file','--calfile', action="store", dest="calibration_file",   default=None,  help="Calibration file [default: %]")
    
    parser.add_option('--pol_swap','--polarisation_swap','--swap_pols',action="store_true",dest="polarisation_swap",default=False, help="Swap polarisations as done in EDA2 [default %]")
    
    # use MCCS database :
    parser.add_option('--caldb','--mccs','--mccs_db', action="store_true", dest="use_mccs_db",   default=False,  help="Get delays from MCCS database and convert to coefficients [default: %]")
    parser.add_option("--ch",'--channel','--chan', '--freq_channel', '--frequency_channel',  action="store", dest="freq_channel",   type="int", default=204,  help="Frequency channel [default: %]")

    (conf, args) = parser.parse_args(argv[1:])

    # Connect to station
    station.load_configuration_file(conf.config)
    station = station.Station(station.configuration)

    
    print("##############################################################################################")
    print("PARAMETERS:")
    print("##############################################################################################")
    print("Station ID        = %d" % (station.configuration['station']['id']))
    print("calibrate_station = %s" % (conf.calibrate_station))    
    print("calibration file  = %s" % (conf.calibration_file))
    print("polarisation swap = %s" % (conf.polarisation_swap))
    print("Use MCCS database = %s" % (conf.use_mccs_db))
    print("Frequency channel = %d" % (conf.freq_channel))
    print("##############################################################################################")
                      
    # Connect station (program, initialise and configure if required)
    station.connect()

    if conf.calibrate_station :
        print("ACTION : just calibrating EDA1/TPM station using file = %s" % (conf.calibration_file))
        
        calibration_coefficients = None
        if conf.use_mccs_db :
           print("INFO : station calibration using delays from the MCCS database (frequency channel = %d)" % (conf.freq_channel))
           
           # start channel is 4 channels below the central channel - same as in the .yml configuration file :
           calibration_coefficients = calibration.get_calibration_coeff_from_db( station_id=station.configuration['station']['id'], start_frequency_channel=(conf.freq_channel-4), swap_pols=conf.polarisation_swap )
        else :
           print("INFO : station calibration using provided pkl file (%s)" % (conf.calibration_file))
           calibration_coefficients = calibration.get_calibration_coeff( calibration_file = conf.calibration_file , swap_pols=conf.polarisation_swap )

        if calibration_coefficients is not None : 
           # send coefficients to the station : 
           station.calibrate_station( calibration_coefficients )                      
        else :
           print("ERROR : calibration coefficients could not be calculated -> could not calibrate station")
    else :
        print("ACTION : calibrating and pointing the EDA1/TPM station")
        # Call function to set delays in 16 MWA beamformers to point individual dipoles and get coefficients for 16 TPM17 inputs :
        ( eda1_pointing_coeff, meandelays ) = eda1_tpm_pointing.point_azel( conf.azimuth, conf.elevation )

        # calculate calibration coefficients : based on calibration and pointing coefficients :
        (final_coeff,pointing_coeff,calib_coeff) = calibration.calc_pointing_coeff( eda1_pointing_coeff )

        # send coefficients to the station : 
        # station.calibrate_station(calib_coeff)

        # show final coefficients :
        print("final_coeff = %s" % (final_coeff[:,0,0]))
        print("calib_coeff = %s" % (calib_coeff[:,0,0]))
        print("Number of mean_delays = %d" % (len(meandelays)))
        print("mean_delays = %s [picoseconds]" % (meandelays*1e12))

        
        # set mean delays :
        # Download coefficients
        t0 = time.time()
        for i, tile in enumerate(station.tiles):
           print("i = %d" % (i))
           delay      = meandelays
           delay_rate = meandelays*0.00
           delays_in_seconds = numpy.array([delay, delay_rate]).transpose()
       
           # return delay.transpose()
           # delays_in_seconds = np.array([ meandelays, meandelays * 0]).T.tolist()

           tile.set_pointing_delay(delays_in_seconds, 0)
        t1 = time.time()

        logging.info("Downloaded delays to tiles in {0:.2}s".format(t1 - t0))

        # Done downloading coefficient, switch calibration bank
        station.load_pointing_delay(2048)  # About 0.5 seconds
        logging.info("Loaded pointing delays")
