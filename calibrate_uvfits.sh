#!/bin/bash

# The script assumes that the Sun is above the horizon and uses quiet Sun model to calibrate
# It also tries to calculate apparent flux of the Sun using beam model (single isolated element)
# Changes phase centre of visibilities to position of the Sun (sunpos.py script)

do_xx_yy=0 # WARNING : do not use =1 as this when applied to other observation (calibration transfer) produces wrong flux scale !!!
           # 2023-01-28 : I think the above comment is no longer valid, at least for visibilities phase centred on the Sun 
if [[ -n "$1" && "$1" != "-" ]]; then
   do_xx_yy=$1
fi

channel=204
if [[ -n "$2" && "$2" != "-" ]]; then
   channel=$2
fi

list_file=uvfits_list
if [[ -n "$3" && "$3" != "-" ]]; then
   list_file=$3
fi

generate_beams=1
if [[ -n "$4" && "$4" != "-" ]]; then
   generate_beams=$4
fi

cal_dir=calibration/
if [[ -n "$5" && "$5" != "-" ]]; then
   cal_dir=$5
fi

clean_old_uv_files=1
if [[ -n "$6" && "$6" != "-" ]]; then
   clean_old_uv_files=$6
fi

use_hdf5_files=1
if [[ -n "$7" && "$7" != "-" ]]; then
   use_hdf5_files=$7
fi

set_phase_centre_sun=1
if [[ -n "$8" && "$8" != "-" ]]; then
   set_phase_centre_sun=$8
fi


echo "#############################################"
echo "PARAMETERS:"
echo "#############################################"
echo "list_file = $list_file"
echo "do_xx_yy = $do_xx_yy"
echo "channel  = $channel"
echo "generate_beams = $generate_beams"
echo "cal_dir = $cal_dir"
echo "clean_old_uv_files = $clean_old_uv_files"
echo "use_hdf5_files = $use_hdf5_files"
echo "set_phase_centre_sun = $set_phase_centre_sun"
echo "#############################################"

do_mfcal_object="sun" # use mfcal with proper solar flux scale (as in Randall's script to get SEFD and other proper flux scale)
reference_antenna=3
control_image=1
save_calsolutions=1
station_name=EDA

export PATH=~/aavs-calibration:~/Software/station_beam/python/:$PATH

# Quiet sun (http://extras.springer.com/2009/978-3-540-88054-7/06_vi4b_4116.pdf
# 4.1.1.6 Quiet and slowly varying radio emissions of the sun
# Ref. p. 88] 4.1.1.6 Quiet and slowly varying radio emissions of the sun 81 Table 1. Flux density, F, and brightness temperature, T rad, of the quiet sun. F = radio ﬂux density of the quiet sun during sunspot m
# extras.springer.com )
# note change in spectral index of sun around 150 MHz, so better to use different
# power law at low vs high freqs
# MFCAL flux parameters : 51000,0.15,1.6
solar_flux=51000
apparent_solar_flux=${solar_flux}
apparent_solar_flux_x=${solar_flux}
apparent_solar_flux_y=${solar_flux}
beam_on_sun_x=1.00 # TODO : add option -b which will calculate this two automatically based on sun position at the time of data collection and beam value in this direction
beam_on_sun_y=1.00 # TODO : as above 
beam_set_by_params=0
beam_on_sun_file=beam_on_sun.txt

########################################################################################################3
if [[ ! -s ${list_file} ]]; then
   echo "WARNING : UV FITS file list does not exist -> using all"
   
   echo "ls *.uvfits > ${list_file}"
   ls *.uvfits > ${list_file}
fi

