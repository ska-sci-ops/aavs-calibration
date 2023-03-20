#!/bin/bash

fit_time="2023-03-14 12:23:00+08:00"
if [[ -n "$1" && "$1" != "-" ]]; then
   fit_time="$1"
fi

sqlfile=amp_fitted.sql

rm -f ${sqlfile}

for fitted_file in `ls last_calibration_???_fitted.txt`
do
   ant=`echo $fitted_file | awk '{idx=index($1,"_");str=substr($1,idx+1);idx=index(str,"_");str2=substr(str,idx+1);idx2=index(str2,"_");print substr(str2,1,idx2-1);}'`
   amp_x_list=`cat $fitted_file | awk -v amp_list="" '{if($1!="#"){if(length(amp_list)<=0){amp_list=$2;}else{amp_list=amp_list "," $2;}}}END{print amp_list;}'`
   amp_y_list=`cat $fitted_file | awk -v amp_list="" '{if($1!="#"){if(length(amp_list)<=0){amp_list=$4;}else{amp_list=amp_list "," $4;}}}END{print amp_list;}'`
   
   echo "UPDATE calibration_solution set x_amp_fit='{"$amp_x_list"}',y_amp_fit='{"$amp_y_list"}' where fit_time='"$fit_time"' and ant_id=$ant;" >> ${sqlfile}
done
