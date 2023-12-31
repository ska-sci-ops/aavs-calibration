from __future__ import print_function
import logging
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from datetime import timedelta
from glob import glob

import numpy as np

psycopg2_found=False
try : 
   import psycopg2
   psycopg2_found=True
except :
   print("WARNING : package psycopg2 is not available -> will not be able to save results to the database if required")
   pass   


import fit_phase_delay

# import pyaavs.logger
aavs_calibration_common_ok=False
try :
   from aavs_calibration.common import add_new_calibration_solution
   aavs_calibration_common_ok=True
except :
   print("WARNING : package aavs_calibration.common is not available -> will not save results to the database if required")
   aavs_calibration_common_ok=False
   

nyquist_freq = 400.0  # MHz
nof_antennas = 256
total_channels = 512
start_channel = 1
code_version = """run_calibration_v1"""
username = os.getenv('USER')
dump_time = 1.9818086  # Correlation matrix dump time (seconds)

# Global objects for use in multiprocessing pool
show_output = False
nof_integrations = 1
directory = '.'

g_station_name = "EDA2"
conf = None # command line options

def read_gain_solution_file(filepath):
    """ Read coefficients from filepath """

    # Read file content. First lines contains header, so can be ignored
    with open(filepath, 'r') as f:
        content = f.readlines()

    # Each line contains an index, the time and the coefficient for each antenna
    entries = [0] * nof_antennas
    try:
        entries = [value for value in content[0].split(' ') if value.strip() != '']
        entries = [float(x) for x in entries[2:]]
    except:
        pass

    # Return values
    return entries


def load_coefficients(directory, channel):
    """ Load calibration coefficients from generated files"""

    # Set defaults
    xx_amp = np.ones(nof_antennas)
    xx_phase = np.zeros(nof_antennas)
    yy_amp = np.ones(nof_antennas)
    yy_phase = np.zeros(nof_antennas)

    file_pattern = "{}*.txt".format(os.path.join(directory, "chan_{}_selfcal".format(channel)))

    # Load coefficient files for given file prefix
    for f in glob(file_pattern):
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

    # All f1les loaded, check that we have all required coefficients
    if not all([xx_amp, xx_phase, yy_amp, yy_phase]):
        logging.warning("Missing files in specified directory ({}) for channel {}".format(directory, channel))

    # Return values
    return xx_amp, xx_phase, yy_amp, yy_phase


def calibrate_channel(channel) : # ,station_name="EDA2"): - parameters do not work in multi-threaded version, I used global variable to pass correct station_name (the same for the whole processing)
    """ Run calibration process on channel"""
    global g_station_name
    global conf 
    
    station_name = g_station_name
    options      = conf         

    logging.info("Processing channel {}".format(channel))
    # test if with full path it will work :
    cal_script = "/home/aavs/aavs-calibration/calibration_script.sh"  # This should be in PATH
    command = [cal_script, "-D", directory,
               "-T", str(dump_time),
               "-N", str(nof_integrations),
               "-S", station_name,
               "-k"               
              ]
    # WARNING : do not add -x and -y options here as they are channel dependent and need to be calculated for each channel (cannot use global value good for all channels !!!)              
    #           this should really be done inside the calibration_script.sh 
              
    # dynamically added if required by options :
    if options.calibration_object is not None :
       command.append( "-m" )
       command.append( options.calibration_object )
       logging.info("Added calibration object option -m {}".format(options.calibration_object))
       
    if not options.do_calibration :
       logging.info("Do not execute calibration")
       command.append( "-c" )
       command.append( "0" )
       
    # WARNING : channel MUST GO LAST ADD PARAMETERS EARLIER BUT NOT AFTER !!!
    #           that's why I've moved it here to avoid coding errors :
    command.append( str(channel) )
    
    cmdline=""
    for i in range(0,len(command)):
        cmdline += command[i]
        cmdline += " "

    logging.info("Command : {}".format(cmdline))
    if show_output:
        # # MS : testing call instead of check_call to avoid crash of the whole script due to crash on a single channel :
        subprocess.call(command, stdout=stdout, stderr=subprocess.STDOUT)
    else:
        with open(os.devnull, 'w') as output:
            # # MS : testing call instead of check_call to avoid crash of the whole script due to crash on a single channel :
            subprocess.call(command, stdout=output, stderr=subprocess.STDOUT)


