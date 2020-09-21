#!/bin/bash

# Example :
# observe_object_multifreq.sh B0950 90 400 13

object=J0437
if [[ -n "$1" && "$1" != "-" ]]; then
   object=$1
fi

start_freq_channel=204
if [[ -n "$2" && "$2" != "-" ]]; then
   start_freq_channel=$2
fi

stop_freq_channel=204
if [[ -n "$3" && "$3" != "-" ]]; then
   stop_freq_channel=$3
fi

freq_step_ch=13
if [[ -n "$4" && "$4" != "-" ]]; then
   freq_step_ch=$4
fi

dir=`date +%Y_%m_%d_$object`
data_dir=/data/${data_dir}
if [[ -n "$5" && "$5" != "-" ]]; then
   data_dir=$5
fi

ra="-"
if [[ -n "$6" && "$6" != "-" ]]; then
  ra=$6
fi

dec="-"
if [[ -n "$7" && "$7" != "-" ]]; then
  dec=$7
fi

interval=300
if [[ -n "$8" && "$8" != "-" ]]; then
   interval=$8
fi

pointing_interval=${interval}
if [[ -n "${9}" && "${9}" != "-" ]]; then
   pointing_interval=${9}
fi

repointing_resolution=30
if [[ -n "${10}" && "${10}" != "-" ]]; then
   repointing_resolution=${10}
fi

# config_file=/opt/aavs/config/${station}.yml
# do initialisation :
# echo "python /opt/aavs/bin/station.py --config=$config_file -IPB"
# python /opt/aavs/bin/station.py --config=$config_file -IPB

# BUG WORKAROUND :
# first observation has 2 station initialisation (due to bug), but the next ones can do just one
n_init=2

freq_ch=${start_freq_channel}
while [[ $freq_ch -le ${stop_freq_channel} ]]; 
do
   # 1 - for single -IPB (1st is done before the loop)
   freq_str=`echo $freq_ch | awk '{printf("%03d",$1);}'`
   mkdir -p ${freq_str}
   cd ${freq_str}
   echo "observe_object.sh ${freq_ch} ${data_dir} ${object} ${ra} ${dec} ${interval} -1 1 0 ${pointing_interval} ${repointing_resolution} - $n_init > out"
   observe_object.sh ${freq_ch} ${data_dir} ${object} ${ra} ${dec} ${interval} -1 1 0 ${pointing_interval} ${repointing_resolution} - $n_init  > out 
   cd ../
   
   # BUG WORKAROUND :
   # first observation has 2 station initialisation (due to bug), but the next ones can do just one
   n_init=1

   freq_ch=$(($freq_ch+1))
   sleep 10
done


