#!/bin/bash

end_uxtime=$1

ux=`date +%s`
while [[ $ux -lt $end_uxtime ]];
do
   echo "Waiting 10 seconds ..."
   
   ux=`date +%s`
   sleep 10
done
