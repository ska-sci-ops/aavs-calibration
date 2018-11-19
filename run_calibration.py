import logging
import os
import sys
import subprocess
import time
from datetime import datetime
from datetime import timedelta
from glob import glob

import numpy as np
import psycopg2

import fit_phase_delay

nyquist_freq = 400.0  # MHz
nof_antennas = 256
nof_channels = 512
start_channel = 64
code_version = """run_calibration_v1"""
username = os.getenv('USER')
dump_time = 1.9818086  # Correlation matrix dump time (seconds)

# Global objects for use in multiprocessing pool
show_output = False
nof_integrations = 1
directory = '.'

def read_gain_solution_file(filepath):
    """ Read coefficients from filepath """

    # Read file content. First lines contains header, so can be ignored
    with open(filepath, 'r') as f:
        content = f.readlines()

    # Each line contains an index, the time and the coefficient for each antenna
    entries = [value for value in content[0].split(' ') if value.strip() != '']
    entries = [float(x) for x in entries[2:]]

    # Return values
    return entries


def load_coefficients(directory, channel):
    # Load coefficient files for given file prefix
    xx_amp, xx_phase, yy_amp, yy_phase = None, None, None, None
    for f in glob("{}*.txt".format(os.path.join(directory, "chan_{}_selfcal".format(channel)))):
        if 'XX' in f and 'amp' in f:
            xx_amp = read_gain_solution_file(f)
        elif 'XX' in f and 'pha' in f:
            xx_phase = read_gain_solution_file(f)
        elif 'YY' in f and 'amp' in f:
            yy_amp = read_gain_solution_file(f)
        elif 'YY' in f and 'pha' in f:
            yy_phase = read_gain_solution_file(f)
        else:
            logging.warning("{} has an invalid filename format".format(f))

    # All files loaded, check that we have all required coefficients
    if not all([xx_amp, xx_phase, yy_amp, yy_phase]):
        logging.warn("Missing files in specified directory ({})".format(directory))
        exit()

    # Return values
    return xx_amp, xx_phase, yy_amp, yy_phase


def calibrate_channel(channel):
    """ Run calibration process on channel"""

    logging.info("Processing channel {}".format(channel))
    cal_script = "calibration_script.sh"  # This should be in PATH
    command = [cal_script, "-D", directory, 
                           "-T", str(dump_time), 
                           "-N", str(nof_integrations), 
                           "-k",
                           str(channel)]

    if show_output:
        subprocess.check_call(command, stdout=stdout, stderr=subprocess.STDOUT)
    else:
        with open(os.devnull, 'w') as output:
            subprocess.check_call(command, stdout=output, stderr=subprocess.STDOUT) 


def run_calibration(directory, nof_integrations, threads, show_output=False):
    """ Calibrate channels """

    # If more than 1 thread is required, use process pool
    if threads > 1:
        from multiprocessing.pool import ThreadPool

        p = ThreadPool(threads)
        p.map(calibrate_channel, range(start_channel, nof_channels))

    # Otherwise process serially
    else:
        for channel in range(start_channel, nof_channels):
            run_calibration(channel)

    # All done, cleanup up temporary files
    subprocess.check_call(['cleanup_temp_files.sh', '-D', directory])

