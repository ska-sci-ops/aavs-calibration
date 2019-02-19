from urllib import urlopen

from db import Antenna, connect_to_db

connect_to_db()

# This is used to re-map ADC channels index to the RX
# number going into the TPM
# [Antenna number / RX]
antenna_preadu_mapping = {0: 1, 1: 2, 2: 3, 3: 4,
                          8: 5, 9: 6, 10: 7, 11: 8,
                          15: 9, 14: 10, 13: 11, 12: 12,
                          7: 13, 6: 14, 5: 15, 4: 16}

# Some global params
nof_antennas = 256


def get_antenna_data():
    """
    Reads antenna base locations from the Google Drive sheet and fills the data into the database
    """

    # Read antenna location spreadsheet
    response = urlopen('https://docs.google.com/spreadsheets/d/e/2PACX-1vRIpaYPims9Qq9JEnZ3AfZtTaYJYWMsq2CWRg'
                       'B-KKFAQOZoEsV0NV2Gmz1fDfOJm7cjDAEBQWM4FgyP/pub?gid=220529610&single=true&output=tsv')

    html = response.read().split('\n')

    # Two antennas are not in-place, however we still get an input into the TPM
    missing = 0
    switched_preadu_map = {y: x for x, y in antenna_preadu_mapping.iteritems()}
    # Read all antenna rows from spreadsheet response
    for i in range(1, nof_antennas + 1):
        items = html[i].split('\t')
        # Parse antenna row
        try:
            tpm, rx = int(items[7]), int(items[8])
            east, north, up = float(items[15].replace(',', '.')), float(items[17].replace(',', '.')), 0
        except ValueError:
            if missing == 0:
                tpm, rx = 1, 9
                east, north, up = 17.525, -1.123, 0
            else:
                tpm, rx = 11, 9
                east, north, up = 9.701, -14.627, 0
            missing += 1

        # Fill data into database
        a = Antenna.objects(antenna_nr=(tpm - 1) * 16 + switched_preadu_map[rx], station_id=0).first()
        if not a:
            a = Antenna(antenna_nr=(tpm - 1) * 16 + switched_preadu_map[rx], station_id=0)

        a.x_pos = east
        a.y_pos = north
        a.base_id = int(items[1])
        a.tpm_id = tpm
        a.tpm_rx = rx
        a.antenna_type = Antenna.SKALA2
        a.status_x = ''
        a.status_y = ''
        a.save()


if __name__ == '__main__':
    get_antenna_data()
