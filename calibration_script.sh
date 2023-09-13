#!/usr/bin/env bash

do_calibrate=1
default_dump_time=1.9818086
default_nav=1
default_data_dir=.
dump_time=${default_dump_time}
nav=${default_nav}
data_dir=${default_data_dir}
keep_intermediate=0
convert_hdf5_files=1
station_name=eda2
reference_antenna=3 # 2020-02-07 - back to antenna 3 from 5 (most of data with ANT=3 - MIRIAD)
                    # 2020-01-29 - antenna 3 broken after storm -> using 5 for now (at least for the EDA2)
                    # Changed 2->3 for EDA2 (2 is not working) there might be some issue with EDA2 antenna 2 (index based from 1) or 1 (index based 0), So I might need to test another one

do_mfcal_object="sun" # use mfcal with proper solar flux scale (as in Randall's script to get SEFD and other proper flux scale)

# Quiet sun (http://extras.springer.com/2009/978-3-540-88054-7/06_vi4b_4116.pdf
# 4.1.1.6 Quiet and slowly varying radio emissions of the sun
# Ref. p. 88] 4.1.1.6 Quiet and slowly varying radio emissions of the sun 81 Table 1. Flux density, F, and brightness temperature, T rad, of the quiet sun. F = radio ﬂux density of the quiet sun during sunspot minimum in units of 10 −22 Wm 2Hz −1=1019 erg cm Hz s−1 = solar ﬂux unit (sfu) T rad = brightness temperature of an optical solar disk with a diameter of 32
# extras.springer.com )
# note change in spectral index of sun around 150 MHz, so better to use different
# power law at low vs high freqs
# MFCAL flux parameters : 51000,0.15,1.6
solar_flux=51000
beam_on_sun_x=1.00 # TODO : add option -b which will calculate this two automatically based on sun position at the time of data collection and beam value in this direction
beam_on_sun_y=1.00 # TODO : as above 
beam_set_by_params=0

beam_on_sun_file=beam_on_sun.txt


# Include binaries in calibration directory
#export PATH=$PATH:/home/aavs/randall_calibration
function print_usage {
  echo "Usage:"
  echo "$0 [options] chan_index"
  echo -e "\t-D data_dir\tdirectory to work in. Default: ${default_data_dir}"
  echo -e "\t-T dumptime\tcorrelator integration time. Default: ${default_dump_time}"
  echo -e "\t-N n_av \tpost correlator averaging that has been applied to data. Default: ${default_nav}"
  echo -e "\t-k  \tkeep intermediate data products for debugging"
  echo -e "\t-s  \tskip conversion from hdf5 files to uvfits (just calibrate using exisitng uvfits files). Default: ${convert_hdf5_files}"
  echo -e "\t-S STATION_NAME , name of the station the data was collected with. Default: ${station_name}"
  echo -e "\t-R REFERENCE ANTENNA , default = ${reference_antenna} (miriad index is 1-based)"
  echo -e "\t-m MFCAL_OBJECT , use mfcal instead of selfcal to calibrate, pass object name (at the moment only sun is allowed), by default it is disabled (no object set = empty string)"
  echo -e "\t-x BEAM value on sun in X [default $beam_on_sun_x]"
  echo -e "\t-y BEAM value on sun in Y [default $beam_on_sun_y]"
  echo -e "\t-c run calibration YES/NO (1/0) [default do_calibrate = $do_calibrate]"
}

#echo "Command line: $@"

# parse command-line options
while getopts ":D:T:N:ksS:R:m:x:y:c:" opt; do
  echo "Parsing option ${opt} , argument = ${OPTARG}"
  case ${opt} in
    x)
      beam_on_sun_x=${OPTARG}
      beam_set_by_params=`echo ${beam_on_sun_x} | awk '{if($1!=1.00){print 1;}else{print 0;}}'`
      ;;

    y)
      beam_on_sun_y=${OPTARG}
      beam_set_by_params=`echo ${beam_on_sun_y} | awk '{if($1!=1.00){print 1;}else{print 0;}}'`
      ;;

    D)
      data_dir=${OPTARG}
      echo "user specified directory ${data_dir}"
      ;;
    T)
      dump_time=${OPTARG}
      echo "user specified dump time: ${dump_time}"
      ;;
    N)
      nav=${OPTARG}
      ;;
    c)
      do_calibrate=${OPTARG}
      ;;
    k)
      keep_intermediate=1
      ;;
    s)
      convert_hdf5_files=0
      ;;
    S)
      station_name=${OPTARG}
      ;;
    R)
      reference_antenna=${OPTARG}
      ;;
    m)
      do_mfcal_object=`echo ${OPTARG} | awk '{print tolower($1);}'`
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      print_usage
      exit -1
      ;;
  esac