# Main program
if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %run_calibration.py [options]")
    parser.add_option("-D", "--data_directory", action="store", dest="directory", default=".",
                      help="Data directory [default: .]")
    parser.add_option("-C", "--skip", action="store_true", dest="skip", default=False,
                      help="Skip the calibration step (useful if there are already solutions) [default: False]")
    parser.add_option("-S", "--show-output", action="store_true", dest="show_output", default=False,
                      help="Show output from calibration scripts, for debugging [default: False]")
    parser.add_option("-T", "--threads", action="store", dest="threads", default=4, type=int,
                      help="Number of thread to use [default: 4]")
    (conf, args) = parser.parse_args(argv[1:])

    # Set logging
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(format)
    log.addHandler(ch)

    # Sanity check, make sure directory exists
    if not os.path.exists(conf.directory) or not os.path.isdir(conf.directory):
        logging.error("Specified directory ({}) does not exist".format(conf.directory))
        exit(-1)

    # Set globals
    show_output = conf.show_output
    directory = conf.directory

    # Integrations over which to integrate
    nof_integrations = 1

    # Channel to calibrate
    t0 = time.time()
    xx_amp = np.zeros((nof_channels, nof_antennas))
    xx_phase = np.zeros((nof_channels, nof_antennas))
    yy_amp = np.zeros((nof_channels, nof_antennas))
    yy_phase = np.zeros((nof_channels, nof_antennas))
    x_delay = np.zeros((2, nof_antennas))
    y_delay = np.zeros((2, nof_antennas))

    # If not skipping calibration, generate calibration solutions
    if conf.skip is False:
        run_calibration(conf.directory, nof_integrations, conf.threads, conf.show_output)
    
    # At this point calibration solutions should be ready, read files and save locally
    for channel in range(start_channel, nof_channels):       
        try:
            x_amp, x_pha, y_amp, y_pha = load_coefficients(conf.directory, channel)
            xx_amp[channel, :] = x_amp
            xx_phase[channel, :] = x_pha
            yy_amp[channel, :] = y_amp
            yy_phase[channel, :] = y_pha
        except Exception as e:
            logging.warn("Unable to load data for channel {}: {}".format(channel, e.message))

    # Start timing
    t1 = time.time()

    # Now fit a delay to each pol of each antenna
    for a in range(nof_antennas):
        logging.info('Solving delays for ant {}'.format(a))
        delay_model_x = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(np.copy(xx_phase[:, a])))
        delay_model_y = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(np.copy(yy_phase[:, a])))
        if delay_model_x is None or delay_model_y is None:
            logging.warn("No solution for antenna {}".format(a))
        else:
            x_delay[:, a] = delay_model_x
            y_delay[:, a] = delay_model_y
            logging.info("Ph0/Delay x: {:.3f},{:.3f}, y: {:.3f},{:.3f}".format(delay_model_x[0], delay_model_x[1], delay_model_y[0], delay_model_y[1]))

    # Calibrated all channels of interest
    logging.info("Processed in {}".format(t1 - t0))

    exit(-1)

    # Create connection to the calibration database.
    # Do not have to use password here since DB is set up to recognise aavs user
    conn = psycopg2.connect(database='aavs')
    cur = conn.cursor()

    # Create solution
    # the local time for the dump is encoded in the directory name for now
    if conf.directory != '.':
        currdir = os.path.split(conf.directory)[-1]
    else:
        currdir = os.path.split(os.getcwd())[-1]  # the local time for the dump is encoded in the directory name for now

    # Get fit time from directory name    
    fit_time = datetime.strptime(currdir, "%Y_%m_%d-%H:%M") - timedelta(hours=8)

    logging.info('Creating solutions for fit_time {}'.format(fit_time))
    create_time = datetime.utcnow()
    cur.execute("""set timezone='UTC'""")  # Just do everything in UTC to avoid problems
    cur.execute('''INSERT INTO calibration_fit(create_time, fit_time, creator, code_version)
                   VALUES (%s, %s, %s, %s)''', (create_time, fit_time, username, code_version))

    # Create calibration solutions for each antenna
    for antenna in range(nof_antennas):
        x_amp = '{{{}}}'.format(', '.join([str(i) for i in xx_amp[:, antenna]]))
        x_pha = '{{{}}}'.format(', '.join([str(i) for i in xx_phase[:, antenna]]))
        y_amp = '{{{}}}'.format(', '.join([str(i) for i in yy_amp[:, antenna]]))
        y_pha = '{{{}}}'.format(', '.join([str(i) for i in yy_phase[:, antenna]]))

        q = '''INSERT INTO calibration_solution(fit_time, create_time, ant_id, x_amp, y_amp, x_pha, y_pha,x_delay,x_phase0,y_delay,y_phase0)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '''
        cur.execute(q, (fit_time, create_time, antenna, x_amp, y_amp, x_pha, y_pha, x_delay[1, antenna],
                        x_delay[0, antenna], y_delay[1, antenna], y_delay[0, antenna]))

    # Commit and close connection
    conn.commit()
    conn.close()
