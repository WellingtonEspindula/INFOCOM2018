import json
import random
import re

import networkx as nx
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import (ofp_event, dpset)
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import ethernet, ipv4, arp
from ryu.lib.packet import packet
from ryu.ofproto import ofproto_v1_3, ether
from webob import Response

ARP = arp.arp.__name__
IPV4 = ipv4.ipv4.__name__
UINT32_MAX = 0xffffffff

bqoe_path_api_instance_name = 'bqoe_path_api_name_app'
url = '/bqoepath/{method}'

# Max number of hops in returned PATH from all_simple_paths
PATH_SIZE = 13
BW_THRESHOLD = 4500000.0
DISTANCE_FIX = PATH_SIZE / BW_THRESHOLD
BW_BITRATE = 2000000.0


class BQoEPathApi(app_manager.RyuApp):
    """
    BQoEP Controller Main Class

    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {
        'dpset': dpset.DPSet,
        'wsgi': WSGIApplication
    }

    # Constructor
    def __init__(self, *args, **kwargs):
        super(BQoEPathApi, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(BQoEPathController, {bqoe_path_api_instance_name: self})
        self.nodes = []
        self.ongoingVideos = {}
        self.numNodes = 0
        self.rtt = []
        self.bw = []
        self.numFlowsRound = []
        self.bwMirror = []
        self.loss = []
        self.links = []
        self.dpset = kwargs['dpset']
        self.dp_dict = {}  # dictionary of datapaths
        self.elist = []  # edges list to the graph
        self.edges_ports = {}  # dictionary of ports {src: {dst: port, dst2: port2}, ...}
        self.parse_graph()  # call the function that populates the priors variables
        self.graph = nx.MultiGraph()  # create the graph
        self.graph.add_edges_from(self.elist)  # add edges to the graph
        self.possible_paths = {}  # dictionary {src-id : [[path1],[path2]]}
        self.current_path = None

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
            Receives switch features events (pre-built function)
        """

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        dpid = datapath.id

        # print('************')
        # print(ofproto)
        # print(ev)
        # print(dpid)
        # count = 1
        # for p in self.elist:
        #  self.logger.info('*** %s -> %s', p[0], p[1])
        #  self.graph[p[0]][p[1]] = {'weight': count, 'rtt': count - 1}
        #  self.graph[p[1]][p[0]] = {'weight': count, 'rtt': count - 1}
        #  count = count + 1

        # print(self.edges_ports)
        # print('************')

        self.dp_dict[dpid] = datapath  # saving datapath on a dictionary

        # install table-miss flow entry 
        # drop unknown packets
        match = parser.OFPMatch()
        actions = []  # empty actions == drop packets
        self.add_flow(datapath, 0, match, actions)

        # flow mod to block ipv6 traffic (not related to the work)
        match = parser.OFPMatch(eth_type=0x86dd)
        actions = []
        self.add_flow(datapath, ofproto.OFP_DEFAULT_PRIORITY, match, actions)

    def add_flow(self, datapath, priority, match, actions):
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
        """ Pre-made function that receives OpenFlow packet_in events
            Not used in this version of BQoEP, but will be on next release
        """

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

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

        datapath_id = datapath.id
        self.mac_to_port.setdefault(datapath_id, {})

        if ARP in header_list:
            self.logger.info("ARP packet in s%s, src: %s, dst: %s, in_port: %s", datapath_id, src, dst, in_port)
        else:
            self.logger.info("packet in s%s, src: %s, dst: %s, in_port: %s", datapath_id, ipv4_src, ipv4_dst, in_port)

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
            self.logger.info("Destination unreachable")

    @staticmethod
    def switch_from_host(path):
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

        path_first = path[0]
        path_rest = path[1:]
        switch_index = 0

        if path_first == 'r':
            switch_index = int(path_rest) + ran_lower_bound - 1
        elif path_first == 'm' and path[1] != 'a':
            switch_index = int(path_rest) + metro_lower_bound - 1
        elif path_first == 'a':
            switch_index = int(path_rest) + access_lower_bound - 1
        elif path_first == 'c' and path[1] != 'd':
            switch_index = int(path_rest) + core_lower_bound - 1
        elif path_first == 'i':
            switch_index = int(path_rest) + internet_lower_bound - 1

        if switch_index > 0:
            return 's' + str(switch_index)
        else:
            return path

    def host_from_switch(self, path):
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

        path_first = path[0]
        path_rest = path[1:]
        switch_index = 0

        if path_first == 's':
            switch_index = int(path_rest)
            if ran_lower_bound <= switch_index <= ran_upper_bound:
                r_index = switch_index - ran_lower_bound + 1
                return "r{0}".format(str(r_index))
            elif metro_lower_bound <= switch_index <= metro_upper_bound:
                m_index = switch_index - metro_lower_bound + 1
                return "m{0}".format(str(m_index))
            elif access_lower_bound <= switch_index <= access_upper_bound:
                a_index = switch_index - access_lower_bound + 1
                return "a{0}".format(str(a_index))
            elif core_lower_bound <= switch_index <= core_upper_bound:
                c_index = switch_index - core_lower_bound + 1
                return "c{0}".format(str(c_index))
            elif internet_lower_bound <= switch_index <= internet_upper_bound:
                i_index = switch_index - internet_lower_bound + 1
                return "i{0}".format(str(i_index))
            else:
                return path
        else:
            return path

    def ip_from_host(self, host):
        if host == "src1":
            return "10.0.0.249"
        elif host == "src2":
            return "10.0.0.250"
        elif host == "man1":
            return "10.0.0.251"
        elif host == "man2":
            return "10.0.0.252"
        elif host == "man3":
            return "10.0.0.253"
        elif host == "man4":
            return "10.0.0.254"
        else:
            first = host[0]
            if first == 'u':
                ip_final = host.split("u")[1]
                return "10.0.0.{0}".format(str(int(ip_final)))  # removing leading zeros
            elif first == 'r' or first == 'm' or first == 'a' or first == 'c' or first == 'i' or first == 's':
                sn = self.switch_from_host(host)
                restsn = sn[1:]
                ipfinal = 200 + int(restsn)
                return "10.0.0." + str(ipfinal)

    def deploy_any_path(self, path):
        paths = [path, path[::-1]]
        for path in paths:
            for i in range(1, len(path) - 1):
                # installing rule for the i switch
                sn = self.switch_from_host(path[i])
                dpid = int(sn[1:])
                _next = self.switch_from_host(path[i + 1])
                datapath = self.dp_dict[dpid]
                parser = datapath.ofproto_parser
                ofproto = datapath.ofproto

                out_port = self.edges_ports["s%s" % dpid][_next]
                actions = [parser.OFPActionOutput(out_port)]
                # self.logger.info("installing rule from %s to %s %s %s", path[i], path[i + 1], str(path[0][1:]),
                #                  str(path[-1][1:]))
                self.logger.info("installing rule from %s to %s %s %s", path[i], path[i + 1], str(path[0]),
                                 str(path[-1]))
                ip_src = self.ip_from_host(str(path[0]))  # to get the id
                ip_dst = self.ip_from_host(str(path[-1]))
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst)
                self.add_flow(datapath, 1024, match, actions)
        self.current_path = path

    def deploy_rule(self, src_dst, rule_id):
        """
        Deploy a rule chosen for a pair src-dst

        Parameters
        ----------
        src_dst : str
            pair of two hosts separated by a '-': Ex: 'h1-h2'
        rule_id : int
            id of the possible path between the two hosts
        """
        self.logger.info("<deploy_rule> Path srcdst: %s, rule_id: %s", src_dst, rule_id)
        self.logger.debug("<deploy_rule> Possible paths: %s", self.possible_paths)

        # flushing the rules on switches that belongs to a depoloyed path
        if self.current_path:
            switches_to_clear = [elem for elem in self.current_path if 'h' not in elem]
            for switch in switches_to_clear:
                datapath = self.dp_dict[int(switch[1:])]
                parser = datapath.ofproto_parser
                match = parser.OFPMatch(eth_type=0x0800)
                mod = parser.OFPFlowMod(datapath=datapath,
                                        command=datapath.ofproto.OFPFC_DELETE,
                                        out_port=datapath.ofproto.OFPP_ANY,
                                        out_group=datapath.ofproto.OFPP_ANY,
                                        match=match)

        # Check to see if the src-dst pair has paths listed and if true deploy
        # the chosen path
        if self.possible_paths.has_key(src_dst):
            if self.possible_paths[src_dst].has_key(int(rule_id)):
                path = self.possible_paths[src_dst][int(rule_id)]
                print(path)
                # [1, 2, 3, 4, 5, 6]
                paths = [path, path[::-1]]
                print(paths)
                for path in paths:
                    for i in range(1, len(path) - 1):
                        # installing rule for the i switch
                        dpid = int(path[i][1:])
                        _next = path[i + 1]
                        datapath = self.dp_dict[dpid]
                        parser = datapath.ofproto_parser
                        ofproto = datapath.ofproto

                        out_port = self.edges_ports["s%s" % dpid][_next]
                        actions = [parser.OFPActionOutput(out_port)]
                        self.logger.info("installing rule from %s to %s %s %s", path[i], path[i + 1], str(path[0][1:]),
                                         str(path[-1][1:]))
                        ip_src = "10.0.0.{0}".format(str(path[0][1:]))  # to get the id
                        ip_dst = "10.0.0.{0}".format(str(path[-1][1:]))
                        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst)
                        self.add_flow(datapath, 1024, match, actions)
                self.current_path = path

        else:
            return "Unknown path"

    def get_graph(self):
        return self.graph

    def parse_graph(self):
        """
        Parses the topology.txt file and creates a graph from it

        """

        file = open('topology.txt', 'r')
        reg = re.compile('-eth([0-9]+):([\w]+)-eth[0-9]+')
        reg_switch = re.compile('(s[0-9]+) lo')

        for line in file:
            if "lo:" in line:
                reference_node = (reg_switch.match(line)).group(1)
                connections = line[8:]
                self.edges_ports.setdefault(reference_node, {})
                for conn in reg.findall(connections):
                    self.edges_ports[reference_node][conn[1]] = int(conn[0])
                    self.elist.append((reference_node, conn[1])) if (
                                                                        conn[1],
                                                                        reference_node) not in self.elist else None

    @staticmethod
    def send_arp(datapath, arp_opcode, src_mac, dst_mac,
                 src_ip, dst_ip, arp_target_mac, in_port, output_port):
        """
        Create and sends arp message
        # This function is not used in this version of BQoEP since using autoStaticArp=True in topo config

        Parameters
        ----------
        datapath
            datapath of the switch

        arp_opcode
            ARP_TYPE

        src_mac
            source mac address
        dst_mac
            destine mac address
        src_ip
            source ipv4 address
        dst_ip
            destine ipv4 address
        arp_target_mac
            ethernet address to be the answer in arp reply
        in_port
            port were entered the packet
        output_port
            out_port to send the packet
        """

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

        actions = [datapath.ofproto_parser.OFPActionOutput(output_port)]

        datapath.send_packet_out(in_port=in_port, actions=actions, data=pkt.data)


