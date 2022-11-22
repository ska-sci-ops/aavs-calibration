#!/bin/bash

datadir=/storage/monitoring/integrated_data/eda2/
if [[ -n "$1" && "$1" != "-" ]]; then
   datadir="$1"
fi

while [ 1 ];
do
   echo
   date
   
   echo "time check_antenna_health_eda2.sh ${datadir}"
   time check_antenna_health_eda2.sh ${datadir}
   
   echo "sleep 3600"
   sleep 3600
done
