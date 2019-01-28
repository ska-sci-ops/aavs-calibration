from db import Channel, Fit, Antenna
from datetime import datetime, timedelta
import time

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

while True:
    now = datetime.now()
    for a in Antenna.objects:
        channels_x = []
        channels_y = []
        fit_x = Fit(acquisition_id=now,
                    pol='x',
                    antenna_id=a.id,
                    fit_time=now + timedelta(minutes=2),
                    fit_comment='',
                    flags='',
                    phase_0=a.antenna_nr % 3,
                    delay=a.antenna_nr / 10).save()

        fit_y = Fit(acquisition_id=now,
                    pol='y',
                    antenna_id=a.id,
                    fit_time=now + timedelta(minutes=2),
                    fit_comment='',
                    flags='',
                    phase_0=a.antenna_nr % 4,
                    delay=a.antenna_nr / 10).save()

        for j in range(512):
            channels_x.append(Channel(frequency=j,
                                      amp=j + j / 10,
                                      phase=j + j / 10,
                                      fit_id=fit_x.id,
                                      antenna_id=a.id).save())
            channels_y.append(Channel(frequency=j,
                                      amp=j + j / 10,
                                      phase=j + j / 10,
                                      fit_id=fit_y.id,
                                      antenna_id=a.id).save())

        fit_x.amp_phase_per_freq = channels_x
        fit_x.save()
        fit_y.amp_phase_per_freq = channels_y
        fit_y.save()

        print fit_x

    time.sleep(30)
