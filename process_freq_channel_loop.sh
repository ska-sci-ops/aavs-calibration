#!/bin/bash

export PATH=~/aavs-calibration/:$PATH

template="2023_??_??-??:??"
if [[ -n "$1" && "$1" != "-" ]]; then
   template="$1"
fi

station_id=3
station_name="AAVS2"

for dir in `ls -d ${template}`
do
   cd ${dir}
   echo "python ~/aavs-calibration/run_calibration.py -D . --station_id ${station_id} --station_name ${station_name} --show-output --keep_uv_files --no_calibration --do_not_update_last_cal"
   python ~/aavs-calibration/run_calibration.py -D . --station_id ${station_id} --station_name ${station_name} --show-output --keep_uv_files --no_calibration --do_not_update_last_cal

   # convert .uvfits to .uv files:   
   for uvfitsfile in `ls *.uvfits`
   do
      src=${uvfitsfile%%.uvfits}
      uv=${uvfitsfile%%uvfits}uv
      
      if [[ -d ${src}.uv ]]; then      
         echo "INFO : ${uvfitsfile} -> ${src}.uv alreadu done -> skipped"
      else
         echo "fits op=uvin in=\"$uvfitsfile\" out="${src}.uv" options=compress"
         fits op=uvin in="$uvfitsfile" out="${src}.uv" options=compress
      
         echo "puthd in=${src}.uv/jyperk value=1310.0"
         puthd in=${src}.uv/jyperk value=1310.0
      
         echo "puthd in=${src}.uv/systemp value=200.0"
         puthd in=${src}.uv/systemp value=200.0
      
         echo "uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv"
         uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
      
         echo "uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv"
         uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv
     fi
   done
   
   cd ..
done