done
shift $((OPTIND-1))

# check that miriad environment is set up
if [[ -z "${MIR}" ]]; then
  echo "ERROR: miriad environment is not set up"
  exit 1
fi

# Extract channel to work on
channel=$1
if [ "$channel" = "" ] ; then
  echo "invalid channel index $channel"
  exit 1
fi

# Go to directory where data is stored
cd "${data_dir}"
if [ $? -ne 0 ] ; then
  exit 1
fi
echo "channel: $channel. PWD: $PWD"

if [[ $beam_set_by_params -le 0 ]]; then
   echo "DEBUG : experimental version, beam not set by external parameters -> checking text file ${beam_on_sun_file} ..."
   if [[ -s ${beam_on_sun_file} ]]; then
       echo "DEBUG : file ${beam_on_sun_file} exists -> trying to find beam-on-sun values for the specific channel"
       line=`awk -v channel=${channel} '{if($1!="#" && $1==channel){print $0;}}' ${beam_on_sun_file}`
       
       if [[ -n $line ]]; then
          beam_on_sun_x=`echo $line | awk '{print $2;}'`
          beam_on_sun_y=`echo $line | awk '{print $3;}'`
          echo "DEBUG : Sun beam information = |$line| -> Beam on sun values beam_x = $beam_on_sun_x , beam_y = $beam_on_sun_y"          
       else       
          echo "WARNING : beam values not calculated for channel = $channel -> will use the default beam settings for the Sun location beam_x/beam_y = $beam_on_sun_x / $beam_on_sun_y -> no Sun beam correction"
       fi
   else
       echo "WARNING : file $beam_on_sun_file does not exist -> will use the default beam settings for the Sun location beam_x/beam_y = $beam_on_sun_x / $beam_on_sun_y -> no Sun beam correction"
   fi
fi



# calculate apparent solar flux 
apparent_solar_flux_x=`echo $solar_flux" "$beam_on_sun_x | awk '{print ($1*$2);}'` 
apparent_solar_flux_y=`echo $solar_flux" "$beam_on_sun_y | awk '{print ($1*$2);}'` 
apparent_solar_flux=`echo "$apparent_solar_flux_x $apparent_solar_flux_y" | awk '{print ($1+$2)/2.00;}'`

echo "######################################################################################################"
echo "PARAMETERS :"
echo "######################################################################################################"
echo "channel           = $channel"
echo "reference_antenna = $reference_antenna"
echo "station_name      = $station_name"
if [[ -n "do_mfcal_object" ]]; then
   echo "do_mfcal_object   = $do_mfcal_object"
fi
echo "Apparent solar flux x / y / mean = $apparent_solar_flux_x / $apparent_solar_flux_y / $apparent_solar_flux ( from $solar_flux * ( beam_on_sun_x = $beam_on_sun_x and beam_on_sun_y = $beam_on_sun_y ) )"
echo "do_calibrate = $do_calibrate"
echo "######################################################################################################"


# TODO : instead of copying ~/aavs-calibration/header_eda2_cal.txt - same generation function should be used here and in Lfile2uvfits_eda.sh and Lfile2uvfits.sh
# MS : 20191204 - I changed symbolic links to copies to keep track of what we used at the time of calibration
#      with symbolic link if the target changes, we don't know what was used at the time
# Link some configuration files
station_id=2
echo "Creating links to config files for a default station (station name = $station_name)"
if [[ $station_name == "eda2" || $station_name == "EDA2" ]]; then
   echo "Creating links to config files for station $station_name"
         
   echo "cp ~/aavs-calibration/instr_config_eda2.txt instr_config.txt"                    
   cp ~/aavs-calibration/instr_config_eda2.txt instr_config.txt
   cp ~/aavs-calibration/antenna_locations_eda2.txt antenna_locations.txt
   cp ~/aavs-calibration/header_eda2_cal.txt header.txt
   station_id=2
else
   if [[ $station_name == "aavs2" || $station_name == "AAVS2" ]]; then
      echo "Creating links to config files for station AAVS2"
      
      # cp ~/aavs-calibration/config/aavs2/instr_config_aavs2_20191129.txt instr_config.txt
      echo "cp ~/aavs-calibration/config/aavs2/instr_config.txt instr_config.txt"
      cp ~/aavs-calibration/config/aavs2/instr_config.txt instr_config.txt
      cp ~/aavs-calibration/config/aavs2/antenna_locations_20191202.txt antenna_locations.txt
      cp ~/aavs-calibration/header_cal.txt header.txt 
      station_id=3
   else
      echo "Creating links to config files for default station (AAVS1)"
      
      cp ~/aavs-calibration/instr_config.txt .
      cp ~/aavs-calibration/antenna_locations.txt .
      cp ~/aavs-calibration/header_cal.txt header.txt .
      station_id=1
   fi
