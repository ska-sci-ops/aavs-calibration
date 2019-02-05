from db import *
from time import time
import datetime
import bson
import pytz

db = connect('aavs_test', host='localhost', port=27017)
# for more information on queries: http://docs.mongoengine.org/guide/querying.html#filtering-queries

# get fits for all antennas for the latest fit_time (one entry for each pol per antenna)
f = Fit.objects[Fit.objects.count() - 1]

start = time()
f = Fit.objects(id=f.id)[0]
print f
print time() - start
fits = Fit.objects(fit_time=f.fit_time)
print fits[0].fit_time
print time() - start


start = time()
# get all entries for channel 128 for an antenna (station_id=1, antenna_nr=1) and a fit_time starting from 2019-01-29
channel_128 = Channel.objects(frequency=128,
                              antenna_id=Antenna.objects(antenna_nr=1, station_id=1).first().id,
                              fit_id__in=Fit.objects(fit_time__gte='2019-01-29 00:09:00.000000 +0000').distinct('id')
                              )
print time() - start
print channel_128.count()