########################################################### Calculating flux density using beam models ###########################################################
# generate beam values for the sun: 
# 20180102T010203 -> 2018_01_01-00:00 
dtm=`head -1 ${list_file} | cut -b 10-24`
dtm2=`echo ${dtm} | awk '{print substr($1,1,4)"_"substr($1,5,2)"_"substr($1,7,2)"-"substr($1,10,2)":"substr($1,12,2);}'`
dtm_utc=`echo ${dtm} | awk '{print substr($1,1,4)"-"substr($1,5,2)"-"substr($1,7,2)" "substr($1,10,2)":"substr($1,12,2)":"substr($1,14,2);}'`
ux=`date -u -d "${dtm_utc}" +%s`
echo "INFO : based on the first .uvfits file dtm = $dtm , dtm2 = $dtm2 , dtm_utc = $dtm_utc -> ux = $ux"
sun_pos_line=`python ~/aavs-calibration/sunpos.py $ux | tail -1`
ra_deg=`echo $sun_pos_line | awk '{print $1*15.00;}'`
ra_h=`echo $sun_pos_line | awk '{print $1;}'`
dec_deg=`echo $sun_pos_line | awk '{print $2;}'`
ra_string=`echo $ra_h | awk '{ra_h=int($1);ra_frac=$1-ra_h;ra_min=int(ra_frac*60.00);ra_s=(ra_frac*60.00-ra_min)*60.00;printf("%02d,%02d,%02d\n",ra_h,ra_min,int(ra_s));}'`
dec_string=`echo $dec_deg | awk '{dec=$1;dec_abs=$1;sign=1;if(dec<0){dec_abs=-dec;sign=-1;}dec_deg=sign*int(dec_abs);dec_arcmin=(dec_abs-int(dec_abs))*60.00;dec_arcsec=(dec_arcmin-int(dec_arcmin))*60.00;printf("%02d,%02d,%02d\n",dec_deg,dec_arcmin,int(dec_arcsec));}'`
echo "INFO : sun position (RA,DEC) = ($ra_deg,$dec_deg) [deg] -> string for uvedit $ra_string,$dec_string"

if [[ $generate_beams -gt 0 ]]; then
   # echo "~/Software/station_beam/scripts/beam_correct_latest_cal.sh ${station} ${dtm2}"
   # ~/Software/station_beam/scripts/beam_correct_latest_cal.sh ${station} ${dtm2}
   hdf5_cnt=`ls *.hdf5 2>/dev/null | wc -l`
   echo "INFO : generation of beams on the Sun is required (HDF5 file count = $hdf5_cnt)"
   path=`which fits_beam.py`
   
   if [[ $hdf5_cnt -gt 0 && $use_hdf5_files -gt 0 ]]; then
      echo "INFO : hdf5 files found -> calculating beam on sun based on HDF5"
      ls -tr *.hdf5 > hdf5_list   
      echo "python $path --infile_hdf5list=hdf5_list --outfile_beam_on_sun=beam_on_sun.txt --station=${station_name}"
      python $path --infile_hdf5list=hdf5_list --outfile_beam_on_sun=beam_on_sun.txt --station=${station_name}
   else
      echo "INFO : HDF5 files not found or not supposed to be used (use_hdf5_files=$use_hdf5_files) -> using unix time of the first file"
      
      echo "python $path --outfile_beam_on_sun=beam_on_sun.txt --station=${station_name} --unix_time=${ux} --channel=${channel}"
      python $path --outfile_beam_on_sun=beam_on_sun.txt --station=${station_name} --unix_time=${ux} --channel=${channel}      
   fi
else
   echo "WARNING : generation of beams on the Sun is not required"   
fi   

echo "DEBUG : experimental version, beam not set by external parameters -> checking text file ${beam_on_sun_file} ..."
if [[ -s ${beam_on_sun_file} ]]; then
    echo "DEBUG : file ${beam_on_sun_file} exists -> trying to find beam-on-sun values for the specific channel"
    line=`awk -v channel=${channel} '{if($1!="#" && $1==channel){print $0;}}' ${beam_on_sun_file}`
       
    if [[ -n $line ]]; then
       beam_on_sun_x=`echo $line | awk '{print $2;}'`
       beam_on_sun_y=`echo $line | awk '{print $3;}'`
          
       # calculate apparent solar flux 
       apparent_solar_flux_x=`echo $solar_flux" "$beam_on_sun_x | awk '{print ($1*$2);}'` 
       apparent_solar_flux_y=`echo $solar_flux" "$beam_on_sun_y | awk '{print ($1*$2);}'` 
       apparent_solar_flux=`echo "$apparent_solar_flux_x $apparent_solar_flux_y" | awk '{print ($1+$2)/2.00;}'`

       echo "DEBUG : Sun beam information = |$line| -> Beam on sun values beam_x = $beam_on_sun_x , beam_y = $beam_on_sun_y -> solar flux $solar_flux -> apparent solar flux X/Y = $apparent_solar_flux_x / $apparent_solar_flux_y"
    else
       echo "WARNING : beam values not calculated for channel = $channel -> will use the default beam settings for the Sun location beam_x/beam_y = $beam_on_sun_x / $beam_on_sun_y -> no Sun beam correction"
    fi
else
    echo "WARNING : file $beam_on_sun_file does not exist -> will use the default beam settings for the Sun location beam_x/beam_y = $beam_on_sun_x / $beam_on_sun_y -> no Sun beam correction"
fi


