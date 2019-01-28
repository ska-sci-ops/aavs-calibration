from db import *
from dateutil.parser import parse


def cond_1():
    for f in Fit.objects(fit_time=parse('2019-01-25 08:48:21.201000')):
        print f.amp_phase_per_freq


def cond_2():
    for c in Channel.objects(frequency=128, antenna_id=a.id):
        print c


cond_1()
# cond_2()
