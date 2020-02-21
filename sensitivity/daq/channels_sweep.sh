#!/bin/bash

# default EDA2:
config_file=/opt/aavs/config/eda2_full_delayperant.yml
if [[ -n "$1" && "$1" != "-" ]]; then
   config_file=$1
fi

start_channel=51
if [[ -n "$2" && "$2" != "-" ]]; then
   start_channel=$2
fi

end_channel=450
if [[ -n "$3" && "$3" != "-" ]]; then
   end_channel=$3
fi

step=13
if [[ -n "$4" && "$4" != "-" ]]; then
  step=$4
fi

# interval between channel loops 
interval=1800
if [[ -n "$5" && "$5" != "-" ]]; then
   interval=$5
fi


rm -f current_channel.txt

iteration=1
while [ 1 ];
do
   
   echo
   echo "--------------------------------------------------- $iteration ---------------------------------------------------"
   date   
   echo "-1" > current_channel.txt
   # just one iteration over channels :      
   echo "python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=${config_file} --time_per_channel=28 --start_channel=${start_channel} --end_channel=${end_channel} --step-channel=${step} --n_iterations=1"
   python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=${config_file} --time_per_channel=28 --start_channel=${start_channel} --end_channel=${end_channel} --step-channel=${step} --n_iterations=1
   
   echo "rm -f current_channel.txt"
   rm -f current_channel.txt   

   echo "sleep $interval"
   sleep $interval
   
   iteration=$(($iteration+1))
done