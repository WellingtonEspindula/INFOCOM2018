#!/bin/bash

schedule_uuid=$(uuid)
period=$1
hostname=$2
manager=$3

script="/usr/netmetric/sbin/metricagent -c -f schedules/agenda-$3.xml -w -l 1000 -u 100 -u $(uuid)"
#time_to_run=$(( (60*($RANDOM % 10)) + (30 + ($RANDOM % 29)) ))
time_to_run=$(( (30 + ($RANDOM % 29)) ))
echo ${time_to_run}s
sleep ${time_to_run}s

while true; do
	$script
		
	sleep $period
done

