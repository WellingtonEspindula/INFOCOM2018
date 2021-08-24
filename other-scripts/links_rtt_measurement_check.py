#!/usr/bin/env python3.9
import csv
import math

ABS_TOLERANCE_LINK_RTT_MS= 0.15

theorical_rtt_results: dict[dict[float]] = {}
measured_rtt_results: dict[dict[float]] = {}

with open('../rtt_theorical_links.csv', mode='r') as thr_rtt:
    csv_reader = csv.reader(thr_rtt, delimiter=';')
    for row in csv_reader:
        host1 = row[0]
        host2 = row[1]
        rtt = float(row[2]) * 2

        if theorical_rtt_results.get(host2) is None or \
        theorical_rtt_results.get(host2).get(host1) is None:
            theorical_rtt_results.update({host1: {host2: rtt}})

with open('../results/link-results.csv', mode='r') as res_file:
    csv_reader = csv.reader(res_file, delimiter=';')
    for row in csv_reader:
        host1 = row[0]
        host2 = row[1]
        rtt = float(row[5])
        #print(host1, host2, rtt)

        measured_rtt_results.update({host1: {host2: rtt}})

# print(theorical_rtt_results)
# print(measured_rtt_results)

for host1 in theorical_rtt_results:
    for host2 in theorical_rtt_results.get(host1):
        theorical_rtt = theorical_rtt_results.get(host1).get(host2)
        measured_rtt = measured_rtt_results.get(host1).get(host2)
        measured_rtt = measured_rtt_results.get(host1).get(host2) if \
            measured_rtt_results.get(host1) is not None and \
            measured_rtt_results.get(host1).get(host2) is not None \
            else (measured_rtt_results.get(host2).get(host1) if \
            measured_rtt_results.get(host2) is not None and \
            measured_rtt_results.get(host2).get(host1) is not None else None)
        assert(measured_rtt is not None)
        measured_rtt_ms = measured_rtt * 1000
        are_values_close = math.isclose(theorical_rtt, measured_rtt_ms, abs_tol=ABS_TOLERANCE_LINK_RTT_MS)
        assert are_values_close
        print(f'Pair {host1}-{host2} measured {measured_rtt_ms:.3f} for theorical {theorical_rtt} : {"Accepted" if are_values_close else "Denied"}')
