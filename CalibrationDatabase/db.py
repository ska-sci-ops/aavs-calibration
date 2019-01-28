from mongoengine import *

db = connect('aavs_test', host='localhost', port=27017)


class Antenna(Document):
    antenna_nr = IntField()
    station_id = IntField()
    x_pos = FloatField()
    y_pos = FloatField()
    base_id = IntField()
    tpm_id = IntField()
    tpm_rx = IntField()
    antenna_type = StringField()
    status_x = StringField()
    status_y = StringField()

    def __str__(self):
        return 'id: ' + str(self.antenna_nr).rjust(2)\
               + ' x: ' + str(self.x_pos).rjust(4)\
               + ' y: ' + str(self.y_pos).rjust(4)\
               + ' tpm: ' + str(self.tpm_id).rjust(1)\
               + ' rx: ' + str(self.tpm_rx).rjust(2)


class Fit(Document):
    acquisition_id = DateTimeField()
    pol = BinaryField()
    antenna_id = ObjectIdField()
    fit_time = DateTimeField()
    fit_comment = StringField()
    channels = ListField()
    flags = StringField()
    phase_0 = FloatField()
    delay = FloatField()

    def __str__(self):
        return 'id: ' + str(self.antenna_id).rjust(2) + ' fit_time: ' + unicode(self.fit_time)


class Channel(Document):
    frequency = IntField()
    amp = FloatField()
    phase = FloatField()
    fit_id = ObjectIdField()
    antenna_id = ObjectIdField()

    def __str__(self):
        return 'freq: ' + str(self.frequency).rjust(2) \
               + ' ant: ' + str(self.antenna_id).rjust(2) \
               + ' amp: ' + str(self.amp).rjust(4)\
               + ' phase: ' + str(self.phase).rjust(4)


class Coefficient(Document):
    antenna_id = ObjectIdField()
    pol = StringField()
    calibration = ListField()
    download_time = DateTimeField()
