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

def rename_switch(switchname: str) -> str:
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
        return f"{switchname}"

def create_switch_name(sp, lower_bound, swtich_char) -> str:
    new_sp = sp - lower_bound
    new_sp = new_sp + 1
    return f'{swtich_char}{new_sp}'


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


if __name__ == '__main__':
    # Informing script arguments
    parser = ArgumentParser(
        description='Performs a repeated measure in a pair src-dst given period of each measure type')
    parser.add_argument("hostname", type=str, help="hostname")
    args = parser.parse_args()
    
    print(rename_switch(args.hostname))
