#!/usr/bin/python3

import csv
import os
import shutil
import time
import uuid
import xml.etree.ElementTree as et
from datetime import datetime
from argparse import ArgumentParser
import subprocess
import signal

m="/home/mininet/mininet/util/m"

# def read_results_xml(filename):
#     root = et.parse(filename).getroot()
#     upload_min = root.find("./ativas/upmin").text
#     upload_max = root.find("./ativas/upmax").text
#     upload_avg = root.find("./ativas/upavg").text
#     download_min = root.find("./ativas/downmin").text
#     download_max = root.find("./ativas/downmax").text
#     download_avg = root.find("./ativas/downavg").text
#     status = root.find("./ativas/status").text
#     return [upload_min, upload_max, upload_avg, download_min, download_max, download_avg, status]

def rename_switch(switchname):
    RAN_LOWER_BOUND = 1
    RAN_UPPER_BOUND = 20

    METRO_LOWER_BOUND = 21
    METRO_UPPER_BOUND = 25

    ACCESS_LOWER_BOUND = 26
    ACCESS_UPPER_BOUND = 29

    CORE_LOWER_BOUND = 30
    CORE_UPPER_BOUND = 33

    INTERNET_LOWER_BOUND = 34
    INTERNET_UPPER_BOUND = 34

    sp = int(switchname[1:])
    if RAN_LOWER_BOUND <= sp <= RAN_UPPER_BOUND:
        newsp = sp - RAN_LOWER_BOUND
        newsp = newsp + 1
        return f"r{newsp}"
    elif METRO_LOWER_BOUND <= sp <= METRO_UPPER_BOUND:
        newsp = sp - METRO_LOWER_BOUND
        newsp = newsp + 1
        return f"m{newsp}"
    elif ACCESS_LOWER_BOUND <= sp <= ACCESS_UPPER_BOUND:
        newsp = sp - ACCESS_LOWER_BOUND
        newsp = newsp + 1
        return f"a{newsp}"
    elif CORE_LOWER_BOUND <= sp <= CORE_UPPER_BOUND:
        newsp = sp - CORE_LOWER_BOUND
        newsp = newsp + 1
        return f"c{newsp}"
    elif INTERNET_LOWER_BOUND <= sp <= INTERNET_UPPER_BOUND:
        newsp = sp - INTERNET_LOWER_BOUND
        newsp = newsp + 1
        return f"i{newsp}"
    else:
        return f"{switchname}"


def calculate_ip(p):
    if p == "src1":
        return "10.0.0.249"
    elif p == "src2":
        return "10.0.0.250"
    elif p == "cdn1":
        return "10.0.0.251"
    elif p == "cdn2":
        return "10.0.0.252"
    elif p == "cdn3":
        return "10.0.0.253"
    elif p == "ext1":
        return "10.0.0.254"
    else:
        pfirst = p[0]
        if pfirst == "s":
            prest = p[1:]
            ipfinal = 200 + int(prest)
            return f"10.0.0.{ipfinal}"
        elif pfirst == "u":
            ipfinal = p[1:]
            return f"10.0.0.{ipfinal}"


def create_schedule(sch_uuid, agent, manager_ip, metric):
    has_tp = metric == "throughput_tcp"
    has_rtt = metric == "rtt"
    has_loss = metric == "loss"

    tp = "<plugins>throughput_tcp</plugins>\n" if has_tp else "" 
    rtt = "<plugins>rtt</plugins>\n" if has_rtt else ""
    loss = "<plugins>loss</plugins>\n" if has_loss else ""

    schedule = f"""<metrics>
    <ativas>
        <agt-index>1090</agt-index>
        <manager-ip>{manager_ip}</manager-ip>
        <literal-addr>{agent}</literal-addr>
        <android>1</android>
        <location>
            <name>-</name>
            <city>-</city>
            <state>-</state>
        </location>
        {tp}{rtt}{loss}
        <timeout>12</timeout>
        <probe-size>14520</probe-size>
        <train-len>1440</train-len>
        <train-count>1</train-count>
        <gap-value>100000</gap-value>
        <protocol>1</protocol>
        <num-conexoes>3</num-conexoes>
        <time-mode>2</time-mode>
        <max-time>12</max-time>
        <port>12001</port>
        <output>OUTPUT-SNMP</output>
    </ativas>
</metrics>"""

    with open(f'/tmp/schedule-{sch_uuid}.xml', 'w+') as file:
        file.write(schedule)


