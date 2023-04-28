#!/bin/bash

# Script creating MIRIAD .uv files with calibration tables filled according to text files.
# These text files can come from the database dump using either raw or fitted amplitudes 
# Script created by Jishnu Thekkeppattu and modified by Marcin Sokolowski (2023-03)

uvfilename=chan_176_20230315T040001.uvfits
if [[ -n "$1" && "$1" != "-" ]]; then
   uvfilename="$1"
fi

do_control_image=1
if [[ -n "$2" && "$2" != "-" ]]; then
   do_control_image=$2
fi

do_median_filter=0
if [[ -n "$3" && "$3" != "-" ]]; then
   do_median_filter=$3
fi


echo "####################################"
echo "PARAMETERS:"
echo "####################################"
echo "uvfilename       = $uvfilename"
echo "do_control_image = $do_control_image"
echo "do_median_filter = $do_median_filter"
echo "####################################"


DATA_PATH=`pwd`
CODE_PATH=~/aavs-calibration/
CALFILE_PATH=${DATA_PATH}

cd $DATA_PATH
rm -rf *.mir
rm -rf *.imap
rm -rf *.csv
rm -rf *.fits
rm -rf *.uv

imdim=512
cellres=10

# mv cal_csv cal_csv_ver1.00
rm -fr cal_csv/
mkdir -p cal_csv

