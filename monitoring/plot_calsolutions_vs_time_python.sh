#!/bin/bash

dir=/home/aavs/msok/plots/aavs1
if [[ -n "$1" && "$1" != "-" ]]; then
   dir=$1
fi

get_data_from_db=1
if [[ -n "$2" && "$2" != "-" ]]; then
    get_data_from_db=$2
fi

www_dir=/exports/calibration/
if [[ -n "$3" && "$3" != "-" ]]; then
    www_dir="$3"    
fi

y_min=-7
if [[ -n "$4" && "$4" != "-" ]]; then
   y_min=$4
fi

y_max=12
if [[ -n "$5" && "$5" != "-" ]]; then
   y_max=$5
fi

plotting_options=""
if [[ -n "$6" && "$6" != "-" ]]; then
   plotting_options=$6
fi

station_name="aavs1"
station_id=2
antenna_config="~/aavs-calibration/antenna_locations_eda2.txt"
if [[ -n "$7" && "$7" != "-" ]]; then
   station_id=$7
fi

start_date="2000-01-01 00:00:00"
if [[ -n "$8" && "$8" != "-" ]]; then
   start_date=$8
   
   first_word=`echo $start_date | awk '{print $1;}'`
   if [[ $first_word -lt 0 ]];  then
      echo "First word in start date = $first_word"
      n_back_days=$first_word
      ux_now=`date +%s`
      start_ux=`echo $ux_now $n_back_days | awk '{print ($1+$2*86400);}'`
      start_date_tmp=`date -d "1970-01-01 UTC $start_ux seconds" +"%Y-%m-%d 00:00:00"`
      start_date="$start_date_tmp"
      echo "Start date = |$start_date| ($start_date_tmp)"
   fi
fi

out_subdir=""
if [[ -n "$9" && "$9" != "-" ]]; then
   out_subdir="$9"
   mkdir -p ${www_dir}/${out_subdir}
   if [[ ! -s ${www_dir}/${out_subdir}/index.html ]]; then
      echo "cp ${www_dir}/index.html ${www_dir}/${out_subdir}/"
      cp ${www_dir}/index.html ${www_dir}/${out_subdir}/
   fi
fi

if [[ $station_id == 2 ]]; then
   antenna_config="~/aavs-calibration/antenna_locations_eda2.txt"
   station_name="eda2"
fi

if [[ $station_id == 3 ]]; then
   antenna_config="~/aavs-calibration/config/aavs2/antenna_locations_20191202.txt"
   station_name="aavs2"
fi


# scripts_path=/home/aavs/msok/caldb/
# scripts_path=/home/msok/bighorns/software/analysis/scripts/aavs1/
# if [[ -n "$2" && "$2" != "-" ]]; then
# fi
export PATH=~/aavs-calibration/monitoring/:${PATH}

plot_delay_path=`which plot_delay.py`
scripts_path=`dirname $plot_delay_path`

dt=`date +%Y%m%d`
mkdir -p ${dir}
cd ${dir}
mkdir -p caldb/
cd caldb/

if [[ $get_data_from_db -gt 0 ]]; then
    echo "python $scripts_path/plot_calsolutions_vs_time.py --last_calibration_file=\"last_calibration.txt\" --outdir=\"${dt}\" --station_id=${station_id} --start_date=${start_date}"
    python $scripts_path/plot_calsolutions_vs_time.py --last_calibration_file="last_calibration.txt" --outdir="${dt}" --station_id=${station_id} --start_date=${start_date}
else
    echo "WARNING : getting data from DB is not required"
fi


if [[ -d ${dt} ]]; then
    count=`ls  ${dt}/calsol_delay_antid???.txt |wc -l`

    if [[ $count -le 0 ]]; then
       echo "WARNING : no new calibration solutions detected in the database -> no plotting done"
       exit
    fi
else
    echo "WARNING : directory ${dt} does not exist -> nothing to be done"
    exit;
fi

cd ${dt}

echo "cp ${antenna_config} antenna_locations.txt"
cp ${antenna_config} antenna_locations.txt

# export PATH=/home/msok/bighorns/software/analysis/scripts/aavs1:$PATH
# plot_delay_path=/home/msok/bighorns/software/analysis/scripts/aavs1/plot_delay.py

