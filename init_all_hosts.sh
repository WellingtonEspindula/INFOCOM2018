#!/usr/bin/env bash

host="192.168.15.148"
port=8080

for i in {001..201}; do
  # Creates hostname from iteration (u001-u201) and create the url to build the path
  hostname="u${i}"
  url="http://${host}:${port}/bqoepath/admweights-${hostname}-all"

  # Calls the URL by GET using curl to create the path
  output=$(curl -q -s $url)

  # Get the destination info from curl's output
  destination=$(echo "$output" | jq -r ".dst")
#  destination_ip=$(echo "$output" | jq -r ".dest_ip")

  $m "$hostname" ./temporal_randomizer.py -f 5 "$hostname" "$destination" &
done
