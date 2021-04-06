from __future__ import division
from future import standard_library
standard_library.install_aliases()
# from builtins import range
# from past.utils import old_div
# from pyaavs import station
import numpy 
import psycopg2
import logging
import time


def get_latest_delays( station_id, nof_antennas=256, debug=True ):
    """ Read latest coefficients from database """

    # Create connection to the calibration database.
    conn = psycopg2.connect(database='aavs')
    cur = conn.cursor()

#    szSQL = "SELECT MAX(calibration_fit.fit_time) FROM calibration_fit,calibration_solution WHERE calibration_fit.fit_time=calibration_solution.fit_time and x_delay IS NOT NULL"
    szSQL = "SELECT MAX(fit_time) FROM calibration_solution WHERE x_delay IS NOT NULL AND station_id={}".format(station_id)
    if debug :
       print("DEBUG : %s" % (szSQL))
    cur.execute( szSQL )
    fittime = cur.fetchone()[0]
    print("Latest calibration was at %s" % (fittime))

    # Compute the required delays for the station beam channels

    # Grab antenna coefficients one by one (X pol)
    x_delays = numpy.zeros((nof_antennas, 2), dtype=numpy.float)
    for ant_id in range(nof_antennas):
        szSQL = "SELECT fit_time, x_delay, x_phase0 from calibration_solution WHERE x_delay IS NOT NULL AND station_id={} AND ant_id={} AND fit_time='''{}'''".format(station_id,ant_id,fittime)
        if debug :
           print("%d : %s" % (ant_id,szSQL))
           
        cur.execute( szSQL )
        x_delays[ant_id, :] = cur.fetchone()[1:]
        # print("Got fittime %s" % ())

    # Grab antenna coefficients one by one (Y pol)
    y_delays = numpy.zeros((nof_antennas, 2), dtype=numpy.float)
    for ant_id in range(nof_antennas):
        szSQL = "SELECT fit_time, y_delay, y_phase0 from calibration_solution WHERE x_delay IS NOT NULL AND station_id={} AND ant_id={} AND fit_time='''{}'''".format( station_id,ant_id,fittime)
        if debug :
           print("%d : %s" % (ant_id,szSQL))
           
        cur.execute( szSQL )
        y_delays[ant_id, :] = cur.fetchone()[1:]

    # Ready from database
    conn.close()

    # Return values
    return (x_delays,y_delays)

def get_latest_amps( station_id, freq_channel, nof_antennas=256, debug=True ):
    """ Read latest coefficients from database """

    # Create connection to the calibration database.
    conn = psycopg2.connect(database='aavs')
    cur = conn.cursor()

#    szSQL = "SELECT MAX(calibration_fit.fit_time) FROM calibration_fit,calibration_solution WHERE calibration_fit.fit_time=calibration_solution.fit_time and x_delay IS NOT NULL"
    szSQL = "SELECT MAX(fit_time) FROM calibration_solution WHERE x_delay IS NOT NULL AND station_id={}".format(station_id)
    if debug :
       print("DEBUG : %s" % (szSQL))
    cur.execute( szSQL )
    fittime = cur.fetchone()[0]
    print("Latest calibration was at %s" % (fittime))

    # Compute the required delays for the station beam channels

    # Grab antenna coefficients one by one (X pol)
    x_amp = numpy.zeros((nof_antennas), dtype=numpy.float)
    for ant_id in range(nof_antennas):
        szSQL = "SELECT x_amp from calibration_solution WHERE x_delay IS NOT NULL AND station_id={} AND ant_id={} AND fit_time='''{}'''".format(station_id,ant_id,fittime)
        if debug :
           print("%d : %s" % (ant_id,szSQL))
           
        cur.execute( szSQL )
        all_amps = cur.fetchone()[0]
        x_amp[ant_id] = all_amps[freq_channel]
        # print("Got fittime %s" % ())

    # Grab antenna coefficients one by one (Y pol)
    y_amp = numpy.zeros((nof_antennas), dtype=numpy.float)
    for ant_id in range(nof_antennas):
        szSQL = "SELECT y_amp from calibration_solution WHERE x_delay IS NOT NULL AND station_id={} AND ant_id={} AND fit_time='''{}'''".format( station_id,ant_id,fittime)
        if debug :
           print("%d : %s" % (ant_id,szSQL))
           
        cur.execute( szSQL )
        all_amps = cur.fetchone()[0]
        y_amp[ant_id] = all_amps[freq_channel]

    # Ready from database
    conn.close()

    # Return values
    return (x_amp,y_amp)

