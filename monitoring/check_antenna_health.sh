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

out_file=${outdir}_antenna_health.out

echo "###################################################"
echo "PARAMETERS:"
echo "###################################################"
echo "hdf5_file_template = $hdf5_file_template"
echo "Data dir = $data_dir"
echo "Outdir   = $outdir"
echo "Outfile  = $out_file"
echo "last     = $last"
echo "station_name = $station_name"
echo "###################################################"

# --last 
mkdir -p ${outdir}/
echo "python ~/aavs-calibration/monitoring/check_antenna_health.py $hdf5_file_template --n_timesteps=${n_timesteps} --outdir=${outdir} --station=${station_name} ${extra_options} > ${outdir}/${out_file}"
python ~/aavs-calibration/monitoring/check_antenna_health.py $hdf5_file_template --n_timesteps=${n_timesteps} --outdir=${outdir} --station=${station_name} ${extra_options} > ${outdir}/${out_file}


# make plots :
cd ${outdir}/
ls *_median_x.txt *_median_spectrum_ant?????_x.txt > x.list
ls *_median_y.txt *_median_spectrum_ant?????_y.txt > y.list

mkdir -p images/
root_path=`which root`
if [[ -n $root_path ]]; then
   root -l "plot_eda2_spectra.C(\"x.list\")"
   root -l "plot_eda2_spectra.C(\"y.list\")"
else
   echo "WARNING : root program is not installed"
fi  
cd ..


