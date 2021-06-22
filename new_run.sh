#!/usr/bin/env bash

# Run Agents
host="localhost"
port=8080

while read -r line
do
  # Creates hostname from iteration (u001-u201) and create the url to build the path
#  hostname="u${i}"
#  url="http://${host}:${port}/bqoepath/admweights-${hostname}-all"


  # Calls the URL by GET using curl to create the path
#  output=$(curl -q -s $url)

  # Get the destination info from curl's output
#  destination=$(echo "$output" | jq -r ".dst")
#  destination_ip=$(echo "$output" | jq -r ".dest_ip")

  hostname=$(echo "$line" | cut -d ';' -f 1) # First csv column
  manager=$(echo "$line" | cut -d ';' -f 2) # Second one
  metric=$(echo "$line" | cut -d ';' -f 3) # Third one
  polling_time=$(echo "$line" | cut -d ';' -f 4) # ...

  $m "$hostname" ./new_run.py "$hostname" "$manager" "$metric" "$polling_time" &
done < measuring_profile.csv
