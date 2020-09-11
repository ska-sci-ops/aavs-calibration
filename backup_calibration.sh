#!/bin/bash

backup_dir=NoSunBeamCorr
if [[ -n "$1" && "$1" != "-" ]]; then
   backup_dir=$1
fi

mkdir -p ${backup_dir}

echo "mv *.txt ${backup_dir}/"
mv *.txt ${backup_dir}/

echo "mv *.png ${backup_dir}/"
mv *.png ${backup_dir}/

echo "mv *conf ${backup_dir}/"
mv *conf ${backup_dir}/

echo "mv *.hdr ${backup_dir}/"
mv *.hdr ${backup_dir}/
