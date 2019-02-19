import unittest
from pymongo.mongo_client import MongoClient
from pytz import UTC
from datetime import datetime

from db import Antenna, Fit, convert_datetime_to_timestamp, connect_to_db

# connect to test db
database = connect_to_db('aavs_unit_test')


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ clears the test db and fills some data into db for testing"""
        cls.tearDownClass()
        for i in range(0, 100):
            Antenna(antenna_nr=i,
                    station_id=1,
                    x_pos=i,
                    y_pos=i,
                    base_id=i % 10,
                    tpm_id=int(i / 16),
                    tpm_rx=i % 16,
                    antenna_type='type_1',
                    status_x='' if i % 3 else 'OK',
                    status_y='' if i % 4 else 'OFF').save()

    @classmethod
    def tearDownClass(cls):
        """ purges db after tests """
        database.drop_database('aavs_unit_test')

    def test_connection(self):
        """ tests connection to the db """
        self.assertIsInstance(database, MongoClient, 'Test Connection')

    def test_antenna_collection_length(self):
        """ tests the number of antennas added """
        self.assertEqual(100, len(Antenna.objects), 'Antenna Count')

    def test_get_antenna_with_max_id(self):
        """ tests retrieval of an antenna """
        last = Antenna.objects().order_by('-antenna_nr').first()
        self.assertEqual(last.antenna_nr, 99, 'Get Max Antenna ID')

    def test_add_fit(self):
        """ tests adding fits to the db """
        fit_x = None

        for a in Antenna.objects():
            now = convert_datetime_to_timestamp(datetime.now(UTC))

            fit_x = Fit(acquisition_time=now,
                        pol=0,
                        antenna_id=a.id,
                        fit_time=now,
                        fit_comment='',
                        flags='',
                        phase_0=a.antenna_nr,
                        delay=a.antenna_nr * 10).save()

        self.assertEqual(100, len(Fit.objects), 'Fit Count')
        self.assertEqual(990, fit_x.delay, 'Fit example')
