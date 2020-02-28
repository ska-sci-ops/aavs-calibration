#!/bin/bash

station=EDA2
if [[ -n "$1" && "$1" != "-" ]]; then
   station=$1
fi

ch=50
while [[ $ch -le 400 ]];
do
   echo "~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -k ${ch}"
   ~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -k ${ch}

   ch=$(($ch+1))
done
