#! /usr/bin/python

from __future__ import print_function
import logging
import os
import time
import warnings
from builtins import object
from builtins import range
from datetime import datetime

import numpy as np
from astropy import constants
from astropy.coordinates import Angle, AltAz, SkyCoord, EarthLocation, get_sun
from astropy.time import TimeDelta
from astropy.time.core import Time
from astropy.utils.exceptions import AstropyWarning

from pyaavs import station
import pyaavs.logger

try:
    import aavs_calibration.common as calib_utils
except ImportError:
    logging.debug("Could not load calibration database. Pointing cannot be performed")

warnings.simplefilter('ignore', category=AstropyWarning)

__author__ = 'Alessio Magro'

antennas_per_tile = 16

def read_antenna_list( filename, 
                       start_column=1, 
                       overwrite=False # overwrite default EDA1 antenna list 
                     ):
   file = open( filename , 'r' )
   data = file.readlines()

   x_arr = []
   y_arr = []
   z_arr = []
   count = 0
   for line in data : 
       words = line.split() # was ' ' , but when none is provided -> all white-space characters are ok !
       print( "DEBUG : words = %s (len = %d)" % (words,len(words)) )

       if line[0] == '#' :
          continue

       if line[0] != "#" :
           x = float(words[0+start_column])
           y = float(words[1+start_column])
           z = 0
           if len(words) >= 3 :
              z = float(words[2+start_column])

           x_arr.append(x)
           y_arr.append(y)
           z_arr.append(z)
           count = count + 1

   file.close()

   print("Read %d / %d / %d of x, y, z positions from file %s" % (len(x_arr),len(y_arr),len(z_arr),filename))

   return (np.array(x_arr), np.array(y_arr), np.array(z_arr) )



