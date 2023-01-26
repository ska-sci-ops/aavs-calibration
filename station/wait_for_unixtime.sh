#!/bin/bash

end_uxtime=$1

sleep_time=1
if [[ -n "$2" && "$2" != "-" ]]; then
   sleep_time=$2
fi

ux=`date +%s`
while [[ $ux -lt $end_uxtime ]];
do
   echo "Waiting $sleep_time seconds ..."
   
   ux=`date +%s`
   sleep $sleep_time
done
