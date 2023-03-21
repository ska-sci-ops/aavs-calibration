#!/bin/bash

do_dump=1
if [[ -n "$1" && "$1" != "-" ]]; then
   do_dump=$1
fi

do_plot=0
if [[ -n "$2" && "$2" != "-" ]]; then
   do_plot=$2
fi

generate_sql=0
if [[ -n "$3" && "$3" != "-" ]]; then
   generate_sql=$3
fi

fit_time=""
if [[ -s fittime.txt ]]; then
   fit_time=`cat fittime.txt`
fi
if [[ -n "$4" && "$4" != "-" ]]; then
   fit_time=$4
fi

station_id=2
if [[ -n "$5" && "$5" != "-" ]]; then
   station_id=$5
fi

db_field_postfix="_amp"
if [[ -n "$6" && "$6" != "-" ]]; then
   db_field_postfix=$6
fi

do_fit=1
if [[ -n "$7" && "$7" != "-" ]]; then
   do_fit=$7
fi


polynomial_order=2
channels_around=10

echo "#########################################"
echo "PARAMETERS:"
echo "#########################################"
echo "station_id = $station_id"
echo "do_dump = $do_dump"
echo "do_plot = $do_plot"
echo "generate_sql = $generate_sql"
echo "fit_time = $fit_time"
echo "db_field_postfix = $db_field_postfix"
echo "polynomial_order = $polynomial_order"
echo "channels_around  = $channels_around"
echo "do fit           = $do_fit"
echo "#########################################"


if [[ $do_dump -gt 0 ]]; then
   echo "python ~/aavs-calibration/station/calibration.py --save_db_cal_file=last_calibration_%03d.txt --station_id=${station_id} --start_freq_channel=0 --save_n_channels=512 --db_field_postfix=${db_field_postfix}"
   python ~/aavs-calibration/station/calibration.py --save_db_cal_file=last_calibration_%03d.txt --station_id=${station_id} --start_freq_channel=0 --save_n_channels=512 --db_field_postfix=${db_field_postfix}
   
   if [[ -n "$fit_time" ]]; then
      echo "DEBUG : fit_time externally set to $fit_time"
   else
     if [[ -s fittime.txt ]]; then
        echo "DEBUG : trying to get fit_time from fittime.txt"
        fit_time=`cat fittime.txt`
     fi
   fi
   echo "DEBUG : final fit_time = $fit_time"
else
   echo "WARNING : dump of calibration soltuions from the database is not required"
   sleep 1
fi

for infile in `ls last_calibration_???.txt`
do
   # OLD - without iterations and excluding outliers :
   # echo "python ~/aavs-calibration/station/fit_amplitude.py ${infile} --delta_channels=${channels_around} --polynomial_order=${polynomial_order} --do_not_exclude"
   # python ~/aavs-calibration/station/fit_amplitude.py ${infile} --delta_channels=${channels_around} --polynomial_order=${polynomial_order} --do_not_exclude
   
   # NEW : see 20230321_test_fitting_and_removing_outliers.odt
   if [[ $do_fit -gt 0 ]]; then
      echo "python ~/aavs-calibration/station/fit_amplitude.py ${infile} --delta_channels=${channels_around} --polynomial_order=${polynomial_order} --n_iterations=5 --do_not_exclude"
      python ~/aavs-calibration/station/fit_amplitude.py ${infile} --delta_channels=${channels_around} --polynomial_order=${polynomial_order} --n_iterations=5 --do_not_exclude    
   else
      echo "WARNING : fitting is not required"
   fi
   
   fitfile=${infile%%.txt}_fitted.txt

   if [[ $do_plot -gt 0 ]]; then
      mkdir -p images/
      pngfile_X=${infile%%.txt}_X
      pngfile_Y=${infile%%.txt}_Y
      
      root_path=`which root`
      if [[ -n $root_path ]]; then
         root -b -q -l "plotcalsol_vs_channel_2files.C(\"${infile}\",\"${fitfile}\",\"${pngfile_X}\")"
         root -b -q -l "plotcalsol_vs_channel_2files.C(\"${infile}\",\"${fitfile}\",\"${pngfile_Y}\",0,3)"
      else
         echo "WARNING : ROOT CERN package is not installed and no plotting alternative has been implemented yet ..."
      fi
   else
      echo "WARNING : plotting is not required"
   fi
done

if [[ $generate_sql -gt 0 && -n $fit_time ]]; then
   echo "INFO : generating sql file to update fitted amplitudes in the database for fit_time='$fit_time'"

   echo "~/aavs-calibration/station/create_amp_fit_update_sql.sh \"$fit_time\""
   ~/aavs-calibration/station/create_amp_fit_update_sql.sh "$fit_time"
else
   echo "WARNING : generation of SQL update file is not required or fit_time (4th parameter not specified)"
fi   

