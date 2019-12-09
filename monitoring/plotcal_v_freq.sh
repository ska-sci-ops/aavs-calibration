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

echo "python ~/aavs-calibration/monitoring/plotcal_v_freq.py"
python ~/aavs-calibration/monitoring/plotcal_v_freq.py

# prepare directorios and copy images to WWW server :
images_dir=${www_dir}/${station_name_lower}/${cal_dtm}

echo "ssh aavs@aavs1-server \"mkdir -p ${images_dir} ${www_dir}/${station_name_lower}/current\""
ssh aavs@aavs1-server "mkdir -p ${images_dir} ${www_dir}/${station_name_lower}/current"

# echo "ssh aavs@aavs1-server \"ln -sf ${images_dir} ${www_dir}/${station_name_lower}/current\""
# ssh aavs@aavs1-server "ln -sf ${images_dir} ${www_dir}/${station_name_lower}/current"

echo "scp ~/aavs-calibration/monitoring/html/plot_calsol_index.html aavs@aavs1-server:${images_dir}/index.html"
scp ~/aavs-calibration/monitoring/html/plot_calsol_index.html aavs@aavs1-server:${images_dir}/index.html


echo "scp *.png aavs@aavs1-server:${images_dir}/"
scp *.png aavs@aavs1-server:${images_dir}/

echo "scp *.png aavs@aavs1-server:${www_dir}/${station_name_lower}/current/"
scp *.png aavs@aavs1-server:${www_dir}/${station_name_lower}/current/

# Get delays from DB and format them for the station config file:
# PGUSER=aavs
echo "python ~/aavs-calibration/monitoring/delay_per_tpm.py --db=$PGUSER --station_id=3"
python ~/aavs-calibration/monitoring/delay_per_tpm.py --db=$PGUSER --station_id=3
