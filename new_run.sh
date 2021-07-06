#!/usr/bin/env bash

# Run Agents
host="localhost"
port=8080

sudo echo ""

# Run Managers
sudo $m man1 /usr/netmetric/sbin/metricmanager &
sudo $m man2 /usr/netmetric/sbin/metricmanager &
sudo $m man3 /usr/netmetric/sbin/metricmanager &
sudo $m man4 /usr/netmetric/sbin/metricmanager &

while read -r line
do
  hostname=$(echo "$line" | cut -d ';' -f 1) # First csv column
  manager=$(echo "$line" | cut -d ';' -f 2) # Second one
  #metric=$(echo "$line" | cut -d ';' -f 3) # Third one
  #polling_time=$(echo "$line" | cut -d ';' -f 4) # ...
  polling_tp=$(echo "$line" | cut -d ';' -f 4) # ...
  polling_rtt=$(echo "$line" | cut -d ';' -f 5) # ...
  polling_loss=$(echo "$line" | cut -d ';' -f 6) # ...

  curl -X GET "http://$host:$port/bqoepath/pathtomanager-$hostname-$manager" -s

  pid=$(sudo ./run_test.py -m "$hostname" "$manager" "$polling_tp" "$polling_rtt" "$polling_loss" & echo $!)
  echo "Monsieur, Mon PID est $pid"
  #echo "sudo ./run_test.py -m "$hostname" "$manager" "$polling_tp" "$polling_rtt" "$polling_loss" &"
done < <(tail -n +2 measuring_profile.csv)
