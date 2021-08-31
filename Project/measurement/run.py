#!/usr/bin/env python3.9
import csv
import os
from argparse import ArgumentParser

from Project.measurement.measurement_service import MeasurementService
from Project.measurement.metric import MetricTypes
from Project.measurement.procs import start_managers


def find_managers(__file: str):
    with open(__file) as __measurement_profiles:
        __csv_reader = csv.reader(__measurement_profiles, delimiter=";")
        __managers = ([*{__row[1]
                         for __row_count, __row in enumerate(__csv_reader)
                         if __row and __row_count != 0}])
        __managers.sort()
        return __managers


def save_pid(pid: int, pids_file: str) -> None:
    with open(pids_file, mode="a+") as pfile:
        pfile.write(f"{pid}\n")


# def run_unitary_measure(agent_hostname, manager_hostname, first_trigger_time_seconds) -> None:
#     # save_pid(os.getpid(), "/tmp/pids_running.txt")
#
#
#     mes_thread = Thread(target=measurement_service, args=(agent_hostname, manager_hostname,
#                                                           first_trigger_time_seconds,
#                                                           MetricTypes.RTT.value,
#                                                           -1,))
#     mes_thread.start()
#     measurement_service_started(mes_thread)

if __name__ == '__main__':
    # Informing script arguments
    parser = ArgumentParser(
        description='Performs a repeated measure in a pair src-dst given period of each measure type')
    parser.add_argument("-f", "--file", help="Open from a file", type=str, nargs='?')
    parser.add_argument("-o", "--output", help='File to store results', type=str, nargs='?')
    # opts, rem_args = parser.parse_known_args()

    args = parser.parse_args()
    file_input = args.file
    output_file = args.output

    # print(find_managers(file_input), len(find_managers(file_input)))
    start_managers(find_managers(file_input))

    # time.sleep(30)

    # Save parent's pid
    if os.path.exists("/tmp/pids_running"):
        os.remove("/tmp/pids_running.txt")
    save_pid(os.getpid(), "/tmp/pids_running.txt")

    with open(file_input) as measurement_profiles:
        csv_reader = csv.reader(measurement_profiles, delimiter=";")
        for line_number, line in enumerate(csv_reader):

            # Skip blank lines and header line
            if line is not None and line_number != 0:
                # Read parameters from file
                agent_hostname = line[0]
                manager_hostname = line[1]
                first_trigger_time_seconds = float(line[2]) * 60

                # run_unitary_measure(agent_hostname, manager_hostname, first_trigger_time_seconds)
                measurement_service = MeasurementService(agent_hostname, manager_hostname,
                                                         first_trigger_time_seconds,
                                                         40 * 60, [MetricTypes.RTT.value], 1)
                measurement_service.start()
