#!/bin/bash

station=eda2
if [[ -n "$1" && "$1" != "-" ]]; then
   station=$1
fi

while [ 1 ];
do
   echo
   date

   if [[ $station == aavs2 ]]; then      
      echo "time antenna_health/check_antenna_health_aavs2.sh"
      time antenna_health/check_antenna_health_aavs2.sh   
   else
      echo "time antenna_health/check_antenna_health_eda2.sh"
      time antenna_health/check_antenna_health_eda2.sh   
   fi
   
   echo "sleep 3600"
   sleep 3600
done
