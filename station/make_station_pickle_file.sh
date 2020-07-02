#!/bin/bash

ch=204
if [[ -n "$1" && "$1" != "-" ]]; then
   ch=$1
fi

station=eda2
if [[ -n "$2" && "$2" != "-" ]]; then
   station=$2
fi

curr_dir=`pwd`
dtm=`basename $curr_dir` # assuming current directory is ending with date/time :
if [[ -n "$3" && "$3" != "-" ]]; then
  dtm=$3
fi

options=""
if [[ -n "$4" && "$4" != "-" ]]; then
   options="$4"
fi


~/aavs-calibration/station/calsol2col.sh chan_${ch}_selfcal_pha_XX.txt > phase_vs_antenna_X.txt
~/aavs-calibration/station/calsol2col.sh chan_${ch}_selfcal_pha_YY.txt > phase_vs_antenna_Y.txt


dt=`echo $dtm | awk '{gsub("_","");print substr($1,1,8);}'`
outfile=${dt}_${station}_ch${ch}_calcoefficients.pkl

echo "python ~/aavs-calibration/station/calibration.py --outfile=${outfile} --filebase=phase_vs_antenna ${options}"
python ~/aavs-calibration/station/calibration.py --outfile=${outfile} --filebase=phase_vs_antenna ${options}

