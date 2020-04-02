from __future__ import print_function
from datetime import datetime
from datetime import timedelta
import os, sys, getopt
import psycopg2
import numpy as np
import fit_phase_delay
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)

# Create connection to the calibration database.
# Do not have to use password here since DB is set up to recognise aavs user
conn = psycopg2.connect(database='aavs')
cur = conn.cursor()
cur.execute("""set timezone='UTC'""")  # Just do everything in UTC to avoid problems

# get latest solution for each fit_time
q = 'select fit_time,max(create_time) from calibration_fit group by fit_time order by fit_time;'
cur.execute(q)
fit_rows = cur.fetchall()

# get all calibration solutions that don't have a delay fit
# q='SELECT fit_time,create_time,ant_id FROM calibration_solution where x_delay is NULL and y_delay is NULL'
# cur.execute(q)
# sol_rows = cur.fetchall()

# process each row
for row in fit_rows:
    fit_time = row[0]
    create_time = row[1]
    logger.info('Processing fit time: %s, create time: %s' % (fit_time, create_time))
    for ant_id in range(256):
        q = 'SELECT x_pha,y_pha,x_delay,y_delay FROM calibration_solution where fit_time=%s and create_time=%s and ant_id=%s'
        cur.execute(q, (fit_time, create_time, ant_id))
        cal_info = cur.fetchall()
        # do sanity checks, are all phases zero?
        assert len(cal_info) == 1
        ph_x = np.array(cal_info[0][0])
        ph_y = np.array(cal_info[0][1])
        x_delay = cal_info[0][2]
        y_delay = cal_info[0][3]
        if x_delay is not None and y_delay is not None:
            logger.info('Skipping existing solution for ant %s: %f, %f' % (ant_id, x_delay, y_delay))
            continue
        if np.count_nonzero(ph_x) == 0:
            logger.info("X phases are all zero for ant %d, skipping" % (ant_id))
            fit_x = None
        else:
            fit_x = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(ph_x))
        if np.count_nonzero(ph_y) == 0:
            logger.info("Y phases are all zero for ant %d, skipping" % (ant_id))
            fit_y = None
        else:
            fit_y = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(ph_y))
        if fit_x is None or fit_y is None:
            logger.warn('Failed to fit delay for ant %d' % (ant_id))
            continue
        print("Fit time: %s, ant: %d, delay x: %f, delay y: %f" % (str(fit_time), ant_id, fit_x[1], fit_y[1]))
        # check for polarity reversed antennas
        if fit_x[0] > 2.0 or fit_y[0] > 2.0:
            logger.warning(
                'Ant: %d is polarity reversed. Zero freq intercept: x: %f, y: %f' % (ant_id, fit_x[0], fit_y[0]))
        q = 'UPDATE calibration_solution SET  x_delay = %s ,x_phase0 = %s, y_delay = %s, y_phase0 = %s where fit_time=%s and create_time=%s and ant_id=%s'
        cur.execute(q, (fit_x[1], fit_x[0], fit_y[1], fit_y[0], fit_time, create_time, ant_id))
    conn.commit()
