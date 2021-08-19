#!/usr/bin/python3.9

import logging
from functools import partial
from subprocess import Popen

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch

from Project.common.main_topology import MAIN_TOPOLOGY


def add_rule(switch_name, required_ip, port_out):
    route_param = f'priority=1024,ip,nw_dst={required_ip},actions=output:{port_out}'
    logging.debug(route_param)
    p = Popen(['ovs-ofctl', 'add-flow', switch_name, route_param, '-O OpenFlow13'])
    p.wait()


def deploy_flow_rules(rules_map: list[dict[str, str]]):
    for rule in rules_map:
        add_rule(rule['name'], rule['ip'], rule['port'])


def evaluate_topology():
    """
    Service Provider Topology
    """

    switch = partial(OVSSwitch, protocols="OpenFlow13")
    # switch = partial ( OVSSwitch, protocols="sp" )
    net = Mininet(topo=None, controller=RemoteController, switch=switch, autoStaticArp=True, link=TCLink)

    net.addController('c0', RemoteController, ip="127.0.0.1", port=6633)

    for _switch in MAIN_TOPOLOGY.switches:
        net.addSwitch(_switch)

    for _hostname, _host in MAIN_TOPOLOGY.hosts.items():
        net.addHost(_hostname, ip=_host.ip_address, mac=_host.mac_address)

    for _link in MAIN_TOPOLOGY.links:
        net.addLink(_link.switch.name, _link.network_element.name,
                    _link.switch_port.port_number, _link.element_port.port_number,
                    **_link.degradation.to_dict())
    net.start()

    deploy_flow_rules(MAIN_TOPOLOGY.retrieve_rules())
    # while True:
    #     time.sleep(60)
    CLI(net)
    logging.info("Running...")
    net.stop()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create a Mininet Topology')
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        setLogLevel('debug')
    elif args.quiet:
        setLogLevel('warning')
    else:
        setLogLevel('info')

    evaluate_topology()
