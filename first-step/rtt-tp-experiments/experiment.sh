#!/usr/bin/env bash

run_test_path="$HOME/INFOCOM2018/run_test.py"

log_info () { echo -e "\033[1;33m[INFO] $1\033[1;0m"; }

if sudo true
then
	log_info "Hey, I have superuser privilegies"
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
		log_info "Init Mininet Topology $i: $mininet_file"
		sudo python3.9 "$mininet_file" &
		pid_mininet=$!
		sleep 5
		log_info "Mininet initialized"
	
		# Start measurements
		log_info "Starting Measurements"
		"$run_test_path" u001 cdn1 0.3 0.3 0.3 -stt 0.1 -o "results_$i.csv" -sm --rounds 5
		sleep 2
		log_info "Measurements Finished"

		log_info "Cleaning Infra"
		log_info "Killing Mininet PID: $pid_mininet"
		sudo kill -9 "$pid_mininet"
		sudo kill -9 "$pid_mininet"
		sudo killall -9 metricmanager
		sudo killall -9 metricmanager
		sudo killall -9 metricagent
		sudo killall -9 metricagent
		sudo mn -c
	done

	end_time=$(date +%s)
	elapsed=$(( end_time - start_time ))
	log_info "Elapsed $(date -ud @$elapsed +'%H hr %M min %S sec')"
else 
	log_info "I really need sudo :/"
fi