last_uvfits=""
for uvfitsfile in `cat ${list_file}` ; 
do
    src=`basename $uvfitsfile .uvfits`    
    echo "Processing $uvfitsfile to ${src}.uv"
    last_uvfits=${src}

    if [[ $clean_old_uv_files -gt 0 ]]; then    
       echo "rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv"
       rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv
       
       if [[ $set_phase_centre_sun -gt 0 ]]; then
          echo "python ~/aavs-calibration/setkey.py ${uvfitsfile}"
          python ~/aavs-calibration/setkey.py ${uvfitsfile}
       fi
       
       echo "fits op=uvin in=\"$uvfitsfile\" out=\"${src}.uv\" options=compress"
       fits op=uvin in="$uvfitsfile" out="${src}.uv" options=compress
    else
       echo "WARNING : cleaning of .uv files is not required"
    fi
    
    # change phase centre of visibilities to Sun :
    if [[ $set_phase_centre_sun -gt 0 ]]; then
      echo "uvedit vis=${src}.uv ra=${ra_string} dec=${dec_string}"
      uvedit vis=${src}.uv ra=${ra_string} dec=${dec_string}
    
      echo "mv ${src}.uv ${src}.uv_old_phase_centre"
      mv ${src}.uv ${src}.uv_old_phase_centre
    
      echo "mv ${src}.uv_c ${src}.uv"
      mv ${src}.uv_c ${src}.uv
      
      # TODO:
      # before conversion 
      # add python ./setkey.py ${uvfits_file} 
    else
      echo "WARNING : changing phase centre to Sun is not required"
    fi
    
    # FINAL extra flagging here  :
    # uvflag flagval=flag vis=${src}.uv select='ant(49,50,51,52,57,58,59)'
    
    echo "puthd in=${src}.uv/jyperk value=1310.0"
    puthd in=${src}.uv/jyperk value=1310.0
    
    echo "puthd in=${src}.uv/systemp value=200.0"
    puthd in=${src}.uv/systemp value=200.0

    if [[ $do_xx_yy -gt 0 ]]; then    
      if [[ ! -d ${src}_XX.uv ]]; then
         echo "uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv"
         uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
      else
         echo "WARNING : using existing file ${src}_XX.uv"
      fi
    
      if [[ ! -d ${src}_YY.uv ]]; then
         echo "uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv"
         uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv
      else
         echo "WARNING : using existing file ${src}_YY.uv"
      fi
    fi

    # MFCAL : 
    if [[ $channel -gt 192 ]]; then # f > 150 MHz (192 *(400/512) = 150 MHz ) :
       echo "Channel = $channel > 192 -> using the high-frequency power law:"

       if [[ $do_xx_yy -gt 0 ]]; then
          # mfcal on XX and YY or rather uvcat to split .uv -> _XX.uv and _YY.uv ?
          # current way is a bit in-efficient, so I will change it later
          echo "mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"  
          mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz

          echo "mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"  
          mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz          
       else
          echo "mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"
          mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz          
       fi
    else
        # verifyed on 2020-04-23 :
        # Lower limit of 0.005 kLambda means 10m at 150 MHz to make it 10 m everywhere use the following formula
        #    It comes from B_min = 10m expressed in kLambda -> (B_min/Lambda[m])*Lambda[m] = (B_min/Lambda[m])*(kLambda/1000.00) as kLambda = Lambda[m]/1000.00
        #    and Lambda[m] = 300 / ( (400/512)*ch ) [m] 
        # below 150 MHz the uvrange has to be different as otherwise we can end up with 0 baselines 
        # I set limit to B>10m and calculate 
        min_klambda=`echo $channel | awk '{print ($1*(400.00/512.00))/30000.00;}'`

        echo "Channel = $channel <= 192 -> using the low-frequency power law, lower uvrange limit = $min_klambda kLambda"

        if [[ $do_xx_yy -gt 0 ]]; then
           # mfcal on XX and YY or rather uvcat to split .uv -> _XX.uv and _YY.uv ?
           # current way is a bit in-efficient, so I will change it later
           echo "mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
           mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz

           echo "mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
           mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz                          
        else
           echo "mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
           mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz
        fi
    fi
    
    if [[ $do_xx_yy -gt 0 ]]; then
       # set validity of calibraton solutions to 365 days !!!
       echo "puthd in=${src}_XX.uv/interval value=365"
       puthd in=${src}_XX.uv/interval value=365

       echo "puthd in=${src}_YY.uv/interval value=365"
       puthd in=${src}_YY.uv/interval value=365
    else
       # set validity of calibraton solutions to 365 days !!!
       echo "puthd in=${src}.uv/interval value=365"
       puthd in=${src}.uv/interval value=365   
    fi

    if [[ $control_image -gt 0 || $save_calsolutions -gt 0 ]]; then
       if [[ ! -d ${src}_XX.uv ]]; then
          echo "uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv"
          uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
       fi   

       if [[ ! -d ${src}_YY.uv ]]; then
          echo "uvcat vis=${src}.uv stokes=xx out=${src}_YY.uv"
          uvcat vis=${src}.uv stokes=xx out=${src}_YY.uv
       fi

       if [[ $save_calsolutions -gt 0 ]]; then
          echo "INFO : saving calibration solutions to *.txt files"
       
          # save solutions :
          for stokes in `echo "XX YY"`
          do
             gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_amp.txt
             gpplt vis=${src}_${stokes}.uv log=aavs_gain_${stokes}_pha.txt yaxis=phase
             gain_extract_selfcal.sh aavs_gain_${stokes}_amp.txt >> "amp_${stokes}.txt"
             gain_extract_selfcal.sh aavs_gain_${stokes}_pha.txt >> "phase_${stokes}.txt"
          done
       else
          echo "WARNING : saving calibration solutions to text files is not required"
       fi


       if [[ $control_image -gt 0 ]]; then       
          echo "INFO : creating control images"
        
          rm -fr ${src}_XX.map ${src}_XX.beam ${src}_YY.map ${src}_YY.beam
          echo "invert vis=${src}_XX.uv map=${src}_XX.map imsize=180,180 beam=${src}_XX.beam robust=-0.5 options=double,mfs" 
          invert vis=${src}_XX.uv map=${src}_XX.map imsize=180,180 beam=${src}_XX.beam robust=-0.5 options=double,mfs
       
          echo "invert vis=${src}_YY.uv map=${src}_YY.map imsize=180,180 beam=${src}_YY.beam robust=-0.5 options=double,mfs" 
          invert vis=${src}_YY.uv map=${src}_YY.map imsize=180,180 beam=${src}_YY.beam robust=-0.5 options=double,mfs
       
          echo "fits op=xyout in=${src}_XX.map out=${src}_XX.fits"
          fits op=xyout in=${src}_XX.map out=${src}_XX.fits
       
          echo "fits op=xyout in=${src}_YY.map out=${src}_YY.fits"
          fits op=xyout in=${src}_YY.map out=${src}_YY.fits
       else
          echo "WARNING : control images are not required"       
       fi
    fi