def run_calibration(directory, nof_channels, threads, station_name="EDA2", update_last_calibration=True, post_calibration=True ):
    """ Calibrate channels """
    global g_station_name
    global conf
    # set value of global variable before call to calibrate_channel in either single or multi-threaded version 
    g_station_name = station_name 
    options      = conf

    # If more than 1 thread is required, use process pool
    if threads > 1:
        logging.info('Multithreaded processing of channels')
        from multiprocessing.pool import ThreadPool

        p = ThreadPool(threads)
        p.map(calibrate_channel, range(start_channel, nof_channels))

    # Otherwise process serially
    else:
        logging.info('Serial processing of channels')
        for channel in range(start_channel, nof_channels):
            calibrate_channel(channel) # removed this parameters and use global now : station_name=station_name)
  
    # All done, first update last calibration :
    if update_last_calibration :
       subprocess.check_call(['update_last_calibration.sh',station_name])
    else :
       logging.info('Do not updating last calibration')

    # post calibration actions :
#    if post_calibration :
#       post_cal_parameters = ['post_calibration_actions.sh',station_name]
#       subprocess.check_call( post_cal_parameters )       
    
    # then cleanup up temporary files
    cleanup_parameters = ['cleanup_temp_files.sh', '-D', directory]
    if options.keep_uv_files :
       cleanup_parameters.append("-u")
       cleanup_parameters.append("0")
       
    subprocess.check_call( cleanup_parameters )

def get_acquisition_time(conf):
    """ Get acqusition time from directory """

    # Grab directory
    if conf.directory != '.' and conf.directory != './' and len(conf.directory) >= 15 : # minimum length to contain format "%Y_%m_%d-%H:%M"
        currdir = os.path.split(conf.directory)[-1]
    else:
        currdir = os.path.split(os.getcwd())[-1]  

    # Try to get fit time from directory name
    try:
        logging.info('Trying to parse acquisition time from currdir = %s' % (currdir))
        return datetime.strptime(currdir, "%Y_%m_%d-%H:%M") - timedelta(hours=8)
    except:
        pass

    # Acqusition time not encoded in directory. Try grabbing it from a file
    file_pattern = os.path.join(conf.directory, "correlation_burst*.hdf5")
    for f in glob(file_pattern):
        # Check whether we can grab date time from filename
        try:
            filename = os.path.basename(os.path.abspath(f))
            logging.info('Trying to parse acquisition time from filename = %s' % (filename))            
            pattern = r"correlation_burst_(?P<channel>\d+)_(?P<timestamp>\d+_\d+)_(?P<part>\d+).hdf5"
            parts = re.match(pattern, filename).groupdict()
            parts = parts['timestamp'].split('_')
            sec = timedelta(seconds=int(parts[1]))
            sec  = sec - 8*3600 # 20190812 - bugfix by MS as these seconds are in LOCAL TIME NOT UTC -> have to subtract 8 hours 
            date = datetime.strptime(parts[0], '%Y%m%d') + sec
            date = time.mktime(date.timetuple())
            logging.info('Returning date %s parsed from filename = %s' % (date,filename))
            return datetime.fromtimestamp(date)
        except:
            continue

    logging.warning('get_acquisition_time returning current date/time instead of acquisition date/time')

    # Failed to get acquisition time, return current time
    return datetime.utcnow()

def save_coefficients_postgres(conf, xx_amp, xx_phase, yy_amp, yy_phase, x_delay, y_delay, station_id, db_host_ip="10.0.10.200" ):
    global username
    # Create connection to the calibration database.
    # Do not have to use password here since DB is set up to recognise aavs user
    logging.info('Connecting to PostgreSQL database aavs/aavs at {}'.format(db_host_ip))
    conn = psycopg2.connect(database='aavs' , user='aavs' , host=db_host_ip ) # do not use paramter but rely on PGHOST 
    cur = conn.cursor()

    # Get acqusition time
    fit_time = get_acquisition_time(conf)
    
    # 
    if username is None or len(username)<=0 :
       print("WARNING : username not set (probably a CRONTAB job) -> setting to aavs")
       username="aavs"

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

        q = '''INSERT INTO calibration_solution(fit_time, create_time, ant_id, x_amp, y_amp, x_pha, y_pha,x_delay,x_phase0,y_delay,y_phase0,station_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '''
        cur.execute(q, (fit_time, create_time, antenna, x_amp, y_amp, x_pha, y_pha, x_delay[1, antenna],
                        x_delay[0, antenna], y_delay[1, antenna], y_delay[0, antenna], station_id ))

    # Commit and close connection
    conn.commit()
    conn.close()

    logging.info("Persisted calibration coefficients in Postgres database")


