#!/usr/bin/env python3.9

import os
from argparse import ArgumentParser
from Project.common.constants import MININET_M

if __name__ == '__main__':
    parser = ArgumentParser(description='Serve videos according to his hostname')
    parser.add_argument('server', help='Server hostname',
                        type=str, nargs='?')
    args = parser.parse_args()
    server_hostname = args.server

    os.system(f'{MININET_M} {server_hostname} ./start_apache.sh {server_hostname}')


