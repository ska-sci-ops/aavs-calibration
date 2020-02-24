#!/bin/bash

station=eda2
if [[ -n "$1" && "$1" != "-" ]]; then
   station=$1
fi
station_upper=`echo $station | awk '{print toupper($1);}'`

ch=-1 # means copy all txt files 
if [[ -n "$2" && "$2" != "-" ]]; then
   ch=$2
fi

local_caldir="/home/msok/Desktop/${station_upper}/real_time_calibration"

last_cal_dir=`ssh ${station} "ls -dtr /data/real_time_calibration/2???_??_??-??:??/ |tail -1"`
last_cal_dtm=`basename ${last_cal_dir}`

echo "last_cal_dtm = $last_cal_dtm ( $last_cal_dir )"

if [[ ! -d ${local_caldir}/${last_cal_dtm} ]]; then
   mkdir -p ${local_caldir}/${last_cal_dtm}
   cd ${local_caldir}/${last_cal_dtm}
   pwd

   if [[ $ch -ge 0 ]]; then
      echo "rsync -avP ${station}:${last_cal_dir}/*${ch}*.txt ."
      rsync -avP ${station}:${last_cal_dir}/*${ch}*.txt .
   else
      echo "rsync -avP ${station}:${last_cal_dir}/*.txt ."
      rsync -avP ${station}:${last_cal_dir}/*.txt .
   fi   
else
   echo "INFO : ${local_caldir}/${last_cal_dtm} already exists -> nothing done (use force=1 parameter)"
fi   

