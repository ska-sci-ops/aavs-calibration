#!/bin/bash

export PATH=~/aavs-calibration/station/pointing:$PATH

object_radec()
{
   object=$1
   
   ret=""
   if [[ $object == "B0950" || $object == "J0950" ]]; then
      ra=148.28879042
      dec=7.92659722
   fi 
   
   if [[ $object == "VELA" || $object == "J0835" || $object == "0835" || $object == "Vela" ]]; then
      ra=128.83583333
      dec=-45.17633333
   fi

   if [[ $object == "J1752" || $object == "1752" ]]; then
      ra=268.1475
      dec=23.99672222
   fi

   if [[ $object == "J2145" || $object == "2145" ]]; then
      ra=326.45833333 
      dec=-7.83333333
   fi

   if [[ $object == "CRAB" || $object == "B0531" || $object == "0531" || $object == "J0534" || $object == "0534" ]]; then
      ra=83.6334
      dec=22.01444444
   fi
}


freq_channel=204
if [[ -n "$1" && "$1" != "-" ]]; then
   freq_channel=$1
fi

object=J0437
if [[ -n "$3" && "$3" != "-" ]]; then
   object=$3
fi

dir=`date +%Y_%m_%d`
data_dir=/data/${dir}_pulsars/${object}
if [[ -n "$2" && "$2" != "-" ]]; then
   data_dir=$2
fi
mkdir -p ${data_dir}

# checking if object is one of the pre-defined ones:
ra=0.00
dec=0.00
object_radec $object
echo "DEBUG : $object -> ra,dec = $ra , $dec"

if [[ -n "$4" && "$4" != "-" ]]; then
  ra=$4
fi

if [[ -n "$5" && "$5" != "-" ]]; then
  dec=$5
fi

interval=1800
if [[ -n "$6" && "$6" != "-" ]]; then
   interval=$6
fi

start_uxtime=-1
if [[ -n "$7" && "$7" != "-" ]]; then
   start_uxtime=$7
fi

n_iter=1
if [[ -n "$8" && "$8" != "-" ]]; then
   n_iter=$8
fi

sleep_time=1800
if [[ -n "$9" && "$9" != "-" ]]; then
   sleep_time=$9
fi

pointing_interval=${interval}
if [[ -n "${10}" && "${10}" != "-" ]]; then
   pointing_interval=${10}
fi

repointing_resolution=30
if [[ -n "${11}" && "${11}" != "-" ]]; then
   repointing_resolution=${11}
fi

station=eda2
if [[ -s /opt/aavs/config/station.yml ]]; then
   station=`awk -v station_section=0 '{if(index($1,":")>0 && NF==1){if(index($1,"station")>0 ){station_section=1;}else{station_section=0;}}if(station_section>0){if($1=="name:"){station_name=$2;gsub("\"","",station_name);gsub("\r","",station_name);print tolower(station_name);}}}' /opt/aavs/config/station.yml`
   echo "Station config file (or symbolik link) exists -> getting station_name = $station"
else
   echo "ERROR : /opt/aavs/config/station.yml file or symbolic link does not exist will use default station_name = $station or value passed in parameter -s"   
   exit;
fi
if [[ -n "${12}" && "${12}" != "-" ]]; then
   station=${12}
fi

ip=10.0.10.190
if [[ ${station} == "aavs2" ]]; then
   ip=10.0.10.210
fi


do_init_station=2
if [[ -n "${13}" && "${13}" != "-" ]]; then
   do_init_station=${13}
fi

full_time_resolution=1
if [[ -n "${14}" && "${14}" != "-" ]]; then
   full_time_resolution=${14}
fi

calibration_options=""
if [[ -n "${15}" && "${15}" != "-" ]]; then
   calibration_options=${15}
fi



# RW/Chris Lee : I'm 99% sure the offset is 3 channels. (not 4). And that confirms the 3-channel offset also.
channel_from_start=4

echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "station               = $station (ip = $ip)"
echo "Object                = $object"
echo "(ra,dec)              = ( $ra , $dec ) [deg]"
echo "freq_channel          = $freq_channel"
echo "data_dir              = $data_dir"
echo "interval              = $interval"
echo "pointing_interval     = $pointing_interval"
echo "start_uxtime          = $start_uxtime"
echo "n_iter                = $n_iter"
echo "sleep_time            = $sleep_time"
echo "repointing_resolution = $repointing_resolution"
echo "do_init_station       = $do_init_station"
echo "channel_from_start    = $channel_from_start"
echo "full_time_resolution  = $full_time_resolution"
echo "calibration_options   = $calibration_options"
echo "###################################################"

ux=`date +%s`
start_uxtime_int=`echo $start_uxtime | awk '{printf("%d",$1);}'`
if [[ $start_uxtime_int -gt $ux ]]; then
   echo "Start unix time = $start_uxtime ($start_uxtime_int) -> waiting ..."
   which wait_for_unixtime.sh
   echo "wait_for_unixtime.sh $start_uxtime_int"
   wait_for_unixtime.sh $start_uxtime_int
fi

calibrate_station=1

mkdir -p ${data_dir}
cd ${data_dir}

config_file=/opt/aavs/config/${station}.yml

