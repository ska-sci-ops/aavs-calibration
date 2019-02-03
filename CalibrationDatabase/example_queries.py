from db import *
from time import time
import datetime
import bson
import pytz

# get fits for all antennas for the latest fit_time (one entry for each pol per antenna)
# fits = Fit.objects(fit_time=Fit.objects().order_by('-fit_time').first().fit_time)
print Antenna.objects.count()
print Fit.objects.count()

for f in Fit.objects:
    print len(f.channels)

now = datetime.datetime.now(pytz.utc) + datetime.timedelta(minutes=2)
print now.tzinfo
start = time()
# get all entries for channel 128 for an antenna (station_id=1, antenna_nr=1) and a fit_time starting from 2019-01-29
channel_128 = Channel.objects(frequency=128,
                              antenna_id=Antenna.objects(antenna_nr=1, station_id=1).first().id,
                              fit_id__in=Fit.objects(fit_time__gte='2019-01-29 00:09:00.000000 +0000').distinct('id')
                              )


print time() - start
print channel_128.count()
