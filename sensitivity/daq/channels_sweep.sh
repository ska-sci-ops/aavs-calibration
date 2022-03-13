#!/bin/bash

# default EDA2:
config_file=/opt/aavs/config/eda2.yml
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

reprogram_every_n_iter=20
if [[ -n "$6" && "$6" != "-" ]]; then
   reprogram_every_n_iter=$6
fi

n_iter=-1 # <0 -> infinite loop
if [[ -n "$7" && "$7" != "-" ]]; then
   n_iter=$7
fi

options=""
if [[ -n "$8" && "$8" != "-" ]]; then
   options="$8"
fi

time_per_channel=28
if [[ -n "$9" && "$9" != "-" ]]; then
   time_per_channel=$9
fi

rm -f current_channel.txt

iteration=1
while [[ $n_iter -le 0 || $iteration -le $n_iter ]];
do
   
   echo
   echo "--------------------------------------------------- $iteration / $n_iter ---------------------------------------------------"
   date   
   echo "-1" > current_channel.txt
   
   extra_options="$options"
   rest=$(($iteration%$reprogram_every_n_iter))
   echo "Iteration = $iteration -> rest from division by $reprogram_every_n_iter is $rest"
   reprogram=0
   if [[ $rest == 0 && $iteration -gt 0 ]]; then
      extra_options="-IP"
      reprogram=1
   fi
   
   if [[ $interval -le 0 ]]; then
      # file started.txt is expected to be created in daq_sensitivity.sh script just before daq_receiver.py is started, we allow additional 10seconds for it to launch and 
      # start looping over channels after this 
      echo "~/aavs-calibration/sensitivity/daq/wait_for_file.sh started.txt"
      ~/aavs-calibration/sensitivity/daq/wait_for_file.sh started.txt

      if [[ $reprogram -le 0 ]]; then
         echo "sleep 10"
         sleep 10
      fi
   fi
   
   # just one iteration over channels :      
   echo "python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=${config_file} --time_per_channel=${time_per_channel} --start_channel=${start_channel} --end_channel=${end_channel} --step-channel=${step} --n_iterations=1 $extra_options"
   python ~/aavs-calibration/sensitivity/daq/channels_sweep.py --config=${config_file} --time_per_channel=${time_per_channel} --start_channel=${start_channel} --end_channel=${end_channel} --step-channel=${step} --n_iterations=1 $extra_options
   
   echo "rm -f current_channel.txt"
   rm -f current_channel.txt   

   if [[ $interval -gt 0 ]]; then
      echo "sleep $interval"
      sleep $interval
   fi
   
   iteration=$(($iteration+1))
done
