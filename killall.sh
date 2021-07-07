#!/usr/bin/env bash


# Kill all run_test.py processes
while read -r pid
do
	sudo kill -9 "$pid"
done < /tmp/pids_running.txt

#sudo pkill -9 -e -F pids_running.txt

# Kill remaining netmetric managers and agents
sudo killall metricmanager
sudo killall metricagent