# for uvfilename in $(ls chan_176_20230315T040*.uvfits)
if [[ -s ${uvfilename} ]]; then
    ######## load the uvfits ########

    echo "Processing : $uvfilename"
    fname_head=$(echo $uvfilename | awk -F "." '{print $1}')
    mirfilename="${fname_head}.mir"
    uv_x=${fname_head}_XX.uv
    uv_y=${fname_head}_YY.uv

    fits "in=${uvfilename}" "op=uvin" "out=${mirfilename}" >> /dev/null
    chan_num=$(echo $fname_head | awk -F "_" '{print $2}')
    echo $chan_num

    ######## median filter the database gains ########

    tmp_calfile_x=$(echo $(pwd)"/""tmp_calx_$chan_num.csv")
    tmp_calfile_y=$(echo $(pwd)"/""tmp_caly_$chan_num.csv")
    calfile_filx="filtered_db_gainsx.csv"
    calfile_fily="filtered_db_gainsy.csv"
    rm -f $tmp_calfile_x
    rm -f $tmp_calfile_y
    rm -f $calfile_filx
    rm -f $calfile_fily

    for an_number_0 in {0..255} #as the calibration tables start with 0 while miriad has 1 as the first antenna
    do 
        cal_sol_annumber=$(printf "%03d" $(echo $an_number_0))
        calfile="${CALFILE_PATH}/last_calibration_${cal_sol_annumber}_fitted.txt"
        gain_x=$(awk -v chan_num_dec="${chan_num}.000" '$1 == chan_num_dec {print $2}' < ${calfile})
        phase_x=$(awk -v chan_num_dec="${chan_num}.000" '$1 == chan_num_dec {print $3}' < ${calfile})
        gain_y=$(awk -v chan_num_dec="${chan_num}.000" '$1 == chan_num_dec {print $4}' < ${calfile})
        phase_y=$(awk -v chan_num_dec="${chan_num}.000" '$1 == chan_num_dec {print $5}' < ${calfile})
        echo "DEBUG : ant($an_number_0) calibration solutions : $gain_x/$phase_x , $gain_y/$phase_y"
        echo "${gain_x},${phase_x}" >> ${tmp_calfile_x}
        echo "${gain_y},${phase_y}" >> ${tmp_calfile_y}
    done

    if [[ $do_median_filter -gt 0 ]]; then
      # WARNING : it can produce strange results !!! see 20230425 data where some gain_x got set to ZERO !
      echo "WARNING : using median filter for gain amplitudes -> it can produce strange results !!! see 20230425 data where some gain_x got set to ZERO !"      
      echo "python3 ${CODE_PATH}/medfilgains.py -x ${tmp_calfile_x} -y ${tmp_calfile_y}"
      python3 ${CODE_PATH}/medfilgains.py -x ${tmp_calfile_x} -y ${tmp_calfile_y}
    else
      echo "INFO : not using median filter just using fitted amplitudes as they are"
      
      echo "cp ${tmp_calfile_x} ${calfile_filx}"
      cp ${tmp_calfile_x} ${calfile_filx}
    
      echo "cp ${tmp_calfile_y} ${calfile_fily}"
      cp ${tmp_calfile_y} ${calfile_fily}
    fi
        

    uvcat vis=${mirfilename} stokes=xx out=${uv_x} options=nocal,nopol,nopass
    uvcat vis=${mirfilename} stokes=yy out=${uv_y} options=nocal,nopol,nopass
    
    mfcal "vis=${mirfilename}" "refant=3" "flux=44372"
    mfcal "vis=${uv_x}" "refant=3" "flux=44372" 
    mfcal "vis=${uv_y}" "refant=3" "flux=44372" 

    ######## replace gains in the miriad file with the database gains ########

    for an_number in {1..256}
    do 
        gpx=$(head -${an_number} ${calfile_filx} | tail +${an_number})
        gpy=$(head -${an_number} ${calfile_fily} | tail +${an_number})
        gpedit "vis=${mirfilename}" "select=antenna(${an_number})" "feeds=X" "gain=${gpx}" "options=replace"
        gpedit "vis=${mirfilename}" "select=antenna(${an_number})" "feeds=Y" "gain=${gpy}" "options=replace"
        
        echo "gpedit vis=${uv_x} select=antenna(${an_number}) gain=${gpx} options=replace"
        gpedit "vis=${uv_x}" "select=antenna(${an_number})" "gain=${gpx}" "options=replace"
        
        echo "gpedit vis=${uv_y} select=antenna(${an_number}) gain=${gpy} options=replace"
        gpedit "vis=${uv_y}" "select=antenna(${an_number})" "gain=${gpy}" "options=replace"
    done

    ########  Image stokes I and after that, split the data into xx and yy ########

    if [[ $do_control_image -gt 0 ]]; then
       invert "vis=${mirfilename}" "map=${fname_head}_dbcal_I.imap" "imsize=${imdim},${imdim}" "stokes=i" "cell=${cellres},${cellres},res"
       fits "in = ${fname_head}_dbcal_I.imap" "out = ${fname_head}_dbcal_I.fits" "op = xyout"
    
       # check XX image for a test 
       invert "vis=${mirfilename}" "map=${fname_head}_dbcal_XX.imap" "imsize=${imdim},${imdim}" "stokes=XX" "cell=${cellres},${cellres},res"
       fits "in = ${fname_head}_dbcal_XX.imap" "out = ${fname_head}_dbcal_XX.fits" "op = xyout"
    
       # for comparison image uv_x file 
       # invert "vis=${uv_x}" "map=${fname_head}_XX.imap" "imsize=${imdim},${imdim}" "stokes=XX" "cell=${cellres},${cellres},res"
       # fits "in = ${fname_head}_XX.imap" "out = ${fname_head}_XX.fits" "op = xyout"

       # check YY image for a test 
       invert "vis=${mirfilename}" "map=${fname_head}_dbcal_YY.imap" "imsize=${imdim},${imdim}" "stokes=YY" "cell=${cellres},${cellres},res"
       fits "in = ${fname_head}_dbcal_YY.imap" "out = ${fname_head}_dbcal_YY.fits" "op = xyout"
    
       # for comparison image uv_x file 
       # invert "vis=${uv_x}" "map=${fname_head}_YY.imap" "imsize=${imdim},${imdim}" "stokes=YY" "cell=${cellres},${cellres},res"
       # fits "in = ${fname_head}_YY.imap" "out = ${fname_head}_YY.fits" "op = xyout"
    else
       echo "WARNING : control image is not required"
    fi 
    
    # fname_head
    mv $tmp_calfile_x cal_csv/${fname_head}.tmp_calfile_x
    mv $tmp_calfile_y cal_csv/${fname_head}.tmp_calfile_y
    mv $calfile_filx cal_csv/${fname_head}.calfile_filx
    mv $calfile_fily cal_csv/${fname_head}.calfile_fily
    mv ${mirfilename} cal_csv/

    # rm -rf *.mir
    rm -rf *.imap
    # rm -rf *.mirim
else
   echo "ERROR : file $uvfilename does not exist"
fi

# kvis *.imap
# ds9 *_I.fits
