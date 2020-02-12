#!/bin/bash

# assuming full loop takes ~600 seconds 

iteration=0
while [ 1 ];
do
   dtm=`date +%Y%m%d_%H%M%S`
   mkdir -p ${dtm}

   echo
   echo "--------------------------------------------------- $iteration ---------------------------------------------------"   
   echo "Date/time = $dtm"   
   cd ${dtm}   
   pwd
   echo "python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -d . -X --channel_samples=262144 -t 16 --continuous_period 4 --duration 1200"
   python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -d . -X --channel_samples=262144 -t 16 --continuous_period 4 --duration 1200
   cd ../

   while [[ ! -s started_channel_loop.txt ]];
   do
      echo "Waiting for new channel loop file ( started_channel_loop.txt )"
      sleep 1
   done

   iteration=$(($iteration+1))
done
