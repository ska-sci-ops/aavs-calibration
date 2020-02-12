#!/bin/bash

interval=300

rm -f started_channel_loop.txt

iteration=1
while [ 1 ];
do
   
   echo
   echo "--------------------------------------------------- $iteration ---------------------------------------------------"
   date   
   date +%s > started_channel_loop.txt
   # just one iteration over channels :      
   echo "python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=/opt/aavs/config/eda2_full_delayperant.yml --time_per_channel=28 --start_channel=51 --end_channel=450 --step-channel=13 --n_iterations=1"
   python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=/opt/aavs/config/eda2_full_delayperant.yml --time_per_channel=28 --start_channel=51 --end_channel=450 --step-channel=13 --n_iterations=1
   
   echo "rm -f started_channel_loop.txt"
   rm -f started_channel_loop.txt   

   echo "sleep $interval"
   sleep $interval
   
   iteration=$(($iteration+1))
done
