from aavs_calibration.models import CalibrationSolution, CalibrationCoefficient, Antenna, Station
import mongoengine

DB_NAME = 'aavs'    # change name to create another database
HOST = 'localhost'  # insert IP address or url here
PORT = 27017        # mongodb standard port


def connect(db_name='', host='', port=''):
    """ connect to standard db, if not otherwise specified """
    if not db_name:
        db_name = DB_NAME
    if not host:
        host = HOST
    if not port:
        port = PORT
    connection = mongoengine.connect(db_name, host=host, port=port)
    return connection.aavs


def purge_database():
    """ Drops all collections """
    Antenna.drop_collection()
    Station.drop_collection()
    CalibrationSolution.drop_collection()
    CalibrationCoefficient.drop_collection()


def purge_fits():
    """ Drops all calibration-related collections """
    CalibrationSolution.drop_collection()
    CalibrationCoefficient.drop_collection()


def purge_antennas():
    """ Drops antenna collection"""
    Antenna.drop_collection()


if __name__ == "__main__":
    connect()
    purge_fits()