class Pointing(object):
    """ Helper class for generating beamforming coefficients """

    def __init__(self, station_identifier, station_config=None, antenna_location_file=None ):
        """ Pointing class, generates delay and delay rates to be downloaded to TPMs
        :param station_identifier: Calibration database station identifier
        :param station_config: Path to station configuration file
        """

        # Store arguments
        self._station_id = station_identifier
        self._station_config = station_config

        # Get station location
        info = calib_utils.get_station_information(self._station_id)
        self._longitude = info.longitude
        self._latitude = info.latitude
        self._nof_antennas = info.nof_antennas

        x = np.zeros( self._nof_antennas )
        y = np.zeros( self._nof_antennas )
        z = np.zeros( self._nof_antennas )
        # Grab antenna locations and create displacement vectors
        if antenna_location_file is not None :
            # assuming format : Ant001 X Y Z 
            x, y, z =  read_antenna_list( antenna_location_file )
        else :
            _, x, y = calib_utils.get_antenna_positions(self._station_id)

        self._displacements = np.full([self._nof_antennas, 3], np.nan)
        for i in range(self._nof_antennas):
            self._displacements[i, :] = x[i], y[i], z[i]

        # Get reference antenna location
        self._reference_antenna_loc = EarthLocation.from_geodetic(self._longitude, self._latitude, ellipsoid='WGS84')

        # Placeholder for delays and flag for below horizon
        self._below_horizon = False
        self._delays = None
        self._delay_rate = None
        

    # -------------------------------- POINTING FUNCTIONS -------------------------------------
    def point_to_sun(self, pointing_time=None):
        """ Generate delays to point towards the sun for the given time
        :param pointing_time: Time at which delays should be generated"""

        # If no time is specified, get current time
        if pointing_time is None:
            pointing_time = Time(datetime.utcnow(), scale='utc')
        else:
            pointing_time = Time(pointing_time, scale='utc')

        # Get sun position in RA, DEC and convert to Alz, Az in telescope reference frame
        sun_position = get_sun(pointing_time)
        alt, az = self._ra_dec_to_alt_az(sun_position.ra, sun_position.dec,
                                         pointing_time, self._reference_antenna_loc)

        # show alt,az :
        logging.info("Pointing to sun at (azim,elev) = ({},{}) [deg]".format(az,alt))

        # Compute delays
        self.point_array_static(alt, az)

    def point_array_static(self, altitude, azimuth, update_delays=True):
        """ Calculate the delay given the altitude and azimuth coordinates of a sky object as astropy angles
        :param altitude: altitude coordinates of a sky object as astropy angle
        :param azimuth: azimuth coordinates of a sky object as astropy angles
        :return: The (delay,delay rate) tuple for each antenna
        """

        # Type conversions if required
        altitude = self.convert_to_astropy_angle(altitude)
        azimuth = self.convert_to_astropy_angle(azimuth)

        # Set above horizon flag
        if altitude < 0.0:
            self._below_horizon = True
        else:
            self._below_horizon = False

        # Compute the delays
        new_delays = self._delays_from_altitude_azimuth(altitude.rad, azimuth.rad)
        new_delay_rate = new_delays * 0
        if update_delays :
           # could be : self._delays = new_delays - just not sure about python doing the same thing
           self._delays = self._delays_from_altitude_azimuth(altitude.rad, azimuth.rad)
           self._delay_rate = self._delays * 0
        else:
           print("INFO : Delays are not updated (self._delays not set)")
        
        # show delays :
        for i in range(0,len(self._delays)):
           print("Delay[%d] = %.4f [ns] = %.2f [ps]" % (i,new_delays[i]*1e9,new_delays[i]*1e12))

  
        return (new_delays)

    def point_array(self, right_ascension, declination, pointing_time=None, delta_time=1.0):
        """ Calculate the phase shift between two antennas which is given by the phase constant (2 * pi / wavelength)
        multiplied by the projection of the baseline vector onto the plane wave arrival vector
        :param right_ascension: Right ascension of source (astropy angle, or string that can be converted to angle)
        :param declination: Declination of source (astropy angle, or string that can be converted to angle)
        :param pointing_time: Time of observation (in format astropy time)
        :param delta_time: Delta timing for calculating delay rate
        :return: The (delay,delay rate) tuple for each antenna
        """

        # If no time is specified, get current time
        if pointing_time is None:
            pointing_time = Time(datetime.utcnow(), scale='utc')
        else:
            pointing_time = Time(pointing_time, scale='utc')

        # Type conversions if required
        right_ascension = self.convert_to_astropy_angle(right_ascension)
        declination = self.convert_to_astropy_angle(declination)

        # Calculate required delay
        alt, az = self._ra_dec_to_alt_az(right_ascension, declination,
                                         Time(pointing_time), self._reference_antenna_loc)

        # If required source is not above horizon, generate zeros
        if alt < 0.0:
            self._delays = np.zeros(self._nof_antennas)
            self._delay_rate = np.zeros(self._nof_antennas)
            self._below_horizon = True
            return

        # Generate delays from calculated altitude and azimuth
        self.point_array_static(altitude=alt, azimuth=az)        

        # Calculate required delay rate
        if delta_time == 0:
            self._delay_rate = self._delays * 0
        else:
            pointing_time = pointing_time + TimeDelta(delta_time, format='sec')
            alt, az = self._ra_dec_to_alt_az(right_ascension, declination,
                                             Time(pointing_time), self._reference_antenna_loc)
            
            # just calculate delays for the time after delta_time to calculate delay_rate, but do not update                                 
            next_delays = self.point_array_static(alt, az, update_delays=False)                                 
            self._delay_rate = next_delays - self._delays
            
            print("DEBUG : delay rates:")
            for i in range(0,len(self._delays)):
                print("Next delay[%d] = %.4f [ns] , current_delay = %.4f [ns] -> delay_rate = %.8f [ns/sec]" % (i,next_delays[i]*1e9,self._delays[i]*1e9,self._delay_rate[i]*1e9))


        # Set above horizon flag
        self._below_horizon = False

    def get_pointing_coefficients(self, start_channel, nof_channels):
        """ Get complex pointing coefficients from generated delays
        :param start_channel: Start channel index
        :param nof_channels: Number of channels starting with start_channel"""

        if self._delays is None:
            logging.error("No pointing delays generated")
            return

        # If below horizon flat is set, return 0s
        if self._below_horizon:
            return np.zeros((self._nof_antennas, nof_channels), dtype=np.complex)

        # Compute frequency range
        channel_bandwidth = 400e6 / 512.0
        frequencies = np.array([start_channel * channel_bandwidth + i * channel_bandwidth for i in range(nof_channels)])

        # Generate coefficients
        coefficients = np.zeros((self._nof_antennas, nof_channels), dtype=np.complex)
        for i in range(nof_channels):
            delays = 2.0 * np.pi * frequencies[i] * self._delays
            coefficients[:, i] = np.cos(delays) + 1j * np.sin(delays)

        # All done, return coefficients
        return coefficients

    def download_delays(self, delay_sign=1 ): # delay_sign parameter added at least for the testing stage, should later become -1 for good, once both stations have upgraded firmware
        """ Download generated delays to station """
        if self._delays is None:
            logging.error("Delays have not been computed yet")
            return

        if self._station_config is None:
            logging.error("Station configuration required to download delays")
            return

        # Connect to tiles in station
        try:
            station.load_configuration_file(self._station_config)
            aavs_station = station.Station(station.configuration)
            aavs_station.connect()

            # Form TPM-compatible delays
            tpm_delays = np.zeros((self._nof_antennas, 2))
            tpm_delays[:, 0] = delay_sign * self._delays
            tpm_delays[:, 1] = delay_sign * self._delay_rate # test -1 and it was much much worse !!!

            # Download to tiles
            t0 = time.time()
            for i, tile in enumerate(aavs_station.tiles):
                tile.set_pointing_delay(tpm_delays[i * antennas_per_tile: (i + 1) * antennas_per_tile], 0)
            t1 = time.time()
            logging.info("Downloaded delays to tiles in {0:.2}s".format(t1 - t0))

            # Load downloaded delays
            aavs_station.load_pointing_delay(2048)

        except Exception as e:
            logging.error("Could not configure or connect to station, not loading delays ({})".format(e))

    def _delays_from_altitude_azimuth(self, altitude, azimuth):
        """
        Calculate the delay using a target altitude Azimuth
        :param altitude: The altitude of the target astropy angle
        :param azimuth: The azimuth of the target astropy angle
        :return: The delay in seconds for each antenna
        """

        # Calculate transformation
        scale = np.array([np.cos(altitude) * np.sin(azimuth),
                          np.cos(altitude) * np.cos(azimuth),
                          np.sin(altitude)])

        # Apply to antenna displacements
        path_length = np.dot(scale, self._displacements.T)

        # Return frequency-independent geometric delays
        return np.multiply(1.0 / constants.c.value, path_length)

    @staticmethod
    def _ra_dec_to_alt_az(right_ascension, declination, time, location):
        """ Calculate the altitude and azimuth coordinates of a sky object from right ascension and declination and time
        :param right_ascension: Right ascension of source (in astropy Angle on string which can be converted to Angle)
        :param declination: Declination of source (in astropy Angle on string which can be converted to Angle)
        :param time: Time of observation (as astropy Time")
        :param location: astropy EarthLocation
        :return: Array containing altitude and azimuth of source as astropy angle
        """

        # Initialise SkyCoord object using the default frame (ICRS) and convert to horizontal
        # coordinates (altitude/azimuth) from the antenna's perspective.
        sky_coordinates = SkyCoord(ra=right_ascension, dec=declination, unit="deg")
        altaz = sky_coordinates.transform_to(AltAz(obstime=time, location=location))

        return altaz.alt, altaz.az

    @staticmethod
    def convert_to_astropy_angle(angle):
        """ Convert a number or string to an Astropy angle"""
        if type(angle) is not Angle:
            return Angle(angle)
        return angle

    def is_above_horizon(self, right_ascension, declination, pointing_time):
        """
        Determine whether the target is above the horizon, at the specified time for the reference antenna.
        :param right_ascension: The right ascension of the target as a astropy angle
        :param declination: The declination of the target as an astropy angle.
        :param pointing_time: The observation time as an astropy Time.
        :return: True if the target coordinates are above the horizon at the specified time, false otherwise.
        """
        alt, az = self._ra_dec_to_alt_az(Angle(right_ascension), Angle(declination), Time(pointing_time),
                                         self._reference_antenna_loc)

        return alt > 0.0



