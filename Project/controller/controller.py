#!/usr/bin/env ryu-manager

# Projeto Final - Redes de Computadores I - CMP182 - 2016 - UFRGS
# Professor: Luciano Paschoal Gaspary
# Controlador para OpenFlow - Best QoE Path (BQoEP) - Seletor de melhor caminho baseado em predicao de QoE
# OpenFlow v. 1.3
# Desenvolvido por:
#    Roberto Costa Filho - 237091 - rtcosta@gmail.com
# Esqueleto do codigo baseado no codigo simple_switch_13.py - Ryu Controller

import json
import os
import pickle
import re
from shutil import copyfile

import networkx as nx
from networkx.algorithms.shortest_paths import bellman_ford_predecessor_and_distance as bellman_ford
from ryu.app.wsgi import WSGIApplication, route, ControllerBase
from ryu.base import app_manager
from ryu.controller import (ofp_event, dpset)
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import ethernet, ipv4, arp
from ryu.lib.packet import packet
from ryu.ofproto import ofproto_v1_3, ether
from ryu.ofproto.ofproto_v1_5_parser import OFPMatch
from webob import Response

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
class BQoEPathApi(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

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

    # # Descr: Function that parses the topology.txt file and creates a graph from it
    # # Args: None
    # def parse_graph(self):
    #     file = open('topology.txt', 'r')
    #     reg = re.compile('-eth([0-9]+):([\w]+)-eth[0-9]+')
    #     regSwitch = re.compile('(s[0-9]+) lo')
    #
    #     for line in file:
    #         if "lo:" not in line:
    #             continue
    #         refnode = (regSwitch.match(line)).group(1)
    #         connections = line[8:]
    #         # print(refnode, connections)
    #         self.edges_ports.setdefault(refnode, {})
    #         for conn in reg.findall(connections):
    #             self.edges_ports[refnode][conn[1]] = int(conn[0])
    #             print(f'self.edges_ports[{refnode=}][{conn[1]=}] = {conn[0]=}')
    #             self.edges_list.append((refnode, conn[1])) if (conn[1], refnode) not in self.edges_list else None

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Receives switch features events (pre-built function)
        """

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        dpid = datapath.id

        count = 1
        for u, v, d in self.graph.edges(data=True):
            d['weight'] = count
            d['rtt'] = count / 100.0
            count = count + 1

        self.datapaths[dpid] = datapath  # saving datapath on a dictionary

        # install table-miss flow entry
        # drop unknown packets
        match = parser.OFPMatch()
        actions = []  # empty actions == drop packets
        self.add_flow(datapath, 0, match, actions)

        # flow mod to block ipv6 traffic (not related to the work)
        match = parser.OFPMatch(eth_type=0x86dd)
        actions = []
        self.add_flow(datapath, ofproto.OFP_DEFAULT_PRIORITY, match, actions)

    @staticmethod
    def add_flow(datapath, priority: int, match: OFPMatch, actions):
        """
        Installs flow entry on switch

        Parameters
        ----------
        datapath
            datapath of the switch to install the entry
        priority
            priority of the flow entry
        match
            rule to be matched (ipv4=....,)
        actions
            actions to be made after a match
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Receives OpenFlow packet_in events
        Ps.: Not used in this version of BQoEP, but will be on next release
        """

        self.logger.info("I'm a packet in a router. Please say what I have to do")

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        self.logger.info(
            f"Packet in handler -> [msg={msg}], [datapath={datapath}], [ofproto={ofproto}], [in_port={in_port}]")

        reg = re.compile(".([0-9]+)$")

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        ip = pkt.get_protocol(ipv4.ipv4)
        p_arp = pkt.get_protocol(arp.arp)

        header_list = dict((p.protocol_name, p)
                           for p in pkt.protocols if type(p) != str)

        ipv4_src = ip.src if ip is not None else p_arp.src_ip
        ipv4_dst = ip.dst if ip is not None else p_arp.dst_ip

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        if ARP in header_list:
            self.logger.info("ARP packet in s%s, src: %s, dst: %s, in_port: %s", dpid, src, dst, in_port)
        else:
            self.logger.info("packet in s%s, src: %s, dst: %s, in_port: %s", dpid, ipv4_src, ipv4_dst, in_port)

        # ipv4 addresses
        src_id = reg.search(ipv4_src).group(1)
        dst_id = reg.search(ipv4_dst).group(1)
        src_host = "h" + src_id
        dst_host = "h" + dst_id
        # defining switch paths to install rules

        paths = list(nx.all_simple_paths(self.graph, src_host, dst_host, PATH_SIZE))
        if len(paths) > 0:
            # check to see if already exists a path (rules in switches) between such hosts
            key = ipv4_src + '-' + ipv4_dst
            if key in self.paths_defineds.keys():
                self.logger.info("already created this path")
            else:
                self.logger.info("we must create this path")
                self.paths_defineds[key] = paths

                # first we need to check how many paths we have at all minimum cutoff is PATH_SIZE
                path_num = len(paths)
                if path_num > MULTIPATH_LEVEL:  # if num of paths is bigger than MULTIPATH_LEVEL slices the array
                    paths = paths[:MULTIPATH_LEVEL]
                self.logger.info("we have: %s path(s)", path_num)
                self.logger.info("Using %s paths: ", len(paths))
                for path in paths:
                    self.logger.info("\t%s", path)
                group_dict = self.get_group_routers(paths)

                # print (mod_group_entry(paths))
                self.create_route(paths, group_dict)

            # create mac host to send arp reply
            mac_host_dst = "00:04:00:00:00:0" + dst_id if len(dst_id) == 1 else "00:04:00:00:00:" + dst_id

            # check to see if it is an ARP message, so if it is send a reply
            if ARP in header_list:
                self.send_arp(datapath, arp.ARP_REPLY, mac_host_dst, src,
                              ipv4_dst, ipv4_src, src, ofproto.OFPP_CONTROLLER, in_port)
            else:  # if it is not ARP outputs the message to the corresponding port
                # print self.edges_ports
                out_port = self.edges_ports[paths[0][1]][paths[0][2]]
                actions = [parser.OFPActionOutput(out_port)]
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)
        else:
            self.logger.info("Destination unreacheable")

    def readNmCsv(self):
        auxSet = set()

        csvFile = "nm_static_results.csv"
        countControlFile = "count_control.csv"

        fin = open(csvFile, "r")

        for line in fin:
            aux = line.split(";")
            auxSet.add(aux[0])
            auxSet.add(aux[1])

        self.nodes = list(auxSet)
        self.numNodes = len(self.nodes)

        self.links = [[0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
        self.rtt = [[0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
        self.loss = [[0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
        self.bandwidths = [[1.0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
        self.numFlowsRound = [[0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]

        fin = open(csvFile, "r")
        cc = open(countControlFile, "wb")

        for line in fin:

            aux = line.split(";")
            index1 = -1
            index2 = -1

            for i in range(0, self.numNodes):
                if self.nodes[i] == aux[0]:
                    index1 = i
                if self.nodes[i] == aux[1]:
                    index2 = i
                if index1 != -1 and index2 != -1:
                    break

            if index1 != -1 and index2 != -1:

                self.links[index1][index2] = 1
                self.rtt[index1][index2] = float(aux[2])
                self.loss[index1][index2] = float(aux[3])  # up
                if aux[4] == "" or aux[4] == "\n":
                    brute_bw = 1.0
                else:
                    brute_bw = float(aux[4])
                if brute_bw == 0.0:
                    brute_bw = 1.0
                self.bandwidths[index1][index2] = brute_bw / ATTENUATION_RATE  # up
                cc.write(self.nodes[index1] + ";" + self.nodes[index2] + ";" + str(
                    int(self.bandwidths[index1][index2] / 2000000.0)) + "\n")

            else:
                print("error -- something went wrong...")

        # print str(aux[0]) + " " + str(aux[1] + " " + str(bw[index1][index2]))

        fin.close()
        cc.close()
        self.bwMirror = self.bandwidths

    def check_for_viability(self, path, isBest, src, dst):
        if self.ongoingVideos is None:
            return False
        if self.ongoingVideos.get(src) is None:
            return False
        if self.ongoingVideos.get(src).get(dst) is None:
            return False
        if len(self.ongoingVideos.get(src).get(dst)) <= 0:
            return False

        if isBest:
            tolerance = 4000000.0
            # Se for o melhor, tenho que verificar se alem da rota que quero mudar,
            # tenho espaco para pelo menos um novo video que entrara no best destination
        else:
            tolerance = 2000000.0

        res = True
        for i in range(0, (len(path) - 2)):
            index2 = self.nodes.index(path[i + 1])
            index1 = self.nodes.index(path[i])
            if self.bwMirror[index1][index2] < tolerance:
                res = False
                break

        if res:
            for i in range(0, (len(path) - 2)):
                index2 = self.nodes.index(path[i + 1])
                index1 = self.nodes.index(path[i])
                self.bwMirror[index1][index2] = self.bwMirror[index1][index2] - 2000000.0
                if self.bwMirror[index1][index2] < 0:
                    self.bwMirror[index1][index2] = 0

        return res

    def update_netmetric_snapshot(self):
        # mydict = {}

        # if os.path.exists('bestpaths.serialize'):
        #    with open('bestpaths.serialize', 'rb') as f:
        #        mydict = pickle.load(f)
        #        f.close()
        # else:
        #    mydict = {}

        # if os.path.exists('/tmp/best_destinations.csv'):
        #    os.remove('/tmp/best_destinations.csv')

        # bdfile = open('/tmp/best_destinations.csv', 'wb')
        self.readNmCsv()
        print("[RYU] ------------------- SNAPSHOT UPDATED ---------------------")
        if os.path.exists('/tmp/current_mos.csv'):
            os.remove('/tmp/current_mos.csv')

        cmfile = open('/tmp/current_mos.csv', 'wb')
        betterAvailable = "N"
        for host in self.mydict:
            for entry in self.mydict.get(host):
                composedMos = self.calculate_composed_mos(self.mydict.get(host).get(entry).get("path"))
                cmfile.write(host + ";" + self.mydict.get(host).get(entry).get("ip") + ";" + str(
                    composedMos) + ";" + betterAvailable + "\n")

        cmfile.close()
        copyfile("/tmp/current_mos.csv", "current_mos.csv")

        with open('bestpaths.serialize', 'wb') as f:
            pickle.dump(self.mydict, f)
            f.close()

    def all_paths_sd(self, src, dst) -> dict:
        """
        Searches and lists all possible paths between a given SRC and DST


        Parameters
        ----------
        src
            source host
        dst
            destination host


        Return
        ----------
        Returns a dictionary with all possible paths between src and dst
        """

        self.logger.info("<all_paths_sd> Path src: %s, dst: %s", src, dst)
        paths = list(nx.all_simple_paths(self.graph, src, dst))
        dict_path = {}
        for i, path in zip(range(0, len(paths)), paths):
            dict_path[i] = path

        self.possible_paths["%s-%s" % (src, dst)] = dict_path
        self.logger.info("Possible paths between src: %s and dst: %s\n%s", src, dst, json.dumps(dict_path, indent=4))
        return dict_path

    # Descr: Method responsible for deploying the rule chosen for a pair src-dst
    # Args: srcdst: pair of two hosts separeted by a '-': Ex: 'h1-h2'
    #       rule_id: id of the possible path between the two hosts
    def deploy_rule(self, srcdst, rule_id):
        self.logger.info("<deploy_rule> Path srcdst: %s, rule_id: %s", srcdst, rule_id)
        self.logger.debug("<deploy_rule> Possible paths: %s", self.possible_paths)

        # flushing the rules on switches that belongs to a depoloyed path
        if self.current_path:
            switches_to_clear = [elem for elem in self.current_path if 'h' not in elem]
            for switch in switches_to_clear:
                datapath = self.datapaths[int(switch[1:])]
                parser = datapath.ofproto_parser
                match = parser.OFPMatch(eth_type=0x0800)
                mod = parser.OFPFlowMod(datapath=datapath,
                                        command=datapath.ofproto.OFPFC_DELETE,
                                        out_port=datapath.ofproto.OFPP_ANY,
                                        out_group=datapath.ofproto.OFPP_ANY,
                                        match=match)

        # Check to see if the src-dst pair has paths listed and if true deploy
        # the chosen path
        print("****")
        if self.possible_paths.has_key(srcdst):
            print("AAAAA")
            if self.possible_paths[srcdst].has_key(int(rule_id)):
                path = self.possible_paths[srcdst][int(rule_id)]
                print(">>>>")
                print(path)
                # [1, 2, 3, 4, 5, 6]
                paths = [path, path[::-1]]
                print(paths)
                for path in paths:
                    for i in range(1, len(path) - 1):
                        # instaling rule for the i switch
                        dpid = int(path[i][1:])
                        _next = path[i + 1]
                        datapath = self.datapaths[dpid]
                        parser = datapath.ofproto_parser
                        ofproto = datapath.ofproto

                        out_port = self.edges_ports["s%s" % dpid][_next]
                        actions = [parser.OFPActionOutput(out_port)]
                        self.logger.info("installing rule from %s to %s %s %s", path[i], path[i + 1], str(path[0][1:]),
                                         str(path[-1][1:]))
                        ip_src = "10.0.0." + str(path[0][1:])  # to get the id
                        ip_dst = "10.0.0." + str(path[-1][1:])
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst)
                        self.add_flow(datapath, 1024, match, actions)
                self.current_path = path

        else:
            print("UP")
            return "Unknown path"

    # Descr: Function that create and sends arp message
    # Args: datapath: datapath of the switch,
    #       arp_opcode: ARP_TYPE
    #       src_mac, dst_mac: ethernet addresses
    #       src_ip, dst_ip: ipv4 addresses
    #       arp_target_mac: ethernet addr to be the answer in arp reply
    #       in_port: port were entered the packet, output: out_port to send the packet
    # This function is not used in this version of BQoEP since using autoStaticArp=True in topo config
    def send_arp(self, datapath, arp_opcode, src_mac, dst_mac,
                 src_ip, dst_ip, arp_target_mac, in_port, output):
        # Generate ARP packet
        ether_proto = ether.ETH_TYPE_ARP
        hwtype = 1
        arp_proto = ether.ETH_TYPE_IP
        hlen = 6
        plen = 4

        pkt = packet.Packet()
        e = ethernet.ethernet(dst_mac, src_mac, ether_proto)
        a = arp.arp(hwtype, arp_proto, hlen, plen, arp_opcode,
                    src_mac, src_ip, arp_target_mac, dst_ip)
        pkt.add_protocol(e)
        pkt.add_protocol(a)
        pkt.serialize()

        actions = [datapath.ofproto_parser.OFPActionOutput(output)]

        datapath.send_packet_out(in_port=in_port, actions=actions, data=pkt.data)


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
