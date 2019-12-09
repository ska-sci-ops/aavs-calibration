#!/bin/bash

# caldir="/data/aavs2/real_time_calibration/"
station_name="eda2"
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name="$1"
fi
station_name_lower=`echo $station_name | awk '{print tolower($1);}'`

data_dir="./"
if [[ -n "$2" && "$2" != "-" ]]; then
   data_dir=$2
   cd ${data_dir}
fi

# but on aavs1-server
www_dir="/exports/calibration/"
if [[ -n "$3" && "$3" != "-" ]]; then
   www_dir=$3
fi


curr_path=`pwd`
cal_dtm=`basename $curr_path`
echo "Real-time calibration path = $curr_path -> cal_dtm = $cal_dtm"

images_dir=${www_dir}/${station_name_lower}/${cal_dtm}

echo "ssh aavs@aavs1-server \"mkdir -p ${images_dir}\""
ssh aavs@aavs1-server "mkdir -p ${images_dir}"

echo "python ~/aavs-calibration/monitoring/plotcal_v_freq.py"
python ~/aavs-calibration/monitoring/plotcal_v_freq.py


echo "scp *.png aavs@aavs1-server:${images_dir}/"
scp *.png aavs@aavs1-server:${images_dir}/

