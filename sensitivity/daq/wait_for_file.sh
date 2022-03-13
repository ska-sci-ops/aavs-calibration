#!/bin/bash

print_usage()
{
	echo "usage:"
	echo "wait_for_file.sh FILE_NAME[default=daqExitOK.txt] MAX_TIME_IN_SECONDS[default=86400]"	
}

FILE=daqExitOK.txt
if [[ -n "$1" && "$1" != "-" ]]; then
	FILE="$1"
fi

MAX_WAIT_TIME=3600
if [[ -n "$2" && "$2" != "-" ]]; then
	MAX_WAIT_TIME="$2"
fi

to_exist=1
if [[ -n "$3" && "$3" != "-" ]]; then
	to_exist=$3
fi

wait_time=0

while [ $wait_time -lt $MAX_WAIT_TIME ];
do
        # this FILE / file_path is because I started 
#        FILE=`ls -d ${file_path} | tail -1`        
        
	if [[ -s $FILE || -d $FILE ]]; then
		if [ $to_exist -gt 0 ]; then
			echo "File $FILE found - exiting waiting loop"
			exit;
		fi
	else
		if [[ $to_exist -le 0 ]]; then
			echo "File $FILE not found - exiting waiting loop"
			exit;
		fi
	fi

	if [[ $to_exist -gt 0 ]]; then
		echo "waiting for file $FILE, sleeping 60 sec ..."
	else
		echo "waiting for file $FILE to be removed, sleeping 60 sec ..."
	fi

	wait_time=$(($wait_time+60));
	sleep 60
done

echo "Timeout of $MAX_WAIT_TIME exceeded, exited waiting loop !"

