#!/bin/bash

# calibrates station using the most recent calibration solutions in /data/real_time_calibration/last_calibration/

channel=204
if [[ -n "$1" && "$1" != "-" ]]; then
   channel=$1
fi

station_name=eda2
if [[ -n "$2" && "$2" != "-" ]]; then
   station_name=$2
fi

cal_dir=/data/real_time_calibration/last_calibration


cd ${cal_dir}

last_calib=`ls -tr *_ch${channel}*.pkl | tail -1`
echo "Last calibration pickle file is $last_calib"

echo "python ~/aavs-calibration/station/calibrate_station_newsoft.py -- --config=/opt/aavs/config/${station_name}.yml  --calibrate_station --calibrate_file=${last_calib}"
sleep 5
python ~/aavs-calibration/station/calibrate_station_newsoft.py -- --config=/opt/aavs/config/${station_name}.yml  --calibrate_station --calibrate_file=${last_calib}

cd -
