#!/bin/bash

while [ 1 ];
do
   
   echo "python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -d . -X --channel_samples=262144 -t 16 --continuous_period 4 --duration 620"
   python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -d . -X --channel_samples=262144 -t 16 --continuous_period 4 --duration 620 

   while [[ ! -s started_channel_loop.txt ]];
   do
      echo "Waiting for new channel loop file ( started_channel_loop.txt )"
      sleep 1
   done
done
