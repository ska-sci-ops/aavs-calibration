#!/bin/bash

# default EDA2:
config_file=/opt/aavs/config/eda2_full_delayperant.yml
if [[ -n "$1" && "$1" != "-" ]]; then
   config_file=$1
fi

# interval between channel loops 
interval=1800

rm -f started_channel_loop.txt

iteration=1
while [ 1 ];
do
   
   echo
   echo "--------------------------------------------------- $iteration ---------------------------------------------------"
   date   
   date +%s > started_channel_loop.txt
   # just one iteration over channels :      
   echo "python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=${config_file} --time_per_channel=28 --start_channel=51 --end_channel=450 --step-channel=13 --n_iterations=1"
   python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=${config_file} --time_per_channel=28 --start_channel=51 --end_channel=450 --step-channel=13 --n_iterations=1
   
   echo "rm -f started_channel_loop.txt"
   rm -f started_channel_loop.txt   

   echo "sleep $interval"
   sleep $interval
   
   iteration=$(($iteration+1))
done
