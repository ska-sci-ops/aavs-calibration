from datetime import datetime, timedelta
from random import randint
from pytz import UTC
from multiprocessing import freeze_support, Pool
from time import sleep
from sys import stdout

from db import Channel, Fit, Antenna, Coefficient, convert_datetime_to_timestamp
from purge_db import purge
from connect import connect_to_db


COMPLEX_LIST = [complex(randint(0, 5), imag=randint(0, 5)).__str__() for c in range(512)]

db = connect_to_db()

ANTENNAS = 256  # number of antennas
MONITOR = True  # print status updates
MONITOR_INTERVAL = 60  # interval of status updates in seconds
PROCESSES = 2  # number of processes to fill the db
RUNS = 1440  # 1 run generates 1 fit and 1 coefficient / antenna and pol (256 antennas -> 512 fits
CLEAR = True  # clear db before fill


def add_antennas():
    """ adds n antennas to the db. n = ANTENNA """
    for i in range(ANTENNAS):
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


def add_coefficients(runs):
    """
    adds a coefficient calibration to every antenna in the db. number of executions defined by RUNS
    """
    for r in range(runs):
        now = convert_datetime_to_timestamp(datetime.now(UTC))
        for a in Antenna.objects:
            Coefficient(antenna_id=a.id,
                        pol=0,
                        calibration=COMPLEX_LIST,
                        download_time=now).save()

            Coefficient(antenna_id=a.id,
                        pol=1,
                        calibration=COMPLEX_LIST,
                        download_time=now).save()


def add_fit_and_channels(runs):
    """
    adds a fit per antenna and pol including the channels to the db.
    :param runs number of executions
    """
    for r in range(runs):
        now = convert_datetime_to_timestamp(datetime.now(UTC))
        for a in Antenna.objects:
            fit_x = Fit(acquisition_time=now,
                        pol=0,
                        antenna_id=a.id,
                        fit_time=now,
                        fit_comment='',
                        flags='',
                        phase_0=r * 3,
                        delay=r * 10).save()

            fit_y = Fit(acquisition_time=now,
                        pol=1,
                        antenna_id=a.id,
                        fit_time=now,
                        fit_comment='',
                        flags='',
                        phase_0=r * 4,
                        delay=r * 11).save()

            fit_x.channels = [
                Channel(frequency=j,
                        amp=j + j / 10,
                        phase=j + j / 10,
                        fit_id=fit_x.id,
                        antenna_id=fit_x.antenna_id).save()
                for j in range(512)]
            fit_y.channels = [
                Channel(frequency=j,
                        amp=j + j / 10,
                        phase=j + j / 10,
                        fit_id=fit_y.id,
                        antenna_id=fit_y.antenna_id).save()
                for j in range(512)]

            fit_x.save()
            fit_y.save()


def monitor_progress(interval):
    """
    :param interval of seconds for status update
    prints progress of populating the db
    """
    total_fits = RUNS * ANTENNAS * 2
    fit_count = 0
    coef_count = 0
    while fit_count < total_fits or coef_count < total_fits:

        out = 'Antennas ' + str(Antenna.objects.count()).rjust(len(str(ANTENNAS))) + '/' + str(ANTENNAS) +\
              '  Fits ' + str(fit_count).rjust(len(str(total_fits))) + '/' + str(total_fits) +\
              '  Channels ' + str(Channel.objects.count()).rjust(len(str(total_fits * 512))) + '/' + str(total_fits * 512) + \
              '  Coefficients ' + str(coef_count).rjust(len(str(total_fits))) + '/' + str(total_fits) +\
              '  fit run # ' + str(int(fit_count / ANTENNAS / 2)).rjust(len(str(RUNS))) + '/' + str(RUNS) +\
              '  coef run # ' + str(int(coef_count / ANTENNAS / 2)).rjust(len(str(RUNS))) + '/' + str(RUNS)
        stdout.write('\r' + out)
        stdout.flush()

        sleep(interval)
        fit_count = Fit.objects.count()
        coef_count = Coefficient.objects.count()


def divide_runs():
    """
    splits runs into number of processes
    :returns list of batch sizes
    """
    quotient = RUNS / PROCESSES
    remainder = RUNS % PROCESSES
    results = []
    for i in range(PROCESSES):
        results.append(quotient + 1 if i < remainder else quotient)
    return results


def main():
    if CLEAR:
        purge()
        Antenna.drop_collection()
    p = Pool(PROCESSES + 1 if MONITOR_INTERVAL else PROCESSES)
    if MONITOR:
        p.map_async(monitor_progress, [MONITOR_INTERVAL])
    add_antennas()
    p.map_async(add_coefficients, [RUNS])
    p.map_async(add_fit_and_channels, divide_runs())

    p.close()
    p.join()


if __name__ == '__main__':
    freeze_support()
    main()
