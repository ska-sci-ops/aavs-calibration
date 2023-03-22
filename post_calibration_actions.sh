#!/bin/bash

export PATH=~/aavs-calibration/station/:$PATH

station_name=eda2
station_id=2
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name=$1
fi


if [[ $station_name == "aavs2" ]]; then
   station_id=3
else
   station_id=1
fi


echo "########################################"
echo "PARAMETERS:"
echo "########################################"
echo "Station name = $station_name (id = $station_id)"
echo "########################################"


mkdir -p fit2db
cd fit2db/
echo "~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1"
~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1

