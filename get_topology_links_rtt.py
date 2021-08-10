#!/usr/bin/env python3.9
import csv
import re
from dataclasses import dataclass
from typing import AnyStr

TOPOLOGY_FILE = "Topo_DBR.py"
CSV_FILE = "links-measurement-profile.csv"


@dataclass
class LinkInfo:
    host1: str
    host2: str
    bandwidth: float
    delay: float

    def pack_h1_h2(self) -> list:
        return [self.host1, self.host2, self.delay, 0, self.bandwidth]

    def pack_h2_h1(self) -> list:
        return [self.host2, self.host1, self.delay, 0, self.bandwidth]

    def measurement_profile(self):
        if re.match(r'u\d+', self.host1):
            ftt = 0.5
        elif re.match(r'r\d+', self.host1):
            ftt = 5
        else:
            ftt = 10
        # ftt = 0.5 if (re.match(r'u\d+', __h1) is not None) else (5 (if re.match(r'r\d+', __h1) is not None) else 10)
        return [self.host1, self.host2, ftt, 10, 1, 1]


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


def read_topology() -> list[LinkInfo]:
    links_pattern = re. \
        compile(r"(link[0-9]*_[kmg]bps(_\d+){1,2}) = {'bw': ([0-9]*), 'delay': '((\d+)|(\d+\.\d+))ms'}")

    links_labels = {"linknodeg": ("0", "inf")}

    switch_to_switch_pattern = re. \
        compile(r"link_switch_to_switch\(net, (s\d+), (s\d+), \d+, \d+, (link[0-9]*_[kmg]bps(?:_[0-9]+){1,2})\)")

    switch_to_host_pattern = re. \
        compile(r"link_switch_to_host\(net, (u\d+|cdn\d+|man\d+), (s\d+), \d+, \d+, (?:True|False), "
                r"(link[0-9]*_[kmg]bps(?:_[0-9]+){1,2}|linknodeg)\)")

    __links: list[LinkInfo] = list()

    with open(TOPOLOGY_FILE, "r") as topology:
        for line_number, line in enumerate(topology):
            for match in re.finditer(links_pattern, line):
                link_label = match.group(1)
                link_bw = match.group(3)
                link_delay = match.group(4)

                links_labels.update({link_label: (link_bw, link_delay)})

            find_link_pattern(line, __links, links_labels, switch_to_switch_pattern, False)
            find_link_pattern(line, __links, links_labels, switch_to_host_pattern, True)

    return __links


def find_link_pattern(line, __links, links_labels, pattern, switch_to_host: bool = False):
    for match in re.finditer(pattern, line):
        switch1 = match.group(1)
        switch2 = match.group(2)
        link_label = match.group(3)

        source = switch1 if switch_to_host else rename_switch(switch1)
        destine = rename_switch(switch2)

        link_info = links_labels.get(link_label)
        bw = float(link_info[0])
        delay = float(link_info[1])

        link = LinkInfo(host1=source, host2=destine, bandwidth=bw, delay=delay)
        __links.append(link)


def export_csv(topology_info: list[LinkInfo]) -> None:
    with open(CSV_FILE, 'w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for link in topology_info:
            csv_writer.writerow(link.measurement_profile())
            # csv_writer.writerow(link.pack_h1_h2())
            # csv_writer.writerow(link.pack_h2_h1())


links = read_topology()
# print(links)
export_csv(links)
