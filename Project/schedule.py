import csv
import os
import shutil
import uuid as uuid
from dataclasses import dataclass
from datetime import datetime
from xml.etree import ElementTree

from Project import host_utils as hu
from Project.metric import Metric
from Project.result import Result
from Project import queue_manager as qm


@dataclass
class Schedule:
    agent_hostname: str
    manager_hostname: str
    metric: Metric
    uuid: str = str(uuid.uuid4())

    def measure(self):
        filename = f"/tmp/schedule-{self.uuid}.xml"
        _command = f"{m} {self.agent_hostname} /usr/netmetric/sbin/metricagent -c -f {filename} -w -l 1000 -u " \
                   f"100 -u {self.uuid} "
        os.system(_command)
        self.read_store_results()
        qm.measurement_finish()

    def __create(self, agent_hostname: str, manager_ip: str, port: int = 12001) -> str:
        plugins = "".join(
            f'<plugins>{plugin}</plugins>\n\t\t\t ' for plugin in self.metric.names
        ).rstrip()

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
        manager_ip = hu.calculate_ip(self.manager_hostname)
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
                    name,
                    upload_avg,
                    download_avg,
                ]

                self.store_result("results/nm_last_results.csv", data)

            shutil.move(f"agent-{self.uuid}.xml", f"./results/xml/agent-{self.uuid}.xml")

    @staticmethod
    def store_result(filename: str, data: list) -> bool:
        with open(filename, mode='a+') as file:
            file_writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            file_writer.writerow(data)
            return True

    def __str__(self):
        return f"Schedule [uuid={self.uuid}, metric={self.metric.names}]"
