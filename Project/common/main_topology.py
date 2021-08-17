#!/usr/bin/env python3.9

from Project.common.topology import *

USERS_PER_RAN = 10

EDGE_RANGE = range(1, 201)
RAN_RANGE = range(1, 21)
METRO_RANGE = range(21, 26)
AGGREGATION_RANGE = range(26, 30)
CORE_RANGE = range(30, 34)
INTERNET_RANGE = range(34, 35)


# Utils methods
def __create_switches_from_layer__(layer: NetworkLayer, __range: range) -> dict[str]:
    return {name: Switch(name, layer)
            for __i, name in [(__i, f's{__i}') for __i in __range]}


def __create_hosts_from_layer__(prefix: str, layer: NetworkLayer, __range: range) -> dict[str]:
    return {name: Host(name=name, ip_address=f'10.0.0.{(200 + __i):02d}',
                       mac_address=f'00:04:00:00:0F:{__i:02d}',
                       network_layer=layer)
            for __i, name in [(i, f'{prefix}{i}') for i in __range]}


# Defining the Main Topology
MAIN_TOPOLOGY = Topology()

# Adding switches
MAIN_TOPOLOGY.append_switches(__create_switches_from_layer__(NetworkLayer.RAN, RAN_RANGE))
MAIN_TOPOLOGY.append_switches(__create_switches_from_layer__(NetworkLayer.METRO, METRO_RANGE))
MAIN_TOPOLOGY.append_switches(__create_switches_from_layer__(NetworkLayer.AGGREGATION, AGGREGATION_RANGE))
MAIN_TOPOLOGY.append_switches(__create_switches_from_layer__(NetworkLayer.CORE, CORE_RANGE))
MAIN_TOPOLOGY.append_switches(__create_switches_from_layer__(NetworkLayer.INTERNET, INTERNET_RANGE))

# 1.   DESTINATIONS
# 1.1. CREATING HOSTS
MAIN_TOPOLOGY.append_hosts({'cdn1': Host(name='cdn1', ip_address='10.0.0.251', mac_address='00:04:00:00:02:51',
                                         network_layer=NetworkLayer.METRO)})
MAIN_TOPOLOGY.append_hosts({'cdn2': Host(name='cdn2', ip_address='10.0.0.252', mac_address='00:04:00:00:02:52',
                                         network_layer=NetworkLayer.AGGREGATION)})
MAIN_TOPOLOGY.append_hosts({'cdn3': Host(name='cdn3', ip_address='10.0.0.253', mac_address='00:04:00:00:02:53',
                                         network_layer=NetworkLayer.CORE)})
MAIN_TOPOLOGY.append_hosts({'ext1': Host(name='ext1', ip_address='10.0.0.254', mac_address='00:04:00:00:02:54',
                                         network_layer=NetworkLayer.INTERNET)})

# 1.2 CREATING MANAGERS
MAIN_TOPOLOGY.append_hosts({'man1': Host(name='man1', ip_address='10.0.0.241', mac_address='00:04:00:00:02:41',
                                         network_layer=NetworkLayer.CORE)})
MAIN_TOPOLOGY.append_hosts({'man2': Host(name='man2', ip_address='10.0.0.242', mac_address='00:04:00:00:02:42',
                                         network_layer=NetworkLayer.CORE)})
MAIN_TOPOLOGY.append_hosts({'man3': Host(name='man3', ip_address='10.0.0.243', mac_address='00:04:00:00:02:43',
                                         network_layer=NetworkLayer.CORE)})
MAIN_TOPOLOGY.append_hosts({'man4': Host(name='man4', ip_address='10.0.0.244', mac_address='00:04:00:00:02:44',
                                         network_layer=NetworkLayer.CORE)})

# 1.2. CREATING LINKS
MAIN_TOPOLOGY.create_link_switch_host('s25', 99, 'cdn1', 0, LinkTypes.LINK_2_MBPS_0_5.value)
MAIN_TOPOLOGY.create_link_switch_host('s29', 99, 'cdn2', 0, LinkTypes.LINK_20_MBPS_0_5.value)
MAIN_TOPOLOGY.create_link_switch_host('s31', 99, 'cdn3', 0, LinkTypes.LINK_20_MBPS_0_5.value)
MAIN_TOPOLOGY.create_link_switch_host('s34', 99, 'ext1', 0, LinkTypes.LINK_20_MBPS_15.value)

