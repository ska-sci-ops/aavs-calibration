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
   echo "Loop $loop_count started at:"
   date
   
   echo "python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=$curr_dir"
   python ~/aavs-calibration/calibration_loop.py --config=/opt/aavs/config/aavs2.yml -i enp216s0f0 --do_not_calibrate --directory=$curr_dir
   
   loop_count=$(($loop_count+1))
done

