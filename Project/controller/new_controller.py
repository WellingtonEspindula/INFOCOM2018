#!/usr/bin/env ryu-manager
import json
from dataclasses import dataclass, field
from typing import Any

import networkx as nx
from networkx.algorithms.shortest_paths import bellman_ford_predecessor_and_distance as bellman_ford
from ryu.app.wsgi import WSGIApplication, route, ControllerBase, Response
from ryu.base import app_manager
from ryu.controller import (ofp_event, dpset)
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import ethernet, ipv4, arp
from ryu.lib.packet import packet
from ryu.ofproto import ofproto_v1_3, ether
from ryu.ofproto.ofproto_v1_5_parser import OFPMatch

from Project.common.main_topology import MAIN_TOPOLOGY

ARP = arp.arp.__name__
IPV4 = ipv4.ipv4.__name__
UINT32_MAX = 0xffffffff

MOS_THRESHOLD = 4.0
ATTENUATION_RATE = 1.0
MOS_DIFF_THR = 0.3

bqoe_path_api_instance_name = 'bqoe_path_api_name_app'
url = '/bqoepath/{method}'

# Max number of hops in returned PATH from all_simple_paths
PATH_SIZE = 13
BW_THRESHOLD = 4500000.0
DISTANCE_FIX = PATH_SIZE / BW_THRESHOLD
BW_BITRATE = 2000000.0


# Main class for BQoEP Controller
@dataclass
class BQoEPathApi(app_manager.RyuApp):
    nodes: list = field(default_factory=list)
    nodes_count: int = 0
    links: list = field(default_factory=list)
    bandwidths: list = field(default_factory=list)
    rtts: list = field(default_factory=list)
    losses: list = field(default_factory=list)
    datapath_set: Any = field(default_factory=Any)  # I have no idea which type is it
    num_flows_round: list = field(default_factory=list)  # is it needed yet?
    bandwidth_mirrors: list = field(default_factory=list)  # is it needed yet?

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    def __post_init__(self, *args, **kwargs):
        wsgi = kwargs['wsgi']
        wsgi.register(BQoEPathController, {bqoe_path_api_instance_name: self})
        self.datapath_set = kwargs['dpset']

    def __init__(self, *args, **kwargs):
        super(BQoEPathApi, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(BQoEPathController, {bqoe_path_api_instance_name: self})
        self.nodes = []
        self.ongoingVideos = {}
        self.numNodes = 0
        self.bandwidths = []
        self.rtt = []
        self.loss = []
        self.numFlowsRound = []
        self.bwMirror = []
        self.links = []
        self.datapath_set = kwargs['dpset']
        self.mydict = {}
        self.datapaths: dict[int] = {}  # dictionary of datapaths
        # self.edges_list: list = []  # edges list to the graph
        # self.edges_ports = {}  # dictionary of ports {src: {dst: port, dst2: port2}, ...}
        # self.parse_graph()  # call the function that populates the priors variables
        self.edges_list: list = MAIN_TOPOLOGY.retrieve_edge_list()
        self.edges_ports: dict[dict[int]] = MAIN_TOPOLOGY.retrieve_graph()
        self.graph = nx.MultiGraph()  # create the graph
        self.graph.add_edges_from(self.edges_list)  # add edges to the graph
        self.possible_paths = {}  # dictionary {src-id : [[path1],[path2]]}
        self.current_path = None
        # nx.write_edgelist(self.graph, "net.edgelist")
        bar = self.graph.nodes()
        self.logger.info("%s", bar)


# Class responsible for the definitions and exposure of webservices
class BQoEPathController(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(BQoEPathController, self).__init__(req, link, data, **config)
        self.bqoe_path_spp = data[bqoe_path_api_instance_name]

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'listpaths-[a-z0-9\-]*'})
    def list_paths(self, req, **kwargs):
        src = kwargs['method'][10:].split('-')[0]
        dst = kwargs['method'][10:].split('-')[1]
        dict_path = self.bqoe_path_spp.all_paths_sd(src, dst)
        print("DPS: " + str(len(dict_path)))
        body = json.dumps(dict_path, indent=4)
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'getalledges'})
    def get_all_edges(self, req, **kwargs):
        graph = self.bqoe_path_spp.get_graph()
        local_edges = ""
        for u, v, d in graph.edges(data=True):
            local_edges += f'{v} {u}\n'
        body = local_edges
        return Response(content_type='text/plain', body=body, charset="UTF-8")
