#!/usr/bin/env bash

m="/home/mininet/mininet/util/m"

# Run Agents
host="localhost"
port=8080

sudo echo ""

# Run Managers
taskset -c 1 $m man1 /usr/netmetric/sbin/metricmanager &
taskset -c 2 $m man2 /usr/netmetric/sbin/metricmanager &
taskset -c 3 $m man3 /usr/netmetric/sbin/metricmanager &
taskset -c 4 $m man4 /usr/netmetric/sbin/metricmanager &

echo "Waiting to managers starts... 20s"
sleep 20s
echo "Managers are ready to execute!"

process_ids=()

trap ctrl_c INT

function cntrl_c() {
  echo "SIG INT Detected"
  echo "Killing processes..."
  for pid in "${process_ids[@]}"; do
    echo "Killing process PID=$pid"
    sudo kill -9 "$pid"
  done
}

rm /tmp/pids_running.txt

while read -r line; do
  if [ -n "$line" ]; then
    hostname=$(echo "$line" | cut -d ';' -f 1)     # First csv column
    manager=$(echo "$line" | cut -d ';' -f 2)      # Second one
    #metric=$(echo "$line" | cut -d ';' -f 3) # Third one
    #polling_time=$(echo "$line" | cut -d ';' -f 4) # ...
    ftt=$(echo "$line" | cut -d ';' -f 3)
    polling_tp=$(echo "$line" | cut -d ';' -f 4)   # ...
    polling_rtt=$(echo "$line" | cut -d ';' -f 5)  # ...
    polling_loss=$(echo "$line" | cut -d ';' -f 6) # ...

    curl -X GET "http://$host:$port/bqoepath/pathtomanager-$hostname-$manager" -s

    python3.9 run_test.py -m "$hostname" "$manager" "$polling_tp" "$polling_rtt" "$polling_loss" -ftt "$ftt" &
    pid=$!
    echo $pid >>/tmp/pids_running.txt
    process_ids+=(pid)
  fi
done < <(tail -n +2 measuring_profile.csv)
