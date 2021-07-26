#!/usr/bin/env python3.9
import abc
import csv
from abc import ABC
from dataclasses import dataclass
import os
import sys
import re
import shutil
import signal
import subprocess
import time
import uuid
import threading
import xml.etree.ElementTree as et
from collections import namedtuple
from argparse import ArgumentParser
from datetime import datetime
from enum import Enum
# from random import random as random
import random as rand
from typing import Optional
from xml.etree import ElementTree

m = "/home/mininet/mininet/util/m"
manager_procs = []


class Protocol(Enum):
    UDP = 0
    TCP = 1


@dataclass
class Metric:
    """ Class for managing a Metric with its attributes"""
    names: list[str]
    timeout: int
    probe_size: int
    train_length: int
    train_count: int
    gap: int
    protocol: Protocol
    connections: int
    time_mode: int
    max_time: int

    def create_schedule(self, agent: str, manager_ip: str, port: int = 12001) -> str:
        plugins = "".join([f'<plugins>{plugin}</plugins>\n\t\t\t ' for plugin in self.names]).rstrip()
        return f"""<metrics>
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
             {plugins}
             <timeout>{self.timeout}</timeout>
             <probe-size>{self.probe_size}</probe-size>
             <train-len>{self.train_length}</train-len>
             <train-count>{self.train_count}</train-count>
             <gap-value>{self.gap}</gap-value>
             <protocol>{self.protocol.value}</protocol>
             <num-conexoes>{self.connections}</num-conexoes>
             <time-mode>{self.time_mode}</time-mode>
             <max-time>{self.max_time}</max-time>
             <port>{port}</port>
             <output>OUTPUT-SNMP</output>
         </ativas>\n</metrics>"""


class MetricTypes(Enum):
    RTT = Metric(names=["rtt"], timeout=3, probe_size=100, train_length=1, train_count=20, gap=50000,
                 protocol=Protocol.UDP, connections=1, time_mode=0, max_time=0)
    LOSS = Metric(names=["loss"], timeout=3, probe_size=100, train_length=1, train_count=20, gap=50000,
                  protocol=Protocol.UDP, connections=1, time_mode=0, max_time=0)
    UDP_PACK = Metric(names=["rtt", "loss"], timeout=3, probe_size=100, train_length=1, train_count=20, gap=50000,
                      protocol=Protocol.UDP, connections=1, time_mode=0, max_time=0)
    THROUGHPUT_TCP = Metric(names=["throughput_tcp"], timeout=12, probe_size=14520, train_length=1440, train_count=1,
                            gap=100000, protocol=Protocol.TCP, connections=3, time_mode=2, max_time=12)


def random():
    return int.from_bytes(os.urandom(16), byteorder="big")


def rename_switch(switch_name: str) -> str:
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

    sp = int(switch_name[1:])
    if ran_lower_bound <= sp <= ran_upper_bound:
        return create_switch_name(sp, ran_lower_bound, 'r')
    elif metro_lower_bound <= sp <= metro_upper_bound:
        return create_switch_name(sp, metro_lower_bound, 'm')
    elif access_lower_bound <= sp <= access_upper_bound:
        return create_switch_name(sp, access_lower_bound, 'a')
    elif core_lower_bound <= sp <= core_upper_bound:
        return create_switch_name(sp, core_lower_bound, 'c')
    elif internet_lower_bound <= sp <= internet_upper_bound:
        return create_switch_name(sp, internet_lower_bound, 'i')
    else:
        return f"{switch_name}"


def create_switch_name(sp, lower_bound, switch_char) -> str:
    new_sp = sp - lower_bound
    new_sp = new_sp + 1
    return f'{switch_char}{new_sp}'


def calculate_ip(p) -> str:
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


def parse_xml_text_if_exists(root, xpath):
    element = root.find(xpath)
    if element is not None:
        return element.text
    else:
        return ""


def write_data_csv(filename: str, data: list) -> None:
    with open(filename, mode='a+') as file:
        file_writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        file_writer.writerow(data)
        # print("File saved")


