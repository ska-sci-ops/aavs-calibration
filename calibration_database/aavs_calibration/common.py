import logging

from aavs_calibration import database
from aavs_calibration.definitions import *
from aavs_calibration.models import CalibrationSolution, Station, CalibrationCoefficient

import numpy as np
import pymongo


def change_antenna_status(station_id, base_id, polarisation, status):
    """ Change the status of an antenna """

    # Connect to database
    db = database.connect()

    # Query to find and update depends on polarisation
    if polarisation == Polarisation.X:
        r = db.antenna.find_one_and_update({'station_id': station_id, 'base_id': base_id},
                                           {"$set": {"status_x": status.name}})
    elif polarisation == Polarisation.Y:
        r = db.antenna.find_one_and_update({'station_id': station_id, 'base_id': base_id},
                                           {"$set": {"status_x": status.name}})
    else:
        r = db.antenna.find_one_and_update({'station_id': station_id, 'base_id': base_id},
                                           {"$set": {"status_x": status.name, "status_y": status.name}})

    return r


def get_antenna_positions(station_id):
    """ Get antenna positions for a given station id"""
    # Connect to database
    db = database.connect()

    # Create lists with base_id, x and y pos and return
    base, x, y = [], [], []
    for item in db.antenna.find({'station_id': station_id},
                                {'base_id': 1, 'x_pos': 1, 'y_pos': 1, '_id': 0}):
        base.append(item['base_id'])
        x.append(item['x_pos'])
        y.append(item['y_pos'])

    return base, x, y


def add_new_calibration_solution(station, acquisition_time, solution, comment="",
                                 delay_x=0, phase_x=0, delay_y=0, phase_y=0):
    """ Add a new calibration fit to the database.
    :param station: Station identifier
    :param acquisition_time: The time at which the data was acquired
    :param solution: A 4D array containing the computed solutions. The array should be
                     in antenna/pol/frequency/(amp/pha), where for the last dimension
                     index 0 is amplitude and index 1 is phase.
    :param comment: Any user-defined comment to add to the fit"
    :param delay_x: Computed solution gradient for X pol
    :param phase_x: Computed solution intercept for X pol
    :param delay_y: Computed solution gradient for Y pol
    :param phase_y: Computed solution intercept for Y pol"""

    # Convert timestamps
    acquisition_time = convert_timestamp_to_datetime(acquisition_time)
    fit_time = datetime.utcnow()

    # Connect to database
    db = database.connect()

    # Grab all antenna for station and sort in order in which fits are provided
    station = Station.objects(name=station)

    if len(station) == 0:
        logging.warning("Station {} not found in calibration database, not adding new calibration solutions")

    station_info = station.first()
    antennas = db.antenna.find({'station_id': station_info.id}).sort("antenna_station_id", pymongo.ASCENDING)

    # Loop over all antennas and save solutions to database
    for a, antenna in enumerate(antennas):
        # Create X and Y fit solutions
        CalibrationSolution(acquisition_time=acquisition_time,
                            fit_time=fit_time,
                            pol=0,
                            antenna_id=antenna['_id'],
                            fit_comment=comment,
                            flags='',
                            amplitude=solution[a, 0, :, 0],
                            phase=solution[a, 0, :, 1],
                            phase_0=phase_x,
                            delay=delay_x).save()

        CalibrationSolution(acquisition_time=acquisition_time,
                            fit_time=fit_time,
                            pol=1,
                            antenna_id=antenna['_id'],
                            fit_comment=comment,
                            flags='',
                            amplitude=solution[a, 1, :, 0],
                            phase=solution[a, 1, :, 1],
                            phase_0=phase_y,
                            delay=delay_y).save()


def add_coefficient_download(station, download_time, coefficients):
    """ Add a new calibration download entry to the database.
    :param station: Station identifier
    :param download_time: Time at which coefficients were downloaded to the station
    :param coefficients: A 3D array containing the complex coefficients downloaded to the station.
                         The array should be in antenna/pol/frequency order."""

    # Convert timestamps
    download_time = convert_timestamp_to_datetime(download_time)

    # Connect to database
    db = database.connect()

    # Grab all antenna for station and sort in order in which fits are provided
    station = Station.objects(name=station)

    if len(station) == 0:
        logging.warning("Station {} not found in calibration database, not adding new downloaded coefficients")

    station_info = station.first()
    antennas = db.antenna.find({'station_id': station_info.id}).sort("antenna_station_id", pymongo.ASCENDING)

    for a, antenna in enumerate(antennas):
        CalibrationCoefficient(antenna_id=antenna['_id'],
                               pol=0,
                               calibration_coefficients_real=coefficients[a, 0, :].real,
                               calibration_coefficients_imag=coefficients[a, 0, :].imag,
                               download_time=download_time).save()

        CalibrationCoefficient(antenna_id=antenna['_id'],
                               pol=1,
                               calibration_coefficients_real=coefficients[a, 1, :].real,
                               calibration_coefficients_imag=coefficients[a, 1, :].imag,
                               download_time=download_time).save()


