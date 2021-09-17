import shutil
import time
import uuid as uuid
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from xml.etree import ElementTree

from Project.common import host_utils as hu
from Project.common.constants import MININET_M
from Project.common.csv_utils import csv_store
from Project.measurement.metric import Metric, MetricTypes


class ScheduleListener(ABC):
    @abstractmethod
    def measure_finished(self):
        raise NotImplementedError


@dataclass
class Schedule:
    agent_hostname: str
    manager_hostname: str
    schedule_listener: ScheduleListener
    metrics: list[Metric] = field(default_factory=list)
    uuid: str = field(init=False)

    def __post_init__(self):
        self.uuid = str(uuid.uuid4())

    def create_and_save(self):
        schedule_filename = f"/tmp/schedule-{self.uuid}.xml"
        manager_ip = hu.calculate_ip(self.manager_hostname)
        schedule = self.__create(self.agent_hostname, manager_ip)
        self.__save(schedule_filename, schedule)

    def __create(self, agent_hostname: str, manager_ip: str, port: int = 12001) -> str:
        return "<metrics>\n".join([f"""
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
                {metric.name}
                <timeout>{metric.timeout}</timeout>
                <probe-size>{metric.probe_size}</probe-size>
                <train-len>{metric.train_length}</train-len>
                <train-count>{metric.train_count}</train-count>
                <gap-value>{metric.gap}</gap-value>
                <protocol>{metric.protocol.value}</protocol>
                <num-conexoes>{metric.connections}</num-conexoes>
                <time-mode>{metric.time_mode}</time-mode>
                <max-time>{metric.max_time}</max-time>
                <port>{port}</port>
                <output>OUTPUT-SNMP</output>
            </ativas>\n""" for metric in self.metrics]).join("</metrics>")

    @staticmethod
    def __save(filename: str, schedule: str) -> bool:
        with open(filename, 'w+') as file:
            file.write(schedule)
            return True

    def measure(self):
        filename = f"/tmp/schedule-{self.uuid}.xml"
        _command = f"{MININET_M} {self.agent_hostname} /usr/netmetric/sbin/metricagent -c -f {filename} -w -l 1000 -u " \
                   f"100 -u {self.uuid} "
        os.system(_command)
        # time.sleep(2)
        self.read_store_results()
        self.schedule_listener.measure_finished()

    def read_results(self) -> list[tuple[Metric, int, int]]:
        results: list[tuple[Metric, int, int]] = []

        filename = f"agent-{self.uuid}.xml"
        root = ElementTree.parse(filename).getroot()

        current_timestamp = str(datetime.now())
        for metric in self.metrics:
            # noinspection PyTypeChecker
            upload_avg = root.findtext(f'./ativas[@metrica="{metric.name}"]/upavg', '')
            # noinspection PyTypeChecker
            download_avg = root.findtext(f'./ativas[@metrica="{metric.name}"]/downavg', '')

            results.append((metric, upload_avg, download_avg))

        return results

    # @staticmethod
    # def store_metric_results(results: list[Result]) -> None:
    #     for result in results:
    #         result.store('results/measurement_results.csv')

    def store_schedule_results(self, results: list[tuple[Metric, int, int]]) -> None:
        results: dict[str, tuple[int, int]] = {result[0].name: (result[1], result[2]) for result in results}
        data_h1_h2 = [
            self.agent_hostname,
            self.manager_hostname,
            results.get(MetricTypes.RTT.name)[0] if results.get(MetricTypes.RTT.name) is not None else -1,
            results.get(MetricTypes.LOSS.name)[1] if results.get(MetricTypes.LOSS.name) is not None else -1,
            results.get(MetricTypes.THROUGHPUT_TCP.name)[1]
            if results.get(MetricTypes.THROUGHPUT_TCP.name) is not None else -1,
        ]
        data_h2_h1 = [
            self.manager_hostname,
            self.agent_hostname,
            results.get(MetricTypes.RTT.name)[1] if results.get(MetricTypes.RTT.name) is not None else -1,
            results.get(MetricTypes.LOSS.name)[1] if results.get(MetricTypes.LOSS.name) is not None else -1,
            results.get(MetricTypes.THROUGHPUT_TCP.name)[1]
            if results.get(MetricTypes.THROUGHPUT_TCP.name) is not None else -1,
        ]

        csv_store('nm_last_results.csv', data_h1_h2)
        csv_store('nm_last_results.csv', data_h2_h1)

    def read_store_results(self) -> None:
        filename = f"agent-{self.uuid}.xml"
        print(f'{filename=}')
        root = ElementTree.parse(filename).getroot()

        current_timestamp = str(datetime.now())
        for metric in self.metrics:
            # noinspection PyTypeChecker
            upload_avg = root.findtext(f'./ativas[@metrica="{metric.name}"]/upavg', '')
            # noinspection PyTypeChecker
            download_avg = root.findtext(f'./ativas[@metrica="{metric.name}"]/downavg', '')

            data = [
                self.agent_hostname,
                self.manager_hostname,
                current_timestamp,
                self.uuid,
                metric.name,
                upload_avg,
                download_avg,
            ]

            csv_store("results/nm_last_results.csv", data)

        shutil.move(f"agent-{self.uuid}.xml", f"./results/xml/agent-{self.uuid}.xml")

    def __repr__(self):
        return f"Schedule [{self.uuid=}, {self.agent_hostname=}, {self.manager_hostname=}, {self.metrics=}]"
