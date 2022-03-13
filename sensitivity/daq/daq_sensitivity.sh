#!/bin/bash

# assuming full loop takes ~600 seconds 

daq_run_time=3600
if [[ -n "$1" && "$1" != "-" ]]; then
   daq_run_time=$1
fi

iteration=0
while [ 1 ];
do
   dtm=`date +%Y%m%d_%H%M%S`
   mkdir -p ${dtm}

   echo
   echo "--------------------------------------------------- $iteration ---------------------------------------------------"   
   echo "Date/time = $dtm"   
   pwd
   
   echo "date > started.txt"
   date > started.txt
   
   echo "python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -d ${dtm}/ -X --channel_samples=262144 -t 16 --continuous_period 4 --duration ${daq_run_time}"
   python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -d ${dtm}/ -X --channel_samples=262144 -t 16 --continuous_period 4 --duration ${daq_run_time}
   
   echo "rm -f started.txt"
   rm -f started.txt

   while [[ ! -s current_channel.txt ]];
   do
      echo "Waiting for new channel loop file ( current_channel.txt )"
      sleep 1
   done

   iteration=$(($iteration+1))
done
