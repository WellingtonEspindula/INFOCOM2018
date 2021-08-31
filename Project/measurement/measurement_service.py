import math
import sys
import threading
import time
from dataclasses import dataclass
from threading import Thread

from Project.measurement.metric import Metric
from Project.measurement.procs import kill_all_managers
from Project.measurement.schedule import Schedule, ScheduleListener
from Project.measurement import scheduler

_active_meas_services: dict[int, Thread] = {}
_finished_meas_services: dict[int, Thread] = {}


class ScheduleListenerImpl(ScheduleListener):
    def measure_finished(self):
        scheduler.measurement_finish()


class MeasurementService(threading.Thread):
    def __init__(self, agent_hostname: str, manager_hostname: str,
                 first_trigger_time_seconds: float, period_seconds: float,
                 metrics: list[Metric] = None, rounds: int = math.inf):
        threading.Thread.__init__(self)
        if metrics is None:
            metrics = []
        self.agent_hostname: str = agent_hostname
        self.manager_hostname: str = manager_hostname
        self.first_trigger_time_seconds: float = first_trigger_time_seconds
        self.metrics: list[Metric] = metrics
        self.period_seconds: float = period_seconds
        self.rounds: int = rounds

    def start(self) -> None:
        global _active_meas_services
        print(f'Added {self.ident=} to list')
        _active_meas_services.update({self.ident: self})
        threading.Thread.start(self)

    def run(self) -> None:
        """
        Service whose responsibility is create the measurement schedule, enqueue it and
        waiting for measure polling time
        """

        # First of all, must wait the first trigger time
        # first_trigger_seconds = first_trigger_time_seconds + (3 + (random() % 20))
        first_trigger_seconds = self.first_trigger_time_seconds
        print(f'Waiting for {first_trigger_seconds} s for stating this measure')
        time.sleep(first_trigger_seconds)

        for i in range(0, self.rounds):
            schedule = Schedule(self.agent_hostname, self.manager_hostname, ScheduleListenerImpl(),
                                metrics=self.metrics)
            schedule.create_and_save()
            # scheduler.enqueue_schedule(schedule)
            schedule.measure()

            time.sleep(self.period_seconds)
        self.finish()

    def finish(self) -> None:
        print(f'Removed {self.ident=} from list')
        _active_meas_services.pop(self.ident)
        _finished_meas_services.update({self.ident: self})

        if are_all_measurement_service_finished():
            print("All measurements are finished. Let's finish it all")
            kill_all_managers()
            sys.exit(0)


def are_all_measurement_service_finished() -> bool:
    global _active_meas_services
    global _finished_meas_services
    return len(_active_meas_services) == 0 and len(_finished_meas_services) > 0
