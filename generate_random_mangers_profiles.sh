#!/usr/bin/bash

echo "agent;manager;first-trigger-time;polling-throughput-tcp;polling-rtt;polling-loss"
for i in {001..010}; do
	random_manager=$((1 + $RANDOM % 4))
	random_tp="$((2 + $RANDOM % 4)).$(printf "%02d" $(($RANDOM % 60)) )"
	random_rtt="$(($RANDOM % 3)).$(printf "%02d" $(($RANDOM % 60)) )"
	# While rtt < 0.30 comparison. Floating point comparison in bash is not really supported
	while [ $(echo "$random_rtt < 0.30" |bc -l) -eq 1 ]; do
		random_rtt="$(($RANDOM % 3)).$(printf "%02d" $(($RANDOM % 60)) )"
	done
	#random_loss="$(($RANDOM % 3)).$(($RANDOM % 60))"
	random_loss=$random_rtt

	echo "u$i;man$random_manager;1;$random_tp;$random_rtt;$random_loss"
done