if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %point_station [options]")
    parser.add_option("--station", action="store", dest="station", default="AAVS1",
                      help="Station identifier (default: AAVS1)")
    parser.add_option("--config", action="store", dest="config",
                      default=None, help="Station configuration file to use")
    parser.add_option("--ra", action="store", dest="ra", type=str,
                      default="0", help="RA [default: 0]")
    parser.add_option("--dec", action="store", dest="dec", type=str,
                      default="0", help="DEC [default: 0]")
    parser.add_option("--static", action="store_true", dest="static", default=False,
                      help="Generate static beams based on theta and phi arguments [default: False]")
    parser.add_option("--altitude", action="store", dest="alt", type=str,
                      default="0", help="Altitude [default: 0]")
    parser.add_option("--azimuth", action="store", dest="az", type=str,
                      default="0", help="Azimuth [default: 0]")
    parser.add_option("--sun", action="store_true", dest="sun",
                      default=False, help="Point to sun [default: False]")
    parser.add_option("--time", action="store", dest="time", default="now",
                      help="Time at which to generate pointing delays. Format: dd/mm/yyyy_hh:mm [default: now]")
    parser.add_option("--antenna_locations", "--antenna_file","--locations", action="store", dest="antenna_location_file", default=None,
                      help="Antenna location file [default: %]")                      
    parser.add_option("--interval", "--track_time", "--tracking_time", dest="tracking_time", default=None,
                      help="How long to track in seconds, <0 -> infinite [default: %default]",type="int")
    parser.add_option("--sleep_time", "--track_delta", "--track_resolution", dest="tracking_resolution", default=30,
                      help="Tracking resolution in seconds [default: %default]",type="int")
    # 2022-12-18 : default delay sign changed to -1 which is correct for the new firmware (after sign of imaginary changed):                  
    parser.add_option("--delay_sign", "--firmware_delay_sign", dest="delay_sign", default=-1,
                      help="Sign of delays loaded to firmware [default: %default]",type="int")
    # 2022-12-18 : default delta_time=30 seconds the same as standard re-pointing time this delta time is used to calculate delay_rate as delay_rate = DELAYS(T+30secons) - DELAYS(T) :
    parser.add_option("--delta_time", "--dt_delay_rate", "--delay_rate_dt", dest="delta_time", default=1,
                      help="Delta time to calculate delay rate [default: %default]. When 0 [default] delay rate is not used",type="int")
                      
                      
                      

    (opts, args) = parser.parse_args(argv[1:])
    
    print("#########################################")
    print("PARAMETERS:")
    print("#########################################")
    print("delta_time = %d" % (opts.delta_time))
    print("#########################################")

    # Check if a configuration file was defined
    if opts.config is None or not os.path.exists(opts.config):
        log.error("A station configuration file is required, exiting")
        exit()

    # Parse time
    pointing_time = datetime.utcnow()
    if opts.time != "now":
        try:
            pointing_time = datetime.strptime(opts.starttime, "%d/%m/%Y_%H:%M")
        except:
            logging.info("Could not parse pointing time. Format should be dd/mm/yyyy_hh:mm")
            exit()

    # Generate pointing object
    pointing = Pointing(opts.station, opts.config, antenna_location_file=opts.antenna_location_file )

    # Generate delay and delay rates
    if opts.sun:
        if opts.tracking_time is not None :
           if opts.tracking_time < 0 :
              opts.tracking_time = 86400*365 # one year is close enough to inifinity
           start_uxtime = time.time()
           while time.time() < ( start_uxtime + opts.tracking_time ) :
              logging.info("Pointing to the sun uxtime = %d" % (time.time()))
              pointing.point_to_sun(pointing_time)
              
              # Download coefficients to station
              pointing.download_delays( delay_sign=opts.delay_sign )
              
              if opts.tracking_resolution > 0 :
                 logging.info("Waiting {} seconds before next pointing command".format(opts.tracking_resolution))
                 time.sleep( opts.tracking_resolution )
        else :
           logging.info("Pointing to the sun")
           pointing.point_to_sun(pointing_time)
           
           # Download coefficients to station
           pointing.download_delays( delay_sign=opts.delay_sign )

    elif opts.static:
        opts.alt, opts.az = Angle(opts.alt,"degree"), Angle(opts.az,"degree")