def save_coefficients_mongo(conf, xx_amp, xx_phase, yy_amp, yy_phase, x_delay, y_delay, station_name="AAVS1" ): # was AAVS1
    """ Save calibration coefficients to mongo database
    :param conf: Configuration dictionary
    :param xx_amp: XX amplitude in channel/antenna format
    :param xx_phase: XX phase in channel/antenna format
    :param yy_amp: YY amplitude in channel/antenna format
    :param yy_phase:  YY phase in channel/antenna format
    :param x_delay: XX delay and intercept for all antennas in [delay|intercept]/antennas format
    :param y_delay: YY delay and intercept for all antennas in [delay|intercept]/antennas format
    :return:
    """

    # Get acqusition time
    acquisition_time = time.mktime(get_acquisition_time(conf).timetuple())

    # Create empty solution
    solution = np.zeros((nof_antennas, 2, total_channels, 2), dtype=np.float)
    solution[:, :, :, 0] = 1

    # Add values to solution
    solution[:, 0, :, 0] = xx_amp.T
    solution[:, 0, :, 1] = xx_phase.T
    solution[:, 1, :, 0] = yy_amp.T
    solution[:, 1, :, 1] = yy_phase.T

    # The antenna calibration coefficients order is the one used by Miriad, which
    # should relate to the base number.

    # Save coefficients
    if aavs_calibration_common_ok :
       add_new_calibration_solution(station_name,
                                    acquisition_time,
                                    solution,
                                    delay_x=x_delay[1, :],
                                    phase_x=x_delay[0, :],
                                    delay_y=y_delay[1, :],
                                    phase_y=y_delay[0, :])
    else :       
       raise Exception("ERROR : aavs_calibration_common package is not available -> could not save calibration coefficients to Mongo DB")

    logging.info("Persisted calibration coefficients in Mongo database")


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
    parser.add_option("--skip-postgres", action="store_true", dest="skip_postgres", default=False,
                      help="Skip saving coefficients to postgres database [default: False]")
    parser.add_option("--skip-db", '--no-db', '--nodb', action="store_true", dest="no_db", default=False,
                      help="Skip saving coefficients to any database [default: False]")                      
    parser.add_option("--station_id", '--station', dest="station_id", default=0,
                      help="Station ID (as in the station configuratio file) [default: %]", type=int )                      
    parser.add_option("--station_name", dest="station_name", default="EDA2", # was AAVS1
                      help="Station ID (as in the station configuratio file) [default: %]" )                      
    parser.add_option("-P", "--plots", '--do_plots', '--plot_solutions', action="store_true", dest="plot_solutions", default=True,
                      help="Plot calibration solutions and fits from the database [default: %defualt]")
    parser.add_option("-m","--model","--calibrator",dest="calibration_object",default="sun",help="Calibrator object [default: %]")
    parser.add_option("--keep_uv", '--keep_uv_files','--uv', '--do_not_remove_uv_file', action="store_true", dest="keep_uv_files", default=False,
                      help="Keep UV files (.uv) [default: %]")                      

    parser.add_option("--do_not_update", "--do_not_update_last_cal", action="store_false", dest="update_last_calibration", default=True,
                      help="Do not update last calibration [default: False]")
  
    parser.add_option("--do_not_calibrate", "--no_calibration", action="store_false", dest="do_calibration", default=True, help="Do not execute calibration (only conversion) [default: False]")
                    

    parser.add_option("--no_mongo", "--no_mongodb", "--nomongo", action="store_false", dest="save_to_mongo_db", default=True,
                      help="Turn off saving calibration solutions to Mongo DB too [default: %s]")
                      
    # beam in the direction of Sun :
