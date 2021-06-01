#!/usr/bin/python3

import csv
import os
import shutil
import time
import uuid
import xml.etree.ElementTree as et
from datetime import datetime
from argparse import ArgumentParser


# def random():
#     return int.from_bytes(os.urandom(16), byteorder="big")


# def open_config_csv(filename):
#     with open(filename, mode='r') as file:
#         file_reader = csv.reader(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # file_reader.(data)
        # print("File saved")

def read_xml(filename):
    root = et.parse(filename).getroot()
    upload_min = root.find("./ativas/upmin").text
    upload_max = root.find("./ativas/upmax").text
    upload_avg = root.find("./ativas/upavg").text
    download_min = root.find("./ativas/downmin").text
    download_max = root.find("./ativas/downmax").text
    download_avg = root.find("./ativas/downavg").text
    status = root.find("./ativas/status").text
    return [upload_min, upload_max, upload_avg, download_min, download_max, download_avg, status]


def write_data_csv(filename, data):
    with open(filename, mode='a+') as file:
        file_writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        file_writer.writerow(data)
        # print("File saved")


if __name__ == '__main__':
    # Informing script arguments
    parser = ArgumentParser(description='Runs the metricagent using a random trigger time')
    parser.add_argument("-f", "--fast", help="fast initial trigger", action="store_true")
    parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
    parser.add_argument("period", type=int, help="Trigger period in minutes")
    parser.add_argument("hostname", type=str, help="Agent hostname")
    parser.add_argument("manager", type=str, help="Manager hostname")
    args = parser.parse_args()

    # Read parameters from input
    period = args.period * 60
    hostname = args.hostname
    manager = args.manager

    # Time to run depends on it's running or fast first trigger mode
    # if args.fast:
    #     first_trigger_time = (3 + (random() % 29))
    # else:
    #     first_trigger_time = ((60 * (random() % 10)) + (30 + (random() % 29)))

    print(f"Running in {first_trigger_time} s")
    time.sleep(first_trigger_time)

    # Keep waiting the given period and calls metricagent
    while True:
        # Regenerate UUID from schedule
        sch_uuid = str(uuid.uuid4())
        # Creates the metric agent command
        command = f"/usr/netmetric/sbin/metricagent -c -f schedules/agenda-{manager}.xml -w -l 1000 -u 100 -u {sch_uuid}"
        os.system(command)

        # Gather the data from metricagent xml output
        current_timestamp = str(datetime.now())
        data = [hostname, manager, current_timestamp, sch_uuid]
        data.extend(read_xml(f"agent-{sch_uuid}.xml"))
        write_data_csv("results/load.csv", data)
        # Moves the XML file from results/xml folder
        shutil.move(f"agent-{sch_uuid}.xml", f"./results/xml/agent-{sch_uuid}.xml")

        time.sleep(period)
