#!/bin/bash

station=eda2
if [[ -n "$1" && "$1" != "-" ]]; then
   station=$1
fi

awk -v prev_ant=-1 '{if($1!="#" && $5==1 && $2!=prev_ant){if(prev_ant>=0){printf(",");}printf("%d",$2);prev_ant=$2;}}END{printf("\n");}' config/${station}/instr_config.txt
