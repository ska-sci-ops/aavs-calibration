#!/bin/bash

while [ 1 ];
do
   echo
   date
   
   echo "time check_antenna_health_eda2.sh"
   time check_antenna_health_eda2.sh   
   
   echo "sleep 3600"
   sleep 3600
done
