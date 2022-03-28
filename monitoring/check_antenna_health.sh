#!/bin/bash

# should be later but has to be known before param 1 
data_dir="./"
if [[ -n "$6" && "$6" != "-" ]]; then
   data_dir=$6
   cd ${data_dir}
fi

# aavs@aavs-lmc:/storage/monitoring/integrated_data/eda2$ ls -tr channel_integ_0_*hdf5 | tail -1
# echo channel_integ_0_20210514_61780_0.hdf5 | awk '{gsub("_0_","_%d_");print $1;;}' 
# hdf5_file_template=channel_integ_%d_20210210_59183_0.hdf5
last_hdf5_file=`ls -tr channel_integ_0_*hdf5 | tail -1`
hdf5_file_template=`echo $last_hdf5_file | awk '{gsub("_0_","_%d_");print $1;;}'`
if [[ -n "$1" && "$1" != "-" ]]; then
   hdf5_file_template=$1
fi

n_timesteps=-1
outdir="n_timestepsALL"
if [[ -n "$2" && "$2" != "-" ]]; then
   n_timesteps=$2
   outdir="n_timesteps${n_timesteps}"
fi

# out_file_tmp=${hdf5_file_template%%.hdf5}
# out_file1=`echo $out_file_tmp | awk '{print substr($1,18);}'`
# out_file=${out_file1}_antenna_health.out
# if [[ -n "$3" && "$3" != "-" ]]; then
#    out_file=$3
# fi

last=0
if [[ -n "$3" && "$3" != "-" ]]; then
   last=$3
fi
extra_options=""
if [[ $last -gt 0 ]]; then
   extra_options="$extra_options --last"
   if [[ $n_timesteps -gt 0 ]]; then
      outdir="n_timesteps${n_timesteps}_latest"
   fi
fi

if [[ -n "$4" && "$4" != "-" ]]; then
   outdir="$4"   
fi

station_name=eda2
if [[ -n "$5" && "$5" != "-" ]]; then
   station_name=$5
fi

# if [[ -n "$6" && "$6" != "-" ]]; then
# moved to the front

do_copy=0
if [[ -n "$7" && "$7" != "-" ]]; then
   do_copy=$7
fi

# but on aavs1-server
www_dir="/exports/calibration/${station_name}/antenna_health/"
if [[ -n "$8" && "$8" != "-" ]]; then
   www_dir=$8
fi

backup_dir=/storage/monitoring/antenna_health/${station_name}/
if [[ -n "$9" && "$9" != "-" ]]; then
   backup_dir=$9
fi

max_spreadsheet_age=86400
if [[ -n "${10}" && "${10}" != "-" ]]; then
   max_spreadsheet_age=${10}
fi


out_file=${outdir}_antenna_health.out

echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "hdf5_file_template = $hdf5_file_template"
echo "Data dir     = $data_dir"
echo "Outdir       = $outdir"
echo "Outfile      = $out_file"
echo "last         = $last"
echo "station_name = $station_name"
echo "do_copy      = $do_copy"
echo "www_dir      = $www_dir"
echo "backup_dir   = $backup_dir"
echo "max_spreadsheet_age = $max_spreadsheet_age [sec]"
echo "###################################################"

start_dtm=`date +%Y%m%d%H%M%S`
dtm=`date +%Y%m%d`

# try to get Dave's spreadsheet :
date
echo "get_spreadsheet.sh"
get_spreadsheet.sh

use_spreadsheet=""
uxtime=`date +%s`
if [[ -s ${station_name}.csv ]]; then
   spreadsheet_uxtime=`ls -l --time-style=+%s ${station_name}.csv | awk '{print $6;}'`
   spreadsheet_age=$(($uxtime-$spreadsheet_uxtime))
   
   if [[ $spreadsheet_age -le $max_spreadsheet_age ]]; then
      echo "INFO : spreadsheet age is $spreadsheet_age seconds which is ok (less than allowed $max_spreadsheet_age [sec]) -> setting use_spreadsheet to --use_spreadsheet"
      use_spreadsheet="--use_spreadsheet"
   else
      echo "WARNING : spreadsheet age is $spreadsheet_age seconds more than allowed $max_spreadsheet_age [sec] -> ignored (some information will not be available in the reports)"
   fi
