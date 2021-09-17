#!/usr/bin/env bash

run_test_path='$HOME/INFOCOM2018/run_test.py'
INFO="echo -e \033[1;33m[INFO]$1\033[1;0m"

sudo $INFO "Hey, I have superuser privilegies"
start_time=$(date +%s)

# First killall
sudo mn -c
sudo killall -9 metricmanager
sudo killall -9 metricmanager
sudo killall -9 metricagent
sudo killall -9 metricagent

for i in {01..32}; do
	mininet_file="netconf7/Gent_topo_$i.py"

	# Init mininet
	$INFO "Init Mininet Topology $mininet"
	sudo python3.9 "$mininet_file" &
	sleep 5
	$INFO "Mininet initialized"
	
	# Start measurements
	$INFO "Starting Measurements"
	"$run_test_path" u001 cdn1 0.3 0.3 0.3 -stt 0.1 -o "results_$i.csv" -sm --rounds 5
	sleep 2
	$INFO "Measurements Finished"

	$INFO "Cleaning Infra"
	sudo killall -9 metricmanager
	sudo killall -9 metricmanager
	sudo killall -9 metricagent
	sudo killall -9 metricagent
	sudo mn -c
done

end_time=$(date +%s)
elapsed=$(( end_time - start_time ))
$INFO "Elapsed $(date -ud @$elapsed +'%H hr %M min %S sec')"