fi   

# Compute the integration time for the given dump time and integration skip (nav)
int_time=`echo $nav ${dump_time} | awk '{ printf "%.3f\n",$1*$2 }'`

# Convert all HDF files  for required channel to uvfits files with visibilities phased towards the sun
if [[ $convert_hdf5_files -gt 0 ]]; then
   echo "Executing conversion from hdf5 files to uvfits"
         
   for hdffile in `ls -tr *_${channel}_*.hdf5` ; do
      bname=`basename $hdffile .hdf5`
      hdf2Lfile.sh "$hdffile" $nav
      unixtime=`cat ${bname}_ts_unix.txt`
      echo "python ~/aavs-calibration/sunpos.py $unixtime"
      radec=`python ~/aavs-calibration/sunpos.py $unixtime`

      # MSOK : WARNING/TODO : Lfile2uvfits.sh should really be changed to Lfile2uvfits_eda.sh as there are currently 2 scripts for conversion ...
      station_name_upper=`echo $station_name | awk '{print toupper($1);}'`      
      echo "Lfile2uvfits.sh \"$hdffile\" $int_time $radec $station_name_upper"
      Lfile2uvfits.sh "$hdffile" $int_time $radec $station_name_upper
   done
else
   echo "WARNING : convert_hdf5_files=$convert_hdf5_files -> not executing conversion from hdf5 files to uvfits"
fi

