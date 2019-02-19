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

# Global variables
daq_config = None
stop = False

nof_antennas = 256
nof_channels = 512
start_channel = 64


def stop_observation():
    global stop
    stop = True


def run_observation_burst(config):
    global stop

    # Load station configuration and change required parameters
    station.load_configuration_file(config)

    station_config = station.configuration
    station_config['station']['program'] = opts.program
    station_config['station']['initialise'] = opts.program

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
    receiver.initialise_daq()
    receiver.start_correlator()

    # Wait for DAQ to initialise
    sleep(2)

    logging.info("Setting timer to stop observation in %d" % (1.5 * 512 * 1.5))
    timer = threading.Timer(1.5 * 512 * 1.5, stop_observation)
    timer.start()

    # Start sending data
    aavs_station.stop_data_transmission()
    aavs_station.send_channelised_data(daq_config['nof_correlator_samples'])

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

    # Run calibration on dumped data
    logging.info("Calibrating data")
    integration_time = opts.nof_samples / ((400e6 / 512.0)  * (32.0 / 27.0))

    cal_script = "/home/aavs/aavs-calibration/run_calibration.py"
    subprocess.check_call(["python", cal_script, "-D", directory])


if __name__ == "__main__":
    from optparse import OptionParser

    # Command line options
    p = OptionParser()
    p.set_usage('best2_process_corr.py [options] INPUT_FILE')
    p.set_description(__doc__)

    p.add_option("--config", action="store", dest="config",
                  default=None, help="Station configuration file to use")
    p.add_option("--lmc_ip", action="store", dest="lmc_ip",
                 default="10.0.10.200", help="IP [default: 10.0.10.200]")
    p.add_option("-P", "--program", action="store_true", dest="program",
                 default=False, help="Program and initialise station")
    p.add_option('-d', '--directory', dest='directory', action='store', default="/data/data_2/real_time_calibration",
                 help="Data directory (default: '/data/data_2/real_time_calibration')")
    p.add_option("-i", "--receiver_interface", action="store", dest="receiver_interface",
                 default="eth3", help="Receiver interface [default: eth3]")
    p.add_option("--samples", action="store", dest="nof_samples",
                 default=1835008, type="int", help="Number of samples to correlate. Default: 1835008")
    p.add_option("--period", action="store", dest="period",
                 default=0, type="int", help="Dump period in seconds. Default: 0 (perform once)")
    p.add_option("-s", "--starttime", action="store", dest="starttime",
                 default="now",
                 help="Time at which to start observation. For multi-channel observations, each channel will start"
                      "at the specified on subsequent days. Format: dd/mm/yyyy_hh:mm. Default: now")

    opts, args = p.parse_args(sys.argv[1:])

    # Set logging
    log = logging.getLogger('')
    log.setLevel(logging.INFO)
    format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch = logging.StreamHandler(stdout)
    ch.setFormatter(format)
    log.addHandler(ch)

    # Check if a configuration file was defined
    if opts.config is None:
        log.error("A station configuration file is required, exiting")
        exit()

    # Check if directory exists
    if not (os.path.exists(opts.directory) and os.path.isdir(opts.directory)):
        logging.error("Specified directory (%s) does not exist or is not a directory" % daq_config['directory'])
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
    daq_config = {"nof_correlator_channels": 512,
                  "nof_correlator_samples": opts.nof_samples,
                  "receiver_interface": opts.receiver_interface,
                  "receiver_frame_size": 9000}

    # Perform dump every required period
    while True:
        # Run current iteration
        logging.info("Setting scheduler to run at {}".format(start_time))
        s = sched.scheduler(time.time, time.sleep)
        curr_time = datetime.fromtimestamp(int(time.time()))
        s.enter((start_time - curr_time).total_seconds(), 0, run_observation_burst, [opts.config, ])
        s.run()

        # Schedule next dump
        if opts.period == 0:
            break
        start_time = start_time + timedelta(seconds=opts.period)
