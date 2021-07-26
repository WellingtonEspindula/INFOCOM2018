import uuid as uuid
from dataclasses import dataclass
from xml.etree import ElementTree

from Project import host_utils
from Project.metric import Metric
from Project.result import Result


@dataclass
class Schedule:
    agent_hostname: str
    manager_hostname: str
    metric: Metric
    uuid: str = str(uuid.uuid4())

    def create(self, agent_hostname: str, manager_ip: str, port: int = 12001) -> str:
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
    def save(filename: str, schedule: str) -> bool:
        with open(filename, 'w+') as file:
            file.write(schedule)
            return True

    def create_and_save(self):
        schedule_filename = f"/tmp/schedule-{self.uuid}.xml"
        manager_ip = host_utils.calculate_ip(self.manager_hostname)
        schedule = self.create(self.agent_hostname, manager_ip)
        self.save(schedule_filename, schedule)

    def read_results(self) -> list[Result]:
        results = []

        filename = f"agent-{self.uuid}.xml"
        root = ElementTree.parse(filename).getroot()

        if self.metric is not None:
            for name in self.metric.names:
                upload_avg = root.findtext(f"./ativas[@metrica=\"{name}\"]/upavg", "")
                download_avg = root.findtext(f"./ativas[@metrica=\"{name}\"]/downavg", "")

                results += [name, upload_avg, download_avg]

        return results