for file in `ls calsol_delay_antid???.txt`
do
   # root -b -l -q "plotdelays_vs_time.C(\"${file}\")"
   # 20190410 : outliers can be ignored, but we want to see fine details -> limits (-20,20) changed to (-5,+5)
   
   # for now awk - to be changed to python:
   ant_idx=`echo $file | awk '{start=index($1,"antid")+5;ant_idx=substr($1,start);end=index(ant_idx,".");ant_idx=substr($1,start,end-1);print ant_idx}'`
   antenna_id=$ant_idx
   if [[ $station_id == 2 ]]; then
      if [[ -s antenna_locations.txt ]]; then
         antenna_id=`awk -v idx=0 -v ant_idx=${ant_idx} '{if($1!="#"){if(idx==ant_idx){print $1;}idx++;}}' antenna_locations.txt`
      fi
   fi
   
   echo "python $plot_delay_path $file  --unixtime --delay_unit=\"[ns]\" --y_min=${y_min} --y_max=${y_max} --multiplier=1000.00 --comment=\"AntID $antenna_id\" --outdir=\"./\" $plotting_options"
   python $plot_delay_path $file  --unixtime --delay_unit="[ns]" --y_min=${y_min} --y_max=${y_max} --multiplier=1000.00 --comment="AntID $antenna_id" --outdir="./" $plotting_options
done


# cd images/
list=""
count=0
all=0
for pngfile in `ls calsol_delay_antid???.png`
do
   list="${list} ${pngfile}"
   count=$(($count+1))
      
   rest=$(($count%16))   
   
   if [[ $rest == 0 ]]; then
       all_str=`echo $all | awk '{printf("%03d",$1);}'`
       echo "montage -mode concatenate -tile 4x4 $list -resize 1024x1024 calsol_delays_${all_str}.png"
       montage -mode concatenate -tile 4x4 $list -resize 1024x1024 calsol_delays_${all_str}.png
       
       echo "cp calsol_delays_${all_str}.png ${www_dir}/${out_subdir}/"
       cp calsol_delays_${all_str}.png ${www_dir}/${out_subdir}/
       
       list=""
       all=$(($all+1))
   fi
done

# part plotting mean / stddev :
echo "python $scripts_path/plot_calsolutions_vs_time.py --last_calibration_file=\"last_calibration.txt\" --outdir=\"./\" --station_id=${station_id} --start_date=${start_date} --get_mean_stddev_delay --outfile=${station_name}_mean_stddev_delay.txt"
python $scripts_path/plot_calsolutions_vs_time.py --last_calibration_file="last_calibration.txt" --outdir="./" --station_id=${station_id} --start_date=${start_date} --get_mean_stddev_delay --outfile=${station_name}_mean_stddev_delay.txt

echo "python $scripts_path/plot_delay.py ${station_name}_mean_stddev_delay.txt --delay_unit=\"[ns]\" --multiplier=1000.00 --comment=\"ErrorBar is STDDEV\" --mean_stddev --y_min=-10 --y_max=10 --outdir=\"./\""
python $scripts_path/plot_delay.py ${station_name}_mean_stddev_delay.txt --delay_unit="[ns]" --multiplier=1000.00 --comment="ErrorBar is STDDEV" --mean_stddev --y_min=-10 --y_max=10 --outdir="./"
echo "cp ${station_name}_mean_stddev_delay.png ${www_dir}/${out_subdir}/"
cp ${station_name}_mean_stddev_delay.png ${www_dir}/${out_subdir}/

month=`date +%Y%m`
first_of_month=`date +"%Y-%m-01 00:00:00"`
echo "python $scripts_path/plot_calsolutions_vs_time.py --last_calibration_file="last_calibration.txt" --outdir="./" --station_id=${station_id} --start_date=${first_of_month} --get_mean_stddev_delay --outfile=${month}_${station_name}_mean_stddev_delay.txt"
python $scripts_path/plot_calsolutions_vs_time.py --last_calibration_file="last_calibration.txt" --outdir="./" --station_id=${station_id} --start_date=${first_of_month} --get_mean_stddev_delay --outfile=${month}_${station_name}_mean_stddev_delay.txt

echo "python $scripts_path/plot_delay.py ${month}_${station_name}_mean_stddev_delay.txt --delay_unit=\"[ns]\" --multiplier=1000.00 --comment=\"ErrorBar is STDDEV\" --mean_stddev --y_min=-10 --y_max=10 --outdir=\"./\""
python $scripts_path/plot_delay.py ${month}_${station_name}_mean_stddev_delay.txt --delay_unit="[ns]" --multiplier=1000.00 --comment="ErrorBar is STDDEV" --mean_stddev --y_min=-10 --y_max=10 --outdir="./"

echo "cp ${month}_${station_name}_mean_stddev_delay.png ${www_dir}/${out_subdir}/"
cp ${month}_${station_name}_mean_stddev_delay.png ${www_dir}/${out_subdir}/

echo "cp ${month}_${station_name}_mean_stddev_delay.png ${www_dir}/${out_subdir}/current_month_${station_name}_mean_stddev_delay.png"
cp ${month}_${station_name}_mean_stddev_delay.png ${www_dir}/${out_subdir}/current_month_${station_name}_mean_stddev_delay.png