# 1.2. CREATING LINKS
MAIN_TOPOLOGY.create_link_switch_host('s30', 90, 'man1', 0, LinkTypes.LINK_20_MBPS_0_5.value)
MAIN_TOPOLOGY.create_link_switch_host('s31', 90, 'man2', 0, LinkTypes.LINK_20_MBPS_0_5.value)
MAIN_TOPOLOGY.create_link_switch_host('s32', 90, 'man3', 0, LinkTypes.LINK_20_MBPS_0_5.value)
MAIN_TOPOLOGY.create_link_switch_host('s33', 90, 'man4', 0, LinkTypes.LINK_20_MBPS_0_5.value)

# 2.   SWITCH PROCESSING
# 2.1. CREATING HOSTS
# 2.2. CREATING LINKS
MAIN_TOPOLOGY.append_hosts(__create_hosts_from_layer__('r', NetworkLayer.RAN, RAN_RANGE))
for __i in RAN_RANGE:
    MAIN_TOPOLOGY.create_link_switch_host(f's{__i}', 100, f'r{__i}', 0, LinkTypes.LINK_NO_DEGRADATION.value, True)

MAIN_TOPOLOGY.append_hosts(__create_hosts_from_layer__('m', NetworkLayer.METRO, METRO_RANGE))
for __i in METRO_RANGE:
    MAIN_TOPOLOGY.create_link_switch_host(f's{__i}', 100, f'm{__i}', 0, LinkTypes.LINK_NO_DEGRADATION.value, True)

MAIN_TOPOLOGY.append_hosts(__create_hosts_from_layer__('a', NetworkLayer.AGGREGATION, AGGREGATION_RANGE))
for __i in AGGREGATION_RANGE:
    MAIN_TOPOLOGY.create_link_switch_host(f's{__i}', 100, f'a{__i}', 0, LinkTypes.LINK_NO_DEGRADATION.value, True)

MAIN_TOPOLOGY.append_hosts(__create_hosts_from_layer__('c', NetworkLayer.CORE, CORE_RANGE))
for __i in CORE_RANGE:
    MAIN_TOPOLOGY.create_link_switch_host(f's{__i}', 100, f'c{__i}', 0, LinkTypes.LINK_NO_DEGRADATION.value, True)

MAIN_TOPOLOGY.append_hosts(__create_hosts_from_layer__('i', NetworkLayer.INTERNET, INTERNET_RANGE))
for __i in INTERNET_RANGE:
    MAIN_TOPOLOGY.create_link_switch_host(f's{__i}', 100, f'i{__i}', 0, LinkTypes.LINK_NO_DEGRADATION.value, True)

# 3. CREATING LINKS BETWEEN SWITCHES
# Level 3.1 - RAN / Metro
MAIN_TOPOLOGY.create_link_switch_switch('s1', 31, 's21', 1, LinkTypes.LINK_2_MBPS_3.value)
MAIN_TOPOLOGY.create_link_switch_switch('s2', 31, 's21', 2, LinkTypes.LINK_2_MBPS_4.value)
MAIN_TOPOLOGY.create_link_switch_switch('s3', 31, 's21', 3, LinkTypes.LINK_2_MBPS_3.value)
MAIN_TOPOLOGY.create_link_switch_switch('s4', 31, 's21', 4, LinkTypes.LINK_2_MBPS_3_5.value)

MAIN_TOPOLOGY.create_link_switch_switch('s5', 31, 's22', 1, LinkTypes.LINK_2_MBPS_2.value)
MAIN_TOPOLOGY.create_link_switch_switch('s6', 31, 's22', 2, LinkTypes.LINK_2_MBPS_2.value)
MAIN_TOPOLOGY.create_link_switch_switch('s7', 31, 's22', 3, LinkTypes.LINK_2_MBPS_2.value)
MAIN_TOPOLOGY.create_link_switch_switch('s8', 31, 's22', 4, LinkTypes.LINK_2_MBPS_3.value)

