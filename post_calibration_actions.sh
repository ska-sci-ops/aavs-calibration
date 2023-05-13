#!/bin/bash

export PATH=~/aavs-calibration/station/:$PATH

# DEFAULT IS EDA2 :
station_name=eda2
station_id=2
pghost=10.128.16.52
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name=$1
fi

if [[ $station_name == "aavs2" || $station_name == "AAVS2" ]]; then
   station_id=3
   pghost=10.0.10.200
fi

last_cal_dir=`pwd`
if [[ ! -s chan_204_selfcal_pha_XX.txt ]]; then
   # checking a single file to check if this is folder with calibration solutions from MIRIAD (Randall's calibration loop format) :
   echo "INFO : no calibration in local directory : $last_cal_dir -> looking for last calibration automatically in $cal_path ..."
   
   last_cal_dir=`ls -dtr /data/real_time_calibration/2???_??_??-??:??/ |tail -1`   
fi


echo "########################################"
echo "PARAMETERS:"
echo "########################################"
echo "Station name = $station_name (id = $station_id)"
echo "Last cal dir = $last_cal_dir"
echo "########################################"


pwd
cd $last_cal_dir
pwd

mkdir -p fit2db
cd fit2db/
echo "~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1"
~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1

echo "psql aavs -h ${pghost} -f amp_fitted.sql"
psql aavs -h ${pghost} -f amp_fitted.sql

# add fitted calibration solutions to .uv files so that they are ready to use in any future calibration :
# only copy .uvfits files in 50 - 350 MHz range :
echo "cp ../chan_4[0-4]?_*.uvfits ."
cp ../chan_4[0-4]?_*.uvfits .

echo "cp ../chan_[1-3]??_*.uvfits ."
cp ../chan_[1-3]??_*.uvfits .

echo "cp ../chan_[6-9]?_*.uvfits ."
cp ../chan_[6-9]?_*.uvfits .

# adding calibration to .uv files in XX and YY :
for uvfits in `ls *.uvfits`
do
   logfile=${uvfits%%uvfits}log
   
   echo "database_cal.sh ${uvfits} > ${logfile} 2>&1"
   database_cal.sh ${uvfits} > ${logfile} 2>&1
done

# create calibration files per frequency channel :
for channel in {60..450}
do
   caltxtfile=`echo $channel | awk '{printf("calsol_merged_ch%05d.txt\n",$1);}'`
   callogfile=${caltxtfile%%txt}log
   
   echo "calperant2calperch.sh $channel - ${caltxtfile} > ${callogfile} 2>&1"
   calperant2calperch.sh $channel - ${caltxtfile} > ${callogfile} 2>&1
done
