#!/usr/bin/python3

import csv
import os
import sys
import shutil
import signal
import subprocess
import time
import uuid
import threading
import xml.etree.ElementTree as et
from argparse import ArgumentParser
from datetime import datetime
# from random import random as random
import random as rand

m = "/home/mininet/mininet/util/m"
manager_procs = []


def random():
    return int.from_bytes(os.urandom(16), byteorder="big")


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

def rename_switch(switchname: str):
    ran_lower_bound = 1
    ran_upper_bound = 20

    metro_lower_bound = 21
    metro_upper_bound = 25

    access_lower_bound = 26
    access_upper_bound = 29

    core_lower_bound = 30
    core_upper_bound = 33

    internet_lower_bound = 34
    internet_upper_bound = 34

    sp = int(switchname[1:])
    if ran_lower_bound <= sp <= ran_upper_bound:
        new_sp = sp - ran_lower_bound
        new_sp = new_sp + 1
        return f"r{new_sp}"
    elif metro_lower_bound <= sp <= metro_upper_bound:
        new_sp = sp - metro_lower_bound
        new_sp = new_sp + 1
        return f"m{new_sp}"
    elif access_lower_bound <= sp <= access_upper_bound:
        new_sp = sp - access_lower_bound
        new_sp = new_sp + 1
        return f"a{new_sp}"
    elif core_lower_bound <= sp <= core_upper_bound:
        new_sp = sp - core_lower_bound
        new_sp = new_sp + 1
        return f"c{new_sp}"
    elif internet_lower_bound <= sp <= internet_upper_bound:
        new_sp = sp - internet_lower_bound
        new_sp = new_sp + 1
        return f"i{new_sp}"
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
    elif p == "man1":
        return "10.0.0.241"
    elif p == "man2":
        return "10.0.0.242"
    elif p == "man3":
        return "10.0.0.243"
    elif p == "man4":
        return "10.0.0.244"
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


def read_results_xml(metric: str, filename: str):
    root = et.parse(filename).getroot()

    if metric == 'throughput_tcp':
        throughput_tcp_upload_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"throughput_tcp\"]/upavg")
        throughput_tcp_download_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"throughput_tcp\"]/downavg")

        return [metric, throughput_tcp_upload_avg, throughput_tcp_download_avg]

    elif metric == 'rtt':
        rtt_upload_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"rtt\"]/upavg")
        rtt_download_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"rtt\"]/downavg")

        return [metric, rtt_upload_avg, rtt_download_avg]

    elif metric == 'loss':
        loss_upload_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"loss\"]/upavg")
        loss_download_avg = parse_xml_text_if_exists(root, "./ativas[@metrica=\"loss\"]/downavg")

        return [metric, loss_upload_avg, loss_download_avg]
    # return [throughput_tcp_upload_avg, throughput_tcp_download_avg, rtt_upload_avg, rtt_download_avg,
    #         loss_upload_avg, loss_download_avg]


def parse_xml_text_if_exists(root, xpath):
    element = root.find(xpath)
    if element is not None:
        return element.text
    else:
        return ""


def write_data_csv(filename, data):
    with open(filename, mode='a+') as file:
        file_writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        file_writer.writerow(data)
        # print("File saved")


def measurement_service(metric, period):
    # First of all, must wait the first trigger time
    first_trigger_time = (3 + (random() % 29))
    print(f'Waiting for {first_trigger_time} s for stating this measure')
    time.sleep(first_trigger_time)

    # Keep waiting the given period (polling) and calls metricagent
    while True:
        # Generate Schedule's UUID
        sch_uuid = str(uuid.uuid4())
        print(f"This measure is identified by uuid={sch_uuid}")
        print(f"Manager IP={calculate_ip(manager_hostname)}")

        # Generate Schedule XML for this measure
        create_schedule(sch_uuid, agent_hostname, calculate_ip(manager_hostname), metric)

        # Creates the metric agent command
        command = f"{m} {agent_hostname} /usr/netmetric/sbin/metricagent -c -f /tmp/schedule-{sch_uuid}.xml -w -l 1000 -u " \
                  f"100 -u {sch_uuid} "
        os.system(command)

        # Gather the data from metricagent xml output
        current_timestamp = str(datetime.now())
        data = [agent_hostname, manager_hostname, current_timestamp, sch_uuid]
        data.extend(read_results_xml(metric, f"agent-{sch_uuid}.xml"))

        write_data_csv("results/nm_last_results.csv", data)
        # Moves the XML file from results/xml folder
        shutil.move(f"agent-{sch_uuid}.xml", f"./results/xml/agent-{sch_uuid}.xml")

        time.sleep(period)


