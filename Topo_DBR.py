#!/usr/bin/python3
import logging
from functools import partial
from subprocess import Popen

from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch

host_ip_map = {}
switches_to_aux_hosts = {}
rules_map = []


def create_host(net, hostname, host_ip, host_mac):
    global host_ip_map
    host_ip_map[hostname] = host_ip
    return net.addHost(hostname, ip=host_ip, mac=host_mac)


def simple_create_host(net, hostname, host_ip, host_mac):
    global host_ip_map
    host_ip_map[hostname] = host_ip
    return net.addHost(hostname, ip=host_ip, mac=host_mac)


def add_rule(switch_name, required_ip, port_out):
    route_param = 'priority=1024,ip,nw_dst=' + required_ip + ',actions=output:' + port_out
    logging.debug(route_param)
    p = Popen(['ovs-ofctl', 'add-flow', switch_name, route_param, '-O OpenFlow13'])
    p.wait()


def link_switch_to_host(net, host, switch, port_host, port_switch, is_aux, degradation):
    global switches_to_aux_hosts
    global rules_map
    net.addLink(host, switch, port_host, port_switch, **degradation)
    if is_aux:
        switches_to_aux_hosts[switch] = host
    rules_map.append({'name': switch.name, 'ip': host_ip_map[host.name], 'port': str(port_switch)})
    # addRule(switch.name, hostIpMap[host.name], str(portSwitch))


def link_switch_to_switch(net, switch_a, switch_b, port_a, port_b, degradation):
    global rules_map
    net.addLink(switch_a, switch_b, port_a, port_b, **degradation)
    ip_a = host_ip_map[switches_to_aux_hosts[switch_a].name]
    ip_b = host_ip_map[switches_to_aux_hosts[switch_b].name]

    # addRule(sA.name, ipB, str(pA))
    rules_map.append({'name': switch_a.name, 'ip': ip_b, 'port': str(port_a)})

    # addRule(sB.name, ipA, str(pB))
    rules_map.append({'name': switch_b.name, 'ip': ip_a, 'port': str(port_b)})


def deploy_flow_rules():
    for rule in rules_map:
        add_rule(rule['name'], rule['ip'], rule['port'])


