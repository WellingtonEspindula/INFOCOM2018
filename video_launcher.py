#!/usr/bin/env python3.9
import csv
import time
from argparse import ArgumentParser

import requests

SERVER = 'localhost'
PORT = '8080'
API_URL = f'http://{SERVER}:{PORT}/bqoepath/'


def update_controller():
    is_snapshot_loaded = False
    while not is_snapshot_loaded:
        response = requests.get(f'{API_URL}/bestqoepath-test-all').json()
        is_snapshot_loaded = True if response.get('status') == 'OK' else False
        time.sleep(0.5)


def create_route(client_hostname: str) -> str:
    response = requests.get(f'{API_URL}/shortestpath-{client_hostname}-all').json()
    return response.get('dst')


if __name__ == '__main__':
    parser = ArgumentParser(description='Execute videos according to the given workload')
    parser.add_argument('-f', '--file', help='Workload trace csv file (host;video_option;sleep_fraction;)',
                        type=str, nargs='?', default='static_trace.csv')
    args = parser.parse_args()
    trace_file = args.file


    # Main script
    update_controller()
    with open(trace_file, 'r') as file:
        csv_reader = csv.reader(file, delimiter=';')

        for row in csv_reader:
            client = row[0]
            video_option = row[1]
            sleep_fraction = row[2]

            server_hostname = create_route(client)