#        logging.info("Pointing to ALT {}, AZ {}".format(opts.alt, opts.az))
        logging.info("Pointing to ALT {}, AZ {} vs. radians {} , {}".format(opts.alt, opts.az,opts.alt.rad,opts.az.rad))
#        print("Pointing (az,el) = (%.4f,%.4f) [deg] = (%.4f,%.4f) [radians]" % (opts.alt,opts.az,opts.alt.rad,opts.az.rad))
        pointing.point_array_static(opts.alt, opts.az)
        
        # Download coefficients to station
        pointing.download_delays( delay_sign=opts.delay_sign )
    else:        
        opts.ra, opts.dec = Angle(opts.ra,"degree"), Angle(opts.dec,"degree")
        
        if opts.tracking_time is not None :
           if opts.tracking_time < 0 :
              opts.tracking_time = 86400*365 # one year is close enough to inifinity
           start_uxtime = time.time()
           while time.time() < ( start_uxtime + opts.tracking_time ) :
              logging.info("Pointing to RA {}, DEC {} at unix_time {} , delta_time {}".format(opts.ra, opts.dec,time.time(),opts.delta_time))
              pointing.point_array(opts.ra, opts.dec,  pointing_time=pointing_time, delta_time=opts.delta_time)
              
              # Download coefficients to station
              pointing.download_delays( delay_sign=opts.delay_sign )

              if opts.tracking_resolution > 0 :
                 logging.info("Waiting {} seconds before next pointing command".format(opts.tracking_resolution))
                 time.sleep( opts.tracking_resolution )
        else :        
           logging.info("Pointing to RA {}, DEC {} , delta_time {}".format(opts.ra, opts.dec, opts.delta_time))
           pointing.point_array(opts.ra, opts.dec,  pointing_time=pointing_time, delta_time=opts.delta_time)

           # Download coefficients to station
           pointing.download_delays( delay_sign=opts.delay_sign )