else 
   echo "WARNING : spreadsheet file ${station_name}.csv does not exist -> some information will not be available in the reports"   
fi   


# --last 
mkdir -p ${outdir}/
echo "python ~/aavs-calibration/monitoring/check_antenna_health.py $hdf5_file_template --n_timesteps=${n_timesteps} --outdir=${outdir} --station=${station_name} --images --plot_db ${extra_options} ${use_spreadsheet} > ${outdir}/${out_file}"
python ~/aavs-calibration/monitoring/check_antenna_health.py $hdf5_file_template --n_timesteps=${n_timesteps} --outdir=${outdir} --station=${station_name} --images --plot_db ${extra_options} ${use_spreadsheet} > ${outdir}/${out_file}


# make plots :
cd ${outdir}/
ls *_median_x.txt *_median_spectrum_ant?????_x.txt > x.list
ls *_median_y.txt *_median_spectrum_ant?????_y.txt > y.list

if [[ $do_copy -gt 0 ]]; then
   pwd   
   echo "cp ${station_name}_health_report.txt /exports/calibration/${station_name}/antenna_health/"
   cp ${station_name}_health_report.txt /exports/calibration/${station_name}/antenna_health/
   
   echo "cp ${station_name}_bad_antennas.txt /exports/calibration/${station_name}/antenna_health/"
   cp ${station_name}_bad_antennas.txt /exports/calibration/${station_name}/antenna_health/

   echo "cp ${station_name}_bad_antennas.html /exports/calibration/${station_name}/antenna_health/"
   cp ${station_name}_bad_antennas.html /exports/calibration/${station_name}/antenna_health/
   
   echo "cp ${station_name}_bad_antennas.csv /exports/calibration/${station_name}/antenna_health/"
   cp ${station_name}_bad_antennas.csv /exports/calibration/${station_name}/antenna_health/
   
   echo "cp ${station_name}_median_?.txt /exports/calibration/${station_name}/antenna_health/"
   cp ${station_name}_median_?.txt /exports/calibration/${station_name}/antenna_health/

   echo "cp ${station_name}_instr_config.txt /exports/calibration/${station_name}/antenna_health/"
   cp ${station_name}_instr_config.txt /exports/calibration/${station_name}/antenna_health/

   # create copy named by today's date :   
   mkdir -p /exports/calibration/${station_name}/antenna_health/${dtm}
   echo "cp ${station_name}_instr_config.txt /exports/calibration/${station_name}/antenna_health/${dtm}/${station_name}_instr_config_${start_dtm}.txt"
   cp ${station_name}_instr_config.txt /exports/calibration/${station_name}/antenna_health/${dtm}/${station_name}_instr_config_${start_dtm}.txt
   
   echo "cp ${station_name}_health_report.txt /exports/calibration/${station_name}/antenna_health/${dtm}/${station_name}_health_report_${start_dtm}.txt"
   cp ${station_name}_health_report.txt /exports/calibration/${station_name}/antenna_health/${dtm}/${station_name}_health_report_${start_dtm}.txt
   
   echo "cp ${station_name}_bad_antennas.txt /exports/calibration/${station_name}/antenna_health/${dtm}/${station_name}_bad_antennas_${start_dtm}.txt"
   cp ${station_name}_bad_antennas.txt /exports/calibration/${station_name}/antenna_health/${dtm}/${station_name}_bad_antennas_${start_dtm}.txt

   # images :
   echo "mkdir -p /exports/calibration/${station_name}/images/"
   mkdir -p /exports/calibration/${station_name}/images/
   
   echo "cp images/*.png /exports/calibration/${station_name}/images/"
   cp images/*.png /exports/calibration/${station_name}/images/   
fi


mkdir -p images/
root_path=`which root`
if [[ -n $root_path ]]; then
   root -l "plot_eda2_spectra.C(\"x.list\")"
   root -l "plot_eda2_spectra.C(\"y.list\")"
else
   echo "WARNING : root program is not installed"
fi  
cd ..

if [[ -d $backup_dir ]]; then
   backup_subdir=`date +%Y%m%d_%H%M`
   echo "cp -a ${outdir} ${backup_dir}/${backup_subdir}"
   cp -a ${outdir} ${backup_dir}/${backup_subdir}
else
   echo "WARNING : backup directory $backup_dir does not exist -> not backing up"
fi
