import datetime

from db import Fit, Antenna, Channel, convert_datetime_to_timestamp
from connect import connect_to_db


db = connect_to_db()
# for more information on queries: http://docs.mongoengine.org/guide/querying.html#filtering-queries


# get fits for all antennas for the latest fit_time (one entry for each pol per antenna)
fits = Fit.objects(fit_time=Fit.objects().order_by('-id').first().fit_time)

dt = datetime.datetime.strptime('2019-01-29 00:09:00.000000 UTC', '%Y-%m-%d %H:%M:%S.%f %Z')
# get all entries for channel 128 for an antenna (station_id=1, antenna_nr=1) and a fit_time starting from 2019-01-29
channel_128 = Channel.objects(frequency=128,
                              antenna_id=Antenna.objects(antenna_nr=1, station_id=1).first().id,
                              fit_id__in=Fit.objects(fit_time__gte=convert_datetime_to_timestamp(dt)).distinct('id'))
