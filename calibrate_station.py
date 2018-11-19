from pyaavs.station import *
import numpy as np
import psycopg2

# TPMs to use
tpms = ["tpm-{}".format(i) for i in range(1, 17)]

# Preadu mapping
antenna_preadu_mapping = {0: 1, 1: 2, 2: 3, 3: 4,
                          8: 5, 9: 6, 10: 7, 11: 8,
                          15: 9, 14: 10, 13: 11, 12: 12,
                          7: 13, 6: 14, 5: 15, 4: 16}
channel_bandwidth = 400e6 / 512.0
nof_antennas_per_tile = 16
nof_antennas = 256
nof_stokes = 4

def antenna_coordinates():
    """ Reads antenna base locations from the Google Drive sheet
    :param save_to_file: Save remapped location and baselines to file
    :return: Re-mapped antenna locations
    """
    import urllib

    # Antenna mapping placeholder
    antenna_mapping = []
    for i in range(nof_antennas_per_tile):
        antenna_mapping.append([[]] * nof_antennas_per_tile)

    # Read antenna location spreadsheet
    response = urllib.urlopen('https://docs.google.com/spreadsheets/d/e/2PACX-1vQTo60lZmrvBfT0gpa4BwyaB_QkPplqfHga'
                              '7RCsLDR9J_lv15BQTqb3loBHFhMp6U0X_FIwyByfFCwG/pub?gid=220529610&single=true&output=tsv')
    html = response.read().split('\n')

    # Two antennas are not in-place, however we still get an input into the TPM
    missing = 0

    # Read all antenna rows from spreadsheet response
    for i in range(1, nof_antennas + 1):
        items = html[i].split('\t')

        # Parse antenna row
        try:
            base, tpm, rx = int(items[1]), int(items[7]) - 1, int(items[8]) - 1
            east, north, up = float(items[15].replace(',', '.')), float(items[17].replace(',', '.')), 0
        except:
            if missing == 0:
                base, tpm, rx = 3, 0, 8
                east, north, up = 17.525, -1.123, 0
            else:
                base, tpm, rx = 41, 10, 8
                east, north, up = 9.701, -14.627, 0
            missing += 1

        # Rotate the antenna and place in placeholder
        antenna_mapping[tpm][rx] = (base, east, north)

    # Create lookup table (uses preadu mapping)
    antenna_positions = np.zeros((nof_antennas, 3))
    for i in range(nof_antennas):
        tile_number = i / nof_antennas_per_tile
        rx_number = antenna_preadu_mapping[i % nof_antennas_per_tile] - 1
        antenna_positions[i] = (antenna_mapping[tile_number][rx_number])

    return antenna_positions

def get_latest_coefficients():
    """ Read latest coefficients from database """

    # Create connection to the calibration database.
    conn = psycopg2.connect(database='aavs')
    cur = conn.cursor()

    # Compute the required delays for the station beam channels
    nof_channels = int(obs_bandwidth / channel_bandwidth)
    frequencies = np.arange(obs_start_channel_frequency / channel_bandwidth, 
                           (obs_start_channel_frequency + obs_bandwidth) / channel_bandwidth) * channel_bandwidth

    # Grab antenna coefficients one by one (X pol)
    x_delays = np.zeros((nof_antennas, 2), dtype=np.float)
    for ant_id in range(nof_antennas):
        cur.execute('''SELECT fit_time, x_delay, x_phase0 from calibration_solution WHERE x_delay IS NOT NULL   AND ant_id={} ORDER BY FIT_TIME LIMIT 1'''.format(ant_id))
        x_delays[ant_id, :] = cur.fetchone()[1:]

    # Grab antenna coefficients one by one (Y pol)
    y_delays = np.zeros((nof_antennas, 2), dtype=np.float)
    for ant_id in range(nof_antennas):
        cur.execute('''SELECT fit_time, y_delay, y_phase0 from calibration_solution WHERE x_delay IS NOT NULL   AND ant_id={} ORDER BY FIT_TIME LIMIT 1'''.format(ant_id))
        y_delays[ant_id, :] = cur.fetchone()[1:]

    # Ready from database
    conn.close()

    # Create default calibration coefficient array
    # Index 0 is XX, 3 is YY. Indices 2 and 3 are the cross-pols, which should be initialised to 0
    coeffs = np.ones((nof_antennas, nof_channels, nof_stokes), dtype=np.complex64)

    # Create antenna indicies
    base_numbers = antenna_coordinates()[:, 0].tolist()
    base_indices = [base_numbers.index(i) for i in range(1, nof_antennas + 1)]

    # Compute phase for all channels
    for i, freq in enumerate(frequencies):
        phase_x = x_delays[:, 1] + 2 * np.pi * freq * x_delays[:, 0]
        phase_y = y_delays[:, 1] + 2 * np.pi * freq * y_delays[:, 0]
        
        coeffs[base_indices, i, 0] = np.cos(phase_x) + np.sin(phase_x) * 1j
        coeffs[base_indices, i, 3] = np.cos(phase_y) + np.sin(phase_y) * 1j

    # Return values
    return coeffs

def check_station():
    """ Check if the station is properly formed """

    # Connect to tiles in station 
    station = Station(0)
    [station.add_tile(t) for t in tpms]
    station.connect()

    return station.properly_formed_station

def download_coefficients(coefficients):
    """ Download coefficients to station """

    # Connect to tiles in station 
    station = Station(0)
    [station.add_tile(t) for t in tpms]
    station.connect()

    # Download coefficients
    t0 = time.time()
    for i, tile in enumerate(station.tiles):
        # Get coefficients range for current tile
        for antenna in range(nof_antennas_per_tile):
            tile.load_calibration_coefficients(antenna, coefficients[i * nof_antennas_per_tile + antenna, :, :].tolist())
    t1 = time.time()

    logging.info("Downloaded coefficients to tiles in {0:.2}s".format(t1 - t0))

    # Done downloading coefficient, switch calibration bank
    station.switch_calibration_banks(2048)  # About 0.5 seconds
    logging.info("Switched calibration banks")

def update_calibration_coefficients():
    """ Update calibration coefficients in station """
    if check_station():
        download_coefficients(get_latest_coefficients())
    else:
        logging.info("Station not well formed")

if __name__ == "__main__":
    from optparse import OptionParser
    from sys import argv, stdout

    parser = OptionParser(usage="usage: %calibrate_station [options]")

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

    # Update calibration coefficients
    update_calibration_coefficients()

    # If period is defined, loop forever with given period
    if opts.period != 0:
        while True:
            logging.info("Waiting for {} seconds".format(opts.period))
            time.sleep(opts.period)
            update_calibration_coefficients()

