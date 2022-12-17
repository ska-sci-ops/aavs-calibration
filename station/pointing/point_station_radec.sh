#!/bin/bash

RA_deg=0
if [[ -n "$1" && "$1" != "-" ]]; then
   RA_deg=$1
fi

DEC_deg=0
if [[ -n "$2" && "$2" != "-" ]]; then
   DEC_deg=$2
fi

station_name=eda2
if [[ -n "$3" && "$3" != "-" ]]; then
   station_name=$3
fi
station_name_lower=`echo $station_name | awk '{print tolower($1);}'`

object="-"
object_set=0
if [[ -n "$4" && "$4" != "-" ]]; then
   object=$4
   object_set=1
fi

options=""
if [[ -n "$5" && "$5" != "-" ]]; then
   options="$5"
fi


if [[ $object_set -gt 0 ]]; then
   if [[ $object == "SUN" || $object == "sun" ]]; then       
      echo "DEBUG : pointing to object $object - is sun"
      if [[ -s ~/aavs-calibration/sunpos.py ]]; then
         ux=`date +%s`
         radec_string=`python ~/aavs-calibration/sunpos.py $ux | awk '{print $1*15.00" "$2;}'`         
         RA_deg=`echo $radec_string | awk '{print $1;}'`
         DEC_deg=`echo $radec_string | awk '{print $2;}'`         
         echo "DEBUG : $object position updated accoring to string |$radec_string| -> RA_deg = $RA_deg , DEC_deg = $DEC_deg"
      else
         echo "WARNING : script ~/aavs-calibration/sunpos.py not found -> cannot update $object position dynamically"
      fi
   fi
fi

antfile=~/aavs-calibration/config/${station_name_lower}/antenna_locations.txt
config_file=/opt/aavs/config/${station_name_lower}.yml

cd ~/aavs-calibration/station/pointing
date
# 2022-11-03 : after both stations use the same firmware --delay_sign=-1 option added as default here :
# --delta_time=1 -> ripple from 30 seconds to ~60 seconds , sign of delay rate -> -1 -> horrible seesaw
# 2022-12-17 : testing --delta_time=30
echo "python ./point_station_newsoft.py --ra=$RA_deg --dec=$DEC_deg --antenna_locations=${antfile} --delay_sign=-1 --delta_time=30 --config=${config_file} ${options}"
python ./point_station_newsoft.py --ra=$RA_deg --dec=$DEC_deg --antenna_locations=${antfile} --delay_sign=-1 --delta_time=30 --config=${config_file} ${options}