if [[ $do_calibrate -gt 0 ]]; then
   # Unpack and flag
   for uvfitsfile in `ls -tr chan_${channel}_*.uvfits` ; do
       src=`basename $uvfitsfile .uvfits`
       echo "Processing $uvfitsfile to ${src}.uv"
       rm -rf ${src}.uv ${src}_XX.uv ${src}_YY.uv
       fits op=uvin in="$uvfitsfile" out="${src}.uv" options=compress
       puthd in=${src}.uv/jyperk value=1310.0
       puthd in=${src}.uv/systemp value=200.0
       uvcat vis=${src}.uv stokes=xx out=${src}_XX.uv
       uvcat vis=${src}.uv stokes=yy out=${src}_YY.uv    
   done

   # Perform self calibration on data
   for uvfitsfile in `ls -tr chan_${channel}_*.uvfits` ; do
       src=`basename $uvfitsfile .uvfits`
       utc=`echo ${uvfitsfile} | awk -F "_" '{print $3}'`
       utc_dt=`echo $utc | cut -b 1-8`
       utc_tm=`echo $utc | cut -b 10- | awk '{print substr($1,1,2)":"substr($1,3,2)":"substr($1,5,2);}'`
       ux=`date -u -d "$utc_dt $utc_tm" +%s`
       echo "Processing $uvfitsfile to ${src}.uv ( $utc UTC -> $utc_dt $utc_tm UTC -> ux = $ux )"
    
       # newly added part to try to use proper spectral model of the Sun (selfcal cannot do it):
       mfcal_ok=0
       if [[ -n "$do_mfcal_object" ]]; then
          if [[ $do_mfcal_object == "sun" ]]; then
             mfcal_ok=1
          
             # calculate beam value using station_beam/fits_beam.py for given file and solar position 
          
             # Quiet sun (http://extras.springer.com/2009/978-3-540-88054-7/06_vi4b_4116.pdf
             # 4.1.1.6 Quiet and slowly varying radio emissions of the sun
             # Ref. p. 88] 4.1.1.6 Quiet and slowly varying radio emissions of the sun 81 Table 1. Flux density, F, and brightness temperature, T rad, of the quiet sun. F = radio ﬂux density of the quiet sun during sunspot minimum in units of 10 −22 Wm 2Hz −1=1019 erg cm Hz s−1 = solar ﬂux unit (sfu) T rad = brightness temperature of an optical solar disk with a diameter of 32
             # extras.springer.com )
             # note change in spectral index of sun around 150 MHz, so better to use different
             # power law at low vs high freqs
             if [[ $channel -gt 192 ]]; then # f > 150 MHz (192 *(400/512) = 150 MHz ) :
                echo "Channel = $channel > 192 -> using the high-frequency power law :"
                echo "mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"
                mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz

                # mfcal on XX and YY or rather uvcat to split .uv -> _XX.uv and _YY.uv ?
                # current way is a bit in-efficient, so I will change it later
                echo "mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"  
                mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz

                echo "mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna}"  
                mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.6 select='uvrange(0.005,1)' refant=${reference_antenna} # f > 150 MHz
             else
                # verifyed on 2020-04-23 :
                # Lower limit of 0.005 kLambda means 10m at 150 MHz to make it 10 m everywhere use the following formula
                #    It comes from B_min = 10m expressed in kLambda -> (B_min/Lambda[m])*Lambda[m] = (B_min/Lambda[m])*(kLambda/1000.00) as kLambda = Lambda[m]/1000.00
                #    and Lambda[m] = 300 / ( (400/512)*ch ) [m] 
                # below 150 MHz the uvrange has to be different as otherwise we can end up with 0 baselines 
                # I set limit to B>10m and calculate 
                min_klambda=`echo $channel | awk '{print ($1*(400.00/512.00))/30000.00;}'`
             
                       
                echo "Channel = $channel <= 192 -> using the low-frequency power law, lower uvrange limit = $min_klambda kLambda"             
                echo "mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
                mfcal vis=${src}.uv flux=${apparent_solar_flux},0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz
             
                # mfcal on XX and YY or rather uvcat to split .uv -> _XX.uv and _YY.uv ?
                # current way is a bit in-efficient, so I will change it later
                echo "mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
                mfcal vis=${src}_XX.uv flux=${apparent_solar_flux_x},0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz

                echo "mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.9 select=\"uvrange($min_klambda,1)\" refant=${reference_antenna}"
                mfcal vis=${src}_YY.uv flux=${apparent_solar_flux_y},0.15,1.9 select="uvrange($min_klambda,1)" refant=${reference_antenna} # f < 150 MHz                          
             fi
          else
             echo "WARNING : object $mfcal_ok of unknown flux specified -> will use standard selfcal"
          fi       
       else
          echo "INFO : no mfcal object specified -> will use normal selfcal"
       fi
       
       # normal code using selfcal (if mfcal is not requested to have correct flux scale) :
       if [[ $mfcal_ok -le 0 ]]; then
          echo "WARNING : using standard selfcal procedure flux scale (also for Sun) is not optimal (set to 100000)"
          selfcal vis=${src}_XX.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=${reference_antenna} flux=100000
          selfcal vis=${src}_YY.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=${reference_antenna} flux=100000
       fi
    
       # set calibration solution validity interval to 365 days :
       echo "puthd in=${src}.uv/interval value=365"
       puthd in=${src}.uv/interval value=365

       echo "puthd in=${src}_XX.uv/interval value=365"
       puthd in=${src}_XX.uv/interval value=365

       echo "puthd in=${src}_YY.uv/interval value=365"
       puthd in=${src}_YY.uv/interval value=365
   done

   # Extract calibration solutions
   outfile_amp="chan_${channel}_selfcal_amp"
   outfile_pha="chan_${channel}_selfcal_pha"

   tmpcal=`mktemp -d`
   for uvfitsfile in `ls -tr chan_${channel}_*.uvfits` ; do
     src=`basename $uvfitsfile .uvfits`
     echo "Processing $uvfitsfile"
     for stokes in XX YY ; do
       gpplt vis=${src}_${stokes}.uv log=$tmpcal/aavs_gain_${stokes}_amp.txt
       gpplt vis=${src}_${stokes}.uv log=$tmpcal/aavs_gain_${stokes}_pha.txt yaxis=phase
       gain_extract_selfcal.sh $tmpcal/aavs_gain_${stokes}_amp.txt >> "${outfile_amp}_${stokes}.txt"
       gain_extract_selfcal.sh $tmpcal/aavs_gain_${stokes}_pha.txt >> "${outfile_pha}_${stokes}.txt"
     done
   done
else
   echo "WARNING : calibration is not required"
fi   

# Remove all generated files
if [ $keep_intermediate -ne 1 ] ; then
#  rm -fr *.uvfit
  rm -fr *ts_unix.txt # MS : keeping these to be able to later apply and form images in real-time, please do not change without consulting with MS : *.uv
fi
for hdffile in `ls -tr *_${channel}_*.hdf5` ; do
  bname=`basename $hdffile .hdf5`
  rm -fr ${bname}.LACSPC ${bname}.LCCSPC 
done
rm -r $tmpcal

# getting recent cal.sol. amplitudes from DB, fitting them with a low-order polynomial and updating fields x_amp_fit, y_amp_fit in DB :
# mkdir -p fit2db
# cd fit2db/
# export PATH=~/aavs-calibration/station/:$PATH
# echo "~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1"
# ~/aavs-calibration/station/fit_all_ant_amplitudes.sh 1 1 1 - ${station_id} _amp > fit.out 2>&1

