#!/bin/bash

total_duration=86400
if [[ -n "$1" && "$1" != "-" ]]; then
   total_duration=$1
fi

curr_dir=`pwd`
if [[ -n "$2" && "$2" != "-" ]]; then
   curr_dir="$2"
   cd $curr_dir
fi

n_integrations_per_file=2
if [[ -n "$3" && "$3" != "-" ]]; then
   n_integrations_per_file=$3
fi

n_samples=458752 # was 917504
if [[ -n "$4" && "$4" != "-" ]]; then
   n_samples="$4"
fi

echo "~/bin/init_station.sh"
~/bin/init_station.sh

export PYTHONPATH=/home/amagro/multi_chan_station_acq/aavs-system/python/:$PYTHONPATH

start_ux=`date +%s`
end_ux=$(($start_ux+$total_duration))

echo "##########################"
echo "PARAMETERS:"
echo "##########################"
echo "total_duration = $total_duration [sec]"
echo "Start ux = $start_ux"
echo "End   ux = $end_ux"
echo "n_integrations_per_file = $n_integrations_per_file"
echo "n_samples = $n_samples"
echo "##########################"

echo "Multiple calibration loops started at:"
date
echo "In the directory:"
pwd

loop_count=0
ux=$start_ux
while [[ $ux -lt $end_ux ]];
do
   echo
   echo "Loop $loop_count started at unixtime = $ux :"
   date
   
#   echo "python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=$curr_dir"
#   python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=$curr_dir

   # 
   dtm_utc=`date --utc +%Y%m%d%H%M%S`
   echo "python ~/aavs-calibration/calibration_loop_aavs2.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=${curr_dir} --daq_library=/opt/aavs/lib/libaavsdaq_fast_corr.so --samples=${n_samples} --first_channel=64 --last_channel=448 --correlator-channels=1 --n_integrations_per_file=${n_integrations_per_file} > ${dtm_utc}.log 2>&1"
   python ~/aavs-calibration/calibration_loop_aavs2.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=${curr_dir} --daq_library=/opt/aavs/lib/libaavsdaq_fast_corr.so --samples=${n_samples} --first_channel=64 --last_channel=448 --correlator-channels=1 --n_integrations_per_file=${n_integrations_per_file} > ${dtm_utc}.log 2>&1
   
   ux=`date +%s`
   loop_count=$(($loop_count+1))
done