@dataclass
class Schedule:
    agent_hostname: str
    manager_hostname: str
    metric: Metric
    uuid: str = str(uuid.uuid4())

    def measure(self):
        filename = "/tmp/schedule-{self.uuid}.xml"
        _command = f"{m} {agent_hostname} /usr/netmetric/sbin/metricagent -c -f {filename} -w -l 1000 -u " \
                   f"100 -u {self.uuid} "
        os.system(_command)
        measurement_finish()

    def __create(self, agent_hostname: str, manager_ip: str, port: int = 12001) -> str:
        plugins = "".join([f'<plugins>{plugin}</plugins>\n\t\t\t ' for plugin in self.metric.names]).rstrip()
        return f"""<metrics>
             <ativas>
               <agt-index>1090</agt-index>
                <manager-ip>{manager_ip}</manager-ip>
                <literal-addr>{agent_hostname}</literal-addr>
                <android>1</android>
                <location>
                    <name>-</name>
                    <city>-</city>
                    <state>-</state>
                </location>
                {plugins}
                <timeout>{self.metric.timeout}</timeout>
                <probe-size>{self.metric.probe_size}</probe-size>
                <train-len>{self.metric.train_length}</train-len>
                <train-count>{self.metric.train_count}</train-count>
                <gap-value>{self.metric.gap}</gap-value>
                <protocol>{self.metric.protocol.value}</protocol>
                <num-conexoes>{self.metric.connections}</num-conexoes>
                <time-mode>{self.metric.time_mode}</time-mode>
                <max-time>{self.metric.max_time}</max-time>
                <port>{port}</port>
                <output>OUTPUT-SNMP</output>
            </ativas>\n</metrics>"""

    @staticmethod
    def __save(filename: str, schedule: str) -> bool:
        with open(filename, 'w+') as file:
            file.write(schedule)
            return True

    def create_and_save(self):
        schedule_filename = f"/tmp/schedule-{self.uuid}.xml"
        manager_ip = calculate_ip(self.manager_hostname)
        schedule = self.__create(self.agent_hostname, manager_ip)
        self.__save(schedule_filename, schedule)

    def read_store_results(self) -> None:
        filename = f"agent-{self.uuid}.xml"
        root = ElementTree.parse(filename).getroot()

        current_timestamp = str(datetime.now())
        if self.metric is not None:
            for name in self.metric.names:
                upload_avg = root.findtext(f"./ativas[@metrica=\"{name}\"]/upavg", "")
                download_avg = root.findtext(f"./ativas[@metrica=\"{name}\"]/downavg", "")

                data = [
                    self.agent_hostname,
                    self.manager_hostname,
                    current_timestamp,
                    self.uuid,
                    upload_avg,
                    download_avg,
                ]

                self.store_result(filename, data)

            shutil.move(f"agent-{self.uuid}.xml", f"./results/xml/agent-{self.uuid}.xml")

    @staticmethod
    def store_result(filename: str, data: list) -> bool:
        with open(filename, mode='a+') as file:
            file_writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            file_writer.writerow(data)
            return True

    def __str__(self):
        return f"Schedule [uuid={self.uuid}, metric={self.metric.names}]"


_schedule_queue: list[Schedule] = list[Schedule]()
_current_schedule: Optional[Schedule] = None


def enqueue_schedule(schedule: Schedule) -> None:
    global _schedule_queue
    print("Enqueue Schedule!")
    _schedule_queue.append(schedule)
    rotate()


def rotate() -> None:
    global _current_schedule
    global _schedule_queue
    if _current_schedule is None:
        _current_schedule = _schedule_queue.pop(0)
        print(f"Queue: {_schedule_queue}, Current Schedule = {_current_schedule.uuid}")
        _current_schedule.measure()
    else:
        print("Couldn't execute current schedule since a measure is already running")


def measurement_finish() -> None:
    global _current_schedule
    global _schedule_queue
    print("Measure Finished!")
    _current_schedule.read_store_results()
    _current_schedule = None
    rotate()


def measurement_service(metric: Metric, period_in_minutes: float):
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
        schedule = Schedule(agent_hostname=agent_hostname, manager_hostname=manager_hostname, metric=metric)
        schedule.create_and_save()

        enqueue_schedule(schedule)
        # create_schedule(sch_uuid, agent_hostname, calculate_ip(manager_hostname), metric)

        # # Creates the metric agent command
        # command = f"{m} {agent_hostname} /usr/netmetric/sbin/metricagent -c -f /tmp/schedule-{sch_uuid}.xml -w -l 1000 -u " \
        #           f"100 -u {sch_uuid} "
        # os.system(command)
        #
        # # Gather the data from metricagent xml output
        # current_timestamp = str(datetime.now())
        # data = [
        #     agent_hostname,
        #     manager_hostname,
        #     current_timestamp,
        #     sch_uuid,
        #     *read_results_xml(metric, f"agent-{sch_uuid}.xml"),
        # ]
        #
        # write_data_csv("results/nm_last_results.csv", data)
        # # Moves the XML file from results/xml folder
        # shutil.move(f"agent-{sch_uuid}.xml", f"./results/xml/agent-{sch_uuid}.xml")

        time.sleep(period_in_minutes)


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
        mes_thread = threading.Thread(target=measurement_service, args=(MetricTypes.THROUGHPUT_TCP.value, tp_period,))
        mes_thread.start()

    if rtt_period > 0:
        mes_thread = threading.Thread(target=measurement_service, args=(MetricTypes.RTT.value, rtt_period,))
        mes_thread.start()

    if loss_period > 0:
        mes_thread = threading.Thread(target=measurement_service, args=(MetricTypes.LOSS.value, loss_period,))
        mes_thread.start()

    # Test zone
    # manager_hostname = "man1"
    # agent_hostname = "u001"
    # measurement_service(MetricTypes.RTT.value, 0.5)