#    parser.add_option("--beam_x", '--beamx', '--bx' , dest="beam_x", default=1.00, help="Beam power in X polarisation [default: %]", type=float )
#    parser.add_option("--beam_y", '--beamy', '--by' , dest="beam_y", default=1.00, help="Beam power in Y polarisation [default: %]", type=float )
                      


    (conf, args) = parser.parse_args(argv[1:])
    
    
    logging.info("PARAMETERS:")
    logging.info("calibration_object = %s" % (conf.calibration_object))

    # Set current thread name
    threading.currentThread().name = "Run calibration"

    # Sanity check, make sure directory exists
    if not os.path.exists(conf.directory) or not os.path.isdir(conf.directory):
        logging.error("Specified directory ({}) does not exist".format(conf.directory))
        exit(-1)

    # Set globals
    show_output = conf.show_output
    directory = conf.directory

    # Integrations over which to integrate
    nof_integrations = 1

    # Calculate number of channels
    nof_channels = total_channels - start_channel

    # Channel to calibrate
    xx_amp = np.ones((total_channels, nof_antennas))
    xx_phase = np.zeros((total_channels, nof_antennas))
    yy_amp = np.ones((total_channels, nof_antennas))
    yy_phase = np.zeros((total_channels, nof_antennas))
    x_delay = np.zeros((2, nof_antennas))
    y_delay = np.zeros((2, nof_antennas))

    # If not skipping calibration, generate calibration solutions
    if conf.skip is False:
        run_calibration(conf.directory, nof_channels, conf.threads, station_name=conf.station_name, update_last_calibration=conf.update_last_calibration )

    # At this point calibration solutions should be ready, read files and save locally
    for channel in range(start_channel, nof_channels):
        try:
            x_amp, x_pha, y_amp, y_pha = load_coefficients(conf.directory, channel)
            xx_amp[channel, :] = x_amp
            xx_phase[channel, :] = x_pha
            yy_amp[channel, :] = y_amp
            yy_phase[channel, :] = y_pha
        except Exception as e:
            logging.warning("Unable to load data for channel {}: {}".format(channel, e))

    # Now fit a delay to each pol of each antenna
    for a in range(nof_antennas):
        logging.info('Solving delays for ant {}'.format(a))
        delay_model_x = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(np.copy(xx_phase[:, a])))
        delay_model_y = fit_phase_delay.fitDelay(fit_phase_delay.zeroBadFreqs(np.copy(yy_phase[:, a])))
        if delay_model_x is None or delay_model_y is None:
            logging.warning("No solution for antenna {}".format(a))
        else:
            x_delay[:, a] = delay_model_x
            y_delay[:, a] = delay_model_y

    # Sanity check. If all coefficients are 0 then do not save to database
    if np.all(x_delay == 0) and np.all(y_delay) == 0:
        logging.warning("Calculated delays are all zero, not saving to database")
        exit()

    # Save calibration to Postgres database
    print('Before PostgreSQL if %d/%d' % (conf.skip_postgres,conf.no_db))
    if not conf.skip_postgres and not conf.no_db :
        print('Before if psycopg2_found (%d)' % (psycopg2_found))
        if psycopg2_found :
           db_host="127.0.0.1"
           try : 
              db_host=os.environ['PGHOST']
           except :
              logging.warning("PGHOST environment variable not defined, using default db_host = {}".format(db_host))              
              
           save_coefficients_postgres(conf, xx_amp, xx_phase, yy_amp, yy_phase, x_delay, y_delay, station_id=conf.station_id, db_host_ip=db_host )
           print("DEBUG : connected to database on host = %s" % (db_host))
        else :
           raise Exception("ERROR : module psycopg2 could not be loaded -> calibration solutions not saved to the database")

    print('After PostgreSQL')
    

    # Save calibration to Mongo database
    if not conf.no_db and conf.save_to_mongo_db :
        try :
           save_coefficients_mongo(conf, xx_amp, xx_phase, yy_amp, yy_phase, x_delay, y_delay, station_name=conf.station_name )
        except :
           logging.warning("Could not save solutions to MongoDB - please verify the errors above")

    if conf.plot_solutions :
       print("Plotting the latest calibration solutions with fits from the database:")
       cal_script = "/home/aavs/aavs-calibration/monitoring/plotcal_v_freq.sh"
       command = [ cal_script , conf.station_name, conf.directory ] # add parameters separated by commas : , "-D", directory,  etc 
       subprocess.call(command, stdout=stdout, stderr=subprocess.STDOUT)
       print("Plotting done - OK ???")       