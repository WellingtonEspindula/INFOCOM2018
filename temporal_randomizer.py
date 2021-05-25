#!/usr/bin/python3

import sys
import uuid
from random import seed, random
import os
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import csv
import shutil


period= int(sys.argv[1]) * 60
hostname=sys.argv[2]
manager=sys.argv[3]

def random():
    return int.from_bytes(os.urandom(16), byteorder="big")

def read_xml(filename):
    root = ET.parse(filename).getroot()
    upmin = root.find("./ativas/upmin").text
    upmax = root.find("./ativas/upmax").text
    upavg = root.find("./ativas/upavg").text
    downmin = root.find("./ativas/downmin").text
    downmax = root.find("./ativas/downmax").text
    downavg = root.find("./ativas/downavg").text
    status = root.find("./ativas/status").text
    return [upmin, upmax, upavg, downmin, downmax, downavg, status]

def write_data_csv(filename, data):
    with open('results/results.csv', mode='a+') as file:
        file_writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        file_writer.writerow(data)
        print("File saved")


#time_to_run=( (60*(random() % 10)) + (30 + (random() % 29)) )
time_to_run=(3 + (random() % 29))
print(f"{time_to_run}s")
time.sleep(time_to_run)

while True:
    #print(script)
    #print(period)
    sch_uuid=str(uuid.uuid4())
    script=f"/usr/netmetric/sbin/metricagent -c -f schedules/agenda-{manager}.xml -w -l 1000 -u 100 -u {sch_uuid}"
    os.system(script)

    current_timestamp = str(datetime.now())
    data = [hostname, manager, current_timestamp, sch_uuid] 
    data.extend(read_xml(f"agent-{sch_uuid}.xml"))
    print(data)
    write_data_csv("results/load.csv", data)
    shutil.move(f"agent-{sch_uuid}.xml", f"./results/xml/agent-{sch_uuid}.xml")

    time.sleep(period)



