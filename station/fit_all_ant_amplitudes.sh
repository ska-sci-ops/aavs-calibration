#!/bin/bash

do_dump=1
if [[ -n "$1" && "$1" != "-" ]]; then
   do_dump=$1
fi

do_plot=0
if [[ -n "$2" && "$2" != "-" ]]; then
   do_plot=$2
fi

polynomial_order=2
channels_around=10

if [[ $do_dump -gt 0 ]]; then
   echo "python ~/aavs-calibration/station/calibration.py --save_db_cal_file=last_calibration_%03d.txt --station_id=2 --start_freq_channel=50 --save_n_channels=400"
   python ~/aavs-calibration/station/calibration.py --save_db_cal_file=last_calibration_%03d.txt --station_id=2 --start_freq_channel=50 --save_n_channels=400 
else
   echo "WARNING : dump of calibration soltuions from the database is not required"
   sleep 1
fi

for infile in `ls last_calibration_???.txt`
do
   echo "python ~/aavs-calibration/station/fit_amplitude.py ${infile} --delta_channels=${channels_around} --polynomial_order=${polynomial_order} --do_not_exclude"
   python ~/aavs-calibration/station/fit_amplitude.py ${infile} --delta_channels=${channels_around} --polynomial_order=${polynomial_order} --do_not_exclude
   
   fitfile=${infile%%.txt}_fitted.txt

   if [[ $do_plot -gt 0 ]]; then
      mkdir -p images/
      pngfile_X=${infile%%.txt}_X
      pngfile_Y=${infile%%.txt}_Y
      root -b -q -l "plotcalsol_vs_channel_2files.C(\"${infile}\",\"${fitfile}\",\"${pngfile_X}\")"
      root -b -q -l "plotcalsol_vs_channel_2files.C(\"${infile}\",\"${fitfile}\",\"${pngfile_Y}\",0,3)"
   else
      echo "WARNING : plotting is not required"
   fi
done
   