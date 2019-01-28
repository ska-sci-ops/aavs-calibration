import unittest

from db import *


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for i in range(0, 100):
            Antenna(antenna_id=i,
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
        db.drop_database('aavs_test')

    def test_antenna_collection_length(self):
        self.assertEqual(100, len(Antenna.objects), 'Antenna Count')

    def test_get_antenna_with_max_id(self):
        last = Antenna.objects().order_by('-antenna_id').first()
        self.assertEqual(last.antenna_id, 99, 'Get Max Antenna ID')

    def condition_1(self):
        pass
