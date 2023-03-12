#!/bin/bash

freq_channel=204
if [[ -n "$1" && "$1" != "-" ]]; then
   freq_channel=$1
fi

station_id=2
if [[ -n "$2" && "$2" != "-" ]]; then
   station_id=$2
fi

# how many channels before and after to use to fit/filter outliers points - for example ORBCOMM channels where proper calibration solutions cannot be obtained
channel_fit_range=30
if [[ -n "$3" && "$3" != "-" ]]; then
   channel_fit_range=$3
fi

# getting calibration solutions as they are in the database, however :
#  - PHASE is calculated according to fitted delays
#  - AMPLITUDE is the value as produced by MIRIAD and it will be later filtered/fitted by Savitzky-Goley or other methods : 
echo "python ~/aavs-calibration/station/calibration.py --save_db_cal_file=last_calibration_%03d_db.txt --station_id=${station_id} --start_freq_channel=${freq_channel}"
python ~/aavs-calibration/station/calibration.py --save_db_cal_file=last_calibration_%03d_db.txt --station_id=${station_id} --start_freq_channel=${freq_channel}

# save calibration solutions for a specified range of frequency channels [freq_channel-channel_fit_range,freq_channel+channel_fit_range] :
start_freq_channel=$(($freq_channel-$channel_fit_range))
end_freq_channel=$(($freq_channel+$channel_fit_range))
total_n_channels=$((2*$channel_fit_range))

echo "python ~/aavs-calibration/station/calibration.py --save_db_cal_file=calsol_ant%03d.txt --station_id=${station_id} --start_freq_channel=${start_freq_channel} --save_n_channels=${total_n_channels}"
python ~/aavs-calibration/station/calibration.py --save_db_cal_file=calsol_ant%03d.txt --station_id=${station_id} --start_freq_channel=${start_freq_channel} --save_n_channels=${total_n_channels}



