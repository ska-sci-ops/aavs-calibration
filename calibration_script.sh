#!/usr/bin/env bash

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

do_mfcal_object="" # use mfcal with proper solar flux scale (as in Randall's script to get SEFD and other proper flux scale)

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
}

#echo "Command line: $@"

# parse command-line options
while getopts ":D:T:N:ksS:R:m:" opt; do
  echo "Parsing option ${opt} , argument = ${OPTARG}"
  case ${opt} in
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
      do_mfcal_object=${OPTARG}
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

echo "######################################################################################################"
echo "PARAMETERS :"
echo "######################################################################################################"
echo "channel           = $channel"
echo "reference_antenna = $reference_antenna"
echo "station_name      = $station_name"
if [[ -n "do_mfcal_object" ]]; then
   echo "do_mfcal_object   = $do_mfcal_object"
fi
echo "######################################################################################################"


# MS : 20191204 - I changed symbolic links to copies to keep track of what we used at the time of calibration
#      with symbolic link if the target changes, we don't know what was used at the time
# Link some configuration files
echo "Creating links to config files for a default station (station name = $station_name)"
if [[ $station_name == "eda2" || $station_name == "EDA2" ]]; then
   echo "Creating links to config files for station $station_name"
         
   cp ~/aavs-calibration/instr_config_eda2.txt instr_config.txt
   cp ~/aavs-calibration/antenna_locations_eda2.txt antenna_locations.txt
   cp ~/aavs-calibration/header_eda2_cal.txt header.txt
else
   if [[ $station_name == "aavs2" || $station_name == "AAVS2" ]]; then
      echo "Creating links to config files for station AAVS2"
      
      cp ~/aavs-calibration/config/aavs2/instr_config_aavs2_20191129.txt instr_config.txt
      cp ~/aavs-calibration/config/aavs2/antenna_locations_20191202.txt antenna_locations.txt
      cp ~/aavs-calibration/header_cal.txt header.txt 
   else
      echo "Creating links to config files for default station (AAVS1)"
      
      cp ~/aavs-calibration/instr_config.txt .
      cp ~/aavs-calibration/antenna_locations.txt .
      cp ~/aavs-calibration/header_cal.txt header.txt .
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
      Lfile2uvfits.sh "$hdffile" $int_time $radec
   done
else
   echo "WARNING : convert_hdf5_files=$convert_hdf5_files -> not executing conversion from hdf5 files to uvfits"
fi

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
    echo "Processing $uvfitsfile to ${src}.uv"
    
    mfcal_ok=0
    if [[ -n "$do_mfcal_object" ]]; then
       if [[ $do_mfcal_object == "sun" ]]; then
          mfcal_ok=1
          
          # Quiet sun (http://extras.springer.com/2009/978-3-540-88054-7/06_vi4b_4116.pdf
          # 4.1.1.6 Quiet and slowly varying radio emissions of the sun
          # Ref. p. 88] 4.1.1.6 Quiet and slowly varying radio emissions of the sun 81 Table 1. Flux density, F, and brightness temperature, T rad, of the quiet sun. F = radio ﬂux density of the quiet sun during sunspot minimum in units of 10 −22 Wm 2Hz −1=1019 erg cm Hz s−1 = solar ﬂux unit (sfu) T rad = brightness temperature of an optical solar disk with a diameter of 32
          # extras.springer.com )
          # note change in spectral index of sun around 150 MHz, so better to use different
          # power law at low vs high freqs
          if [[ $channel -gt 192 ]]; then
             echo "Channel = $channel > 192 -> using the high-frequency power law:"
             echo "mfcal vis=${src}.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)'"
             mfcal vis=${src}.uv flux=51000,0.15,1.6 select='uvrange(0.005,1)' # f > 150 MHz
          else
             echo "Channel = $channel <= 192 -> using the high-frequency power law:"             
             echo "mfcal vis=${src}.uv flux=51000,0.15,1.9 select='uvrange(0.005,1)'"
             mfcal vis=${src}.uv flux=51000,0.15,1.9 select='uvrange(0.005,1)' # f < 150 MHz
          fi
       else
          echo "WARNING : object $mfcal_ok of unknown flux specified -> will use standard selfcal"
       fi
    else    
    
    if [[ $mfcal_ok -le 0 ]]; then
       echo "WARNING : using standard selfcal procedure flux scale (also for Sun) is not optimal (set to 100000)"
       selfcal vis=${src}_XX.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=${reference_antenna} flux=100000
       selfcal vis=${src}_YY.uv select='uvrange(0.005,10)' options=amplitude,noscale refant=${reference_antenna} flux=100000
    fi
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
