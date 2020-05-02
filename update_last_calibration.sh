#!/bin/bash

station_name=eda2
if [[ -n "$1" && "$1" != "-" ]]; then
   station_name=$1
fi


cal_path=/data/real_time_calibration/

last_cal_dir=`pwd`
if [[ ! -s chan_204_selfcal_pha_XX.txt ]]; then
   # checking a single file to check if this is folder with calibration solutions from MIRIAD (Randall's calibration loop format) :
   echo "INFO : no calibration in local directory : $last_cal_dir -> looking for last calibration automatically in $cal_path ..."
   
   last_cal_dir=`ls -dtr /data/real_time_calibration/2???_??_??-??:??/ |tail -1`   
fi

echo "INFO : last cal dir = $last_cal_dir -> updating last calibration in ${cal_path}/last_calibration/"

mkdir -p ${cal_path}/last_calibration/

cd ${cal_path}/last_calibration
pwd

mkdir -p Previous/
rm -fr Previous/*.uv Previous/*.txt

echo "mv chan*.uv Previous/"
mv chan*.uv Previous/

echo "mv chan*.txt Previous/"
mv chan*.txt Previous/

# creating info file about the last calibration :
echo "$last_cal_dir" > last_cal_info.txt

# copying .uv to last calibration directory :
for uv_full_path in `ls -d ${last_cal_dir}/chan_*_????????T??????.uv`
do
   uv_file=`basename $uv_full_path`
   uv_dir=`dirname $uv_full_path`
   uv_file_XX=${uv_file%%.uv}_XX.uv
   uv_file_YY=${uv_file%%.uv}_YY.uv

   # chan_204_20200227T044851.uv
   channel=`echo $uv_file | awk '{start=index($1,"_");s=substr($1,start+1);end=index(s,"_");ch=substr(s,1,end-1);print ch;}'`

   echo "$uv_full_path -> $uv_file -> $channel"   
   file_name=`echo $channel | awk '{printf("chan_%03d.uv",$1);}'`
   file_name_XX=`echo $channel | awk '{printf("chan_%03d_XX.uv",$1);}'`
   file_name_YY=`echo $channel | awk '{printf("chan_%03d_YY.uv",$1);}'`


   echo "cp -a ${uv_full_path} ${file_name}"
   cp -a ${uv_full_path} ${file_name}
   
   echo "cp -a ${uv_dir}/${uv_file_XX} ${file_name_XX}"
   cp -a ${uv_dir}/${uv_file_XX} ${file_name_XX}
   
   echo "cp -a ${uv_dir}/${uv_file_YY} ${file_name_YY}"
   cp -a ${uv_dir}/${uv_file_YY} ${file_name_YY}
done

# copying X and Y :
for txt_full_path in `ls -d ${last_cal_dir}/chan_*_selfcal_???_??.txt`
do
   txt_file=`basename $txt_full_path`

   # chan_197selfcal_amp_XX.txt
   channel=`echo $txt_file | awk '{start=index($1,"_");s=substr($1,start+1);end=index(s,"_");ch=substr(s,1,end-1);print ch;}'`
   postfix=`echo $txt_file | awk '{start=index($1,"_");s=substr($1,start+1);end=index(s,"_");ch=substr(s,end+1);print ch;}'`

   file_name=`echo "$channel $postfix" | awk '{printf("chan_%03d_%s\n",$1,$2);}'`
   echo "$txt_full_path -> $txt_file -> $channel -> $file_name"   


   echo
   echo "cp -a ${txt_full_path} ${file_name}"
   cp -a ${txt_full_path} ${file_name}
done


# create pickle files for station calibration :
date
echo "~/aavs-calibration/station/create_pickle_files.sh ${station_name}"
~/aavs-calibration/station/create_pickle_files.sh ${station_name}


echo "update_last_calibration.sh finished at:"
date

