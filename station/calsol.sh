#!/bin/bash

file=chan_204_selfcal_pha_XX.txt
if [[ -n "$1" && "$1" != "-" ]]; then
   file=$1
fi

awk '{for(i=3;i<=NF;i++){printf("%.2f,",$i);}}' ${file}
