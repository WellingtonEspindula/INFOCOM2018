#!/usr/bin/env bash

touch results.csv
echo "topology;metric;up;down" > results.csv

for i in {01..32}
do
	cat "results_$i.csv" | awk "BEGIN{ORS=\"\n\"; FS=\";\"}{print \"$i;\"\$5\";\"\$6\";\"\$7}" >> results.csv
done

sed  -i -e 's/\r//g' results.csv
