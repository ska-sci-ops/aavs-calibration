from pytz import UTC
from datetime import datetime
from mongoengine import Document, IntField, FloatField, StringField, DateTimeField, ObjectIdField, ListField


class Antenna(Document):
    """
    stores static data about an antenna and the status for both pols
    """
    antenna_nr = IntField()        # antenna number within the station
    station_id = IntField()
    x_pos = FloatField()           # meters from the station center in x direction
    y_pos = FloatField()           # meters from the station center in y direction
    base_id = IntField()           # base id where antenna is located
    tpm_id = IntField()
    tpm_rx = IntField()
    antenna_type = StringField()
    status_x = StringField()       # status of the x pol
    status_y = StringField()       # status of the y pol

    # enums
    SKALA2 = 'SKALA2'
    type_2 = 'example_2'
    ON = 'ON'
    OFF = 'OFF'

    def __str__(self):
        return 'id: ' + str(self.antenna_nr).rjust(2)\
               + ' x: ' + str(self.x_pos).rjust(4)\
               + ' y: ' + str(self.y_pos).rjust(4)\
               + ' tpm: ' + str(self.tpm_id).rjust(1)\
               + ' rx: ' + str(self.tpm_rx).rjust(2)


class Fit(Document):
    """
    stores data of a fit for a pol of an antenna
    """
    acquisition_time = IntField()               # UNIX timestamp, use function get_acquisition_time to get datetime instead of timestamp
    pol = IntField(min_value=0, max_value=1)    # 0 for x. 1 for y
    antenna_id = ObjectIdField()                # internal database id of the antenna
    fit_time = IntField()                       # UNIX timestamp, use function get_fit_time to get datetime instead of timestamp
    fit_comment = StringField()
    channels = ListField()                      # list of objects of the Channel class
    flags = StringField()
    phase_0 = FloatField()
    delay = FloatField()

    def get_acquisition_time(self):
        """ returns datetime of the timestamp including time zone info """
        return convert_timestamp_to_datetime(self.acquisition_time)

    def set_acquisition_time(self, dt):
        """ converts datetime to timestamp and saves it to the db"""
        self.acquisition_time = convert_datetime_to_timestamp(dt)
        self.save()

    def get_fit_time(self):
        """ returns datetime of the timestamp including time zone info """
        return convert_timestamp_to_datetime(self.fit_time)

    def set_fit_time(self, dt):
        """ converts datetime to timestamp and saves it to the db"""
        self.fit_time = convert_datetime_to_timestamp(dt)
        self.save()

    def __str__(self):
        return 'id: ' + str(self.antenna_id).rjust(2) + ' fit_time: ' + unicode(self.fit_time)


class Channel(Document):
    """ stores data of a single channel of a fit """
    frequency = IntField()
    amp = FloatField()
    phase = FloatField()
    fit_id = ObjectIdField()        # internal database id of the fit
    antenna_id = ObjectIdField()    # internal database id of the antenna

    def __str__(self):
        return 'freq: ' + str(self.frequency).rjust(2) \
               + ' fit: ' + str(self.fit_id) \
               + ' phase: ' + str(self.phase).rjust(4)


class Coefficient(Document):
    """
    stores coefficient for a calibration per pol and per antenna
    """
    antenna_id = ObjectIdField()        # internal database id of the antenna
    pol = IntField()                    # 0 for x. 1 for y
    calibration = ListField()           # list of complex numbers, use set_calibrations to store and get_calibrations to retrieve
    download_time = IntField()          # UNIX timestamp, use function to get_download_time to get datetime with timezone info

    def get_download_time(self):
        """ returns datetime of the timestamp including time zone info """
        return convert_timestamp_to_datetime(self.download_time)

    def set_download_time(self, dt):
        """ converts datetime to timestamp and saves it to the db"""
        self.download_time = convert_datetime_to_timestamp(dt)

    def set_calibrations(self, complex_list):
        """ converts list of complex numbers to strings and stores them """
        self.calibration = map(str, complex_list)

    def get_calibrations(self):
        """ returns list of complex numbers """
        return map(complex, self.calibration)


def convert_timestamp_to_datetime(timestamp):
    """
    converts timestamp to datetime
    :param timestamp: UNIX timestamp
    :return: datetime with UTC timezone
    """
    return datetime.utcfromtimestamp(timestamp).replace(tzinfo=UTC)


def convert_datetime_to_timestamp(dt):
    """
    converts datetime to timestamp
    :param dt: datetime, assumed to be UTC
    :return: UNIX timestamp
    """
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=UTC)
    return int((dt - datetime(1970, 1, 1, tzinfo=UTC)).total_seconds())
