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

export PYTHONPATH=/home/amagro/multi_chan_station_acq/aavs-system/python/:$PYTHONPATH

start_ux=`date +%s`
end_ux=$(($start_ux+$total_duration))

echo "##########################"
echo "PARAMETERS:"
echo "##########################"
echo "total_duration = $total_duration [sec]"
echo "Start ux = $start_ux"
echo "End   ux = $end_ux"
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
   echo "python ~/aavs-calibration/calibration_loop_aavs2.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=${curr_dir} --daq_library=/opt/aavs/lib/libaavsdaq_fast_corr.so --samples=917504 --first_channel=64 --last_channel=448 --correlator-channels=1"
   python ~/aavs-calibration/calibration_loop_aavs2.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=${curr_dir} --daq_library=/opt/aavs/lib/libaavsdaq_fast_corr.so --samples=917504 --first_channel=64 --last_channel=448 --correlator-channels=1
   
   ux=`date +%s`
   loop_count=$(($loop_count+1))
done

