#!/usr/bin/env python3

import csv
import numpy as np
from prettytable import PrettyTable
import re
import sys

if sys.argv[1] == None or not sys.argv[1]:
    exit(1)

with open(sys.argv[1], 'r') as file:
    r = csv.reader(file, delimiter=';')
    metrics = ['throughput_tcp', 'rtt', 'loss'];
    table = PrettyTable(['topology', 'metric', 'mean', 'min', 'max', 'stdev', 'theorical'])
    for i in range(1, 33):
        for metric in metrics:
            rtt_up = np.array([float(row[2]) for line, row in enumerate(r) if line != 0 and row[0] == f'{i:02}' and row[1] == metric])
            mean, _min, _max, stdev = np.average(rtt_up), np.min(rtt_up), np.max(rtt_up), np.std(rtt_up)

            theorical_results = [re.match(r"netconf7/Gent_topo_{:02}.py:  link100Mbps_1 \= dict\(bw\=(\d+), delay\='(\d+)ms'\)".format(i), line) for line in open('../theorical.txt', 'r') if line and line != None]
            theorical_results = [r for r in theorical_results if r != None][0]
            #print(theorical_results.group(1), theorical_results.group(2))

            if (metric == 'throughput_tcp'):
                table.add_row([i, metric, f'{mean*10**(-6):.3} Mbps', f'{_min*10**(-6):.3} Mbps', f'{_max*10**(-6):.3} Mbps', f'{stdev*10**(-6):.3} Mbps', f'{theorical_results.group(1)} Mbps'])
            elif metric == 'rtt':
                table.add_row([i, metric, f'{mean*10**(3):.3} ms', f'{_min*10**(3):.3} ms', f'{_max*10**(3):.3} ms', f'{stdev*10**(3):.3} ms', f'{int(theorical_results.group(2))*2} ms'])

            else:
                table.add_row([i, metric, mean, _min, _max, stdev, 0])

            file.seek(0)
    print(table)