def read_results_xml(filename):
    root = et.parse(filename).getroot()

    throughput_tcp_upload_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"throughput_tcp\"]/upavg")
    throughput_tcp_download_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"throughput_tcp\"]/downavg")

    rtt_upload_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"rtt\"]/upavg")
    rtt_download_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"rtt\"]/downavg")

    loss_upload_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"loss\"]/upavg")
    loss_download_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"loss\"]/downavg")

    return [throughput_tcp_upload_avg, throughput_tcp_download_avg, rtt_upload_avg, rtt_download_avg,
            loss_upload_avg, loss_download_avg]


def parse_xml_text_if_exists(root, xpath):
    element = root.find(xpath)
    if element != None:
        return element.text
    else:
        return ""

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
    parser.add_argument("agent", type=str, help="Agent hostname")
    parser.add_argument("manager", type=str, help="Manager hostname")
    parser.add_argument("throughput_tcp_period", type=float, help="Throughput TCP measurement repeating period (min)")
    parser.add_argument("rtt_period", type=float, help="Rtt measurement repeating period (min)")
    parser.add_argument("loss_period", type=float, help="Loss measurement repeating period (min)")
    args = parser.parse_args()

    # Read parameters from input
    tp_period = args.throughput_tcp_period * 60
    rtt_period = args.rtt_period * 60
    loss_period = args.loss_period * 60
    hostname = args.agent
    manager = args.manager
    #metric = args.metric

    #if metric != "throughput_tcp" and metric != "rtt" and metric != "loss":
    #    print("Undefined Metric. Exiting...")
    #    exit(1)

    # Time to run depends on it's running or fast first trigger mode
    # if args.fast:
    #     first_trigger_time = (3 + (random() % 29))
    # else:
    #     first_trigger_time = ((60 * (random() % 10)) + (30 + (random() % 29)))

    # print(f"Running in {first_trigger_time} s")
    # time.sleep(first_trigger_time)

    if not os.path.exists("results"):
        os.makedirs("results")
    if not os.path.exists("results/xml"):
        os.makedirs("results/xml")

    # Keep waiting the given period (polling) and calls metricagent
    while True:
        # Generate Schedule's UUID
        sch_uuid = str(uuid.uuid4())
        print(f"This measure is identified by uuid={sch_uuid}")

        print(f"Manager IP={calculate_ip(manager)}")
        create_schedule(sch_uuid, hostname, calculate_ip(manager), metric)

        renamed_manager = rename_switch(manager)
        # Starts metric manager first
        command = f"{m} {renamed_manager} /usr/netmetric/sbin/metricmanager -c"
        # Run Netmetric Manager using subprocess
        manager_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, preexec_fn=os.setsid)
        time.sleep(20)
        #print(command)

        # Creates the metric agent command
        command = f"{m} {hostname} /usr/netmetric/sbin/metricagent -c -f /tmp/schedule-{sch_uuid}.xml -w -l 1000 -u 100 -u {sch_uuid}"
        os.system(command)
        #print(command)

        # Kill Netmetric Manager process
        os.killpg(manager_process.pid, signal.SIGTERM)

        # Gather the data from metricagent xml output
        current_timestamp = str(datetime.now())
        data = [hostname, manager, current_timestamp, sch_uuid]
        data.extend(read_results_xml(f"agent-{sch_uuid}.xml"))

        write_data_csv("results/nm_last_results.csv", data)
        # Moves the XML file from results/xml folder
        shutil.move(f"agent-{sch_uuid}.xml", f"./results/xml/agent-{sch_uuid}.xml")

        time.sleep(period)
