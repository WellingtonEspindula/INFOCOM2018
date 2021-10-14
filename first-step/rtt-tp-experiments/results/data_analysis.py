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
    table = PrettyTable(['topology', 'metric', 'mean', 'min', 'max', 'stdev', 'theorical', 'difference', 'error_rate (%)'])
    for i in range(1, 33):
        for metric in metrics:
            rtt_up = np.array([float(row[2]) for line, row in enumerate(r) if line != 0 and row[0] == f'{i:02}' and row[1] == metric])
            mean, _min, _max, stdev = np.average(rtt_up), np.min(rtt_up), np.max(rtt_up), np.std(rtt_up)

            theorical_results = [re.match(r"netconf7/Gent_topo_{:02}.py:  link100Mbps_1 \= dict\(bw\=(\d+), delay\='(\d+)ms'\)".format(i), line) for line in open('../theorical.txt', 'r') if line and line != None]
            theorical_results = [r for r in theorical_results if r != None][0]
            #print(theorical_results.group(1), theorical_results.group(2))

            if (metric == 'throughput_tcp'):
                measured_tp_mean_Mbps = mean*10**(-6)
                theorical_tp_Mbps = float(theorical_results.group(1))
                diff_Mbps = abs(measured_tp_mean_Mbps - theorical_tp_Mbps)
                table.add_row([i, metric, f'{measured_tp_mean_Mbps:.3f} Mbps', f'{_min*10**(-6):.3f} Mbps', 
                               f'{_max*10**(-6):.3f} Mbps', f'{stdev*10**(-6):.3f} Mbps', f'{theorical_tp_Mbps} Mbps', 
                               f'{diff_Mbps:.3f} Mbps', f'{100 * diff_Mbps/theorical_tp_Mbps:.2f}'])
            elif metric == 'rtt':
                measured_rtt_mean_ms = mean*10**(3)
                theorical_rtt_ms = int(theorical_results.group(2))*2
                diff_ms = abs(measured_rtt_mean_ms - theorical_rtt_ms)
                table.add_row([i, metric, f'{measured_rtt_mean_ms:.3f} ms', f'{_min*10**(3):.3f} ms', 
                               f'{_max*10**(3):.3f} ms', f'{stdev*10**(3):.3f} ms', f'{theorical_rtt_ms} ms', 
                               f'{diff_ms:.3f} ms', f'{100 * diff_ms/theorical_rtt_ms:.2f}'])

            else:
                table.add_row([i, metric, f'{mean} %', f'{_min} %', f'{_max} %', f'{stdev} %', f'{0} %', 
                               f'{abs(mean-0):.3} %', f'{0}'])

            file.seek(0)
    print(table)
