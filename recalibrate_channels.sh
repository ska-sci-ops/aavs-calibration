#!/bin/bash

station=EDA2
if [[ -n "$1" && "$1" != "-" ]]; then
   station=$1
fi

start_ch=50
if [[ -n "$2" && "$2" != "-" ]]; then
   start_ch=$2
fi

end_ch=400
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

do_copy=1
if [[ -n "$6" && "$6" != "-" ]]; then
   do_copy=$6
fi

outdir="SunCal"
if [[ -n "$7" && "$7" != "-" ]]; then
   outdir=$7
fi

mkdir -p ${outdir}
cd ${outdir}

if [[ $do_copy -gt 0 ]]; then
   echo "DEBUG : copying files to re-calibrate"
   # correlation_burst_60_
   ch=${start_ch}
   while [[ $ch -le ${end_ch} ]];
   do
      hdf5_count=`ls correlation_burst_${ch}_*hdf5 | wc -l`
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


ch=${start_ch}
while [[ $ch -le ${end_ch} ]];
do
# OLD :
#   echo "~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -k ${ch}"
#   ~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -k ${ch}

   echo "~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -m sun -x ${beam_x} -y ${beam_y} -k ${channel} > ${channel}.out 2>&1"
   ~/aavs-calibration/calibration_script.sh -D ./ -T 1.9818086 -N 1 -S ${station} -m sun -x ${beam_x} -y ${beam_y} -k ${channel} > ${channel}.out 2>&1

   ch=$(($ch+1))
done
