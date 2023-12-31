import logging
import os
import sched
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from sys import stdout
from time import sleep

from pyaavs import station
from pydaq import daq_receiver as receiver
import pyaavs.logger

# Global variables
daq_config = None
stop = False

nof_channels = 512


def stop_observation():
    global stop
    stop = True


def run_observation_burst(config,opts):
    global stop

    # Load station configuration and change required parameters
    station.load_configuration_file(config)

    station_config = station.configuration
    station_config['station']['program'] = opts.program
    station_config['station']['initialise'] = opts.program
    station_id = station_config['station']['id']
    station_name = station_config['station']['name']

    # Create station
    aavs_station = station.Station(station_config)
    aavs_station.connect()

    if not aavs_station.properly_formed_station:
        logging.error("Station not properly formed, exiting")
        exit()

    logging.info("Starting DAQ")

    # Create data directory
    directory = os.path.join(opts.directory, datetime.now().strftime("%Y_%m_%d-%H:%M"))
    os.mkdir(directory)

    # Start DAQ
    daq_config['nof_tiles'] = len(aavs_station.tiles)
    daq_config['directory'] = directory
    receiver.populate_configuration(daq_config)
    receiver.initialise_daq( filepath=opts.daq_library )
    receiver.start_correlator()

    # Wait for DAQ to initialise
    sleep(2)

    n_channels = opts.last_channel - opts.first_channel + 1
    wait_time=round(float(opts.nof_samples)*float(opts.n_integrations_per_file)*float(n_channels)*1.08/1000000.00)+10 # expected execution time +2 seconds
#    integration_time=2
#    observation_duration = integration_time*( opts.last_channel - opts.first_channel + 1) # in seconds
    if opts.observation_duration > 0 :
       wait_time = opts.observation_duration
    logging.info("Setting timer to stop observation in %.4f [sec]" % (wait_time))
    timer = threading.Timer( wait_time, stop_observation)
    timer.start()

    # Start sending data
    logging.info("Number of correlator samples will be %d * %d = %d" % (daq_config['nof_correlator_samples'],opts.n_integrations_per_file,(daq_config['nof_correlator_samples']*opts.n_integrations_per_file)))
    aavs_station.stop_data_transmission()    
    aavs_station.send_channelised_data(daq_config['nof_correlator_samples']*opts.n_integrations_per_file,first_channel=opts.first_channel, last_channel=opts.last_channel)

    # Wait for observation to finish
    logging.info("Observation started")
    while not stop:
        time.sleep(5)
    stop = False

    # All done, clear everything
    logging.info("Observation ended")
    aavs_station.stop_data_transmission()

    try:
        receiver.stop_daq()
    except Exception as e:
        logging.error("Failed to stop DAQ cleanly: {}".format(e))

    if opts.do_calibration :
       # Run calibration on dumped data
       logging.info("Calibrating data")
    
       if opts.beam_correct :
          logging.info("Calculating beam values in the direction of the Sun (for now it's just Sun)")
          dtm=os.path.basename(directory)
          dirpath=os.path.dirname(directory)
          cmdline = ("/home/aavs/Software/station_beam/scripts/beam_correct_latest_cal.sh %s %s %s" % (station_name,dtm,dirpath))
          logging.info("Executing command : %s" % cmdline )
       
          # subprocess.call( cmdline )
          os.system( cmdline )

       cal_script = "/home/aavs/aavs-calibration/run_calibration.py"
       # # MS : testing call instead of check_call to avoid crash of the whole script due to crash on a single channel :
       # 2023-03-21 : added --keep_uv_files to keep .uv files for the future calibration from the database to be inserted there (it has all the other metadata correct) :
       param_list = ["python", cal_script, "-D", directory, "--station_id", str(station_id), "--station_name", station_name , "--show-output" , "--keep_uv_files" ] # , "--beam_x" , config.beam_x , "--beam_y" , config.beam_y ]

       if opts.no_db :
           param_list.append( "--nodb" )
        
       if not opts.save_to_mongo_db :
           param_list.append( "--nomongo" )
        
       subprocess.call( param_list )
    else:
       print("WARNING : execution of calibration is not required")