MAIN_TOPOLOGY.create_link_switch_switch('s9', 31, 's23', 1, LinkTypes.LINK_2_MBPS_4_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s10', 31, 's23', 2, LinkTypes.LINK_2_MBPS_4.value)
MAIN_TOPOLOGY.create_link_switch_switch('s11', 31, 's23', 3, LinkTypes.LINK_2_MBPS_2.value)
MAIN_TOPOLOGY.create_link_switch_switch('s12', 31, 's23', 4, LinkTypes.LINK_2_MBPS_2_5.value)

MAIN_TOPOLOGY.create_link_switch_switch('s13', 31, 's24', 1, LinkTypes.LINK_2_MBPS_4.value)
MAIN_TOPOLOGY.create_link_switch_switch('s14', 31, 's24', 2, LinkTypes.LINK_2_MBPS_4.value)
MAIN_TOPOLOGY.create_link_switch_switch('s15', 31, 's24', 3, LinkTypes.LINK_2_MBPS_3_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s16', 31, 's24', 4, LinkTypes.LINK_2_MBPS_2.value)

MAIN_TOPOLOGY.create_link_switch_switch('s17', 31, 's25', 1, LinkTypes.LINK_2_MBPS_2.value)
MAIN_TOPOLOGY.create_link_switch_switch('s18', 31, 's25', 2, LinkTypes.LINK_2_MBPS_3.value)
MAIN_TOPOLOGY.create_link_switch_switch('s19', 31, 's25', 3, LinkTypes.LINK_2_MBPS_3_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s20', 31, 's25', 4, LinkTypes.LINK_2_MBPS_2.value)

# Level 3.1.5 - Metro Ring
MAIN_TOPOLOGY.create_link_switch_switch('s21', 5, 's22', 5, LinkTypes.LINK_2_MBPS_4_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s22', 6, 's23', 6, LinkTypes.LINK_2_MBPS_3.value)
MAIN_TOPOLOGY.create_link_switch_switch('s23', 5, 's24', 5, LinkTypes.LINK_2_MBPS_5_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s24', 6, 's25', 6, LinkTypes.LINK_2_MBPS_2_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s25', 5, 's21', 6, LinkTypes.LINK_2_MBPS_5.value)  # Link to close ring

# Level 3.2 - Metro / Access
MAIN_TOPOLOGY.create_link_switch_switch('s22', 7, 's27', 1, LinkTypes.LINK_20_MBPS_10.value)
MAIN_TOPOLOGY.create_link_switch_switch('s23', 7, 's28', 1, LinkTypes.LINK_20_MBPS_15.value)

# Level 3.2.5 - Access ring
MAIN_TOPOLOGY.create_link_switch_switch('s26', 3, 's27', 3, LinkTypes.LINK_20_MBPS_9.value)
MAIN_TOPOLOGY.create_link_switch_switch('s27', 2, 's28', 2, LinkTypes.LINK_20_MBPS_10.value)
MAIN_TOPOLOGY.create_link_switch_switch('s28', 3, 's29', 3, LinkTypes.LINK_20_MBPS_12_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s29', 2, 's26', 2, LinkTypes.LINK_20_MBPS_11_5.value)  # Link to close ring

# Level 3.3 - Access / Core
MAIN_TOPOLOGY.create_link_switch_switch('s26', 4, 's30', 1, LinkTypes.LINK_20_MBPS_10.value)
MAIN_TOPOLOGY.create_link_switch_switch('s27', 4, 's30', 2, LinkTypes.LINK_20_MBPS_7_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s28', 4, 's31', 1, LinkTypes.LINK_20_MBPS_12_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s29', 4, 's31', 2, LinkTypes.LINK_20_MBPS_15.value)

# Level 3.4 - Full-mesh Core
MAIN_TOPOLOGY.create_link_switch_switch('s30', 3, 's31', 3, LinkTypes.LINK_20_MBPS_6.value)
MAIN_TOPOLOGY.create_link_switch_switch('s30', 4, 's32', 4, LinkTypes.LINK_20_MBPS_10.value)
MAIN_TOPOLOGY.create_link_switch_switch('s30', 5, 's33', 5, LinkTypes.LINK_20_MBPS_9.value)
MAIN_TOPOLOGY.create_link_switch_switch('s31', 5, 's32', 5, LinkTypes.LINK_20_MBPS_11_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s31', 4, 's33', 4, LinkTypes.LINK_20_MBPS_15.value)
MAIN_TOPOLOGY.create_link_switch_switch('s32', 3, 's33', 3, LinkTypes.LINK_20_MBPS_7_5.value)

# Level 3.5 - Core / Internet
MAIN_TOPOLOGY.create_link_switch_switch('s32', 1, 's34', 1, LinkTypes.LINK_20_MBPS_12_5.value)
MAIN_TOPOLOGY.create_link_switch_switch('s33', 1, 's34', 2, LinkTypes.LINK_20_MBPS_15.value)

# Create all User Hosts
user_hosts = {name: Host(name=name, ip_address=f'10.0.0.{i}',
                         mac_address=f'00:04:00:00:{divmod(i, 100)[0]:02d}:{divmod(i, 100)[1]:02d}',
                         network_layer=NetworkLayer.EDGE)
              for i, name in [(i, f'u{i:03d}') for i in EDGE_RANGE]}
MAIN_TOPOLOGY.append_hosts(user_hosts)
for i in RAN_RANGE:
    for j in range(1, (USERS_PER_RAN + 1)):
        MAIN_TOPOLOGY.create_link_switch_host(f's{i}', j, f'u{j:03d}', 0)

# user_links = [for name, host in user_hosts]
# print(user_hosts)
# print(MAIN_TOPOLOGY)
# print(ran_switches)
# print(ran_hosts)
