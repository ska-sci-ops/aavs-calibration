#!/bin/bash

# calibrates station using the most recent calibration solutions in /data/real_time_calibration/last_calibration/

channel=204
if [[ -n "$1" && "$1" != "-" ]]; then
   channel=$1
fi
channel_str=`echo $channel | awk '{printf("%03d",$1);}'`

station_name=eda2
if [[ -n "$2" && "$2" != "-" ]]; then
   station_name=$2
fi

# WARNING : should be later in the script, but this value is required earlier :
pol_swap_options=""
if [[ $station_name == "eda2" ]]; then
   echo "EDA2 station -> polarisation swap required (please make sure the .pkl was not swapped at the time of creation)"
   pol_swap_options="--pol_swap"
fi


cal_dir=/data/real_time_calibration/last_calibration


cd ${cal_dir}

last_calib=`ls -tr *_ch${channel_str}*.pkl | tail -1`
echo "Last calibration pickle file is $last_calib"

echo "python ~/aavs-calibration/station/calibrate_station_newsoft.py --config=/opt/aavs/config/${station_name}.yml  --calibrate_station --calibrate_file=${last_calib} ${pol_swap_options}"
sleep 5
python ~/aavs-calibration/station/calibrate_station_newsoft.py --config=/opt/aavs/config/${station_name}.yml  --calibrate_station --calibrate_file=${last_calib} ${pol_swap_options}

cd -
