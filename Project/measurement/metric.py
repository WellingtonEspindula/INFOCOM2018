from dataclasses import dataclass
from enum import Enum


class Protocol(Enum):
    """ Identify the Metric Protocol """
    UDP = 0
    TCP = 1


@dataclass
class Metric:
    """ Class for managing a Metric with its attributes"""
    names: list[str]
    timeout: int
    probe_size: int
    train_length: int
    train_count: int
    gap: int
    protocol: Protocol
    connections: int
    time_mode: int
    max_time: int


class MetricTypes(Enum):
    """ Metric Types Enum with their own tests parameters """
    RTT = Metric(names=["rtt"], timeout=3, probe_size=100, train_length=1, train_count=20, gap=50000,
                 protocol=Protocol.UDP, connections=1, time_mode=0, max_time=0)
    LOSS = Metric(names=["loss"], timeout=3, probe_size=100, train_length=1, train_count=20, gap=50000,
                  protocol=Protocol.UDP, connections=1, time_mode=0, max_time=0)
    UDP_PACK = Metric(names=["rtt", "loss"], timeout=3, probe_size=100, train_length=1, train_count=20, gap=50000,
                      protocol=Protocol.UDP, connections=1, time_mode=0, max_time=0)
    THROUGHPUT_TCP = Metric(names=["throughput_tcp"], timeout=12, probe_size=14520, train_length=1440, train_count=1,
                            gap=100000, protocol=Protocol.TCP, connections=3, time_mode=2, max_time=12)
