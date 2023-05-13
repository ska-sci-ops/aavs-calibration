#!/usr/bin/env bash

# keeping .uv files to use later as calibrators 
remove_uv_files=1

function print_usage {
  echo "Usage:"
  echo "$0 [options]"
  echo -e "\t-D data_dir\tdirectory to work in. Default: ${default_data_dir}"
  echo -e "\t-u DO_CLEAN_uv_files. Default: ${remove_uv_files}"
}

#echo "Command line: $@"

# parse command-line options
while getopts ":D:T:N:ku:" opt; do
  case ${opt} in
    D)
      data_dir=${OPTARG}
      echo "Cleaning up temp files in ${data_dir}"
      ;;
    u)
      remove_uv_files=${OPTARG}
      echo "remove_uv_files = $remove_uv_files"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      print_usage
      exit -1
      ;;
  esac
done
shift $((OPTIND-1))

# Gto to required directory
cd "${data_dir}"
if [ $? -ne 0 ] ; then
  exit 1
fi

# Remove all generated files
echo "rm -fr *ts_unix.txt"
rm -fr *ts_unix.txt 

echo "rm -fr *.LACSPC *.LCCSPC"
rm -fr *.LACSPC *.LCCSPC 

if [[ $remove_uv_files -gt 0 ]]; then 
   echo "rm -fr *.uv *.uvfits"
   rm -fr *.uv *.uvfits
else
   echo "WARNING : do not removing .uv files (may take some space...)"
fi