class BQoEPathController(ControllerBase):
    """
    Class responsible for the definitions and exposure of webservices

    """

    def __init__(self, req, link, data, **config):
        super(BQoEPathController, self).__init__(req, link, data, **config)
        self.bqoe_path_spp = data[bqoe_path_api_instance_name]

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'admweights-[a-z0-9\-]*'})
    def adm_weights(self, req, **kwargs):
        src = kwargs['method'][11:].split('-')[0]
        dst = kwargs['method'][11:].split('-')[1]

        graph = self.bqoe_path_spp.get_graph()
        for u, v, d in graph.edges(data=True):
            p1 = self.bqoe_path_spp.host_from_switch(u)
            p2 = self.bqoe_path_spp.host_from_switch(v)
            if ((p1 == "a2" and p2 == "a3") or (p1 == "c2" and p2 == "c1") or (p1 == "m5" and p2 == "m1") or (
                    p1 == "a1" and p2 == "a4") or (p1 == "m3" and p2 == "m2")):
                d['weight'] = 1000
            elif p1 == "m5" and p2 == "m4":
                d['weight'] = 3
            else:
                d['weight'] = 1

        min_splen = 100000000
        min_sp = []
        if dst == "all":
            destinations_array = ["man1", "man2", "man3", "man4"]
            random.shuffle(destinations_array)
            for dest in destinations_array:
                prev, dist = nx.algorithms.shortest_paths.bellman_ford_predecessor_and_distance(graph, source=src,
                                                                                                weight='weight')
                sp = [dest]
                # print(f"dest={dest}, sp={sp}, prev={prev}")
                pv = prev[dest][0]
                # print(f"dest = {dest}, prev[dest] = {prev[dest]}")
                while pv != src:
                    sp.append(pv)
                    pv = prev[pv][0]
                    # print(f"dest = {dest}, prev[dest] = {prev[dest]}")
                sp.append(src)

                splen = dist[dest]
                if splen < min_splen:
                    min_sp = sp
                    min_splen = splen

        humanmin_sp = []
        for elem in min_sp:
            humanmin_sp.append(self.bqoe_path_spp.host_from_switch(elem))

        result = dict(dst=humanmin_sp[0], dest_ip=self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), path=humanmin_sp)
        self.bqoe_path_spp.deploy_any_path(humanmin_sp)

        body = json.dumps(result, indent=4)
        return Response(content_type='application/json', body=body, charset="UTF-8")