if __name__ == "__main__":
    from optparse import OptionParser

    # Command line options
    p = OptionParser()
    p.set_usage('calibration_loop.py [options] INPUT_FILE')
    p.set_description(__doc__)

    p.add_option("--config", action="store", dest="config",
                 default=None, help="Station configuration file to use")
    p.add_option("--lmc_ip", action="store", dest="lmc_ip",
                 default="10.0.10.200", help="IP [default: 10.0.10.200]")
    p.add_option("-P", "--program", action="store_true", dest="program",
                 default=False, help="Program and initialise station")
    p.add_option('-d', '--directory', dest='directory', action='store', default=None,
                 help="Data directory (default: '/storage')")
    p.add_option("-i", "--receiver_interface", action="store", dest="receiver_interface",
                 default="eth3:1", help="Receiver interface [default: eth3:1]")
    p.add_option("--samples", action="store", dest="nof_samples",
                 default=1835008, type="int", help="Number of samples to correlate. Default: 1835008")
    p.add_option("--n_integrations_per_file", "--n_int_per_file", action="store", dest="n_integrations_per_file", default=1, type="int", help="Number of integrations per file [default %default]")
    p.add_option("--wait_time", "--observation_duration", action="store", dest="observation_duration", default=-1, type="int", help="Wait time [default %default]. Negative means that it is automatically calculated as number of channels times 2seconds")
    p.add_option("--period", action="store", dest="period",
                 default=0, type="int", help="Dump period in seconds. Default: 0 (perform once)")
    p.add_option("-s", "--starttime", action="store", dest="starttime",
                 default="now",
                 help="Time at which to start observation. For multi-channel observations, each channel will start"
                      "at the specified on subsequent days. Format: dd/mm/yyyy_hh:mm. Default: now")
    p.add_option("--skip-db", '--no-db', '--nodb', action="store_true", dest="no_db", default=False,
                 help="Skip saving coefficients to any database [default: False]")                                       
    p.add_option("--beam_correct", '--beam_corr', action="store_true", dest="beam_correct", default=False,
                 help="Beam correct and calculate apparent flux of the Sun or sky model in general [default: False]")                      

    p.add_option("", "--correlator-channels", action="store", dest="nof_correlator_channels",
                 type="int", default=512, help="Number of channels to channelise into before correlation. Only "
                                              "used in correlator more [default: 1]")
                 
    p.add_option("--no_mongo", "--no_mongodb", "--nomongo", action="store_false", dest="save_to_mongo_db", default=True,
                 help="Turn off saving calibration solutions to Mongo DB too [default: %s]")
                 
    p.add_option("-n", "--do_not_calibrate", action="store_false", dest="do_calibration",
                 default=True, help="Perform calibation after getting the correlated data")
                 
    p.add_option("--daq_library", action="store", dest="daq_library", default=None, help="Directly specify the AAVS DAQ library to use")                 
    p.add_option("--first_channel", "--start_channel", action="store", dest="first_channel", default=0, type="int", help="First channel [default %default]")
    p.add_option("--last_channel", "--end_channel", action="store", dest="last_channel", default=511, type="int", help="Last channel [default %default]")
                                  
                 
    # beam in the direction of Sun :
#    parser.add_option("--beam_x", '--beamx', '--bx' , dest="beam_x", default=1.00, help="Beam power in X polarisation [default: %]", type=float )
#    parser.add_option("--beam_y", '--beamy', '--by' , dest="beam_y", default=1.00, help="Beam power in Y polarisation [default: %]", type=float )
                 
    opts, args = p.parse_args(sys.argv[1:])
    
    print("#################################")
    print("PARAMETERS:")
    print("#################################")
    print("n_integrations_per_file = %d" % (opts.n_integrations_per_file))
    print("#################################")

    # Set current thread name
    threading.currentThread().name = "Calibration Loop"

    # Check if a configuration file was defined
    if opts.config is None:
        logging.error("A station configuration file is required, exiting")
        exit()
    elif not os.path.exists(opts.config):
        logging.error("Invalid config file specified: {}".format(opts.config))
        exit()

    # Check if directory exists
    #if not (os.path.exists(opts.directory) and os.path.isdir(opts.directory)):
    #    logging.error("Specified directory (%s) does not exist or is not a directory" % opts.directory)
    #    exit(0)

    # Expand directory path for station
    station.load_configuration_file(opts.config)
    station_name = station.configuration['station']['name']
    if opts.directory is None :
       opts.directory = os.path.join(opts.directory, station_name.lower(), 'real_time_calibration')
    if not (os.path.exists(opts.directory) and os.path.isdir(opts.directory)):
        logging.error("Full data directory (%s) does not exist or is not a directory" % opts.directory)
        exit(0)

    # Check if start time was specified
    if opts.starttime is None:
        logging.error("Start time must be specified")
        exit(0)

    # Check that start time is valid
    start_time = datetime.now() + timedelta(seconds=10)
    curr_time = datetime.fromtimestamp(int(time.time()))
    if opts.starttime != "now":
        start_time = datetime.strptime(opts.starttime, "%d/%m/%Y_%H:%M")
        curr_time = datetime.fromtimestamp(int(time.time()))
        wait_seconds = (start_time - curr_time).total_seconds()
        if wait_seconds < 10:
            logging.error("Scheduled start time must be at least 10s in the future")
            exit()
    else:
        logging.info("No start time defined, will start in 10 seconds")

    # Populate DAQ configuration
    daq_config = {"nof_correlator_channels": opts.nof_correlator_channels,
                  "nof_correlator_samples":  opts.nof_samples,
                  "receiver_interface":      opts.receiver_interface,
                  "receiver_frame_size": 9000}

    # Perform dump every required period
    while True:
        # Run current iteration
        logging.info("Setting scheduler to run at {}".format(start_time))
        s = sched.scheduler(time.time, time.sleep)
        curr_time = datetime.fromtimestamp(int(time.time()))
        s.enter((start_time - curr_time).total_seconds(), 0, run_observation_burst, [opts.config, opts, ])
        s.run()

        # Schedule next dump
        if opts.period == 0:
            break
        start_time = start_time + timedelta(seconds=opts.period)
