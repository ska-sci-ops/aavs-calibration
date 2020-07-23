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
