import unittest
import pymongo
from db import *
from datetime import datetime

database = connect('aavs_unit_test', host='localhost', port=27017)


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
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
        database.drop_database('aavs_unit_test')

    def test_connection(self):
        self.assertIsInstance(database, pymongo.mongo_client.MongoClient, 'Test Connection')

    def test_antenna_collection_length(self):
        self.assertEqual(100, len(Antenna.objects), 'Antenna Count')

    def test_get_antenna_with_max_id(self):
        last = Antenna.objects().order_by('-antenna_nr').first()
        self.assertEqual(last.antenna_nr, 99, 'Get Max Antenna ID')

    def test_add_fit(self):
        fit_x = None

        for a in Antenna.objects():
            now = datetime.now(pytz.utc)

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
