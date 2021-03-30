#!/bin/bash

station=EDA2
if [[ -n "$1" && "$1" != "-" ]]; then
   station=$1
fi

start_ch=50
if [[ -n "$2" && "$2" != "-" ]]; then
   start_ch=$2
fi

end_ch=450
if [[ -n "$3" && "$3" != "-" ]]; then
   end_ch=$3
fi

beam_x=1.00 # 0.73557007
if [[ -n "$4" && "$4" != "-" ]]; then
   beam_x=$4
fi

beam_y=1.00 # 0.49231657
if [[ -n "$5" && "$5" != "-" ]]; then
   beam_y=$5
fi

do_copy=0
if [[ -n "$6" && "$6" != "-" ]]; then
   do_copy=$6
fi

outdir="SunCal"
if [[ -n "$7" && "$7" != "-" ]]; then
   outdir=$7
fi

update_last_calibration=0
if [[ -n "$8" && "$8" != "-" ]]; then
   update_last_calibration=$8
fi


echo "backup_calibration.sh"
backup_calibration.sh

if [[ ! -s beam_on_sun.txt ]]; then
   # temporary solution - until beam values are generated on the server :
   if [[ -s /tmp/msok/beam_on_sun.txt ]]; then     
      echo "cp /tmp/msok/beam_on_sun.txt"
      cp /tmp/msok/beam_on_sun.txt
   else
      echo "WARNING : file /tmp/msok/beam_on_sun.txt does not exist -> re-calibration will not be able to use correct beam-correction beam values"
#      exit -1
   fi
else
   echo "WARNING : local file beam_on_sun.txt found -> using existing one (not overwritting)"
fi

mkdir -p ${outdir}
cd ${outdir}

if [[ $do_copy -gt 0 ]]; then
   echo "DEBUG : copying files to re-calibrate to directory :"
   pwd
   
   if [[ ! -s beam_on_sun.txt ]]; then
      echo "DEBUG : file beam_on_sun.txt does not exist -> checking main data directory ..."
      echo "cp ../beam_on_sun.txt ."
      cp ../beam_on_sun.txt .
   else
      echo "DEBUG : file beam_on_sun.txt exists -> using it"   
   fi
   
   
   # correlation_burst_60_
   ch=${start_ch}
   while [[ $ch -le ${end_ch} ]];
   do
      hdf5_count=`ls correlation_burst_${ch}_*hdf5 2>/dev/null | wc -l`
      if [[ $hdf5_count -gt 0 ]]; then
         echo "DEBUG : $hdf5_count files correlation_burst_${ch}_*hdf5 found -> no copying required"
      else
         echo "cp ../correlation_burst_${ch}_*hdf5 ."
         cp ../correlation_burst_${ch}_*hdf5 .
      fi
      
      ch=$(($ch+1))
   done
else
   echo "WARNING : copying data is not required"
fi

hdf5_count=`ls *.hdf5 | wc -l`

if [[ $hdf5_count -le 0 ]]; then
   echo "WARNING : no hdf5 files - trying to de-compress ..."
   echo "gzip -df *.hdf5.gz"
   gzip -df *.hdf5.gz
fi

hdf5_count=`ls *.hdf5 | wc -l`

if [[ $hdf5_count -le 0 ]]; then
  echo "ERROR : no hdf5 files in (gzip -df did not help) :"
  pwd
  echo "ERROR : exiting re-calibration script now"
  exit -1
else
  echo "DEBUG : hdf5_count = $hdf5_count"
fi

ch=${start_ch}
while [[ $ch -le ${end_ch} ]];
do
# OLD :
#   echo "~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -k ${ch}"
#   ~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -k ${ch}

   echo "~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -m sun -x ${beam_x} -y ${beam_y} -k ${ch} > ${ch}.out 2>&1"
   ~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -m sun -x ${beam_x} -y ${beam_y} -k ${ch} > ${ch}.out 2>&1

   ch=$(($ch+1))
done


if [[ $update_last_calibration -gt 0 ]]; then
   echo "Updating last calibration"
   echo "update_last_calibration.sh ${station}"
   update_last_calibration.sh ${station}
else
   echo "WARNING : update of last calibration is not required"
fi
