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


def get_latest_delays( nof_antennas=256):
    """ Read latest coefficients from database """

    # Create connection to the calibration database.
    conn = psycopg2.connect(database='aavs')
    cur = conn.cursor()

    cur.execute( '''SELECT MAX(fit_time) FROM calibration_fit''' )
    fittime = cur.fetchone()[0]
    print("Latest calibration was at %s" % (fittime))

    # Compute the required delays for the station beam channels

    # Grab antenna coefficients one by one (X pol)
    x_delays = numpy.zeros((nof_antennas, 2), dtype=numpy.float)
    for ant_id in range(nof_antennas):
        cur.execute(
            "SELECT fit_time, x_delay, x_phase0 from calibration_solution WHERE x_delay IS NOT NULL   AND ant_id={} AND fit_time='''{}'''".format(
                ant_id,fittime))
        x_delays[ant_id, :] = cur.fetchone()[1:]
        # print("Got fittime %s" % ())

    # Grab antenna coefficients one by one (Y pol)
    y_delays = numpy.zeros((nof_antennas, 2), dtype=numpy.float)
    for ant_id in range(nof_antennas):
        cur.execute(
            "SELECT fit_time, y_delay, y_phase0 from calibration_solution WHERE x_delay IS NOT NULL   AND ant_id={} AND fit_time='''{}'''".format(
                ant_id,fittime))
        y_delays[ant_id, :] = cur.fetchone()[1:]

    # Ready from database
    conn.close()

    # Return values
    return (x_delays,y_delays)

