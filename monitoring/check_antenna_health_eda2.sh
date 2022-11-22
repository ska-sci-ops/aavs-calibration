#!/bin/bash

datadir=/storage/monitoring/integrated_data/eda2/
if [[ -n "$1" && "$1" != "-" ]]; then
   datadir="$1"
fi

echo "check_antenna_health.sh - 100 1 - eda2 ${datadir} 1"
check_antenna_health.sh - 100 1 - eda2 ${datadir} 1 