if [[ $do_init_station -gt 0 ]]; then
   echo "Initialising the station"

   use_config_per_freq=1
   
   if [[ $use_config_per_freq -gt 0 ]]; then
      freq_config_file=/opt/aavs/config/freq/${station}_ch${freq_channel}.yml
                  
      if [[ ! -s ${freq_config_file} ]]; then
         if [[ -s /opt/aavs/config/freq/${station}.template ]]; then
            # generate station config file for a specified frequency if does not exist already 
            awk -v ch=${freq_channel} -v channel_from_start=${channel_from_start} 'BEGIN{freq_mhz=(ch-channel_from_start)*(400/512);print "observation:"; printf("   start_frequency_channel: %.3fe6\n",freq_mhz);print"   bandwidth: 6.25e6";}{print $0;}' /opt/aavs/config/freq/${station}.template > ${freq_config_file}
         else 
            echo "ERROR : configuration file $freq_config_file for freq_channel = $freq_channel does not exist and neither the template file /opt/aavs/config/freq/${station}.template -> cannot continue"
            exit;
         fi
      fi
      
      config_file=${freq_config_file}
   else
      echo "DEBUG : initialising station using config file = $config_file"
   fi
 
   # do_init_station=2 for the first time to accomdate for the bug
   while [[ $do_init_station -gt 0 ]];
   do
      # do initialisation :
      echo "python /opt/aavs/bin/station.py --config=$config_file -IPB"
      python /opt/aavs/bin/station.py --config=$config_file -IPB
      
      do_init_station=$(($do_init_station-1))
   done
   
   # TO BE FIXED !!!
   # TWICE DUE TO BUG !!!
   # echo "python /opt/aavs/bin/station.py --config=$config_file -IPB"
   # python /opt/aavs/bin/station.py --config=$config_file -IPB
else
  echo "WARNING : station initialisation is not required"
fi   


if [[ $calibrate_station -gt 0 ]]; then
  echo "~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station} ${config_file} \"${calibration_options}\""
  ~/aavs-calibration/station/calibrate_station.sh ${freq_channel} ${station} ${config_file} "${calibration_options}"
else
  echo "WARNING : station calibration is not required"
fi   

# starting monitoring :
if [[ $full_time_resolution -le 0 ]]; then
   echo "INFO : starting real-time beam monitoring"
   echo "nohup ~/Software/hdf5_correlator/scripts/process_station_beam_loop.sh ${freq_channel} ${station} - 43000 > power.out 2>&1 &"
   nohup ~/Software/hdf5_correlator/scripts/process_station_beam_loop.sh ${freq_channel} ${station} - 43000 > power.out 2>&1 &
else
   echo "WARNING : real-time station beam monitoring is not implemented in full time resolution mode"
fi   


i=0
while [[ $i -lt $n_iter ]];
do
   echo
   echo "------------------------------------------------- i = $i -------------------------------------------------"
   date

   # kill old and start new pointing 
   echo "killall point_station_radec_loop.sh acquire_station_beam"
   killall point_station_radec_loop.sh acquire_station_beam 
   echo "sleep 5"
   sleep 5 

   # start pointing :
   pwd   
   echo "nohup ~/aavs-calibration/station/pointing/point_station_radec_loop.sh ${ra} ${dec} ${pointing_interval} ${repointing_resolution} ${station} ${object} >> pointing.out 2>&1 &"
   nohup ~/aavs-calibration/station/pointing/point_station_radec_loop.sh ${ra} ${dec} ${pointing_interval} ${repointing_resolution} ${station} ${object} >> pointing.out 2>&1 &
   pwd
   ps

   echo "echo ${freq_channel} > channel.txt"
   echo ${freq_channel} > channel.txt

   # waiting for pointing to start - not to collect data earlier !
   echo "sleep 30"
   sleep 30      

   # start acuisition :
   # WAS : /home/aavs/Software/aavs-system/src/build_new/acquire_station_beam
   
   if [[ $full_time_resolution -gt 0 ]]; then
      echo "/opt/aavs/bin/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c ${channel_from_start}  -i enp216s0f0 -p ${ip} >> daq.out 2>&1"
      /opt/aavs/bin/acquire_station_beam -d ./ -t ${interval} -s 1048576 -c ${channel_from_start}  -i enp216s0f0 -p ${ip} >> daq.out 2>&1
   else
      echo "python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -t 16  -d . -SX --channel_samples=262144 --continuous_period=300 --beam_channels=8 --station_samples=1048576 --description=\"DAQ acquisition channel $freq_channel voltages and station beam\" --station-config=$config_file --acquisition_duration=${interval}"
      python /opt/aavs/bin/daq_receiver.py -i enp216s0f0 -t 16  -d . -SX --channel_samples=262144 --continuous_period=300 --beam_channels=8 --station_samples=1048576 --description="DAQ acquisition channel $freq_channel voltages and station beam" --station-config=$config_file --acquisition_duration=${interval}
   fi
   
   # temporary due to the fact that that the program acquire_station_beam ends up with .dat files without group read permission:
   echo "chmod +r *.dat"
   chmod +r *.dat
   
   i=$(($i+1))
   
   if [[ $i -lt $n_iter ]]; then
      echo "i= $i < $n_iter -> sleep $sleep_time"
      sleep $sleep_time
   else
      echo "Iterations finished i = $i ( >= $n_iter ) at :"
      date
   fi
done