done

if [[ -n "$last_uvfits" ]]; then
   echo "INFO : copying last calibration files from $last_uvfits to calibration directory ${cal_dir}"

   if [[ -d ${cal_dir}/OLD/ ]]; then
      echo "rm -fr ${cal_dir}/OLD/*"
      rm -fr ${cal_dir}/OLD/*
   fi   

   ux=`date +%s`
   echo "mkdir -p ${cal_dir}/OLD/${ux}"
   mkdir -p ${cal_dir}/OLD/${ux}
   
   echo "mv ${cal_dir}/cal*uv ${cal_dir}/OLD/${ux}"
   mv ${cal_dir}/cal*uv ${cal_dir}/OLD/${ux}

   echo "cp -a ${last_uvfits}.uv ${cal_dir}/cal.uv"
   cp -a ${last_uvfits}.uv ${cal_dir}/cal.uv

   echo "cp -a ${last_uvfits}_XX.uv ${cal_dir}/cal_XX.uv"
   cp -a ${last_uvfits}_XX.uv ${cal_dir}/cal_XX.uv
   
   echo "cp -a ${last_uvfits}_YY.uv ${cal_dir}/cal_YY.uv"
   cp -a ${last_uvfits}_YY.uv ${cal_dir}/cal_YY.uv

   echo "cp -a ${last_uvfits}*fits ${cal_dir}/"
   cp -a ${last_uvfits}*fits ${cal_dir}/

   echo "cp -a ${last_uvfits}*uv ${cal_dir}/"
   cp -a ${last_uvfits}*uv ${cal_dir}/

   # saving last Unix time :
   dtm=`echo ${last_uvfits} | cut -b 10-24`   
   dtm_utc=`echo ${dtm} | awk '{print substr($1,1,4)"-"substr($1,5,2)"-"substr($1,7,2)" "substr($1,10,2)":"substr($1,12,2)":"substr($1,14,2);}'`
   ux=`date -u -d "${dtm_utc}" +%s`
   echo "DEBUG : $dtm -> $dtm2 -> $dtm_utc -> uxtime = $ux"
   echo $ux > last_calibration.txt
   echo $ux > ${cal_dir}/last_calibration.txt
else
   echo "WARNING : no last UV fits file found"   
fi
