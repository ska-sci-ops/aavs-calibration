#!/bin/bash

export PATH=~/aavs-calibration/:$PATH

template="2023_??_??-??:??"
if [[ -n "$1" && "$1" != "-" ]]; then
   template="$1"
fi

station_id=3
station_name="AAVS2"

for dir in `ls -d ${template}`
do
   cd ${dir}
   echo "python ~/aavs-calibration/run_calibration.py -D . --station_id ${station_id} --station_name ${station_name} --show-output --keep_uv_files --no_calibration --do_not_update_last_cal"
   python ~/aavs-calibration/run_calibration.py -D . --station_id ${station_id} --station_name ${station_name} --show-output --keep_uv_files --no_calibration --do_not_update_last_cal
   cd ..
done


