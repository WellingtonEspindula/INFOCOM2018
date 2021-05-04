#!/usr/bin/python3

import os

for i in range(1, 201):
    hostname = f"u{i:03}"
    url = f"http://192.168.15.148:8080/bqoepath/admweights-{hostname}-all"
    os.system(f'curl -q -s {url}')