def get_latest_calibration_solution(station):
    """ Get the latest calibration solution
    :param station: Station identifier"""

    # Connect to database
    db = database.connect()

    # Grab all antenna for station and sort in order in which fits are provided
    station = Station.objects(name=station)

    if len(station) == 0:
        logging.warning("Station {} not found in calibration database, not adding new calibration solutions")

    station_info = station.first()
    antennas = db.antenna.find({'station_id': station_info.id}).sort("antenna_station_id", pymongo.ASCENDING)

    # Generate arrays to store amp and phase
    amplitudes = np.empty((antennas.count(), 2, 512))
    phases = np.empty((antennas.count(), 2, 512))

    # Loop over all antennas
    for antenna in antennas:
        # Grab values for polarisation X
        results = db.calibration_solution.aggregate([
            {'$sort': {'fit_time': -1}},
            {'$match': {'antenna_id': antenna['_id'], 'pol': 0}},
            {'$limit': 1}])
        entry = results.next()

        amplitudes[antenna['antenna_station_id'], 0, :] = entry['amplitude']
        phases[antenna['antenna_station_id'], 0, :] = entry['phase']

        # Grab values for polarisation Y
        results = db.calibration_solution.aggregate([
            {'$sort': {'fit_time': -1}},
            {'$match': {'antenna_id': antenna['_id'], 'pol': 1}},
            {'$limit': 1}])
        entry = results.next()

        amplitudes[antenna['antenna_station_id'], 1, :] = entry['amplitude']
        phases[antenna['antenna_station_id'], 1, :] = entry['phase']

    return amplitudes, phases


def get_latest_coefficient_download(station):
    """ Get the latest downloaded calibration coefficients to the station
    :param station: The station identifier  """

    # Connect to database
    db = database.connect()

    # Grab all antenna for station and sort in order in which fits are provided
    station = Station.objects(name=station)

    if len(station) == 0:
        logging.warning("Station {} not found in calibration database, not adding new calibration solutions")

    station_info = station.first()
    antennas = db.antenna.find({'station_id': station_info.id}).sort("antenna_station_id", pymongo.ASCENDING)

    # Generate arrays to store amp and phase
    coefficients = np.empty((antennas.count(), 2, 512), dtype=np.complex64)

    # Loop over all antennas
    for antenna in antennas:
        # Grab values for polarisation X
        results = db.calibration_coefficient.aggregate([
            {'$sort': {'download_time': -1}},
            {'$match': {'antenna_id': antenna['_id'], 'pol': 0}},
            {'$limit': 1}])
        entry = results.next()

        values = np.array(entry['calibration_coefficients_real']) + np.array(entry['calibration_coefficients_real'])*1j
        coefficients[antenna['antenna_station_id'], 0, :] = values

        # Grab values for polarisation Y
        results = db.calibration_coefficient.aggregate([
            {'$sort': {'download_time': -1}},
            {'$match': {'antenna_id': antenna['_id'], 'pol': 1}},
            {'$limit': 1}])
        entry = results.next()

        values = np.array(entry['calibration_coefficients_real']) + np.array(entry['calibration_coefficients_real']) * 1j
        coefficients[antenna['antenna_station_id'], 0, :] = values

    return coefficients


if __name__ == "__main__":

    from numpy.random import random
    import time

    add_coefficient_download("AAVS1", time.time(), random((256, 2, 512)) + random((256, 2, 512)) * 1j)
    print get_latest_coefficient_download("AAVS1")
    exit()

    for i in range(1):
        t0 = time.time()
        add_new_calibration_solution(time.time(), "AAVS1", random((256, 2, 512, 2)))
        print "Persisted in {}".format(time.time() - t0)
