#!/bin/bash

dt=`date +%Y_%m_%d`
if [[ -n "$1" && "$1" != "-" ]]; then
   dt="$1"
fi

caldir=/data/real_time_calibration/
if [[ -n "$2" && "$2" != "-" ]]; then
   caldir=$2
fi

destination="nimbus4fix:/data/real_time_calibration/"
if [[ -n "$3" && "$3" != "-" ]]; then
   destination="$3"
fi

echo "############################################"
echo "PARAMETERS:"
echo "############################################"
echo "dt = $dt"
echo "caldir = $caldir"
echo "destination = $destination"
echo "############################################"
date

if [[ -d ${caldir} ]]; then
   cd ${caldir}
   lastcal=`ls -d ${caldir}/${dt}* | tail -1`
   
   echo "rsync -avP ${lastcal} ${destination}"
   rsync -avP ${lastcal} ${destination}
else
   echo "ERROR : calibration directory ${caldir} does not exist"
fi
