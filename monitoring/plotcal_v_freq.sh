#!/bin/bash

# caldir="/data/aavs2/real_time_calibration/"
station_name="eda2"
station_id=2
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name="$1"
fi
station_name_lower=`echo $station_name | awk '{print tolower($1);}'`
if [[ $station_name_lower == "aavs2" ]]; then
   station_id=3
fi

data_dir="./"
if [[ -n "$2" && "$2" != "-" ]]; then
   data_dir=$2
   cd ${data_dir}
fi

options=""
fittime=
if [[ -n "$3" && "$3" != "-" ]]; then
   fittime=$3
   options="--fittime=$fittime"
fi


# but on aavs1-server
www_dir="/exports/calibration/${station_name}/antenna_health/"
if [[ -n "$3" && "$3" != "-" ]]; then
   www_dir=$3
fi

echo "################################################"
echo "PARAMETERS:"
echo "################################################"
echo "station_name = $station_name ( station_id = $station_id )"
echo "fittime      = $fittime ($options)"
echo "################################################"


curr_path=`pwd`
cal_dtm=`basename $curr_path`
echo "Real-time calibration path = $curr_path -> cal_dtm = $cal_dtm"

echo "python ~/aavs-calibration/monitoring/plotcal_v_freq.py --station_id=${station_id} ${options}"
python ~/aavs-calibration/monitoring/plotcal_v_freq.py --station_id=${station_id} ${options}

# prepare directorios and copy images to WWW server :
images_dir=${www_dir}/${station_name_lower}/${cal_dtm}

echo "ssh aavs@aavs1-server \"mkdir -p ${images_dir} ${www_dir}/${station_name_lower}/current\""
ssh aavs@aavs1-server "mkdir -p ${images_dir} ${www_dir}/${station_name_lower}/current"

# echo "ssh aavs@aavs1-server \"ln -sf ${images_dir} ${www_dir}/${station_name_lower}/current\""
# ssh aavs@aavs1-server "ln -sf ${images_dir} ${www_dir}/${station_name_lower}/current"

echo "scp ~/aavs-calibration/monitoring/html/plot_calsol_index_${station_name_lower}.html aavs@aavs1-server:${images_dir}/index.html"
scp ~/aavs-calibration/monitoring/html/plot_calsol_index_${station_name_lower}.html aavs@aavs1-server:${images_dir}/index.html

echo "scp ~/aavs-calibration/monitoring/html/plot_calsol_index_${station_name_lower}.html aavs@aavs1-server:${www_dir}/${station_name_lower}/current/index.html"
scp ~/aavs-calibration/monitoring/html/plot_calsol_index_${station_name_lower}.html aavs@aavs1-server:${www_dir}/${station_name_lower}/current/index.html


echo "scp *.png aavs@aavs1-server:${images_dir}/"
scp *.png aavs@aavs1-server:${images_dir}/

echo "scp *.png aavs@aavs1-server:${www_dir}/${station_name_lower}/current/"
scp *.png aavs@aavs1-server:${www_dir}/${station_name_lower}/current/

# Get delays from DB and format them for the station config file:
# PGUSER=aavs
pwd
echo "python ~/aavs-calibration/monitoring/delay_per_tpm.py --db=$PGUSER --station_id=${station_id}"
python ~/aavs-calibration/monitoring/delay_per_tpm.py --db=$PGUSER --station_id=${station_id}

echo "scp delay_vs_tpm_lastdb.conf aavs@aavs1-server:${www_dir}/${station_name_lower}/current/"
scp delay_vs_tpm_lastdb.conf aavs@aavs1-server:${www_dir}/${station_name_lower}/current/

echo "scp delay_vs_tpm_lastdb.conf aavs@aavs1-server:${images_dir}/"
scp delay_vs_tpm_lastdb.conf aavs@aavs1-server:${images_dir}/
