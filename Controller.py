#!/usr/bin/env ryu-manager

# Projeto Final - Redes de Computadores I - CMP182 - 2016 - UFRGS
# Professor: Luciano Paschoal Gaspary
# Controlador para OpenFlow - Best QoE Path (BQoEP) - Seletor de melhor caminho baseado em predicao de QoE
# OpenFlow v. 1.3
# Desenvolvido por:
#    Roberto Costa Filho - 237091 - rtcosta@gmail.com
# Esqueleto do codigo baseado no codigo simple_switch_13.py - Ryu Controller

import json
import math
import os
import pickle
import queue
import random
import re
from copy import deepcopy
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

ARP = arp.arp.__name__
IPV4 = ipv4.ipv4.__name__
UINT32_MAX = 0xffffffff

MOS_THRESHOLD = 4.0
ATENUATION_RATE = 1.0
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
        self.mydict = {}
        self.dp_dict = {}  # dictionary of datapaths
        self.elist = []  # edges list to the graph
        self.edges_ports = {}  # dictionary of ports {src: {dst: port, dst2: port2}, ...}
        self.parse_graph()  # call the function that populates the priors variables
        self.graph = nx.MultiGraph()  # create the graph
        self.graph.add_edges_from(self.elist)  # add edges to the graph
        self.possible_paths = {}  # dictionary {src-id : [[path1],[path2]]}
        self.current_path = None
        self.mycount = 0
        # nx.write_edgelist(self.graph, "net.edgelist")
        bar = self.graph.nodes()
        self.logger.info("%s", bar)

    # Descr: function that receive switch features events (pre-built function)
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
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

        count = 1
        for u, v, d in self.graph.edges(data=True):
            d['weight'] = count
            d['rtt'] = count / 100.0
            count = count + 1

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

    def appQoSStart(self, tp, loss, delay):
        if loss < 9:
            if tp >= 1400000:
                start = 0.89
            else:
                start = 2.2
            return start
        start = 20
        return start

    def appQoSStcount(self, tp, loss, delay):
        # if tp < 680000:
        #    print "[SC] TP " + str(tp) + " DELAY " + str(delay)

        if tp >= 2000000:
            if tp >= 2300000:
                stcount = 0
            else:
                stcount = 1.8
        else:
            stcount = 10
        # if tp < 677000:
        #    if tp <= 400000:
        #        stcount = 7.5
        #    else:
        #        stcount = 6.5
        # else:
        #    if tp >= 1400000:
        #        stcount = 9.7
        #    else:
        #        stcount = 13
        # if tp < 680000:
        #    print "[SC] TP 2 " + str(tp) + " DELAY " + str(delay) + " STCOUNT: " + str(stcount)

        return stcount

    def appQoSStlen(self, tp, loss, delay):
        stlen = None

        if tp >= 1400000:
            if tp >= 2000000:
                if tp >= 2500000:
                    stlen = 0.039
                else:
                    stlen = 1.2
            else:
                stlen = 33
        else:
            if tp >= 816000:
                if tp >= 977000:
                    stlen = 58
                else:
                    if delay < 0.064:
                        if tp >= 856000:
                            if delay < 0.056:
                                stlen = 68
                            else:
                                stlen = 69
                        else:
                            stlen = 71
                    else:
                        stlen = 72
            else:
                if delay < 0.056:
                    stlen = 73  # 70
                else:
                    if tp >= 677000:
                        stlen = 82
                    else:
                        if delay < 0.081:
                            if delay < 0.057:
                                stlen = 83
                            else:
                                stlen = 88
                        else:
                            stlen = 95

        return stlen

    #    def appQoSStcount(self, tp, loss, delay):
    #        if tp >= 2000000:
    #            if tp >= 2300000:
    #                stcount = 0
    #            else:
    #                stcount = 1.8
    #        else:
    #            if tp <= 677000:
    #                if tp <= 400000:
    #                    stcount = 7.5
    #                else:
    #                    stcount = 6.5
    #            else:
    #                stcount = 11
    #        return stcount
    #
    #    def appQoSStlen(self, tp, loss, delay):
    #        if tp >= 2000000:
    #            if tp >= 2500000:
    #                stlen = 0.029
    #            else:
    #                stlen = 1.2
    #        else:
    #            if tp >= 1400000:
    #                stlen = 33
    #            else:
    #                if tp >= 816000:
    #                    stlen = 67
    #                else:
    #                    if delay <= 0.056:
    #                        stlen = 70
    #                    else:
    #                        stlen = 86
    #        return stlen

    def QoECalc(self, start, stcount, stlen):
        lam = float(stlen) / (stlen + 60.0)
        # if stlen > 80:
        #   print "STLEN: " + str(stlen) + " STCOUNT: " + str(stcount) + " LAMBDA: " + str(lam)
        if stcount > 1000:
            qoe = 1
            return qoe
        else:
            if lam < 0.1:
                a = 3.012682983
            elif lam < 0.2:
                a = 3.098391523
            elif lam < 0.579:
                a = 3.190341904
            elif lam < 0.586:  # 0.5
                #   print "A 0"
                a = 3.248113258
            else:  # 0.5
                #   print "A 1"
                a = 3.302343627
            if lam < 0.1:
                b = 0.765328992
            elif lam < 0.2:
                b = 0.994413063
            elif lam < 0.579:
                b = 1.520322299
            elif lam < 0.586:
                #   print "B 0"
                b = 1.693893480
            else:
                #   print "B 1"
                b = 1.888050118
            if lam < 0.1:
                c = 1.991000000
            elif lam < 0.2:
                c = 1.901000000
            elif lam < 0.579:
                c = 1.810138616
            elif lam < 0.586:
                # print "C 0"
                c = 1.751982415
            else:
                # print "C 1"
                c = 1.697472392
            qoe = a * math.exp(-b * stcount) + c
            # print "MOS: " + str(qoe)
            return qoe

    def readOngoingVideos(self):
        self.ongoingVideos = {}
        if os.path.exists('cursing_videos.csv'):
            copyfile("cursing_videos.csv", "ongoing_videos.csv")
            fin = open("ongoing_videos.csv", "r")
            for line in fin:
                aux = line.split(";")
                if len(aux) < 3:
                    continue
                else:
                    uuid = aux[0]
                    src = aux[1]
                    dst = aux[2].replace("\n", "")
                    if self.ongoingVideos.get(src) == None:
                        self.ongoingVideos[src] = {}
                    if self.ongoingVideos.get(src).get(dst) == None:
                        self.ongoingVideos[src][dst] = {}
                    self.ongoingVideos[src][dst][uuid] = uuid
            fin.close()
            print(json.dumps(self.ongoingVideos, indent=4))
        else:
            self.ongoingVideos = None

    def readBanishedFile(self):
        self.banishedLinks = {}
        if os.path.exists('banished_links.csv'):
            copyfile("banished_links.csv", "banished_links_secure.csv")
            fin = open("banished_links_secure.csv", "r")
            for line in fin:
                aux = line.split(";")
                if len(aux) < 2:
                    continue
                else:
                    src = aux[0]
                    dst = aux[1].replace("\n", "")
                    if self.banishedLinks.get(src) is None:
                        self.banishedLinks[src] = {}
                    if self.banishedLinks.get(src).get(dst) is None:
                        self.ongoingVideos[src][dst] = True
            fin.close()
            print(json.dumps(self.banishedLinks, indent=4))

    def readNmCsv(self):
        auxSet = set()

        csvFile = "link_last_results.csv"
        countControlFile = "count_control.csv"

        fin = open(csvFile, "r")

        for line in fin:
            aux = line.split(";")
            auxSet.add(aux[0])
            auxSet.add(aux[1])

        self.nodes = list(auxSet)
        self.numNodes = len(self.nodes)
        print(sorted(self.nodes), self.numNodes)

        self.links = [[0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
        self.rtt = [[0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
        self.loss = [[0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
        self.bw = [[1.0 for x in range(len(self.nodes))] for y in range(len(self.nodes))]
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
                self.bw[index1][index2] = brute_bw / ATENUATION_RATE  # up
                cc.write(f'{self.nodes[index1]};{self.nodes[index2]};{int(self.bw[index1][index2] / 2000000.0)}\n'.encode())

            else:
                print("error -- something went wrong...")

        # print str(aux[0]) + " " + str(aux[1] + " " + str(bw[index1][index2]))

        fin.close()
        cc.close()
        self.bwMirror = self.bw

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

    # r = list(range(1,201))
    # random.shuffle(r)
    # self.readOngoingVideos()

    # for hostid in r: #1 a 200
    #    host = "u" + str(hostid).zfill(3)
    #    rmap = self.bestQoePath(host, "all")
    #    if self.mydict.get(host) != None:
    #        self.mydict[host] = rmap
    # for entry in rmap:
    #    #print "PATH: " + str(mydict.get(host).get(entry).get("path"))
    #    newMos = rmap.get(entry).get("mos")
    #    if self.mydict.get(host).get(entry) != None:
    #        oldMos = self.calculateComposedMos(self.mydict.get(host).get(entry).get("path"))
    #        betterAvailable = "N"
    #        if newMos - oldMos > MOS_CHANGE_THRESHOLD:
    #            #self.deploy_any_path(rmap.get(entry).get("path"))
    #            #if self.checkForViability(rmap.get(entry).get("path"), rmap.get(entry).get("best"), host, rmap.get(entry).get("ip")):
    #            #    self.deploy_any_path(rmap.get(entry).get("path"))
    #            #    self.mydict[host] = rmap
    #            #    #Nao preciso mudar o "betterAvailable", pois ja estou dando redeploy para o melhor caminho, logo nao existe um melhor disponivel
    #            #else:
    #            betterAvailable = "S"
    #            #mydict[host][entry] = rmap.get(entry)
    #            #print "DST: " + entry + " OM: " + str(oldMos) + " NM: " + str(newMos)
    #        cmfile.write(host + ";" +  rmap.get(entry).get("ip") + ";" + str(oldMos) + ";" + betterAvailable + "\n")
    #    else:
    #        self.mydict[host][entry] = rmap.get(entry)
    #        cmfile.write(host + ";" +  rmap.get(entry).get("ip") + ";" + str(rmap.get(entry).get("mos")) + ";N" + "\n")
    #
    #   if rmap.get(entry).get("best") == True:
    #       bdfile.write(host + ";" +  rmap.get(entry).get("ip") + ";" + str(rmap.get(entry).get("mos")) + ";" + rmap.get(entry).get("name") + "\n")
    #     else:
    #         for entry in rmap:
    #             self.deploy_any_path(rmap.get(entry).get("path"))
    #             cmfile.write(host + ";" +  rmap.get(entry).get("ip") + ";" + str(rmap.get(entry).get("mos")) + ";N" + "\n")
    #             if rmap.get(entry).get("best") == True:
    #                 bdfile.write(host + ";" + rmap.get(entry).get("ip") + ";" + str(rmap.get(entry).get("mos")) + ";" + rmap.get(entry).get("name") + "\n")
    #         self.mydict[host] = rmap

    # bdfile.close()
    # copyfile("/tmp/best_destinations.csv", "best_destinations.csv")

    # cmfile.close()

    def calculate_composed_mos(self, path):
        # print str(aux[0]) + " " + str(aux[1] + " " + str(bw[index1][index2]))

        final_bandwidth = 10000000000
        final_rtt = 0
        final_loss = 0
        for i in range(0, (len(path) - 1)):
            index2 = self.nodes.index(path[i + 1])
            index1 = self.nodes.index(path[i])
            final_bandwidth = self.bw[index1][index2] if (
                    self.bw[index1][index2] < final_bandwidth) else final_bandwidth
            # print("FR: " + str(finalRtt) + " s: " + str(self.rtt[index1][index2]))
            final_rtt = self.rtt[index1][index2] + final_rtt

            loss_p = self.loss[index1][index2] / 100.0
            lossNode_p = final_loss / 100.0

            final_loss = 1 - ((1 - lossNode_p) * (1 - loss_p))
            final_loss = final_loss * 100

        start = self.appQoSStart(final_bandwidth, final_loss, final_rtt)
        stcount = self.appQoSStcount(final_bandwidth, final_loss, final_rtt)
        stlen = self.appQoSStlen(final_bandwidth, final_loss, final_rtt)
        mos = self.QoECalc(start, stcount, stlen)
        print("[RYU] CALCULADO BW: " + str(final_bandwidth) + " RTT: " + str(final_rtt) + " LOSS: " + str(
            final_loss) + " MOS: " + str(mos))
        return round(mos, 2)

    def localBestQoePath(self, src, dst):
        _auxSet = set()

        _csvFile = "link_last_results.csv"

        _fin = open(_csvFile, "r")

        for _line in _fin:
            _aux = _line.split(";")
            _auxSet.add(_aux[0])
            _auxSet.add(_aux[1])

        _nodes = list(_auxSet)
        _numNodes = len(_nodes)

        _fin.close()
        _fin = open(_csvFile, "r")

        _links = [[0 for x in range(len(_nodes))] for y in range(len(_nodes))]
        _rtt = [[0 for x in range(len(_nodes))] for y in range(len(_nodes))]
        _loss = [[0 for x in range(len(_nodes))] for y in range(len(_nodes))]
        _bw = [[0 for x in range(len(_nodes))] for y in range(len(_nodes))]

        self.readBanishedFile()
        print("BF: " + str(self.banishedLinks))
        for _line in _fin:

            _aux = _line.split(";")
            _index1 = -1
            _index2 = -1

            for _i in range(0, _numNodes):
                if self.banishedLinks.get(_aux[0]) != None:
                    if self.banishedLinks.get(_aux[0]).get(_aux[1]) != None:
                        print("A: " + _aux[0] + " B: " + _aux[1] + " Value: " + str(
                            self.banishedLinks.get(_aux[0]).get(_aux[1])))
                        continue

                if _nodes[_i] == _aux[0]:
                    _index1 = _i
                if _nodes[_i] == _aux[1]:
                    _index2 = _i
                if _index1 != -1 and _index2 != -1:
                    break

            if _index1 != -1 and _index2 != -1:
                _links[_index1][_index2] = 1
                _rtt[_index1][_index2] = float(_aux[2])
                _loss[_index1][_index2] = float(_aux[3])  # up
                _bw[_index1][_index2] = float(_aux[4])  # up

            else:
                print("error -- something went wrong...")

        # print str(aux[0]) + " " + str(aux[1] + " " + str(bw[index1][index2]))

        _fin.close()

        _BIGNUMBER = 10000000000
        _destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
        _bwNode = []
        _rttNode = []
        _lossNode = []
        _mosNode = []
        _prevNode = []
        _visited = []

        # print "SMC: " + str(self.mycount)
        # initialization
        for _i in range(0, _numNodes):
            _bwNode.append(_BIGNUMBER)
            _rttNode.append(0)
            _lossNode.append(0)
            _mosNode.append(-1 * _BIGNUMBER)
            _prevNode.append(-1)
            _visited.append(-1)

        _srcNode = _nodes.index(src)
        if dst == "all":
            _dstNode = _destinations_array[0]
            # inicializa com o primeiro elemento da lista de destinos.
            # A escolha definitiva so sera feita apos percorrer
            # todo o grafo para obtencao dos MOS/bw por nodo.
            _best = _destinations_array[0]
        else:
            _dstNode = _nodes.index(dst)
            _best = dst

        _auxList = [_srcNode]

        while len(_auxList) > 0:
            _u = _auxList.pop(0)
            # Ele pode ter sido colocado em auxList por outro nodo vizinho antes de ser visitado, e entao aparecer de novo
            if _visited[_u] == -1:
                # print "-----------"
                for _i in range(0, _numNodes):
                    if _links[_i][_u] == 1:
                        print(">>> Test " + _nodes[_i])
                        _bwNode[0]
                        # calculate qos metrics
                        _bwAux = _bwNode[_u] if (_bwNode[_u] < _bw[_i][_u]) else _bw[_i][_u]
                        _rttAux = _rttNode[_u] + _rtt[_i][_u]
                        _loss_p = _loss[_i][_u] / 100.0
                        _lossNode_p = _lossNode[_u] / 100.0

                        _lossAux = 1 - ((1 - _lossNode_p) * (1 - _loss_p))
                        #             lossAux = lossNode[u] * loss[u][i]
                        #             print str(bwNode[u]) + " " + str(bw[u][i])
                        _lossAux = _lossAux * 100
                        # estimate qoe based on qos
                        _start = self.appQoSStart(_bwAux, _lossAux, _rttAux)
                        _stcount = self.appQoSStcount(_bwAux, _lossAux, _rttAux)
                        _stlen = self.appQoSStlen(_bwAux, _lossAux, _rttAux)
                        _mos = self.QoECalc(_start, _stcount, _stlen)
                        #            print mos
                        # start = commands.getoutput("/home/mininet/exec/start.php " + str(bwAux) + " " + str(lossAux) + " " + str(rttAux))
                        # stcount = commands.getoutput("/home/mininet/exec/stcount.php " + str(bwAux) + " " + str(lossAux) + " " + str(rttAux))
                        # stlen = commands.getoutput("/home/mininet/exec/stlen.php " + str(bwAux) + " " + str(lossAux) + " " + str(rttAux))
                        # mos = commands.getoutput("/home/mininet/exec/qoe.php " + str(start) + " " + str(stcount) + " " + str(stlen))
                        _mos = round(_mos, 2)
                        if (float(_mos) > _mosNode[_i]) or ((float(_mos) == _mosNode[_i]) and (_bwAux > _bwNode[_i])):
                            _prevNode[_i] = _u
                            _mosNode[_i] = float(_mos)
                            _bwNode[_i] = _bwAux
                            _rttNode[_i] = _rttAux
                            _lossNode[_i] = _lossAux
                        # print "link" + str(u) + " " + str(i)
                        # print "Updated MOS: " + str(mosNode[i])

                        # if not visited -- include it to visit
                        if _visited[_i] == -1: _auxList.append(_i)
                # print auxList
                # print mosNode
                _visited[_u] = 1

        if dst == "all":
            _final_mos = -1
            _final_tp = -1
            _humanpath = []
            for _destination_elem in _destinations_array:
                _nopath = False
                _dstNodeAux = _nodes.index(_destination_elem)
                # _auxmap = {}
                # _auxmap["name"] = _destination_elem
                # _auxmap["mos"] = _mosNode[_dstNodeAux]
                # _auxmap["tp"] = _bwNode[_dstNodeAux]
                # _auxmap["ip"] = self.ip_from_host(_destination_elem)

                _auxhumanpath = []
                _auxu = _dstNodeAux
                while _auxu != _srcNode:
                    _auxhumanpath.append(_nodes[_auxu])
                    _auxu = _prevNode[_auxu]
                    if _auxu is None:
                        _nopath = True
                        break

                if _nopath:
                    continue

                _auxhumanpath.append(_nodes[_srcNode])

                # _auxmap["path"] = _auxhumanpath
                # _auxmap["best"] = False
                # descomentar para validar a composicao / derivacao do modelo
                # print "-----------------"
                # print "OBSERVADO: MOS: " + str(mosNode[dstNodeAux]) + " BW: " + str(bwNode[dstNodeAux]) + "RTT: " + str(rttNode[dstNodeAux])
                # self.calculateComposedMos(auxhumanpath)
                # print "----------------"

                if ((_mosNode[_dstNodeAux] > _final_mos) or (
                        (_mosNode[_dstNodeAux] == _final_mos) and (_bwNode[_dstNodeAux] > _final_tp))):
                    _final_mos = _mosNode[_dstNodeAux]
                    _final_tp = _bwNode[_dstNodeAux]
                    _humanpath = _auxhumanpath
                    _dstNode = _dstNodeAux
                    _best = _destination_elem

            if _final_mos == -1:
                result = dict(mos=-1, tp=-1, dst="", dest_ip="", path=[])
            else:
                result = dict(mos=_final_mos, tp=_final_tp, dst=_best, dest_ip=self.ip_from_host(_best),
                              path=_humanpath)
                self.deploy_any_path(_humanpath)

            return result

        # mypath = rmap.get(best).get("path")
        # for i in range(0, (len(mypath) - 2)):
        #   index2 = self.nodes.index(mypath[i+1])
        #   index1 = self.nodes.index(mypath[i])
        #   if self.bw[index1][index2] > 2000000.0:
        #       self.bw[index1][index2] = self.bw[index1][index2] - 2000000.0
        #   else:
        #       self.bw[index1][index2] = 0.0

        else:
            _humanpath = []
            _u = _dstNode
            _nopath = False
            while _u != _srcNode:
                if _u != -1:
                    print("U: " + str(_u) + " NU: " + _nodes[_u])
                _humanpath.append(_nodes[_u])
                _u = _prevNode[_u]
                if _u is None:
                    _nopath = True
                    break

            if _nopath:
                result = dict(mos=-1, tp=-1, dst="", dest_ip="", path=[])
            else:
                _humanpath.append(_nodes[_srcNode])

                # if self.mydict.get(src) == None:
                #    self.mydict[src] = {}
                #    self.mydict[src][dst] = {}
                # else:
                #    if self.mydict.get(src).get(dst) == None:
                #        self.mydict[src][dst] = {}

                # _auxmap={}
                # _auxmap["name"] = dst
                # _auxmap["mos"] = _mosNode[_dstNode]
                # _auxmap["tp"] = _bwNode[dstNode]
                # _auxmap["ip"] = self.ip_from_host(dst)
                # _auxmap["path"] = _humanpath
                # _auxmap["best"] = True #Se esta aqui, eh porque um video que esta entrando mandou dar deploy do melhor caminho

                # mypath = humanpath
                # for i in range(0, (len(mypath) - 2)):
                #   index2 = self.nodes.index(mypath[i+1])
                #   index1 = self.nodes.index(mypath[i])
                #   if self.bw[index1][index2] > 2000000.0:
                #       self.bw[index1][index2] = self.bw[index1][index2] - 2000000.0
                #   else:
                #       self.bw[index1][index2] = 0.0

                # self.mydict[src][dst] = auxmap

                # print (json.dumps(self.mydict, indent=4))
                self.deploy_any_path(_humanpath)
                result = dict(mos=_mosNode[_dstNode], tp=_bwNode[_dstNode], dst=_nodes[_dstNode],
                              dest_ip=self.ip_from_host(_nodes[_dstNode]), path=_humanpath)

            return result

    def calculateDistanceMetric(self, mos, bwDistance):
        return (5 - mos) + (0.1 * bwDistance)
        # return (5-mos) + bwDistance

    # utility function used to print the solution
    def printArr(self, dist):
        print("Vertex   Distance from Source")
        for i in range(self.numNodes):
            print("%s \t\t %f" % (self.nodes[i], dist[i]))

    def BellmanFordPrune(self, src):
        BIGNUMBER = 10000000000
        # Step 1: Initialize distances from src to all other vertices
        # as INFINITE

        if not self.nodes:
            return dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
        elif src == "test":
            return dict(mos=-1, tp=-1, dst="", dest_ip="", path="OK")

        distance = []
        predecessor = []

        for i in range(0, self.numNodes):
            distance.append(float("-Inf"))
            predecessor.append(None)
        src_i = self.nodes.index(src)
        distance[src_i] = 0
        print("SRC: " + str(src) + " INDEX: " + str(src_i) + " M1I " + str(self.nodes.index("m1")))

        bwNode = []
        rttNode = []
        lossNode = []
        mosNode = []
        bwDistanceNode = []

        # initialization
        for i in range(0, self.numNodes):
            bwNode.append(BIGNUMBER)
            rttNode.append(0)
            lossNode.append(0)
            mosNode.append(0)
            bwDistanceNode.append(BIGNUMBER)

        H = PATH_SIZE  # 20#self.numNodes - 1
        M = []
        M = [[float("-Inf") for x in range(0, len(self.nodes))] for y in range(0, H + 1)]

        for h in range(0, H + 1):
            M[h][src_i] = float("Inf")

        exitflag = 0
        destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
        for h in range(1, H + 1):
            print("----------------")
            for j in range(0, self.numNodes):
                M[h][j] = M[h - 1][j]
            MNext = deepcopy(M)
            # print("M[" + str(h) + "][143] = " + str(M[h][143]))
            for node in range(0, self.numNodes):
                for neighbour in range(0, self.numNodes):
                    if self.links[node][neighbour] == 1 and \
                            self.bw[neighbour][node] >= 360000 and \
                            self.loss[neighbour][node] <= 5:
                        bwAux = bwNode[node] if (bwNode[node] < self.bw[neighbour][node]) else self.bw[neighbour][node]
                        rttAux = rttNode[node] + self.rtt[neighbour][node]
                        # rttAux  = rttNode[neighbour] + self.rtt[neighbour][node]
                        loss_p = self.loss[neighbour][node] / 100.0
                        # lossNode_p = lossNode[neighbour] / 100.0
                        lossNode_p = lossNode[node] / 100.0
                        lossAux = 1 - ((1 - lossNode_p) * (1 - loss_p))
                        lossAux = lossAux * 100
                        # bwDistanceAux = bwDistanceNode[node]+ (BW_BITRATE/self.bw[neighbour][node])

                        # if bwAux >= BW_THRESHOLD:
                        #    bwDistanceAux = bwDistanceNode[node] + DISTANCE_FIX
                        # else:
                        #    bwDistanceAux = (PATH_SIZE*PATH_SIZE) / bwAux
                        # bwDistanceAux = 0.0

                        start = self.appQoSStart(bwAux, lossAux, rttAux)
                        stcount = self.appQoSStcount(bwAux, lossAux, rttAux)
                        stlen = self.appQoSStlen(bwAux, lossAux, rttAux)
                        mos = self.QoECalc(start, stcount, stlen)

                        # mos  = mos - (200000 / bwAux)
                        # distance[u] = 5.1 - mos
                        if (M[h][node] != float("-Inf")) and (bwAux > M[h][neighbour]) and (
                                (MNext[h][neighbour] == float("-Inf")) or (bwAux > MNext[h][neighbour])):
                            # if  (distance[node] != float("Inf")) and ((5.1 - mos) < distance[neighbour]):
                            # if (predecessor[neighbour] != None):
                            #    np = self.nodes[predecessor[neighbour]]
                            #    if (predecessor[predecessor[neighbour]] != None):
                            #        npp = self.nodes[predecessor[predecessor[neighbour]]]
                            #    else:
                            #        npp = "None"
                            # else:
                            #    np = "None"
                            #    npp = "None"
                            # print("Neigh: " + self.nodes[neighbour] + " N: " + self.nodes[node] + " MOS: " + str(mos) + " MH: " + str(M[h][neighbour]) + " OP: " + np + " FOP: " + npp)
                            predecessor[neighbour] = node
                            MNext[h][neighbour] = bwAux
                            distance[neighbour] = bwAux
                            mosNode[neighbour] = mos
                            rttNode[neighbour] = rttAux
                            bwNode[neighbour] = bwAux
                            lossNode[neighbour] = lossAux
                            # print(">> M[" + str(h) + "][143] = " + str(M[h][143]))

                            if self.nodes[neighbour] in destinations_array:
                                print("[RYU] FOUND: " + self.nodes[neighbour] + " MOS: " + str(mos) + " stlen: " + str(
                                    stlen) + " stcount: " + str(stcount) + " BW: " + str(bwAux))
                # if mos >= 5:
                #    exitflag = 1

            # bwDistance[neighbour] = bwDistanceAux
            # if exitflag == 1:
            #    break
            M = deepcopy(MNext)
            if exitflag == 1:
                break

        # for i in range(0, len(distance)):
        #   if(predecessor[i] == None):
        #     print("N: " + self.nodes[i] + " D: " + str(distance[i]) + " P: ")# + self.nodes[predecessor[i]])
        #   else:
        #     print("N: " + self.nodes[i] + " D: " + str(distance[i]) + " P: " + self.nodes[predecessor[i]])

        # print all distance
        maxbw = float("-Inf")
        dst = None
        humanpath = []
        maxlen = float("Inf")

        random.shuffle(destinations_array)

        for dest in destinations_array:
            dest_i = self.nodes.index(dest)
            print("[RYU] PREDEST: " + dest + " D: " + str(distance[dest_i]))
            if distance[dest_i] >= maxbw and distance[dest_i] > float("-Inf"):
                print("[RYU] DEST: " + dest + " D: " + str(distance[dest_i]))
                phumanpath = []
                phumanpath.append(self.nodes[dest_i])
                prev = predecessor[dest_i]

                while prev != src_i:
                    phumanpath.append(self.nodes[prev])
                    prev = predecessor[prev]

                phumanpath.append(self.nodes[src_i])
                plen = len(phumanpath)
                if (distance[dest_i] > maxbw) or ((distance[dest_i] == maxbw) and (plen < maxlen)):
                    maxlen = plen
                    humanpath = phumanpath
                    dst = self.nodes[dest_i]

                maxbw = distance[dest_i]

        if len(humanpath) > 0:
            self.deploy_any_path(humanpath)
            # pairarr = []
            # minbw = float("Inf")
            # for i in range(0, (len(humanpath) - 2)):
            #    index2 = self.nodes.index(humanpath[i+1])
            #    index1 = self.nodes.index(humanpath[i])
            #    paux = [index1, index2]
            #    pairarr.append(paux)
            #    if self.bw[index1][index2] < minbw:
            #        minbw = self.bw[index1][index2]
            #    #self.bw[index1][index2] = self.bw[index1][index2] - BW_BITRATE #indentar isso com o if acima
            #    #if self.bw[index1][index2] < 0:
            #    #    self.bw[index1][index2] = 1.0

            # if minbw < BW_BITRATE:
            #    for i in range(0, self.numNodes):
            #        for j in range(0, self.numNodes):
            #            auxp = [i, j]
            #            if auxp not in pairarr:
            #                self.bw[i][j] = self.bw[i][j] + BW_BITRATE
            # else:
            #    for pair in pairarr:
            #        self.bw[pair[0]][pair[1]] = self.bw[pair[0]][pair[1]] - BW_BITRATE

            for i in range(0, (len(humanpath) - 2)):
                index2 = self.nodes.index(humanpath[i + 1])
                index1 = self.nodes.index(humanpath[i])
                self.numFlowsRound[index1][index2] = self.numFlowsRound[index1][index2] + 1
                if self.bw[index1][index2] > 2 * BW_BITRATE:
                    self.bw[index1][index2] = self.bw[index1][index2] - BW_BITRATE  # indentar isso com o if acima
                # if self.bw[index1][index2] < 0:
                #    self.bw[index1][index2] = 10.0
                elif self.bw[index1][index2] > BW_BITRATE:
                    self.bw[index1][index2] = BW_BITRATE * (
                            float(self.numFlowsRound[index1][index2]) / float(self.numFlowsRound[index1][index2] + 1))
                else:
                    self.bw[index1][index2] = self.bw[index1][index2] * (
                            float(self.numFlowsRound[index1][index2]) / float(self.numFlowsRound[index1][index2] + 1))

            auxmap = {"name": dst, "mos": mosNode[self.nodes.index(dst)], "tp": bwNode[self.nodes.index(dst)],
                      "ip": self.ip_from_host(dst), "path": humanpath}

            if self.mydict.get(src) is None:
                self.mydict[src] = {}

            self.mydict[src][dst] = auxmap

            print("[RYU] " + str(auxmap))
            return dict(mos=auxmap["mos"], tp=auxmap["tp"], dst=dst, dest_ip=self.ip_from_host(dst), path=humanpath)
        else:
            return dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_ROUTE")

    def BellmanFord(self, src):
        BIGNUMBER = 10000000000
        # Step 1: Initialize distances from src to all other vertices
        # as INFINITE

        if not self.nodes:
            return dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
        elif src == "test":
            return dict(mos=-1, tp=-1, dst="", dest_ip="", path="OK")

        distance = []
        predecessor = []

        for i in range(0, self.numNodes):
            distance.append(float("-Inf"))
            predecessor.append(None)
        src_i = self.nodes.index(src)
        distance[src_i] = 0
        print("SRC: " + str(src) + " INDEX: " + str(src_i) + " M1I " + str(self.nodes.index("m1")))

        bwNode = []
        rttNode = []
        lossNode = []
        mosNode = []
        bwDistanceNode = []

        # initialization
        for i in range(0, self.numNodes):
            bwNode.append(BIGNUMBER)
            rttNode.append(0)
            lossNode.append(0)
            mosNode.append(0)
            bwDistanceNode.append(BIGNUMBER)

        H = PATH_SIZE  # 20#self.numNodes - 1
        M = []
        M = [[float("-Inf") for x in range(0, len(self.nodes))] for y in range(0, H + 1)]

        for h in range(0, H + 1):
            M[h][src_i] = float("Inf")

        exitflag = 0
        destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
        for h in range(1, H + 1):
            print("----------------")
            for j in range(0, self.numNodes):
                M[h][j] = M[h - 1][j]
            MNext = deepcopy(M)
            # print("M[" + str(h) + "][143] = " + str(M[h][143]))
            for node in range(0, self.numNodes):
                for neighbour in range(0, self.numNodes):
                    if self.links[node][neighbour] == 1:
                        bwAux = bwNode[node] if (bwNode[node] < self.bw[neighbour][node]) else self.bw[neighbour][node]
                        rttAux = rttNode[node] + self.rtt[neighbour][node]
                        # rttAux  = rttNode[neighbour] + self.rtt[neighbour][node]
                        loss_p = self.loss[neighbour][node] / 100.0
                        # lossNode_p = lossNode[neighbour] / 100.0
                        lossNode_p = lossNode[node] / 100.0
                        lossAux = 1 - ((1 - lossNode_p) * (1 - loss_p))
                        lossAux = lossAux * 100
                        # bwDistanceAux = bwDistanceNode[node]+ (BW_BITRATE/self.bw[neighbour][node])

                        # if bwAux >= BW_THRESHOLD:
                        #    bwDistanceAux = bwDistanceNode[node] + DISTANCE_FIX
                        # else:
                        #    bwDistanceAux = (PATH_SIZE*PATH_SIZE) / bwAux
                        # bwDistanceAux = 0.0

                        start = self.appQoSStart(bwAux, lossAux, rttAux)
                        stcount = self.appQoSStcount(bwAux, lossAux, rttAux)
                        stlen = self.appQoSStlen(bwAux, lossAux, rttAux)
                        mos = self.QoECalc(start, stcount, stlen)

                        # mos  = mos - (200000 / bwAux)
                        # distance[u] = 5.1 - mos
                        if (M[h][node] != float("-Inf")) and (bwAux > M[h][neighbour]) and (
                                (MNext[h][neighbour] == float("-Inf")) or (bwAux > MNext[h][neighbour])):
                            # if  (distance[node] != float("Inf")) and ((5.1 - mos) < distance[neighbour]): if (
                            # predecessor[neighbour] != None): np = self.nodes[predecessor[neighbour]] if (
                            # predecessor[predecessor[neighbour]] != None): npp = self.nodes[predecessor[predecessor[
                            # neighbour]]] else: npp = "None" else: np = "None" npp = "None" print("Neigh: " +
                            # self.nodes[neighbour] + " N: " + self.nodes[node] + " MOS: " + str(mos) + " MH: " +
                            # str(M[h][neighbour]) + " OP: " + np + " FOP: " + npp)
                            predecessor[neighbour] = node
                            MNext[h][neighbour] = bwAux
                            distance[neighbour] = bwAux
                            mosNode[neighbour] = mos
                            rttNode[neighbour] = rttAux
                            bwNode[neighbour] = bwAux
                            lossNode[neighbour] = lossAux
                            # print(">> M[" + str(h) + "][143] = " + str(M[h][143]))

                            if self.nodes[neighbour] in destinations_array:
                                print("[RYU] FOUND: " + self.nodes[neighbour] + " MOS: " + str(mos) + " stlen: " + str(
                                    stlen) + " stcount: " + str(stcount) + " BW: " + str(bwAux))
                # if mos >= 5:
                #    exitflag = 1

            # bwDistance[neighbour] = bwDistanceAux
            # if exitflag == 1:
            #    break
            M = deepcopy(MNext)
            if exitflag == 1:
                break

        # for i in range(0, len(distance)):
        #   if(predecessor[i] == None):
        #     print("N: " + self.nodes[i] + " D: " + str(distance[i]) + " P: ")# + self.nodes[predecessor[i]])
        #   else:
        #     print("N: " + self.nodes[i] + " D: " + str(distance[i]) + " P: " + self.nodes[predecessor[i]])

        # print all distance
        maxbw = float("-Inf")
        dst = None
        humanpath = []
        maxlen = float("Inf")

        random.shuffle(destinations_array)

        for dest in destinations_array:
            dest_i = self.nodes.index(dest)
            print("[RYU] PREDEST: " + dest + " D: " + str(distance[dest_i]))
            if distance[dest_i] >= maxbw and distance[dest_i] > float("-Inf"):
                print("[RYU] DEST: " + dest + " D: " + str(distance[dest_i]))
                phumanpath = []
                phumanpath.append(self.nodes[dest_i])
                prev = predecessor[dest_i]

                while prev != src_i:
                    phumanpath.append(self.nodes[prev])
                    prev = predecessor[prev]

                phumanpath.append(self.nodes[src_i])
                plen = len(phumanpath)
                if (distance[dest_i] > maxbw) or ((distance[dest_i] == maxbw) and (plen < maxlen)):
                    maxlen = plen
                    humanpath = phumanpath
                    dst = self.nodes[dest_i]

                maxbw = distance[dest_i]

        self.deploy_any_path(humanpath)
        # pairarr = []
        # minbw = float("Inf")
        # for i in range(0, (len(humanpath) - 2)):
        #    index2 = self.nodes.index(humanpath[i+1])
        #    index1 = self.nodes.index(humanpath[i])
        #    paux = [index1, index2]
        #    pairarr.append(paux)
        #    if self.bw[index1][index2] < minbw:
        #        minbw = self.bw[index1][index2]
        #    #self.bw[index1][index2] = self.bw[index1][index2] - BW_BITRATE #indentar isso com o if acima
        #    #if self.bw[index1][index2] < 0:
        #    #    self.bw[index1][index2] = 1.0

        # if minbw < BW_BITRATE:
        #    for i in range(0, self.numNodes):
        #        for j in range(0, self.numNodes):
        #            auxp = [i, j]
        #            if auxp not in pairarr:
        #                self.bw[i][j] = self.bw[i][j] + BW_BITRATE
        # else:
        #    for pair in pairarr:
        #        self.bw[pair[0]][pair[1]] = self.bw[pair[0]][pair[1]] - BW_BITRATE

        for i in range(0, (len(humanpath) - 2)):
            index2 = self.nodes.index(humanpath[i + 1])
            index1 = self.nodes.index(humanpath[i])
            self.numFlowsRound[index1][index2] = self.numFlowsRound[index1][index2] + 1
            if (self.bw[index1][index2] > 2 * BW_BITRATE):
                self.bw[index1][index2] = self.bw[index1][index2] - BW_BITRATE  # indentar isso com o if acima
            # if self.bw[index1][index2] < 0:
            #    self.bw[index1][index2] = 10.0
            elif (self.bw[index1][index2] > BW_BITRATE):
                self.bw[index1][index2] = BW_BITRATE * (
                        float(self.numFlowsRound[index1][index2]) / float(self.numFlowsRound[index1][index2] + 1))
            else:
                self.bw[index1][index2] = self.bw[index1][index2] * (
                        float(self.numFlowsRound[index1][index2]) / float(self.numFlowsRound[index1][index2] + 1))

        auxmap = {"name": dst, "mos": mosNode[self.nodes.index(dst)], "tp": bwNode[self.nodes.index(dst)],
                  "ip": self.ip_from_host(dst), "path": humanpath}

        if self.mydict.get(src) is None:
            self.mydict[src] = {}

        self.mydict[src][dst] = auxmap

        print("[RYU] " + str(auxmap))
        return dict(mos=auxmap["mos"], tp=auxmap["tp"], dst=dst, dest_ip=self.ip_from_host(dst), path=humanpath)

    def bestQoePath(self, src, dst):
        if not self.nodes:
            return dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
        elif src == "test":
            return dict(mos=-1, tp=-1, dst="", dest_ip="", path="OK")

        BIGNUMBER = 10000000000
        if dst == "all":
            destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
        else:
            destinations_array = [dst]

        bwNode = []
        rttNode = []
        lossNode = []
        mosNode = []
        prevNode = []
        visited = []

        # initialization
        for i in range(0, self.numNodes):
            bwNode.append(BIGNUMBER)
            rttNode.append(0)
            lossNode.append(0)
            prevNode.append(-1)
            visited.append(-1)

        src = self.nodes.index(src)

        visitedNode = [0 for x in range(len(self.nodes))]
        backtrackNode = [0 for x in range(len(self.nodes))]
        mosNode = [0 for x in range(len(self.nodes))]
        # distanceNode = [0 for x in range(len(self.nodes))]
        bwDistanceNode = [0 for x in range(len(self.nodes))]

        for i in range(0, self.numNodes):
            visitedNode[i] = False
            mosNode[i] = 0
            # distanceNode[i] = BIGNUMBER;
            bwDistanceNode[i] = BIGNUMBER

        q = queue.PriorityQueue()
        # distanceNode[src] = 0;
        bwDistanceNode[src] = 0
        gc = 0
        q.put((0, gc, src))
        humanpath = []
        final_md = -BIGNUMBER
        final_tp = -1
        dst = ""
        dest_ip = ""

        while not q.empty():
            p = q.get()
            node = p[2]
            # print "Expanding", nodes[node],p[0]
            visitedNode[node] = True
            local_md = 5 - self.calculateDistanceMetric(mosNode[node], bwDistanceNode[node])

            # if (self.nodes[node] in destinations_array):
            #    print "MN: " + str(mosNode[node]) + " BWD: " + str(bwDistanceNode[node])
            #    print "LMD:  " + str(local_md) +  " PP: " + str(5-p[0]) + " N: " + self.nodes[node] + " FM: " + str(final_md)
            #    print "DISTANCE: " + str(self.calculateDistanceMetric(mosNode[node], bwDistanceNode[node]))
            #    print "BWNODE: " + str(bwNode[node]) + " FINALTP: " + str(final_tp)

            if (5 - p[0]) < local_md:
                continue

            if ((self.nodes[node] in destinations_array) and (
                    (local_md > final_md) or ((local_md == final_md) and (bwNode[node] > final_tp)))):
                # print "found " +  str(mosNode[node]) + " D: " + self.nodes[node] + " BW: "+  str(bwNode[node])

                # if mosNode[node] < MOS_THRESHOLD:
                #   result = dict(mos = -1, tp = -1, dst = "", dest_ip = "", path = "NO_ROUTE")
                #   return result

                phumanpath = [self.nodes[node]]
                prev = prevNode[node]
                while prev != src:
                    phumanpath.append(self.nodes[prev])
                    prev = prevNode[prev]

                phumanpath.append(self.nodes[src])
                print("[RYU] found " + str(mosNode[node]) + " MD: " + str(local_md) + " D: " + self.nodes[
                    node] + " BW: " + str(
                    bwNode[node]) + " - " + str(phumanpath) + " DELAY: " + str(rttNode[node]))

                final_md = 5 - self.calculateDistanceMetric(mosNode[node], bwDistanceNode[node])
                final_tp = bwNode[node]
                dst = self.nodes[node]
                dest_ip = self.ip_from_host(dst)
                humanpath = phumanpath

            # if final_md > 1.1:
            # break
            # found = True

            indarr = range(len(self.nodes))
            random.shuffle(indarr)
            # print ">> Node: " + str(self.nodes[node])
            for neighbour in indarr:
                if self.links[neighbour][node] == 1:
                    # if self.nodes[neighbour] in destinations_array:
                    # print "Neighbour",self.nodes[neighbour], neighbour
                    visitedNode[neighbour] = True

                    bwAux = bwNode[node] if (bwNode[node] < self.bw[neighbour][node]) else self.bw[neighbour][node]
                    rttAux = rttNode[node] + self.rtt[neighbour][node]
                    # rttAux  = rttNode[neighbour] + self.rtt[neighbour][node]
                    loss_p = self.loss[neighbour][node] / 100.0
                    # lossNode_p = lossNode[neighbour] / 100.0
                    lossNode_p = lossNode[node] / 100.0
                    lossAux = 1 - ((1 - lossNode_p) * (1 - loss_p))
                    lossAux = lossAux * 100
                    bwDistanceAux = bwDistanceNode[node] + (BW_BITRATE / self.bw[neighbour][node])

                    # if bwAux >= BW_THRESHOLD:
                    #    bwDistanceAux = bwDistanceNode[node] + DISTANCE_FIX
                    # else:
                    #    bwDistanceAux = (PATH_SIZE*PATH_SIZE) / bwAux
                    # bwDistanceAux = 0.0

                    start = self.appQoSStart(bwAux, lossAux, rttAux)
                    stcount = self.appQoSStcount(bwAux, lossAux, rttAux)
                    stlen = self.appQoSStlen(bwAux, lossAux, rttAux)
                    mos = self.QoECalc(start, stcount, stlen)
                    # if self.calculateDistanceMetric(mos,bwDistanceAux) < 0:
                    # print "MD: " + str(self.calculateDistanceMetric(mos,bwDistanceAux)) + " MOS: " + str(mos) + " BW: " + str(bwAux) + " NODE: " + self.nodes[node] + " NEIGH: " + self.nodes[neighbour]
                    # return dict(mos = -1, tp = -1, dst = "", dest_ip="", path = "OK")
                    # mos = round(mos, 2)
                    if (self.calculateDistanceMetric(mos, bwDistanceAux) < (
                            self.calculateDistanceMetric(mosNode[neighbour],
                                                         bwDistanceNode[
                                                             neighbour]))):  # or ((float(mos) == mosNodenode) and (bwAux > bwNodenode))):
                        # print "NOVO: " + str(self.calculateDistanceMetric(mos,bwDistanceAux)) + " ANTIGO: " + str(self.calculateDistanceMetric(mosNode[neighbour],bwDistanceNode[neighbour])) + " MOS ANTIGO " + str(mosNode[neighbour]) + " MOS NOVO " + str(mos)
                        gc = gc + 1
                        prevNode[neighbour] = node
                        # distanceNode[neighbour] = distanceNode[node]+1;
                        bwDistanceNode[neighbour] = bwDistanceAux
                        mosNode[neighbour] = float(mos)
                        bwNode[neighbour] = bwAux
                        rttNode[neighbour] = rttAux
                        lossNode[neighbour] = lossAux
                        # print "Neighbour",self.nodes[neighbour], neighbour
                        q.put((self.calculateDistanceMetric(mos, bwDistanceNode[neighbour]), gc, neighbour))
        # print str(q)

        # self.mycount = self.mycount + 1

        src = self.nodes[src]
        deploy = True
        # if self.mydict.get(src) != None:
        #    if self.mydict.get(src).get(dst) != None:
        #        current_path = self.mydict.get(src).get(dst).get("path")
        #        old_mos = self.calculateComposedMos(current_path)
        #        if final_mos - old_mos < MOS_DIFF_THR:
        #            final_mos = old_mos
        #            final_tp = self.mydict.get(src).get(dst).get("tp")
        #            humanpath = current_path
        #            deploy = False

        for i in range(0, (len(humanpath) - 2)):
            index2 = self.nodes.index(humanpath[i + 1])
            index1 = self.nodes.index(humanpath[i])
            self.numFlowsRound[index1][index2] = self.numFlowsRound[index1][index2] + 1
            if self.bw[index1][index2] > 2 * BW_BITRATE:
                self.bw[index1][index2] = self.bw[index1][index2] - BW_BITRATE  # indentar isso com o if acima
            # if self.bw[index1][index2] < 0:
            #    self.bw[index1][index2] = 10.0
            elif self.bw[index1][index2] > BW_BITRATE:
                self.bw[index1][index2] = BW_BITRATE * (
                        float(self.numFlowsRound[index1][index2]) / float(self.numFlowsRound[index1][index2] + 1))
            else:
                self.bw[index1][index2] = self.bw[index1][index2] * (
                        float(self.numFlowsRound[index1][index2]) / float(self.numFlowsRound[index1][index2] + 1))

        result = dict(mos=final_md, tp=final_tp, dst=dst, dest_ip=dest_ip, path=humanpath)

        if deploy:
            self.deploy_any_path(humanpath)

        auxmap = {"name": dst, "mos": final_md, "tp": final_tp, "ip": dest_ip, "path": humanpath}

        if self.mydict.get(src) is None:
            self.mydict[src] = {}

        self.mydict[src][dst] = auxmap

        return result

    # Descr: Method responsible for search and list all possible paths between a given SRC and DST
    # Args: src: source host
    #       dst: destination host
    # Return: A dictionary with all possible paths between src and dst
    def all_paths_sd(self, src, dst):
        self.logger.info("<all_paths_sd> Path src: %s, dst: %s", src, dst)
        paths = list(nx.all_simple_paths(self.graph, src, dst))
        dict_path = {}
        for i, path in zip(range(0, len(paths)), paths):
            dict_path[i] = path

        self.possible_paths["%s-%s" % (src, dst)] = dict_path
        self.logger.info("Possible paths between src: %s and dst: %s\n%s", src, dst, json.dumps(dict_path, indent=4))
        return dict_path

    # TODO Improve it using Regex
    def switch_from_host(self, path):
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
                rindex = switch_index - ran_lower_bound + 1  # se switch_index = 3, p.e., 3 - 1 + 1 = 3
                return "r" + str(rindex)
            elif metro_lower_bound <= switch_index <= metro_upper_bound:
                mindex = switch_index - metro_lower_bound + 1  # se switch_index = 21, p.e., 21 - 21 + 1 = 1
                return "m" + str(mindex)
            elif access_lower_bound <= switch_index <= access_upper_bound:
                aindex = switch_index - access_lower_bound + 1
                return "a" + str(aindex)
            elif core_lower_bound <= switch_index <= core_upper_bound:
                cindex = switch_index - core_lower_bound + 1
                return "c" + str(cindex)
            elif internet_lower_bound <= switch_index <= internet_upper_bound:
                iindex = switch_index - internet_lower_bound + 1
                return "i" + str(iindex)
            else:
                return path
        else:
            return path

    def ip_from_host(self, host):
        if host == "src1":
            return "10.0.0.249"
        elif host == "src2":
            return "10.0.0.250"
        elif host == "cdn1":
            return "10.0.0.251"
        elif host == "cdn2":
            return "10.0.0.252"
        elif host == "cdn3":
            return "10.0.0.253"
        elif host == "ext1":
            return "10.0.0.254"
        elif host == "man1":
            return "10.0.0.241"
        elif host == "man2":
            return "10.0.0.242"
        elif host == "man3":
            return "10.0.0.243"
        elif host == "man4":
            return "10.0.0.244"
        else:
            first = host[0]
            if first == 'u':
                ipfinal = host.split("u")[1]
                return "10.0.0." + str(int(ipfinal))  # para remover os leading zeros
            elif first == 'r' or first == 'm' or first == 'a' or first == 'c' or first == 'i' or first == 's':
                sn = self.switch_from_host(host)
                print("LOCAL SN: " + sn)
                restsn = sn[1:]
                ipfinal = 200 + int(restsn)
                return "10.0.0." + str(ipfinal)

    def deploy_any_path(self, path):
        paths = [path, path[::-1]]
        for path in paths:
            for i in range(1, len(path) - 1):
                # instaling rule for the i switch
                sn = self.switch_from_host(path[i])
                dpid = int(sn[1:])
                _next = self.switch_from_host(path[i + 1])
                datapath = self.dp_dict[dpid]
                parser = datapath.ofproto_parser
                ofproto = datapath.ofproto

                out_port = self.edges_ports["s%s" % dpid][_next]
                actions = [parser.OFPActionOutput(out_port)]
                self.logger.info("installing rule from %s to %s %s %s", path[i], path[i + 1], str(path[0][1:]),
                                 str(path[-1][1:]))
                ip_src = self.ip_from_host(str(path[0]))  # to get the id
                ip_dst = self.ip_from_host(str(path[-1]))
                match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip_src, ipv4_dst=ip_dst)
                self.add_flow(datapath, 1024, match, actions)
        self.current_path = path

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
                        datapath = self.dp_dict[dpid]
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

    def get_graph(self):
        return self.graph

    # Descr: Function that parses the topology.txt file and creates a graph from it
    # Args: None
    def parse_graph(self):
        file = open('topology.txt', 'r')
        reg = re.compile('-eth([0-9]+):([\w]+)-eth[0-9]+')
        regSwitch = re.compile('(s[0-9]+) lo')

        for line in file:
            if "lo:" not in line:
                continue
            refnode = (regSwitch.match(line)).group(1)
            connections = line[8:]
            # print(refnode, connections)
            self.edges_ports.setdefault(refnode, {})
            for conn in reg.findall(connections):
                self.edges_ports[refnode][conn[1]] = int(conn[0])
                print(f'self.edges_ports[{refnode=}][{conn[1]=}] = {conn[0]=}')
                self.elist.append((refnode, conn[1])) if (conn[1], refnode) not in self.elist else None

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

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'widestpath-[a-z0-9\-]*'})
    def widest_path(self, req, **kwargs):
        if not self.bqoe_path_spp.nodes:
            result = dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
            body = json.dumps(result, indent=2)
            return Response(content_type='application/json', body=body, charset="UTF-8")

        src = kwargs['method'][11:].split('-')[0]
        dst = kwargs['method'][11:].split('-')[1]

        min_splen = 100000000
        min_sp = []
        humanpath = []

        if True:  # dst == "all":
            global_rtt = float("Inf")
            global_bw = float("-Inf")
            best_path = None
            destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
            for destination in destinations_array:
                paths = list(nx.all_simple_paths(self.bqoe_path_spp.get_graph(), src, destination, PATH_SIZE))
                for path_i in range(0, len(paths)):
                    path = paths[path_i]
                    min_bandwidth = float("Inf")
                    sum_rtt = 0.0
                    # print(str(path))
                    for i in range(len(path) - 2, -1, -1):
                        n1 = path[i + 1]
                        n2 = path[i]
                        # if n2 == "s1":
                        #    n2 = "m1"
                        # if n2 == "s2":
                        #    n2 = "a1"
                        # if n1 == "s1":
                        #    n1 = "m1"
                        # if n1 == "s2":
                        #    n1 = "a1"

                        n2 = self.bqoe_path_spp.host_from_switch(n2)
                        n1 = self.bqoe_path_spp.host_from_switch(n1)
                        # print "NODOS: " + n2 + " " + n1
                        index2 = self.bqoe_path_spp.nodes.index(n2)
                        index1 = self.bqoe_path_spp.nodes.index(n1)
                        # print ("CBW: " + str(self.bqoe_path_spp.bw[index1][index2]) + " MBW " + str(minbw))
                        if self.bqoe_path_spp.bw[index1][index2] < min_bandwidth:
                            min_bandwidth = self.bqoe_path_spp.bw[index1][index2]
                        sum_rtt = sum_rtt + self.bqoe_path_spp.rtt[index1][index2]

                    # print("B: " + str(minbw) + " R: " + str(sumrtt))
                    if min_bandwidth > global_bw:
                        global_bw = min_bandwidth
                        global_rtt = sum_rtt
                        best_path = path

                    if min_bandwidth == global_bw:
                        if sum_rtt < global_rtt:
                            global_bw = min_bandwidth
                            global_rtt = sum_rtt
                            best_path = path

            # splen = nx.shortest_path_length(graph,source=src,target=dest,weight='rtt')

            for p in reversed(best_path):
                ph = self.bqoe_path_spp.host_from_switch(p)
                # ph = p
                # if p == "s1":
                #   ph = "m1"
                # if p == "s2":
                #   ph = "a1"

                humanpath.append(ph)

            print("BW: " + str(global_bw) + " RTT: " + str(global_rtt) + " PATH: " + str(humanpath))

        final_mos = self.bqoe_path_spp.calculate_composed_mos(humanpath)

        result = dict(mos=final_mos, tp=global_bw, dst=humanpath[0],
                      dest_ip=self.bqoe_path_spp.ip_from_host(humanpath[0]), path=humanpath)
        self.bqoe_path_spp.deploy_any_path(humanpath)

        # pairarr = []
        # minbw = float("Inf")
        # for i in range(0, (len(humanpath) - 2)):
        #    index2 = self.bqoe_path_spp.nodes.index(humanpath[i+1])
        #    index1 = self.bqoe_path_spp.nodes.index(humanpath[i])
        #    paux = [index1, index2]
        #    pairarr.append(paux)
        #    if self.bqoe_path_spp.bw[index1][index2] < minbw:
        #        minbw = self.bqoe_path_spp.bw[index1][index2]
        #    #self.bw[index1][index2] = self.bw[index1][index2] - BW_BITRATE #indentar isso com o if acima
        #    #if self.bw[index1][index2] < 0:
        #    #    self.bw[index1][index2] = 1.0

        # if minbw < BW_BITRATE:
        #    for i in range(0, self.bqoe_path_spp.numNodes):
        #        for j in range(0, self.bqoe_path_spp.numNodes):
        #            auxp = [i, j]
        #            if auxp not in pairarr:
        #                self.bqoe_path_spp.bw[i][j] = self.bqoe_path_spp.bw[i][j] + BW_BITRATE
        # else:
        #    for pair in pairarr:
        #        self.bqoe_path_spp.bw[pair[0]][pair[1]] = self.bqoe_path_spp.bw[pair[0]][pair[1]] - BW_BITRATE

        for i in range(0, (len(humanpath) - 2)):
            index2 = self.bqoe_path_spp.nodes.index(humanpath[i + 1])
            index1 = self.bqoe_path_spp.nodes.index(humanpath[i])
            self.bqoe_path_spp.numFlowsRound[index1][index2] = self.bqoe_path_spp.numFlowsRound[index1][index2] + 1
            if self.bqoe_path_spp.bw[index1][index2] > 2 * BW_BITRATE:
                self.bqoe_path_spp.bw[index1][index2] = self.bqoe_path_spp.bw[index1][
                                                            index2] - BW_BITRATE  # indentar isso com o if acima
            # if self.bw[index1][index2] < 0:
            #    self.bw[index1][index2] = 10.0
            elif self.bqoe_path_spp.bw[index1][index2] > BW_BITRATE:
                self.bqoe_path_spp.bw[index1][index2] = BW_BITRATE * (
                        float(self.bqoe_path_spp.numFlowsRound[index1][index2]) / float(
                    self.bqoe_path_spp.numFlowsRound[index1][index2] + 1))
            else:
                self.bqoe_path_spp.bw[index1][index2] = self.bqoe_path_spp.bw[index1][index2] * (
                        float(self.bqoe_path_spp.numFlowsRound[index1][index2]) / float(
                    self.bqoe_path_spp.numFlowsRound[index1][index2] + 1))

        auxmap = {"name": humanpath[0], "mos": final_mos, "tp": global_bw,
                  "ip": self.bqoe_path_spp.ip_from_host(humanpath[0]), "path": humanpath}

        if self.bqoe_path_spp.mydict.get(src) is None:
            self.bqoe_path_spp.mydict[src] = {}

        self.bqoe_path_spp.mydict[src][humanpath[0]] = auxmap

        body = json.dumps(result, indent=4)
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'shortestpath-[a-z0-9\-]*'})
    def shortest_path(self, req, **kwargs):
        if not self.bqoe_path_spp.nodes:
            result = dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
            body = json.dumps(result, indent=2)
            return Response(content_type='application/json', body=body, charset="UTF-8")

        src = kwargs['method'][13:].split('-')[0]
        dst = kwargs['method'][13:].split('-')[1]
        print("[RYU] ---------------------------")
        # file = open('nm_last_results.csv','r')
        # temp = file.read().splitlines()
        # for line in temp:
        #  spl = line.split(';')
        #  l = len(spl)
        #  if l > 2:
        #    p1 = spl[0]
        #    p2 = spl[1]
        #    w = spl[2]

        #    p1 = self.bqoe_path_spp.switch_from_host(p1)
        #    p2 = self.bqoe_path_spp.switch_from_host(p2)

        # self.logger.info('*** %s -> %s (%s)', p1, p2, w)
        graph = self.bqoe_path_spp.get_graph()
        for u, v, d in graph.edges(data=True):
            p1 = self.bqoe_path_spp.host_from_switch(u)
            p2 = self.bqoe_path_spp.host_from_switch(v)
            d['rtt'] = self.bqoe_path_spp.rtt[self.bqoe_path_spp.nodes.index(p1)][self.bqoe_path_spp.nodes.index(p2)]
        #   if (u == p1 and v == p2) or (u == p2 and v == p1):
        #        d['rtt'] = float(w)

        # print(self.graph.edges(data=True))
        min_splen = 100000000
        min_sp = []
        if dst == "all":
            destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
            for dest in destinations_array:
                sp = nx.shortest_path(graph, source=src, target=dest, weight='rtt', method="dijkstra")
                splen = nx.shortest_path_length(graph, source=src, target=dest, weight='rtt')
                print("[RYU] DEST: " + dest + " LEN: " + str(splen) + " PATH " + str(sp) + " MIN: " + str(min_splen))
                if splen < min_splen:
                    min_sp = sp
                    min_splen = splen
        else:
            min_sp = nx.shortest_path(graph, source=src, target=dst, weight='rtt')

        humanmin_sp = [self.bqoe_path_spp.host_from_switch(elem) for elem in min_sp]
        print(min_sp, humanmin_sp)

        final_mos = self.bqoe_path_spp.calculate_composed_mos(humanmin_sp)
        final_tp = 10000000000
        for i in range(0, (len(humanmin_sp) - 2)):
            index2 = self.bqoe_path_spp.nodes.index(humanmin_sp[i + 1])
            index1 = self.bqoe_path_spp.nodes.index(humanmin_sp[i])
            if self.bqoe_path_spp.bw[index1][index2] < final_tp:
                final_tp = self.bqoe_path_spp.bw[index1][index2]
            self.bqoe_path_spp.bw[index1][index2] = self.bqoe_path_spp.bw[index1][index2] - BW_BITRATE
            if self.bqoe_path_spp.bw[index1][index2] < 0:
                self.bqoe_path_spp.bw[index1][index2] = 0.0

        result = dict(mos=final_mos, tp=final_tp, dst=humanmin_sp[0],
                      dest_ip=self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), path=humanmin_sp)
        self.bqoe_path_spp.deploy_any_path(humanmin_sp)

        auxmap = {"name": humanmin_sp[0], "mos": final_mos, "tp": final_tp,
                  "ip": self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), "path": humanmin_sp}

        if self.bqoe_path_spp.mydict.get(src) is None:
            self.bqoe_path_spp.mydict[src] = {}

        self.bqoe_path_spp.mydict[src][humanmin_sp[0]] = auxmap

        body = json.dumps(result, indent=4)
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'admweights-[a-z0-9\-]*'})
    def adm_weights(self, req, **kwargs):
        if not self.bqoe_path_spp.nodes:
            result = dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
            body = json.dumps(result, indent=2)
            return Response(content_type='application/json', body=body, charset="UTF-8")

        src = kwargs['method'][11:].split('-')[0]
        dst = kwargs['method'][11:].split('-')[1]
        # file = open('nm_last_results.csv','r')
        # temp = file.read().splitlines()
        # for line in temp:
        #  spl = line.split(';')
        #  l = len(spl)
        #  if l > 2:
        #    p1 = spl[0]
        #    p2 = spl[1]
        #    w = spl[2]

        #    p1 = self.bqoe_path_spp.switch_from_host(p1)
        #    p2 = self.bqoe_path_spp.switch_from_host(p2)

        # self.logger.info('*** %s -> %s (%s)', p1, p2, w)
        graph = self.bqoe_path_spp.get_graph()
        for u, v, d in graph.edges(data=True):
            p1 = self.bqoe_path_spp.host_from_switch(u)
            p2 = self.bqoe_path_spp.host_from_switch(v)
            # print "NOT AQUI " + p1 + " " + p2
            if ((p1 == "a2" and p2 == "a3") or (p1 == "c2" and p2 == "c1") or (p1 == "m5" and p2 == "m1") or (
                    p1 == "a1" and p2 == "a4") or (p1 == "m3" and p2 == "m2")):
                # print "AQUI " + p1 + " " + p2
                d['rtt'] = 1000
            elif p1 == "m5" and p2 == "m4":
                d['rtt'] = 3
            else:
                d['rtt'] = 1  # self.bqoe_path_spp.rtt[self.bqoe_path_spp.nodes.index(p1)][
                # self.bqoe_path_spp.nodes.index(p2)]
        #   if (u == p1 and v == p2) or (u == p2 and v == p1):
        #        d['rtt'] = float(w)

        # print(self.graph.edges(data=True))
        min_splen = 100000000
        min_sp = []
        if dst == "all":
            destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
            random.shuffle(destinations_array)
            for dest in destinations_array:
                print(dest)
                prev, dist = bellman_ford(graph, source=src, weight='rtt')
                # print str(prev)
                # print "---------------"
                # print str(dist)
                sp = [dest]
                pv = prev[dest]
                while pv != src:
                    sp.append(pv)
                    pv = prev[pv]
                sp.append(src)

                splen = dist[dest]
                print("DEST: " + dest + " LEN: " + str(splen) + " PATH " + str(sp) + " MIN: " + str(min_splen))
                if splen < min_splen:
                    min_sp = sp
                    min_splen = splen
        else:
            min_sp = nx.shortest_path(graph, source=src, target=dst, weight='rtt')

        humanmin_sp = [self.bqoe_path_spp.host_from_switch(elem) for elem in min_sp]

        final_mos = self.bqoe_path_spp.calculate_composed_mos(humanmin_sp)
        final_tp = 10000000000
        for i in range(0, (len(humanmin_sp) - 2)):
            index2 = self.bqoe_path_spp.nodes.index(humanmin_sp[i + 1])
            index1 = self.bqoe_path_spp.nodes.index(humanmin_sp[i])
            if self.bqoe_path_spp.bw[index1][index2] < final_tp:
                final_tp = self.bqoe_path_spp.bw[index1][index2]
        # self.bqoe_path_spp.bw[index1][index2] = self.bqoe_path_spp.bw[index1][index2] - BW_BITRATE
        # if self.bqoe_path_spp.bw[index1][index2] < 0:
        #    self.bqoe_path_spp.bw[index1][index2] = 0.0

        result = dict(mos=final_mos, tp=final_tp, dst=humanmin_sp[0],
                      dest_ip=self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), path=humanmin_sp)
        self.bqoe_path_spp.deploy_any_path(humanmin_sp)

        auxmap = {"name": humanmin_sp[0], "mos": final_mos, "tp": final_tp,
                  "ip": self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), "path": humanmin_sp}

        if self.bqoe_path_spp.mydict.get(src) is None:
            self.bqoe_path_spp.mydict[src] = {}

        self.bqoe_path_spp.mydict[src][humanmin_sp[0]] = auxmap

        body = json.dumps(result, indent=4)
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'pathtomanager-[a-z0-9\-]*'})
    def pathtomanager(self, req, **kwargs):
        # if not self.bqoe_path_spp.nodes:
        #     result = dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
        #     body = json.dumps(result, indent=2)
        #     return Response(content_type='application/json', body=body, charset="UTF-8")

        src = kwargs['method'][14:].split('-')[0]
        dst = kwargs['method'][14:].split('-')[1]

        graph = self.bqoe_path_spp.get_graph()
        for u, v, d in graph.edges(data=True):
            p1 = self.bqoe_path_spp.host_from_switch(u)
            p2 = self.bqoe_path_spp.host_from_switch(v)
            if ((p1 == "a2" and p2 == "a3") or (p1 == "c2" and p2 == "c1") or (p1 == "m5" and p2 == "m1") or (
                    p1 == "a1" and p2 == "a4") or (p1 == "m3" and p2 == "m2")):
                d['rtt'] = 1000
            elif p1 == "m5" and p2 == "m4":
                d['rtt'] = 3
            else:
                d['rtt'] = 1

        min_splen = 100000000
        min_sp = []
        if dst == "all":
            destinations_array = ["man1", "man2", "man3", "man4"]
            random.shuffle(destinations_array)
            for dest in destinations_array:
                print(dest)
                prev, dist = bellman_ford(graph, source=src, weight='rtt')
                sp = [dest]
                pv = prev[dest]
                while pv != src:
                    sp.append(pv)
                    pv = prev[pv]
                sp.append(src)

                splen = dist[dest]
                print("DEST: " + dest + " LEN: " + str(splen) + " PATH " + str(sp) + " MIN: " + str(min_splen))
                if splen < min_splen:
                    min_sp = sp
                    min_splen = splen
        else:
            print(f"src={src}, dst={dst}")
            min_sp = nx.shortest_path(graph, source=src, target=dst, weight='rtt')

        humanmin_sp = [self.bqoe_path_spp.host_from_switch(elem) for elem in min_sp]

        # final_mos = self.bqoe_path_spp.calculate_composed_mos(humanmin_sp)
        # final_tp = 10000000000
        # for i in range(0, (len(humanmin_sp) - 2)):
        #    index2 = self.bqoe_path_spp.nodes.index(humanmin_sp[i + 1])
        #    index1 = self.bqoe_path_spp.nodes.index(humanmin_sp[i])
        #    if self.bqoe_path_spp.bw[index1][index2] < final_tp:
        #        final_tp = self.bqoe_path_spp.bw[index1][index2]
        # self.bqoe_path_spp.bw[index1][index2] = self.bqoe_path_spp.bw[index1][index2] - BW_BITRATE
        # if self.bqoe_path_spp.bw[index1][index2] < 0:
        #    self.bqoe_path_spp.bw[index1][index2] = 0.0

        # result = {"mos": final_mos, "tp": final_tp, "dst": humanmin_sp[0],
        #          "dest_ip": self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), "path": humanmin_sp}
        result = {"dst": humanmin_sp[0],
                  "dest_ip": self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), "path": humanmin_sp}
        self.bqoe_path_spp.deploy_any_path(humanmin_sp)

        # auxmap = {"name": humanmin_sp[0], "mos": final_mos, "tp": final_tp,
        #          "ip": self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), "path": humanmin_sp}

        # if self.bqoe_path_spp.mydict.get(src) is None:
        #    self.bqoe_path_spp.mydict[src] = {}

        # self.bqoe_path_spp.mydict[src][humanmin_sp[0]] = auxmap

        body = json.dumps(result, indent=4)
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'bwbellmanford-[a-z0-9\-]*'})
    def bw_bellman_ford(self, req, **kwargs):
        if not self.bqoe_path_spp.nodes:
            result = dict(mos=-1, tp=-1, dst="", dest_ip="", path="NO_SNAPSHOT")
            body = json.dumps(result, indent=2)
            return Response(content_type='application/json', body=body, charset="UTF-8")

        src = kwargs['method'][14:].split('-')[0]
        dst = kwargs['method'][14:].split('-')[1]
        # file = open('nm_last_results.csv','r')
        # temp = file.read().splitlines()
        # for line in temp:
        #  spl = line.split(';')
        #  l = len(spl)
        #  if l > 2:
        #    p1 = spl[0]
        #    p2 = spl[1]
        #    w = spl[2]

        #    p1 = self.bqoe_path_spp.switch_from_host(p1)
        #    p2 = self.bqoe_path_spp.switch_from_host(p2)

        # self.logger.info('*** %s -> %s (%s)', p1, p2, w)
        graph = self.bqoe_path_spp.get_graph()
        for u, v, d in graph.edges(data=True):
            p1 = self.bqoe_path_spp.host_from_switch(u)
            p2 = self.bqoe_path_spp.host_from_switch(v)
            d['bw'] = 1 / (self.bqoe_path_spp.bw[self.bqoe_path_spp.nodes.index(p1)][
                               self.bqoe_path_spp.nodes.index(p2)] + 1.0)
        #   if (u == p1 and v == p2) or (u == p2 and v == p1):
        #        d['rtt'] = float(w)

        # print(self.graph.edges(data=True))
        min_splen = 100000000
        min_sp = []
        if dst == "all":
            destinations_array = ["cdn1", "cdn2", "cdn3", "ext1"]
            for dest in destinations_array:
                prev, dist = bellman_ford(graph, source=src, weight='bw')
                # print str(prev)
                # print "---------------"
                # print str(dist)
                sp = [dest]
                pv = prev[dest]
                while pv != src:
                    sp.append(pv)
                    pv = prev[pv]
                sp.append(src)

                splen = dist[dest]
                # print "DEST: " + dest + " LEN: " + str(splen) + " PATH " + str(sp) + " MIN: " + str(min_splen)
                if splen < min_splen:
                    min_sp = sp
                    min_splen = splen
        else:
            min_sp = nx.shortest_path(graph, source=src, target=dst, weight='rtt')

        humanmin_sp = []
        for elem in min_sp:
            humanmin_sp.append(self.bqoe_path_spp.host_from_switch(elem))

        final_mos = self.bqoe_path_spp.calculate_composed_mos(humanmin_sp)
        final_tp = 10000000000
        for i in range(0, (len(humanmin_sp) - 2)):
            index2 = self.bqoe_path_spp.nodes.index(humanmin_sp[i + 1])
            index1 = self.bqoe_path_spp.nodes.index(humanmin_sp[i])
            if self.bqoe_path_spp.bw[index1][index2] < final_tp:
                final_tp = self.bqoe_path_spp.bw[index1][index2]
        # self.bqoe_path_spp.bw[index1][index2] = self.bqoe_path_spp.bw[index1][index2] - BW_BITRATE
        # if self.bqoe_path_spp.bw[index1][index2] < 0:
        #    self.bqoe_path_spp.bw[index1][index2] = 0.0

        print(humanmin_sp[0] + " " + str(humanmin_sp) + " " + str(min_splen))
        result = dict(mos=final_mos, tp=final_tp, dst=humanmin_sp[0],
                      dest_ip=self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), path=humanmin_sp)
        self.bqoe_path_spp.deploy_any_path(humanmin_sp)

        auxmap = {"name": humanmin_sp[0], "mos": final_mos, "tp": final_tp,
                  "ip": self.bqoe_path_spp.ip_from_host(humanmin_sp[0]), "path": humanmin_sp}

        if self.bqoe_path_spp.mydict.get(src) is None:
            self.bqoe_path_spp.mydict[src] = {}

        self.bqoe_path_spp.mydict[src][humanmin_sp[0]] = auxmap

        body = json.dumps(result, indent=4)
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'bestqoepath-[a-z0-9\-]*'})
    def bestqoe_path(self, req, **kwargs):
        src = kwargs['method'][12:].split('-')[0]
        dst = kwargs['method'][12:].split('-')[1]

        # print(self.graph.edges(data=True))
        self.bqoe_path_spp.update_netmetric_snapshot()
        # qoeresult = self.bqoe_path_spp.bestQoePath(src, dst)
        # bestqoepath = qoeresult["path"]
        # self.bqoe_path_spp.deploy_any_path(bestqoepath)
        # body = json.dumps(qoeresult, indent=3)
        body = "OK"
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'deploybestqoepath-[a-z0-9\-]*'})
    def deploy_bestqoe_path(self, req, **kwargs):
        src = kwargs['method'][18:].split('-')[0]
        dst = kwargs['method'][18:].split('-')[1]
        print("[RYU] SRC: " + src + " DST: " + dst)
        # print(self.graph.edges(data=True))
        qoe_result = self.bqoe_path_spp.BellmanFordPrune(src)  # bestQoePath(src, dst)
        best_qoe_path = qoe_result["path"]
        # self.bqoe_path_spp.deploy_any_path(bestqoepath)
        body = json.dumps(qoe_result, indent=3)
        return Response(content_type='application/json', body=body, charset="UTF-8")

    @route('bqoepath', url, methods=['GET'], requirements={'method': r'deploy-h[0-9]+-h[0-9]+-[0-9]+'})
    def deploy_path(self, req, **kwargs):
        src = kwargs['method'][7:].split('-')[0]
        dst = kwargs['method'][7:].split('-')[1]
        rule_id = kwargs['method'][7:].split('-')[2]
        src_dst = src + '-' + dst
        self.bqoe_path_spp.deploy_rule(src_dst, rule_id)
