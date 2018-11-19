#!/usr/bin/env bash

function print_usage {
  echo "Usage:"
  echo "$0 [options]"
  echo -e "\t-D data_dir\tdirectory to work in. Default: ${default_data_dir}"
}

#echo "Command line: $@"

# parse command-line options
while getopts ":D:T:N:k" opt; do
  case ${opt} in
    D)
      data_dir=${OPTARG}
      echo "Cleaning up temp files in ${data_dir}"
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
rm -fr *.uvfits *ts_unix.txt *.uv
rm -fr *.LACSPC *.LCCSPC 
