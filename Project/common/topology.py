from abc import ABC
from dataclasses import dataclass, field
from enum import Enum, unique, auto
from typing import Optional


@unique
class NetworkLayer(Enum):
    EDGE = auto(),
    RAN = auto(),
    METRO = auto(),
    AGGREGATION = auto(),
    CORE = auto(),
    INTERNET = auto()

    def __repr__(self):
        return str.lower(self.name)


@dataclass
class Port:
    port_number: int
    port_name: str = field(init=False)

    def __post_init__(self):
        self.port_name = f'eth{self.port_number}'


@dataclass(eq=False)
class NetworkElement(ABC):
    name: str = field(hash=True)
    network_layer: NetworkLayer


@dataclass(eq=False)
class Host(NetworkElement):
    ip_address: str
    mac_address: str
    busy_ports: list[Port] = field(default_factory=list)


@dataclass(eq=False)
class Switch(NetworkElement):
    busy_ports: list[Port] = field(default_factory=list)


@dataclass
class Degradation:
    bandwidth_Mbps: Optional[float] = field(default=None)
    delay_ms: Optional[float] = field(default=None)
    loss: Optional[float] = field(default=None)

    def to_dict(self) -> dict:
        __dict: dict = {}
        if self.bandwidth_Mbps is not None:
            __dict.update({'bw': self.bandwidth_Mbps})
        if self.delay_ms is not None:
            __dict.update({'delay': f'{self.delay_ms}ms'})
        if self.loss is not None:
            __dict.update({'loss': f'{self.delay_ms}ms'})

        return __dict


class LinkTypes(Enum):
    LINK_NO_DEGRADATION = Degradation()
    LINK_2_MBPS_0_5 = Degradation(bandwidth_Mbps=2, delay_ms=0.5)
    LINK_2_MBPS_2 = Degradation(bandwidth_Mbps=2, delay_ms=2)
    LINK_2_MBPS_2_5 = Degradation(bandwidth_Mbps=2, delay_ms=2.5)
    LINK_2_MBPS_3 = Degradation(bandwidth_Mbps=2, delay_ms=3)
    LINK_2_MBPS_3_5 = Degradation(bandwidth_Mbps=2, delay_ms=3.5)
    LINK_2_MBPS_4 = Degradation(bandwidth_Mbps=2, delay_ms=4)
    LINK_2_MBPS_4_5 = Degradation(bandwidth_Mbps=2, delay_ms=4.5)
    LINK_2_MBPS_5 = Degradation(bandwidth_Mbps=2, delay_ms=5)
    LINK_2_MBPS_5_5 = Degradation(bandwidth_Mbps=2, delay_ms=5.5)
    LINK_20_MBPS_0_5 = Degradation(bandwidth_Mbps=20, delay_ms=0.5)
    LINK_20_MBPS_6 = Degradation(bandwidth_Mbps=20, delay_ms=6)
    LINK_20_MBPS_7_5 = Degradation(bandwidth_Mbps=20, delay_ms=7.5)
    LINK_20_MBPS_9 = Degradation(bandwidth_Mbps=20, delay_ms=9)
    LINK_20_MBPS_10 = Degradation(bandwidth_Mbps=20, delay_ms=10)
    LINK_20_MBPS_11_5 = Degradation(bandwidth_Mbps=20, delay_ms=11.5)
    LINK_20_MBPS_12_5 = Degradation(bandwidth_Mbps=20, delay_ms=12.5)
    LINK_20_MBPS_15 = Degradation(bandwidth_Mbps=20, delay_ms=15)


@dataclass
class Link:
    switch: Switch
    switch_port: Port
    network_element: NetworkElement
    element_port: Port
    is_aux: bool
    degradation: Degradation

    def __repr__(self):
        return f'{self.switch.name}:{self.switch_port.port_number}-' \
               f'{self.network_element.name}:{self.element_port.port_number}'


@dataclass
class Topology:
    hosts: dict[str, Host] = field(default_factory=dict)
    switches: dict[str, Switch] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)
    switches_to_aux_hosts: dict[Switch, Host] = field(default_factory=dict)

    def host_to_ip(self, hostname: str) -> str:
        return self.hosts.get(hostname).ip_address

    def append_hosts(self, host: dict[str, Host]) -> None:
        self.hosts |= host

    def append_switches(self, switches: dict[str, Switch]) -> None:
        self.switches |= switches

    def append_link(self, link: Link) -> None:
        self.links.append(link)

    def create_link_switch_host(self, switch_name: str, switch_port: int, host_name: str, host_port: int,
                                degradation: Degradation = LinkTypes.LINK_NO_DEGRADATION, is_aux: bool = False) -> None:
        __switch = self.switches.get(switch_name)
        __host = self.hosts.get(host_name)

        if __switch is not None and __host is not None:
            __switch.busy_ports.append(Port(switch_port))
            __host.busy_ports.append(Port(host_port))

            link = Link(__switch, Port(switch_port), __host, Port(host_port), is_aux, degradation)
            self.switches.update({switch_name: __switch})
            self.hosts.update({host_name: __host})
            self.links.append(link)

            if is_aux:
                self.switches_to_aux_hosts |= {__switch: __host}
        else:
            raise RuntimeError(f'Switch {switch_name} or Host {host_name} was not found')

    def create_link_switch_switch(self, switch_name: str, switch_port: int,
                                  destine_switch_name: str, destine_switch_port: int,
                                  degradation: Degradation = LinkTypes.LINK_NO_DEGRADATION) -> None:
        __src_switch = self.switches.get(switch_name)
        __dst_switch = self.switches.get(destine_switch_name)

        if __src_switch is not None and __dst_switch is not None:
            __src_switch.busy_ports.append(Port(switch_port))
            __dst_switch.busy_ports.append(Port(destine_switch_port))

            link = Link(__src_switch, Port(switch_port), __dst_switch, Port(destine_switch_port), False, degradation)
            self.switches.update({switch_name: __src_switch})
            self.switches.update({destine_switch_name: __dst_switch})
            self.links.append(link)
        else:
            raise RuntimeError(f'Switch {switch_name} or {destine_switch_name} was not found')

    def get_switch_by_name(self, switch_name: str) -> Switch:
        return self.switches.get(switch_name)

    def get_host_by_name(self, host_name: str) -> Host:
        return self.hosts.get(host_name)

    def retrieve_graph(self) -> dict[dict[int]]:
        return {link.switch.name: {link.network_element.name: link.switch_port.port_number} for link in self.links}

    def retrieve_rules(self) -> list[dict[str, str]]:
        rules_map: list[dict[str, str]] = []
        for link in self.links:
            if isinstance(link.network_element, Host):
                rules_map.append({'name': link.switch.name, 'ip': link.network_element.ip_address,
                                  'port': link.switch_port})
            elif isinstance(link.network_element, Switch):
                rules_map.append({'name': link.switch.name, 'ip': self.switches_to_aux_hosts[link.switch].ip_address,
                                  'port': link.switch_port})
                rules_map.append({'name': link.network_element.name,
                                  'ip': self.switches_to_aux_hosts[link.network_element].ip_address,
                                  'port': link.element_port})

        return rules_map