def evaluate_topology():
    """ Service Provider Topology
    """

    switch = partial(OVSSwitch, protocols="OpenFlow13")
    # switch = partial ( OVSSwitch, protocols="sp" )
    net = Mininet(topo=None, controller=RemoteController, switch=switch, autoStaticArp=True, link=TCLink)

    net.addController('c0', RemoteController, ip="127.0.0.1", port=6633)

    link100_mbps = {'bw': 20, 'delay': '15ms'}
    link1_gbps = {'bw': 200, 'delay': '5ms'}
    linknodeg = {}

    link100_mbps_1 = {'bw': 20, 'delay': '1ms'}
    link100_mbps_4 = {'bw': 20, 'delay': '4ms'}
    link100_mbps_5 = {'bw': 20, 'delay': '5ms'}
    link100_mbps_6 = {'bw': 20, 'delay': '6ms'}
    link100_mbps_7 = {'bw': 20, 'delay': '7ms'}
    link100_mbps_8 = {'bw': 20, 'delay': '8ms'}
    link100_mbps_9 = {'bw': 20, 'delay': '9ms'}
    link100_mbps_10 = {'bw': 20, 'delay': '10ms'}
    link100_mbps_11 = {'bw': 20, 'delay': '11ms'}

    link1_gbps_1 = {'bw': 200, 'delay': '1ms'}
    link1_gbps_12 = {'bw': 200, 'delay': '12ms'}
    link1_gbps_15 = {'bw': 200, 'delay': '15ms'}
    link1_gbps_18 = {'bw': 200, 'delay': '18ms'}
    link1_gbps_20 = {'bw': 200, 'delay': '20ms'}
    link1_gbps_23 = {'bw': 200, 'delay': '23ms'}
    link1_gbps_25 = {'bw': 200, 'delay': '25ms'}
    link1_gbps_30 = {'bw': 200, 'delay': '30ms'}

    # net.addLink(Host1,   Switch1,    **linkopts )
    # Adding switches
    s1 = net.addSwitch('s1')  # R1
    s2 = net.addSwitch('s2')  # R2
    s3 = net.addSwitch('s3')  # R3
    s4 = net.addSwitch('s4')  # R4
    s5 = net.addSwitch('s5')  # R5
    s6 = net.addSwitch('s6')  # R6
    s7 = net.addSwitch('s7')  # R7
    s8 = net.addSwitch('s8')  # R8
    s9 = net.addSwitch('s9')  # R9
    s10 = net.addSwitch('s10')  # R10
    s11 = net.addSwitch('s11')  # R11
    s12 = net.addSwitch('s12')  # R12
    s13 = net.addSwitch('s13')  # R13
    s14 = net.addSwitch('s14')  # R14
    s15 = net.addSwitch('s15')  # R15
    s16 = net.addSwitch('s16')  # R16
    s17 = net.addSwitch('s17')  # R17
    s18 = net.addSwitch('s18')  # R18
    s19 = net.addSwitch('s19')  # R19
    s20 = net.addSwitch('s20')  # R20
    s21 = net.addSwitch('s21')  # M1
    s22 = net.addSwitch('s22')  # M2
    s23 = net.addSwitch('s23')  # M3
    s24 = net.addSwitch('s24')  # M4
    s25 = net.addSwitch('s25')  # M5
    s26 = net.addSwitch('s26')  # A1
    s27 = net.addSwitch('s27')  # A2
    s28 = net.addSwitch('s28')  # A3
    s29 = net.addSwitch('s29')  # A4
    s30 = net.addSwitch('s30')  # C1
    s31 = net.addSwitch('s31')  # C2
    s32 = net.addSwitch('s32')  # C3
    s33 = net.addSwitch('s33')  # C4
    s34 = net.addSwitch('s34')  # I1 (Internet)

    # 1.   DESTINATIONS
    # 1.1. CREATING HOSTS
    cdn1 = simple_create_host(net, 'cdn1', '10.0.0.251', '00:04:00:00:02:51')
    cdn2 = simple_create_host(net, 'cdn2', '10.0.0.252', '00:04:00:00:02:52')
    cdn3 = simple_create_host(net, 'cdn3', '10.0.0.253', '00:04:00:00:02:53')
    ext1 = simple_create_host(net, 'ext1', '10.0.0.254', '00:04:00:00:02:54')

    man1 = simple_create_host(net, 'man1', '10.0.0.241', '00:04:00:00:02:51')
    man2 = simple_create_host(net, 'man2', '10.0.0.242', '00:04:00:00:02:52')
    man3 = simple_create_host(net, 'man3', '10.0.0.243', '00:04:00:00:02:53')
    man4 = simple_create_host(net, 'man4', '10.0.0.244', '00:04:00:00:02:54')

    # 1.2. CREATING LINKS
    link_switch_to_host(net, cdn1, s25, 0, 99, False, link100_mbps_1)
    link_switch_to_host(net, cdn2, s29, 0, 99, False, link1_gbps_1)
    link_switch_to_host(net, cdn3, s31, 0, 99, False, link1_gbps_1)
    link_switch_to_host(net, ext1, s34, 0, 99, False, link1_gbps_30)

    # 1.2. CREATING LINKS
    link_switch_to_host(net, man1, s30, 0, 90, False, link100_mbps_1)
    link_switch_to_host(net, man2, s31, 0, 90, False, link1_gbps_1)
    link_switch_to_host(net, man3, s32, 0, 90, False, link1_gbps_1)
    link_switch_to_host(net, man4, s33, 0, 90, False, link1_gbps_30)

    # 2.   SWITCH PROCESSING
    # 2.1. CREATING HOSTS
    r1 = simple_create_host(net, 'r1', '10.0.0.201', '00:04:00:00:0F:01')
    r2 = simple_create_host(net, 'r2', '10.0.0.202', '00:04:00:00:0F:02')
    r3 = simple_create_host(net, 'r3', '10.0.0.203', '00:04:00:00:0F:03')
    r4 = simple_create_host(net, 'r4', '10.0.0.204', '00:04:00:00:0F:04')
    r5 = simple_create_host(net, 'r5', '10.0.0.205', '00:04:00:00:0F:05')
    r6 = simple_create_host(net, 'r6', '10.0.0.206', '00:04:00:00:0F:06')
    r7 = simple_create_host(net, 'r7', '10.0.0.207', '00:04:00:00:0F:07')
    r8 = simple_create_host(net, 'r8', '10.0.0.208', '00:04:00:00:0F:08')
    r9 = simple_create_host(net, 'r9', '10.0.0.209', '00:04:00:00:0F:09')
    r10 = simple_create_host(net, 'r10', '10.0.0.210', '00:04:00:00:0F:10')
    r11 = simple_create_host(net, 'r11', '10.0.0.211', '00:04:00:00:0F:11')
    r12 = simple_create_host(net, 'r12', '10.0.0.212', '00:04:00:00:0F:12')
    r13 = simple_create_host(net, 'r13', '10.0.0.213', '00:04:00:00:0F:13')
    r14 = simple_create_host(net, 'r14', '10.0.0.214', '00:04:00:00:0F:14')
    r15 = simple_create_host(net, 'r15', '10.0.0.215', '00:04:00:00:0F:15')
    r16 = simple_create_host(net, 'r16', '10.0.0.216', '00:04:00:00:0F:16')
    r17 = simple_create_host(net, 'r17', '10.0.0.217', '00:04:00:00:0F:17')
    r18 = simple_create_host(net, 'r18', '10.0.0.218', '00:04:00:00:0F:18')
    r19 = simple_create_host(net, 'r19', '10.0.0.219', '00:04:00:00:0F:19')
    r20 = simple_create_host(net, 'r20', '10.0.0.220', '00:04:00:00:0F:20')
    m1 = simple_create_host(net, 'm1', '10.0.0.221', '00:04:00:00:0F:21')
    m2 = simple_create_host(net, 'm2', '10.0.0.222', '00:04:00:00:0F:22')
    m3 = simple_create_host(net, 'm3', '10.0.0.223', '00:04:00:00:0F:23')
    m4 = simple_create_host(net, 'm4', '10.0.0.224', '00:04:00:00:0F:24')
    m5 = simple_create_host(net, 'm5', '10.0.0.225', '00:04:00:00:0F:25')
    a1 = simple_create_host(net, 'a1', '10.0.0.226', '00:04:00:00:0F:26')
    a2 = simple_create_host(net, 'a2', '10.0.0.227', '00:04:00:00:0F:27')
    a3 = simple_create_host(net, 'a3', '10.0.0.228', '00:04:00:00:0F:28')
    a4 = simple_create_host(net, 'a4', '10.0.0.229', '00:04:00:00:0F:29')
    c1 = simple_create_host(net, 'c1', '10.0.0.230', '00:04:00:00:0F:30')
    c2 = simple_create_host(net, 'c2', '10.0.0.231', '00:04:00:00:0F:31')
    c3 = simple_create_host(net, 'c3', '10.0.0.232', '00:04:00:00:0F:32')
    c4 = simple_create_host(net, 'c4', '10.0.0.233', '00:04:00:00:0F:33')
    i1 = simple_create_host(net, 'i1', '10.0.0.234', '00:04:00:00:0F:34')

    # 2.2. CREATING LINKS
    link_switch_to_host(net, r1, s1, 0, 100, True, linknodeg)
    link_switch_to_host(net, r2, s2, 0, 100, True, linknodeg)
    link_switch_to_host(net, r3, s3, 0, 100, True, linknodeg)
    link_switch_to_host(net, r4, s4, 0, 100, True, linknodeg)
    link_switch_to_host(net, r5, s5, 0, 100, True, linknodeg)
    link_switch_to_host(net, r6, s6, 0, 100, True, linknodeg)
    link_switch_to_host(net, r7, s7, 0, 100, True, linknodeg)
    link_switch_to_host(net, r8, s8, 0, 100, True, linknodeg)
    link_switch_to_host(net, r9, s9, 0, 100, True, linknodeg)
    link_switch_to_host(net, r10, s10, 0, 100, True, linknodeg)
    link_switch_to_host(net, r11, s11, 0, 100, True, linknodeg)
    link_switch_to_host(net, r12, s12, 0, 100, True, linknodeg)
    link_switch_to_host(net, r13, s13, 0, 100, True, linknodeg)
    link_switch_to_host(net, r14, s14, 0, 100, True, linknodeg)
    link_switch_to_host(net, r15, s15, 0, 100, True, linknodeg)
    link_switch_to_host(net, r16, s16, 0, 100, True, linknodeg)
    link_switch_to_host(net, r17, s17, 0, 100, True, linknodeg)
    link_switch_to_host(net, r18, s18, 0, 100, True, linknodeg)
    link_switch_to_host(net, r19, s19, 0, 100, True, linknodeg)
    link_switch_to_host(net, r20, s20, 0, 100, True, linknodeg)
    link_switch_to_host(net, m1, s21, 0, 100, True, linknodeg)
    link_switch_to_host(net, m2, s22, 0, 100, True, linknodeg)
    link_switch_to_host(net, m3, s23, 0, 100, True, linknodeg)
    link_switch_to_host(net, m4, s24, 0, 100, True, linknodeg)
    link_switch_to_host(net, m5, s25, 0, 100, True, linknodeg)
    link_switch_to_host(net, a1, s26, 0, 100, True, linknodeg)
    link_switch_to_host(net, a2, s27, 0, 100, True, linknodeg)
    link_switch_to_host(net, a3, s28, 0, 100, True, linknodeg)
    link_switch_to_host(net, a4, s29, 0, 100, True, linknodeg)
    link_switch_to_host(net, c1, s30, 0, 100, True, linknodeg)
    link_switch_to_host(net, c2, s31, 0, 100, True, linknodeg)
    link_switch_to_host(net, c3, s32, 0, 100, True, linknodeg)
    link_switch_to_host(net, c4, s33, 0, 100, True, linknodeg)
    link_switch_to_host(net, i1, s34, 0, 100, True, linknodeg)

    # 3. CREATING LINKS BETWEEN SWITCHES
    # Level 3.1 - RAN / Metro
    link_switch_to_switch(net, s1, s21, 31, 1, link100_mbps_6)
    link_switch_to_switch(net, s2, s21, 31, 2, link100_mbps_8)
    link_switch_to_switch(net, s3, s21, 31, 3, link100_mbps_6)
    link_switch_to_switch(net, s4, s21, 31, 4, link100_mbps_7)

    link_switch_to_switch(net, s5, s22, 31, 1, link100_mbps_4)
    link_switch_to_switch(net, s6, s22, 31, 2, link100_mbps_4)
    link_switch_to_switch(net, s7, s22, 31, 3, link100_mbps_4)
    link_switch_to_switch(net, s8, s22, 31, 4, link100_mbps_6)

    link_switch_to_switch(net, s9, s23, 31, 1, link100_mbps_9)
    link_switch_to_switch(net, s10, s23, 31, 2, link100_mbps_8)
    link_switch_to_switch(net, s11, s23, 31, 3, link100_mbps_4)
    link_switch_to_switch(net, s12, s23, 31, 4, link100_mbps_5)

    link_switch_to_switch(net, s13, s24, 31, 1, link100_mbps_8)
    link_switch_to_switch(net, s14, s24, 31, 2, link100_mbps_8)
    link_switch_to_switch(net, s15, s24, 31, 3, link100_mbps_7)
    link_switch_to_switch(net, s16, s24, 31, 4, link100_mbps_4)

    link_switch_to_switch(net, s17, s25, 31, 1, link100_mbps_4)
    link_switch_to_switch(net, s18, s25, 31, 2, link100_mbps_6)
    link_switch_to_switch(net, s19, s25, 31, 3, link100_mbps_7)
    link_switch_to_switch(net, s20, s25, 31, 4, link100_mbps_4)

    # Level 3.1.5 - Metro Ring
    link_switch_to_switch(net, s21, s22, 5, 5, link100_mbps_9)
    link_switch_to_switch(net, s22, s23, 6, 6, link100_mbps_6)
    link_switch_to_switch(net, s23, s24, 5, 5, link100_mbps_11)
    link_switch_to_switch(net, s24, s25, 6, 6, link100_mbps_5)
    link_switch_to_switch(net, s25, s21, 5, 6, link100_mbps_10)  # Link to close ring

    # Level 3.2 - Metro / Access
    link_switch_to_switch(net, s22, s27, 7, 1, link1_gbps_20)
    link_switch_to_switch(net, s23, s28, 7, 1, link1_gbps_30)

    # Level 3.2.5 - Access ring
    link_switch_to_switch(net, s26, s27, 3, 3, link1_gbps_18)
    link_switch_to_switch(net, s27, s28, 2, 2, link1_gbps_20)
    link_switch_to_switch(net, s28, s29, 3, 3, link1_gbps_25)
    link_switch_to_switch(net, s29, s26, 2, 2, link1_gbps_23)  # Link to close ring

    # Level 3.3 - Access / Core
    link_switch_to_switch(net, s26, s30, 4, 1, link1_gbps_20)
    link_switch_to_switch(net, s27, s30, 4, 2, link1_gbps_15)
    link_switch_to_switch(net, s28, s31, 4, 1, link1_gbps_25)
    link_switch_to_switch(net, s29, s31, 4, 2, link1_gbps_30)

    # Level 3.4 - Full-mesh Core
    link_switch_to_switch(net, s30, s31, 3, 3, link1_gbps_12)
    link_switch_to_switch(net, s30, s32, 4, 4, link1_gbps_20)
    link_switch_to_switch(net, s30, s33, 5, 5, link1_gbps_18)
    link_switch_to_switch(net, s31, s32, 5, 5, link1_gbps_23)
    link_switch_to_switch(net, s31, s33, 4, 4, link1_gbps_30)
    link_switch_to_switch(net, s32, s33, 3, 3, link1_gbps_15)

    # Level 3.5 - Core / Internet
    link_switch_to_switch(net, s32, s34, 1, 1, link1_gbps_25)
    link_switch_to_switch(net, s33, s34, 1, 2, link1_gbps_30)

    # 4. SOURCES
    # 4.1. CREATING HOSTS
    u001 = simple_create_host(net, 'u001', '10.0.0.1', '00:04:00:00:00:01')
    u002 = simple_create_host(net, 'u002', '10.0.0.2', '00:04:00:00:00:02')
    u003 = simple_create_host(net, 'u003', '10.0.0.3', '00:04:00:00:00:03')
    u004 = simple_create_host(net, 'u004', '10.0.0.4', '00:04:00:00:00:04')
    u005 = simple_create_host(net, 'u005', '10.0.0.5', '00:04:00:00:00:05')
    u006 = simple_create_host(net, 'u006', '10.0.0.6', '00:04:00:00:00:06')
    u007 = simple_create_host(net, 'u007', '10.0.0.7', '00:04:00:00:00:07')
    u008 = simple_create_host(net, 'u008', '10.0.0.8', '00:04:00:00:00:08')
    u009 = simple_create_host(net, 'u009', '10.0.0.9', '00:04:00:00:00:09')
    u010 = simple_create_host(net, 'u010', '10.0.0.10', '00:04:00:00:00:10')
    u011 = simple_create_host(net, 'u011', '10.0.0.11', '00:04:00:00:00:11')
    u012 = simple_create_host(net, 'u012', '10.0.0.12', '00:04:00:00:00:12')
    u013 = simple_create_host(net, 'u013', '10.0.0.13', '00:04:00:00:00:13')
    u014 = simple_create_host(net, 'u014', '10.0.0.14', '00:04:00:00:00:14')
    u015 = simple_create_host(net, 'u015', '10.0.0.15', '00:04:00:00:00:15')
    u016 = simple_create_host(net, 'u016', '10.0.0.16', '00:04:00:00:00:16')
    u017 = simple_create_host(net, 'u017', '10.0.0.17', '00:04:00:00:00:17')
    u018 = simple_create_host(net, 'u018', '10.0.0.18', '00:04:00:00:00:18')
    u019 = simple_create_host(net, 'u019', '10.0.0.19', '00:04:00:00:00:19')
    u020 = simple_create_host(net, 'u020', '10.0.0.20', '00:04:00:00:00:20')
    u021 = simple_create_host(net, 'u021', '10.0.0.21', '00:04:00:00:00:21')
    u022 = simple_create_host(net, 'u022', '10.0.0.22', '00:04:00:00:00:22')
    u023 = simple_create_host(net, 'u023', '10.0.0.23', '00:04:00:00:00:23')
    u024 = simple_create_host(net, 'u024', '10.0.0.24', '00:04:00:00:00:24')
    u025 = simple_create_host(net, 'u025', '10.0.0.25', '00:04:00:00:00:25')
    u026 = simple_create_host(net, 'u026', '10.0.0.26', '00:04:00:00:00:26')
    u027 = simple_create_host(net, 'u027', '10.0.0.27', '00:04:00:00:00:27')
    u028 = simple_create_host(net, 'u028', '10.0.0.28', '00:04:00:00:00:28')
    u029 = simple_create_host(net, 'u029', '10.0.0.29', '00:04:00:00:00:29')
    u030 = simple_create_host(net, 'u030', '10.0.0.30', '00:04:00:00:00:30')
    u031 = simple_create_host(net, 'u031', '10.0.0.31', '00:04:00:00:00:31')
    u032 = simple_create_host(net, 'u032', '10.0.0.32', '00:04:00:00:00:32')
    u033 = simple_create_host(net, 'u033', '10.0.0.33', '00:04:00:00:00:33')
    u034 = simple_create_host(net, 'u034', '10.0.0.34', '00:04:00:00:00:34')
    u035 = simple_create_host(net, 'u035', '10.0.0.35', '00:04:00:00:00:35')
    u036 = simple_create_host(net, 'u036', '10.0.0.36', '00:04:00:00:00:36')
    u037 = simple_create_host(net, 'u037', '10.0.0.37', '00:04:00:00:00:37')
    u038 = simple_create_host(net, 'u038', '10.0.0.38', '00:04:00:00:00:38')
    u039 = simple_create_host(net, 'u039', '10.0.0.39', '00:04:00:00:00:39')
    u040 = simple_create_host(net, 'u040', '10.0.0.40', '00:04:00:00:00:40')
    u041 = simple_create_host(net, 'u041', '10.0.0.41', '00:04:00:00:00:41')
    u042 = simple_create_host(net, 'u042', '10.0.0.42', '00:04:00:00:00:42')
    u043 = simple_create_host(net, 'u043', '10.0.0.43', '00:04:00:00:00:43')
    u044 = simple_create_host(net, 'u044', '10.0.0.44', '00:04:00:00:00:44')
    u045 = simple_create_host(net, 'u045', '10.0.0.45', '00:04:00:00:00:45')
    u046 = simple_create_host(net, 'u046', '10.0.0.46', '00:04:00:00:00:46')
    u047 = simple_create_host(net, 'u047', '10.0.0.47', '00:04:00:00:00:47')
    u048 = simple_create_host(net, 'u048', '10.0.0.48', '00:04:00:00:00:48')
    u049 = simple_create_host(net, 'u049', '10.0.0.49', '00:04:00:00:00:49')
    u050 = simple_create_host(net, 'u050', '10.0.0.50', '00:04:00:00:00:50')
    u051 = simple_create_host(net, 'u051', '10.0.0.51', '00:04:00:00:00:51')
    u052 = simple_create_host(net, 'u052', '10.0.0.52', '00:04:00:00:00:52')
    u053 = simple_create_host(net, 'u053', '10.0.0.53', '00:04:00:00:00:53')
    u054 = simple_create_host(net, 'u054', '10.0.0.54', '00:04:00:00:00:54')
    u055 = simple_create_host(net, 'u055', '10.0.0.55', '00:04:00:00:00:55')
    u056 = simple_create_host(net, 'u056', '10.0.0.56', '00:04:00:00:00:56')
    u057 = simple_create_host(net, 'u057', '10.0.0.57', '00:04:00:00:00:57')
    u058 = simple_create_host(net, 'u058', '10.0.0.58', '00:04:00:00:00:58')
    u059 = simple_create_host(net, 'u059', '10.0.0.59', '00:04:00:00:00:59')
    u060 = simple_create_host(net, 'u060', '10.0.0.60', '00:04:00:00:00:60')
    u061 = simple_create_host(net, 'u061', '10.0.0.61', '00:04:00:00:00:61')
    u062 = simple_create_host(net, 'u062', '10.0.0.62', '00:04:00:00:00:62')
    u063 = simple_create_host(net, 'u063', '10.0.0.63', '00:04:00:00:00:63')
    u064 = simple_create_host(net, 'u064', '10.0.0.64', '00:04:00:00:00:64')
    u065 = simple_create_host(net, 'u065', '10.0.0.65', '00:04:00:00:00:65')
    u066 = simple_create_host(net, 'u066', '10.0.0.66', '00:04:00:00:00:66')
    u067 = simple_create_host(net, 'u067', '10.0.0.67', '00:04:00:00:00:67')
    u068 = simple_create_host(net, 'u068', '10.0.0.68', '00:04:00:00:00:68')
    u069 = simple_create_host(net, 'u069', '10.0.0.69', '00:04:00:00:00:69')
    u070 = simple_create_host(net, 'u070', '10.0.0.70', '00:04:00:00:00:70')
    u071 = simple_create_host(net, 'u071', '10.0.0.71', '00:04:00:00:00:71')
    u072 = simple_create_host(net, 'u072', '10.0.0.72', '00:04:00:00:00:72')
    u073 = simple_create_host(net, 'u073', '10.0.0.73', '00:04:00:00:00:73')
    u074 = simple_create_host(net, 'u074', '10.0.0.74', '00:04:00:00:00:74')
    u075 = simple_create_host(net, 'u075', '10.0.0.75', '00:04:00:00:00:75')
    u076 = simple_create_host(net, 'u076', '10.0.0.76', '00:04:00:00:00:76')
    u077 = simple_create_host(net, 'u077', '10.0.0.77', '00:04:00:00:00:77')
    u078 = simple_create_host(net, 'u078', '10.0.0.78', '00:04:00:00:00:78')
    u079 = simple_create_host(net, 'u079', '10.0.0.79', '00:04:00:00:00:79')
    u080 = simple_create_host(net, 'u080', '10.0.0.80', '00:04:00:00:00:80')
    u081 = simple_create_host(net, 'u081', '10.0.0.81', '00:04:00:00:00:81')
    u082 = simple_create_host(net, 'u082', '10.0.0.82', '00:04:00:00:00:82')
    u083 = simple_create_host(net, 'u083', '10.0.0.83', '00:04:00:00:00:83')
    u084 = simple_create_host(net, 'u084', '10.0.0.84', '00:04:00:00:00:84')
    u085 = simple_create_host(net, 'u085', '10.0.0.85', '00:04:00:00:00:85')
    u086 = simple_create_host(net, 'u086', '10.0.0.86', '00:04:00:00:00:86')
    u087 = simple_create_host(net, 'u087', '10.0.0.87', '00:04:00:00:00:87')
    u088 = simple_create_host(net, 'u088', '10.0.0.88', '00:04:00:00:00:88')
    u089 = simple_create_host(net, 'u089', '10.0.0.89', '00:04:00:00:00:89')
    u090 = simple_create_host(net, 'u090', '10.0.0.90', '00:04:00:00:00:90')
    u091 = simple_create_host(net, 'u091', '10.0.0.91', '00:04:00:00:00:91')
    u092 = simple_create_host(net, 'u092', '10.0.0.92', '00:04:00:00:00:92')
    u093 = simple_create_host(net, 'u093', '10.0.0.93', '00:04:00:00:00:93')
    u094 = simple_create_host(net, 'u094', '10.0.0.94', '00:04:00:00:00:94')
    u095 = simple_create_host(net, 'u095', '10.0.0.95', '00:04:00:00:00:95')
    u096 = simple_create_host(net, 'u096', '10.0.0.96', '00:04:00:00:00:96')
    u097 = simple_create_host(net, 'u097', '10.0.0.97', '00:04:00:00:00:97')
    u098 = simple_create_host(net, 'u098', '10.0.0.98', '00:04:00:00:00:98')
    u099 = simple_create_host(net, 'u099', '10.0.0.99', '00:04:00:00:00:99')
    u100 = simple_create_host(net, 'u100', '10.0.0.100', '00:04:00:00:01:00')
    u101 = simple_create_host(net, 'u101', '10.0.0.101', '00:04:00:00:01:01')
    u102 = simple_create_host(net, 'u102', '10.0.0.102', '00:04:00:00:01:02')
    u103 = simple_create_host(net, 'u103', '10.0.0.103', '00:04:00:00:01:03')
    u104 = simple_create_host(net, 'u104', '10.0.0.104', '00:04:00:00:01:04')
    u105 = simple_create_host(net, 'u105', '10.0.0.105', '00:04:00:00:01:05')
    u106 = simple_create_host(net, 'u106', '10.0.0.106', '00:04:00:00:01:06')
    u107 = simple_create_host(net, 'u107', '10.0.0.107', '00:04:00:00:01:07')
    u108 = simple_create_host(net, 'u108', '10.0.0.108', '00:04:00:00:01:08')
    u109 = simple_create_host(net, 'u109', '10.0.0.109', '00:04:00:00:01:09')
    u110 = simple_create_host(net, 'u110', '10.0.0.110', '00:04:00:00:01:10')
    u111 = simple_create_host(net, 'u111', '10.0.0.111', '00:04:00:00:01:11')
    u112 = simple_create_host(net, 'u112', '10.0.0.112', '00:04:00:00:01:12')
    u113 = simple_create_host(net, 'u113', '10.0.0.113', '00:04:00:00:01:13')
    u114 = simple_create_host(net, 'u114', '10.0.0.114', '00:04:00:00:01:14')
    u115 = simple_create_host(net, 'u115', '10.0.0.115', '00:04:00:00:01:15')
    u116 = simple_create_host(net, 'u116', '10.0.0.116', '00:04:00:00:01:16')
    u117 = simple_create_host(net, 'u117', '10.0.0.117', '00:04:00:00:01:17')
    u118 = simple_create_host(net, 'u118', '10.0.0.118', '00:04:00:00:01:18')
    u119 = simple_create_host(net, 'u119', '10.0.0.119', '00:04:00:00:01:19')
    u120 = simple_create_host(net, 'u120', '10.0.0.120', '00:04:00:00:01:20')
    u121 = simple_create_host(net, 'u121', '10.0.0.121', '00:04:00:00:01:21')
    u122 = simple_create_host(net, 'u122', '10.0.0.122', '00:04:00:00:01:22')
    u123 = simple_create_host(net, 'u123', '10.0.0.123', '00:04:00:00:01:23')
    u124 = simple_create_host(net, 'u124', '10.0.0.124', '00:04:00:00:01:24')
    u125 = simple_create_host(net, 'u125', '10.0.0.125', '00:04:00:00:01:25')
    u126 = simple_create_host(net, 'u126', '10.0.0.126', '00:04:00:00:01:26')
    u127 = simple_create_host(net, 'u127', '10.0.0.127', '00:04:00:00:01:27')
    u128 = simple_create_host(net, 'u128', '10.0.0.128', '00:04:00:00:01:28')
    u129 = simple_create_host(net, 'u129', '10.0.0.129', '00:04:00:00:01:29')
    u130 = simple_create_host(net, 'u130', '10.0.0.130', '00:04:00:00:01:30')
    u131 = simple_create_host(net, 'u131', '10.0.0.131', '00:04:00:00:01:31')
    u132 = simple_create_host(net, 'u132', '10.0.0.132', '00:04:00:00:01:32')
    u133 = simple_create_host(net, 'u133', '10.0.0.133', '00:04:00:00:01:33')
    u134 = simple_create_host(net, 'u134', '10.0.0.134', '00:04:00:00:01:34')
    u135 = simple_create_host(net, 'u135', '10.0.0.135', '00:04:00:00:01:35')
    u136 = simple_create_host(net, 'u136', '10.0.0.136', '00:04:00:00:01:36')
    u137 = simple_create_host(net, 'u137', '10.0.0.137', '00:04:00:00:01:37')
    u138 = simple_create_host(net, 'u138', '10.0.0.138', '00:04:00:00:01:38')
    u139 = simple_create_host(net, 'u139', '10.0.0.139', '00:04:00:00:01:39')
    u140 = simple_create_host(net, 'u140', '10.0.0.140', '00:04:00:00:01:40')
    u141 = simple_create_host(net, 'u141', '10.0.0.141', '00:04:00:00:01:41')
    u142 = simple_create_host(net, 'u142', '10.0.0.142', '00:04:00:00:01:42')
    u143 = simple_create_host(net, 'u143', '10.0.0.143', '00:04:00:00:01:43')
    u144 = simple_create_host(net, 'u144', '10.0.0.144', '00:04:00:00:01:44')
    u145 = simple_create_host(net, 'u145', '10.0.0.145', '00:04:00:00:01:45')
    u146 = simple_create_host(net, 'u146', '10.0.0.146', '00:04:00:00:01:46')
    u147 = simple_create_host(net, 'u147', '10.0.0.147', '00:04:00:00:01:47')
    u148 = simple_create_host(net, 'u148', '10.0.0.148', '00:04:00:00:01:48')
    u149 = simple_create_host(net, 'u149', '10.0.0.149', '00:04:00:00:01:49')
    u150 = simple_create_host(net, 'u150', '10.0.0.150', '00:04:00:00:01:50')
    u151 = simple_create_host(net, 'u151', '10.0.0.151', '00:04:00:00:01:51')
    u152 = simple_create_host(net, 'u152', '10.0.0.152', '00:04:00:00:01:52')
    u153 = simple_create_host(net, 'u153', '10.0.0.153', '00:04:00:00:01:53')
    u154 = simple_create_host(net, 'u154', '10.0.0.154', '00:04:00:00:01:54')
    u155 = simple_create_host(net, 'u155', '10.0.0.155', '00:04:00:00:01:55')
    u156 = simple_create_host(net, 'u156', '10.0.0.156', '00:04:00:00:01:56')
    u157 = simple_create_host(net, 'u157', '10.0.0.157', '00:04:00:00:01:57')
    u158 = simple_create_host(net, 'u158', '10.0.0.158', '00:04:00:00:01:58')
    u159 = simple_create_host(net, 'u159', '10.0.0.159', '00:04:00:00:01:59')
    u160 = simple_create_host(net, 'u160', '10.0.0.160', '00:04:00:00:01:60')
    u161 = simple_create_host(net, 'u161', '10.0.0.161', '00:04:00:00:01:61')
    u162 = simple_create_host(net, 'u162', '10.0.0.162', '00:04:00:00:01:62')
    u163 = simple_create_host(net, 'u163', '10.0.0.163', '00:04:00:00:01:63')
    u164 = simple_create_host(net, 'u164', '10.0.0.164', '00:04:00:00:01:64')
    u165 = simple_create_host(net, 'u165', '10.0.0.165', '00:04:00:00:01:65')
    u166 = simple_create_host(net, 'u166', '10.0.0.166', '00:04:00:00:01:66')
    u167 = simple_create_host(net, 'u167', '10.0.0.167', '00:04:00:00:01:67')
    u168 = simple_create_host(net, 'u168', '10.0.0.168', '00:04:00:00:01:68')
    u169 = simple_create_host(net, 'u169', '10.0.0.169', '00:04:00:00:01:69')
    u170 = simple_create_host(net, 'u170', '10.0.0.170', '00:04:00:00:01:70')
    u171 = simple_create_host(net, 'u171', '10.0.0.171', '00:04:00:00:01:71')
    u172 = simple_create_host(net, 'u172', '10.0.0.172', '00:04:00:00:01:72')
    u173 = simple_create_host(net, 'u173', '10.0.0.173', '00:04:00:00:01:73')
    u174 = simple_create_host(net, 'u174', '10.0.0.174', '00:04:00:00:01:74')
    u175 = simple_create_host(net, 'u175', '10.0.0.175', '00:04:00:00:01:75')
    u176 = simple_create_host(net, 'u176', '10.0.0.176', '00:04:00:00:01:76')
    u177 = simple_create_host(net, 'u177', '10.0.0.177', '00:04:00:00:01:77')
    u178 = simple_create_host(net, 'u178', '10.0.0.178', '00:04:00:00:01:78')
    u179 = simple_create_host(net, 'u179', '10.0.0.179', '00:04:00:00:01:79')
    u180 = simple_create_host(net, 'u180', '10.0.0.180', '00:04:00:00:01:80')
    u181 = simple_create_host(net, 'u181', '10.0.0.181', '00:04:00:00:01:81')
    u182 = simple_create_host(net, 'u182', '10.0.0.182', '00:04:00:00:01:82')
    u183 = simple_create_host(net, 'u183', '10.0.0.183', '00:04:00:00:01:83')
    u184 = simple_create_host(net, 'u184', '10.0.0.184', '00:04:00:00:01:84')
    u185 = simple_create_host(net, 'u185', '10.0.0.185', '00:04:00:00:01:85')
    u186 = simple_create_host(net, 'u186', '10.0.0.186', '00:04:00:00:01:86')
    u187 = simple_create_host(net, 'u187', '10.0.0.187', '00:04:00:00:01:87')
    u188 = simple_create_host(net, 'u188', '10.0.0.188', '00:04:00:00:01:88')
    u189 = simple_create_host(net, 'u189', '10.0.0.189', '00:04:00:00:01:89')
    u190 = simple_create_host(net, 'u190', '10.0.0.190', '00:04:00:00:01:90')
    u191 = simple_create_host(net, 'u191', '10.0.0.191', '00:04:00:00:01:91')
    u192 = simple_create_host(net, 'u192', '10.0.0.192', '00:04:00:00:01:92')
    u193 = simple_create_host(net, 'u193', '10.0.0.193', '00:04:00:00:01:93')
    u194 = simple_create_host(net, 'u194', '10.0.0.194', '00:04:00:00:01:94')
    u195 = simple_create_host(net, 'u195', '10.0.0.195', '00:04:00:00:01:95')
    u196 = simple_create_host(net, 'u196', '10.0.0.196', '00:04:00:00:01:96')
    u197 = simple_create_host(net, 'u197', '10.0.0.197', '00:04:00:00:01:97')
    u198 = simple_create_host(net, 'u198', '10.0.0.198', '00:04:00:00:01:98')
    u199 = simple_create_host(net, 'u199', '10.0.0.199', '00:04:00:00:01:99')
    u200 = simple_create_host(net, 'u200', '10.0.0.200', '00:04:00:00:02:00')

    # 4.2. CREATING LINKS
    link_switch_to_host(net, u001, s1, 0, 1, False, linknodeg)
    link_switch_to_host(net, u002, s1, 0, 2, False, linknodeg)
    link_switch_to_host(net, u003, s1, 0, 3, False, linknodeg)
    link_switch_to_host(net, u004, s1, 0, 4, False, linknodeg)
    link_switch_to_host(net, u005, s1, 0, 5, False, linknodeg)
    link_switch_to_host(net, u006, s1, 0, 6, False, linknodeg)
    link_switch_to_host(net, u007, s1, 0, 7, False, linknodeg)
    link_switch_to_host(net, u008, s1, 0, 8, False, linknodeg)
    link_switch_to_host(net, u009, s1, 0, 9, False, linknodeg)
    link_switch_to_host(net, u010, s1, 0, 10, False, linknodeg)
    link_switch_to_host(net, u011, s2, 0, 1, False, linknodeg)
    link_switch_to_host(net, u012, s2, 0, 2, False, linknodeg)
    link_switch_to_host(net, u013, s2, 0, 3, False, linknodeg)
    link_switch_to_host(net, u014, s2, 0, 4, False, linknodeg)
    link_switch_to_host(net, u015, s2, 0, 5, False, linknodeg)
    link_switch_to_host(net, u016, s2, 0, 6, False, linknodeg)
    link_switch_to_host(net, u017, s2, 0, 7, False, linknodeg)
    link_switch_to_host(net, u018, s2, 0, 8, False, linknodeg)
    link_switch_to_host(net, u019, s2, 0, 9, False, linknodeg)
    link_switch_to_host(net, u020, s2, 0, 10, False, linknodeg)
    link_switch_to_host(net, u021, s3, 0, 1, False, linknodeg)
    link_switch_to_host(net, u022, s3, 0, 2, False, linknodeg)
    link_switch_to_host(net, u023, s3, 0, 3, False, linknodeg)
    link_switch_to_host(net, u024, s3, 0, 4, False, linknodeg)
    link_switch_to_host(net, u025, s3, 0, 5, False, linknodeg)
    link_switch_to_host(net, u026, s3, 0, 6, False, linknodeg)
    link_switch_to_host(net, u027, s3, 0, 7, False, linknodeg)
    link_switch_to_host(net, u028, s3, 0, 8, False, linknodeg)
    link_switch_to_host(net, u029, s3, 0, 9, False, linknodeg)
    link_switch_to_host(net, u030, s3, 0, 10, False, linknodeg)
    link_switch_to_host(net, u031, s4, 0, 1, False, linknodeg)
    link_switch_to_host(net, u032, s4, 0, 2, False, linknodeg)
    link_switch_to_host(net, u033, s4, 0, 3, False, linknodeg)
    link_switch_to_host(net, u034, s4, 0, 4, False, linknodeg)
    link_switch_to_host(net, u035, s4, 0, 5, False, linknodeg)
    link_switch_to_host(net, u036, s4, 0, 6, False, linknodeg)
    link_switch_to_host(net, u037, s4, 0, 7, False, linknodeg)
    link_switch_to_host(net, u038, s4, 0, 8, False, linknodeg)
    link_switch_to_host(net, u039, s4, 0, 9, False, linknodeg)
    link_switch_to_host(net, u040, s4, 0, 10, False, linknodeg)
    link_switch_to_host(net, u041, s5, 0, 1, False, linknodeg)
    link_switch_to_host(net, u042, s5, 0, 2, False, linknodeg)
    link_switch_to_host(net, u043, s5, 0, 3, False, linknodeg)
    link_switch_to_host(net, u044, s5, 0, 4, False, linknodeg)
    link_switch_to_host(net, u045, s5, 0, 5, False, linknodeg)
    link_switch_to_host(net, u046, s5, 0, 6, False, linknodeg)
    link_switch_to_host(net, u047, s5, 0, 7, False, linknodeg)
    link_switch_to_host(net, u048, s5, 0, 8, False, linknodeg)
    link_switch_to_host(net, u049, s5, 0, 9, False, linknodeg)
    link_switch_to_host(net, u050, s5, 0, 10, False, linknodeg)
    link_switch_to_host(net, u051, s6, 0, 1, False, linknodeg)
    link_switch_to_host(net, u052, s6, 0, 2, False, linknodeg)
    link_switch_to_host(net, u053, s6, 0, 3, False, linknodeg)
    link_switch_to_host(net, u054, s6, 0, 4, False, linknodeg)
    link_switch_to_host(net, u055, s6, 0, 5, False, linknodeg)
    link_switch_to_host(net, u056, s6, 0, 6, False, linknodeg)
    link_switch_to_host(net, u057, s6, 0, 7, False, linknodeg)
    link_switch_to_host(net, u058, s6, 0, 8, False, linknodeg)
    link_switch_to_host(net, u059, s6, 0, 9, False, linknodeg)
    link_switch_to_host(net, u060, s6, 0, 10, False, linknodeg)
    link_switch_to_host(net, u061, s7, 0, 1, False, linknodeg)
    link_switch_to_host(net, u062, s7, 0, 2, False, linknodeg)
    link_switch_to_host(net, u063, s7, 0, 3, False, linknodeg)
    link_switch_to_host(net, u064, s7, 0, 4, False, linknodeg)
    link_switch_to_host(net, u065, s7, 0, 5, False, linknodeg)
    link_switch_to_host(net, u066, s7, 0, 6, False, linknodeg)
    link_switch_to_host(net, u067, s7, 0, 7, False, linknodeg)
    link_switch_to_host(net, u068, s7, 0, 8, False, linknodeg)
    link_switch_to_host(net, u069, s7, 0, 9, False, linknodeg)
    link_switch_to_host(net, u070, s7, 0, 10, False, linknodeg)
    link_switch_to_host(net, u071, s8, 0, 1, False, linknodeg)
    link_switch_to_host(net, u072, s8, 0, 2, False, linknodeg)
    link_switch_to_host(net, u073, s8, 0, 3, False, linknodeg)
    link_switch_to_host(net, u074, s8, 0, 4, False, linknodeg)
    link_switch_to_host(net, u075, s8, 0, 5, False, linknodeg)
    link_switch_to_host(net, u076, s8, 0, 6, False, linknodeg)
    link_switch_to_host(net, u077, s8, 0, 7, False, linknodeg)
    link_switch_to_host(net, u078, s8, 0, 8, False, linknodeg)
    link_switch_to_host(net, u079, s8, 0, 9, False, linknodeg)
    link_switch_to_host(net, u080, s8, 0, 10, False, linknodeg)
    link_switch_to_host(net, u081, s9, 0, 1, False, linknodeg)
    link_switch_to_host(net, u082, s9, 0, 2, False, linknodeg)
    link_switch_to_host(net, u083, s9, 0, 3, False, linknodeg)
    link_switch_to_host(net, u084, s9, 0, 4, False, linknodeg)
    link_switch_to_host(net, u085, s9, 0, 5, False, linknodeg)
    link_switch_to_host(net, u086, s9, 0, 6, False, linknodeg)
    link_switch_to_host(net, u087, s9, 0, 7, False, linknodeg)
    link_switch_to_host(net, u088, s9, 0, 8, False, linknodeg)
    link_switch_to_host(net, u089, s9, 0, 9, False, linknodeg)
    link_switch_to_host(net, u090, s9, 0, 10, False, linknodeg)
    link_switch_to_host(net, u091, s10, 0, 1, False, linknodeg)
    link_switch_to_host(net, u092, s10, 0, 2, False, linknodeg)
    link_switch_to_host(net, u093, s10, 0, 3, False, linknodeg)
    link_switch_to_host(net, u094, s10, 0, 4, False, linknodeg)
    link_switch_to_host(net, u095, s10, 0, 5, False, linknodeg)
    link_switch_to_host(net, u096, s10, 0, 6, False, linknodeg)
    link_switch_to_host(net, u097, s10, 0, 7, False, linknodeg)
    link_switch_to_host(net, u098, s10, 0, 8, False, linknodeg)
    link_switch_to_host(net, u099, s10, 0, 9, False, linknodeg)
    link_switch_to_host(net, u100, s10, 0, 10, False, linknodeg)
    link_switch_to_host(net, u101, s11, 0, 1, False, linknodeg)
    link_switch_to_host(net, u102, s11, 0, 2, False, linknodeg)
    link_switch_to_host(net, u103, s11, 0, 3, False, linknodeg)
    link_switch_to_host(net, u104, s11, 0, 4, False, linknodeg)
    link_switch_to_host(net, u105, s11, 0, 5, False, linknodeg)
    link_switch_to_host(net, u106, s11, 0, 6, False, linknodeg)
    link_switch_to_host(net, u107, s11, 0, 7, False, linknodeg)
    link_switch_to_host(net, u108, s11, 0, 8, False, linknodeg)
    link_switch_to_host(net, u109, s11, 0, 9, False, linknodeg)
    link_switch_to_host(net, u110, s11, 0, 10, False, linknodeg)
    link_switch_to_host(net, u111, s12, 0, 1, False, linknodeg)
    link_switch_to_host(net, u112, s12, 0, 2, False, linknodeg)
    link_switch_to_host(net, u113, s12, 0, 3, False, linknodeg)
    link_switch_to_host(net, u114, s12, 0, 4, False, linknodeg)
    link_switch_to_host(net, u115, s12, 0, 5, False, linknodeg)
    link_switch_to_host(net, u116, s12, 0, 6, False, linknodeg)
    link_switch_to_host(net, u117, s12, 0, 7, False, linknodeg)
    link_switch_to_host(net, u118, s12, 0, 8, False, linknodeg)
    link_switch_to_host(net, u119, s12, 0, 9, False, linknodeg)
    link_switch_to_host(net, u120, s12, 0, 10, False, linknodeg)
    link_switch_to_host(net, u121, s13, 0, 1, False, linknodeg)
    link_switch_to_host(net, u122, s13, 0, 2, False, linknodeg)
    link_switch_to_host(net, u123, s13, 0, 3, False, linknodeg)
    link_switch_to_host(net, u124, s13, 0, 4, False, linknodeg)
    link_switch_to_host(net, u125, s13, 0, 5, False, linknodeg)
    link_switch_to_host(net, u126, s13, 0, 6, False, linknodeg)
    link_switch_to_host(net, u127, s13, 0, 7, False, linknodeg)
    link_switch_to_host(net, u128, s13, 0, 8, False, linknodeg)
    link_switch_to_host(net, u129, s13, 0, 9, False, linknodeg)
    link_switch_to_host(net, u130, s13, 0, 10, False, linknodeg)
    link_switch_to_host(net, u131, s14, 0, 1, False, linknodeg)
    link_switch_to_host(net, u132, s14, 0, 2, False, linknodeg)
    link_switch_to_host(net, u133, s14, 0, 3, False, linknodeg)
    link_switch_to_host(net, u134, s14, 0, 4, False, linknodeg)
    link_switch_to_host(net, u135, s14, 0, 5, False, linknodeg)
    link_switch_to_host(net, u136, s14, 0, 6, False, linknodeg)
    link_switch_to_host(net, u137, s14, 0, 7, False, linknodeg)
    link_switch_to_host(net, u138, s14, 0, 8, False, linknodeg)
    link_switch_to_host(net, u139, s14, 0, 9, False, linknodeg)
    link_switch_to_host(net, u140, s14, 0, 10, False, linknodeg)
    link_switch_to_host(net, u141, s15, 0, 1, False, linknodeg)
    link_switch_to_host(net, u142, s15, 0, 2, False, linknodeg)
    link_switch_to_host(net, u143, s15, 0, 3, False, linknodeg)
    link_switch_to_host(net, u144, s15, 0, 4, False, linknodeg)
    link_switch_to_host(net, u145, s15, 0, 5, False, linknodeg)
    link_switch_to_host(net, u146, s15, 0, 6, False, linknodeg)
    link_switch_to_host(net, u147, s15, 0, 7, False, linknodeg)
    link_switch_to_host(net, u148, s15, 0, 8, False, linknodeg)
    link_switch_to_host(net, u149, s15, 0, 9, False, linknodeg)
    link_switch_to_host(net, u150, s15, 0, 10, False, linknodeg)
    link_switch_to_host(net, u151, s16, 0, 1, False, linknodeg)
    link_switch_to_host(net, u152, s16, 0, 2, False, linknodeg)
    link_switch_to_host(net, u153, s16, 0, 3, False, linknodeg)
    link_switch_to_host(net, u154, s16, 0, 4, False, linknodeg)
    link_switch_to_host(net, u155, s16, 0, 5, False, linknodeg)
    link_switch_to_host(net, u156, s16, 0, 6, False, linknodeg)
    link_switch_to_host(net, u157, s16, 0, 7, False, linknodeg)
    link_switch_to_host(net, u158, s16, 0, 8, False, linknodeg)
    link_switch_to_host(net, u159, s16, 0, 9, False, linknodeg)
    link_switch_to_host(net, u160, s16, 0, 10, False, linknodeg)
    link_switch_to_host(net, u161, s17, 0, 1, False, linknodeg)
    link_switch_to_host(net, u162, s17, 0, 2, False, linknodeg)
    link_switch_to_host(net, u163, s17, 0, 3, False, linknodeg)
    link_switch_to_host(net, u164, s17, 0, 4, False, linknodeg)
    link_switch_to_host(net, u165, s17, 0, 5, False, linknodeg)
    link_switch_to_host(net, u166, s17, 0, 6, False, linknodeg)
    link_switch_to_host(net, u167, s17, 0, 7, False, linknodeg)
    link_switch_to_host(net, u168, s17, 0, 8, False, linknodeg)
    link_switch_to_host(net, u169, s17, 0, 9, False, linknodeg)
    link_switch_to_host(net, u170, s17, 0, 10, False, linknodeg)
    link_switch_to_host(net, u171, s18, 0, 1, False, linknodeg)
    link_switch_to_host(net, u172, s18, 0, 2, False, linknodeg)
    link_switch_to_host(net, u173, s18, 0, 3, False, linknodeg)
    link_switch_to_host(net, u174, s18, 0, 4, False, linknodeg)
    link_switch_to_host(net, u175, s18, 0, 5, False, linknodeg)
    link_switch_to_host(net, u176, s18, 0, 6, False, linknodeg)
    link_switch_to_host(net, u177, s18, 0, 7, False, linknodeg)
    link_switch_to_host(net, u178, s18, 0, 8, False, linknodeg)
    link_switch_to_host(net, u179, s18, 0, 9, False, linknodeg)
    link_switch_to_host(net, u180, s18, 0, 10, False, linknodeg)
    link_switch_to_host(net, u181, s19, 0, 1, False, linknodeg)
    link_switch_to_host(net, u182, s19, 0, 2, False, linknodeg)
    link_switch_to_host(net, u183, s19, 0, 3, False, linknodeg)
    link_switch_to_host(net, u184, s19, 0, 4, False, linknodeg)
    link_switch_to_host(net, u185, s19, 0, 5, False, linknodeg)
    link_switch_to_host(net, u186, s19, 0, 6, False, linknodeg)
    link_switch_to_host(net, u187, s19, 0, 7, False, linknodeg)
    link_switch_to_host(net, u188, s19, 0, 8, False, linknodeg)
    link_switch_to_host(net, u189, s19, 0, 9, False, linknodeg)
    link_switch_to_host(net, u190, s19, 0, 10, False, linknodeg)
    link_switch_to_host(net, u191, s20, 0, 1, False, linknodeg)
    link_switch_to_host(net, u192, s20, 0, 2, False, linknodeg)
    link_switch_to_host(net, u193, s20, 0, 3, False, linknodeg)
    link_switch_to_host(net, u194, s20, 0, 4, False, linknodeg)
    link_switch_to_host(net, u195, s20, 0, 5, False, linknodeg)
    link_switch_to_host(net, u196, s20, 0, 6, False, linknodeg)
    link_switch_to_host(net, u197, s20, 0, 7, False, linknodeg)
    link_switch_to_host(net, u198, s20, 0, 8, False, linknodeg)
    link_switch_to_host(net, u199, s20, 0, 9, False, linknodeg)
    link_switch_to_host(net, u200, s20, 0, 10, False, linknodeg)

    net.start()
    deploy_flow_rules()
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
