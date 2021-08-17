#!/usr/bin/env python3.9

import csv
from dataclasses import dataclass
from datetime import datetime

from Project.measurement.metric import Metric
from Project.measurement.schedule import Schedule


@dataclass
class Result:
    schedule: Schedule
    metric: Metric
    up_avg: float = 0
    down_avg: float = 0

    def to_csv(self) -> list:
        current_timestamp = str(datetime.now())
        data = [
            self.schedule.agent_hostname,
            self.schedule.manager_hostname,
            current_timestamp,
            self.schedule.uuid,
            self.up_avg,
            self.down_avg,
        ]

        return data

    def store(self, filename: str) -> bool:
        with open(filename, mode='a+') as file:
            file_writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            file_writer.writerow(self.to_csv())
            return True
