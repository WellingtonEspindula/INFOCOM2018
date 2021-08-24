#!/usr/bin/env bash

export m=/home/mininet/mininet/util/m

echo "[INFO] 0. Cleaning last link results"
sudo rm link_last_results.csv
echo "[INFO] 1. Calling measurement algorithm"
./run_unitary_test.py -f links-measurement-profile.csv -o results/link-results.csv
echo "[INFO] 1.1 Checking if rtt measured are validy"
cd other_scripts/ && ./links_rtt_measurement_check.py && cd ..
echo "[INFO] 2. Starting Workload"
echo "[INFO] 2.1 Starting CDNs servers"
sudo $m cdn1 ./start_apache.sh cdn1
sudo $m cdn2 ./start_apache.sh cdn2
sudo $m cdn3 ./start_apache.sh cdn3
sudo $m ext1 ./start_apache.sh ext1
echo "[INFO] Starting player wrapper"
if [ ! -e '/tmp/video-log.txt']
then
	touch /tmp/video-log.txt
fi
./video_launcher.sh /tmp/video-log.txt
