from __future__ import division
from builtins import range
from past.utils import old_div
from aavs_calibration.common import get_latest_calibration_solution
from pyaavs import station
import numpy as np
import logging
import time

channel_bandwidth = 400e6 / 512.0
nof_antennas_per_tile = 16
nof_antennas = 256
nof_stokes = 4


def normalize_complex_vector(vector):
    """ Normalise the complex coefficients to between 1 and -1 for both real and imaginary """

    normalised = np.zeros(vector.shape, dtype=np.complex64)

    max_val = 0.0
    for p in range(vector.shape[0]):
        for a in range(nof_antennas):
            if abs(vector[p][a].real) > max_val:
                max_val = abs(vector[p][a].real)
            if abs(vector[p][a].imag) > max_val:
                max_val = abs(vector[p][a].imag)

    for p in range(vector.shape[0]):
        for a in range(nof_antennas):
            normalised[p, a] = old_div(vector[p][a], max_val)

    return normalised


def get_latest_coefficients(start_channel_frequency, bandwidth):
    """ Read latest coefficients from database """

    # Calculate number of channels in beam and start channel ID
    nof_channels = int(old_div(bandwidth, channel_bandwidth))
    start_channel = int(old_div(start_channel_frequency, channel_bandwidth))

    # Grab the latest calibration solution
    # Amplitude and phase are in antenna/pol/channel order. Phases are in degrees
    amplitude, phase = get_latest_calibration_solution("AAVS1")

    # Remove spurious ampltidues
    amplitude[np.where(amplitude > 2)] = 1

    # Select required coefficient subset
    phase = phase[:, :, start_channel: start_channel + nof_channels]
    amplitude = amplitude[:, :, start_channel: start_channel + nof_channels]

    # Transform into complex numbers
    coefficients = amplitude * (np.cos(np.deg2rad(phase)) + np.sin(np.deg2rad(phase)) * 1j)

    # Normalise coefficients (not required for now)
    # coefficients = normalize_complex_vector(coefficients)

    # Create default calibration coefficient array
    # Index 0 is XX, 3 is YY. Indices 2 and 3 are the cross-pols, which should be initialised to 0
    coeffs = np.zeros((nof_antennas, nof_channels, nof_stokes), dtype=np.complex64)

    # Insert coefficients from database
    coeffs[:, :, 0] = coefficients[:, 0, :]
    coeffs[:, :, 3] = coefficients[:, 1, :]

    # Return values
    return coeffs


def check_station(config):
    """ Check if the station is properly formed """

    # Connect to tiles in station
    station.load_configuration_file(config)
    aavs_station = station.Station(station.configuration)
    aavs_station.connect()

    if aavs_station.properly_formed_station:
        return aavs_station
    else:
        return None


def update_calibration_coefficients(config):
    """ Update calibration coefficients in station """
    aavs_station = check_station(config)
    if aavs_station is not None:
        start_channel_frequency = aavs_station.configuration['observation']['start_frequency_channel']
        bandwidth = aavs_station.configuration['observation']['bandwidth']

        # Get coefficients and download to the station
        coeffs = get_latest_coefficients(start_channel_frequency, bandwidth)
        aavs_station.calibrate_station(coeffs)
    else:
        logging.info("Station not well formed")


if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %calibrate_station [options]")

    parser.add_option("--config", action="store", dest="config",
                      type="str", default=None, help="Configuration file [default: None]")
    parser.add_option("--period", action="store", dest="period",
                      type="int", default="0", help="Duty cycle in s for updating coefficients [default: 0 (once)]")
    (opts, args) = parser.parse_args(argv[1:])

    # Set logging
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    line_format = logging.Formatter("%(asctime)s - %(levelname)s - %(threadName)s - %(message)s")
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(line_format)
    log.addHandler(ch)

    # Check if a configuration file was defined
    if opts.config is None:
        log.error("A station configuration file is required, exiting")
        exit()

    # Update calibration coefficients
    update_calibration_coefficients(opts.config)

    # If period is defined, loop forever with given period
    if opts.period != 0:
        while True:
            logging.info("Waiting for {} seconds".format(opts.period))
            time.sleep(opts.period)
            update_calibration_coefficients(opts.config)

