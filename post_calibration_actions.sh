#!/bin/bash

export PATH=~/aavs-calibration/station/:$PATH

# DEFAULT IS EDA2 :
station_name=eda2
station_id=2
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name=$1
fi

if [[ $station_name == "aavs2" || $station_name == "AAVS2" ]]; then
   station_id=3
fi

last_cal_dir=`pwd`
if [[ ! -s chan_204_selfcal_pha_XX.txt ]]; then
   # checking a single file to check if this is folder with calibration solutions from MIRIAD (Randall's calibration loop format) :
   echo "INFO : no calibration in local directory : $last_cal_dir -> looking for last calibration automatically in $cal_path ..."
   
   last_cal_dir=`ls -dtr /data/real_time_calibration/2???_??_??-??:??/ |tail -1`   
fi


echo "########################################"
echo "PARAMETERS:"
echo "########################################"
echo "Station name = $station_name (id = $station_id)"
echo "Last cal dir = $last_cal_dir"
echo "########################################"


pwd
cd $last_cal_dir
pwd

mkdir -p fit2db
cd fit2db/
echo "~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1"
~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1

