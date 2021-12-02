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

config=/opt/aavs/config/${station_name}.yml
if [[ -n "$3" && "$3" != "-" ]]; then
   config=$3
fi

calibration_options=""
if [[ -n "$4" && "$4" != "-" ]]; then
   calibration_options=$4
fi

n_channels=-1
if [[ -n "$5" && "$5" != "-" ]]; then
   n_channels=$5
fi


# WARNING : should be later in the script, but this value is required earlier :
pol_swap_options=""
if [[ $station_name == "eda2" ]]; then
   echo "WARNING : X and Y polarisations have been un-swapped on 23 September 2021 -> no need to do anything about it for the new data"
#   echo "EDA2 station -> polarisation swap required (please make sure the .pkl was not swapped at the time of creation)"
#   pol_swap_options="--pol_swap"
fi


cal_dir=/data/real_time_calibration/last_calibration


cd ${cal_dir}

last_calib=`ls -tr *_ch${channel_str}*.pkl | tail -1`
echo "Last calibration pickle file is $last_calib"

if [[ $n_channels -gt 4 ]]; then
   end_channel=$(($channel+$n_channels))

   echo "Calibrating $n_channels channels starting from channel = $channel to $end_channel (inclusive) ..."
   
   while [[ $channel -le $end_channel ]];
   do
      echo "python ~/aavs-calibration/station/calibrate_station_newsoft.py --config=${config}  --calibrate_station --calibrate_file=${last_calib} --frequency_channel=${channel} --mccs_db --n_channels=1 ${pol_swap_options} ${calibration_options}"
      python ~/aavs-calibration/station/calibrate_station_newsoft.py --config=${config}  --calibrate_station --calibrate_file=${last_calib} --frequency_channel=${channel} --mccs_db --n_channels=1 ${pol_swap_options} ${calibration_options}

      channel=$(($channel+1))
   done
else 
   echo "WARNING : calibrating a single channel = $channel , which may not be sufficient when recording multiple channels !"
      
   echo "python ~/aavs-calibration/station/calibrate_station_newsoft.py --config=${config}  --calibrate_station --calibrate_file=${last_calib} --frequency_channel=${channel} --mccs_db ${pol_swap_options} ${calibration_options}"
   python ~/aavs-calibration/station/calibrate_station_newsoft.py --config=${config}  --calibrate_station --calibrate_file=${last_calib} --frequency_channel=${channel} --mccs_db ${pol_swap_options} ${calibration_options}
fi
cd -