def is_manager_busy(manager: str):
    manager_port = "12055"
    netstat_results = subprocess.Popen(f"{m} {manager} netstat -anp", shell=True, stdout=subprocess.PIPE).stdout
    netstat_results = netstat_results.read().decode().split('\n')  # Separates lines
    netstat_results.pop(0)  # Skipping the first line
    netstat_results.pop(0)  # The second one
    for result in netstat_results:
        formatted_result = [r for r in result.replace(' \t', '').split(' ') if r != '']
        if len(formatted_result) >= 4 and formatted_result[3].find(manager_port) != -1:
            return True
    return False


def interruption_handler(sig, frame):
    print('Sig INT detected!')
    print('Killing all Managers processes...')
    for man_proc in manager_procs:
        print(f'Sig KILL send to [PID={man_proc.pid}]')
        os.killpg(man_proc.pid, signal.SIGTERM)
    sys.exit(0)


if __name__ == '__main__':
    # Informing script arguments
    parser = ArgumentParser(
        description='Performs a repeated measure in a pair src-dst given period of each measure type')
    # parser.add_argument("-f", "--fast", help="fast initial trigger", action="store_true")
    # parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
    parser.add_argument("-m", "--manager", help="Uses Manager", action="store_true")
    parser.add_argument("-s", "--start_metricman", help="Start Netmetric Manager on Manager", action="store_true")
    parser.add_argument("agent_hostname", type=str, help="Agent hostname")
    parser.add_argument("manager_hostname", type=str, help="Manager hostname")
    parser.add_argument("throughput_tcp_period", type=float, help="Throughput TCP measurement repeating period (min)")
    parser.add_argument("rtt_period", type=float, help="Rtt measurement repeating period (min)")
    parser.add_argument("loss_period", type=float, help="Loss measurement repeating period (min)")
    args = parser.parse_args()

    # Init with constant seed
    rand.seed(50)

    # Read parameters from input
    tp_period = args.throughput_tcp_period * 60
    rtt_period = args.rtt_period * 60
    loss_period = args.loss_period * 60
    agent_hostname = args.agent_hostname
    manager_hostname = args.manager_hostname
    uses_manager = args.manager
    start_manager = args.start_metricman

    if not os.path.exists("results"):
        os.makedirs("results")
    if not os.path.exists("results/xml"):
        os.makedirs("results/xml")

    if start_manager:
        renamed_manager = manager_hostname if uses_manager else rename_switch(manager_hostname)
        manager_port_busy = is_manager_busy(renamed_manager)
        while manager_port_busy:
            manager_port_busy = is_manager_busy(renamed_manager)
            print(f"Waiting for manager {renamed_manager} free the port up...")
            os.system(f'{m} {renamed_manager} killall metricmanager')
            time.sleep(5)

        # Starts metric manager first
        command = f"{m} {renamed_manager} /usr/netmetric/sbin/metricmanager -c"
        # Run Netmetric Manager using subprocess
        manager_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                           preexec_fn=os.setsid)
        time.sleep(20)

        manager_procs.append(manager_process)
        signal.signal(signal.SIGINT, interruption_handler)

    if tp_period > 0:
        mes_thread = threading.Thread(target=measurement_service, args=("throughput_tcp", tp_period,))
        mes_thread.start()

    if rtt_period > 0:
        mes_thread = threading.Thread(target=measurement_service, args=("rtt", rtt_period,))
        mes_thread.start()

    if loss_period > 0:
        mes_thread = threading.Thread(target=measurement_service, args=("loss", loss_period,))
        mes_thread.start()
