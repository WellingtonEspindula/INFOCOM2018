#!/usr/bin/python

# Projeto Final - Redes de Computadores I - CMP182 - 2016 - UFRGS
# Professor: Luciano Paschoal Gaspary
# Controlador para OpenFlow - Best QoE Path (BQoEP) - Seletor de melhor caminho baseado em predicao de QoE
# OpenFlow v. 1.3
# Desenvolvido por:
#    Roberto Costa Filho - 237091 - rtcosta@gmail.com

from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, Host, OVSKernelSwitch, OVSSwitch
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from subprocess import call, check_call, Popen, PIPE, STDOUT
from functools import partial
import os
import sys
import re
import time

hostIpMap = {}
switchesToAuxHosts = {}
rulesMap = []

def createHostAndManagerConf(net, hostName, hostIp, hostMac):
  #hostIp = hostIp.replace('.','\.')
  global hostIpMap
  with open( os.path.join('.','agent-fixa.xml'), "r" ) as source:
        with open( os.path.join('./manconfs','agent-fixa-' + hostName + '.xml'), "w" ) as target:
            for line in source:
                changed= re.sub(r'<manager-ip>.*</manager-ip>', '<manager-ip>' + hostIp + '</manager-ip>',line);
                target.write( changed )
            target.close()
        source.close()
  #print(hostIp)
  #sedparam = "s|\<manager-ip\>.*\<manager-ip\>|\<manager-ip\>" + hostIp + "\<manager-ip\>|g agent-fixa.xml > manconfs/agent-fixa-" + hostName + ".xml"
  #print(sedparam)
  #p = Popen(['sed', sedparam])
  hostIpMap[hostName] = hostIp
  return net.addHost(hostName, ip=hostIp, mac=hostMac)


def simpleCreateHost(net, hostName, hostIp, hostMac):
  #hostIp = hostIp.replace('.','\.')
  global hostIpMap
  hostIpMap[hostName] = hostIp
  return net.addHost(hostName, ip=hostIp, mac=hostMac)


def addRule(switchName, reqIp, portOut):
  routeParam = 'priority=1024,ip,nw_dst=' + reqIp + ',actions=output:' + portOut
  print(routeParam)
  p = Popen(['ovs-ofctl', 'add-flow', switchName, routeParam, '-O OpenFlow13']) 
  p.wait()

def linkSwitchToHost(net, host, switch, portHost, portSwitch, isAux, degradation):
  global switchesToAuxHosts
  global rulesMap
  net.addLink(host, switch, portHost, portSwitch, **degradation)
  if(isAux):
    switchesToAuxHosts[switch] = host
  rulesMap.append(dict(name = switch.name, ip = hostIpMap[host.name], port = str(portSwitch)))
  # addRule(switch.name, hostIpMap[host.name], str(portSwitch))

def linkSwitchToSwitch(net, sA, sB, pA, pB, degradation):
  global rulesMap
  net.addLink(sA, sB, pA, pB, **degradation)
  ipA = hostIpMap[switchesToAuxHosts[sA].name]
  ipB = hostIpMap[switchesToAuxHosts[sB].name]

  # addRule(sA.name, ipB, str(pA))
  rulesMap.append(dict(name = sA.name, ip = ipB, port = str(pA)))

  # addRule(sB.name, ipA, str(pB))
  rulesMap.append(dict(name = sB.name, ip = ipA, port = str(pB)))

def deployFlowRules():
  for rule in rulesMap:
    addRule(rule['name'], rule['ip'], rule['port'])

def evalTopo():
  "Service Provider Topology"
  switch = partial ( OVSSwitch, protocols="OpenFlow13" )
  #switch = partial ( OVSSwitch, protocols="sp" )
  net = Mininet( topo=None, controller=RemoteController, switch=switch, autoStaticArp=True, link=TCLink )

  net.addController( 'c0', RemoteController, ip="127.0.0.1", port=6633 )

  # linkopts1 = dict(bw=1, delay='150ms' )
  # linkopts2 = dict(bw=2, delay='80ms' )
  link100Mbps = dict(bw=20, delay='15ms' )
  link1Gbps = dict(bw=200, delay='5ms')
  link10Gbps = dict(bw=200, delay='5ms') #Sim, por enquanto vamos deixar o link de 10G igual ao de 1G
  linknodeg = dict()

  link100Mbps_1 = dict(bw=20, delay='1ms')
  link100Mbps_4 = dict(bw=20, delay='4ms')
  link100Mbps_5 = dict(bw=20, delay='5ms')
  link100Mbps_6 = dict(bw=20, delay='6ms')
  link100Mbps_7 = dict(bw=20, delay='7ms')
  link100Mbps_8 = dict(bw=20, delay='8ms')
  link100Mbps_9 = dict(bw=20, delay='9ms')
  link100Mbps_10 = dict(bw=20, delay='10ms')
  link100Mbps_11 = dict(bw=20, delay='11ms')
  
  link1Gbps_1 = dict(bw=200, delay='1ms')
  link1Gbps_12 = dict(bw=200, delay='12ms')
  link1Gbps_15 = dict(bw=200, delay='15ms')
  link1Gbps_18 = dict(bw=200, delay='18ms')
  link1Gbps_20 = dict(bw=200, delay='20ms')
  link1Gbps_23 = dict(bw=200, delay='23ms')
  link1Gbps_25 = dict(bw=200, delay='25ms')
  link1Gbps_30 = dict(bw=200, delay='30ms')




  #net.addLink(Host1,   Switch1,    **linkopts )
  # Adding switches
  s1 = net.addSwitch('s1')    #R1
  s2 = net.addSwitch('s2')    #R2
  s3 = net.addSwitch('s3')    #R3
  s4 = net.addSwitch('s4')    #R4
  s5 = net.addSwitch('s5')    #R5
  s6 = net.addSwitch('s6')    #R6
  s7 = net.addSwitch('s7')    #R7
  s8 = net.addSwitch('s8')    #R8
  s9 = net.addSwitch('s9')    #R9
  s10 = net.addSwitch('s10')  #R10
  s11 = net.addSwitch('s11')  #R11
  s12 = net.addSwitch('s12')  #R12
  s13 = net.addSwitch('s13')  #R13
  s14 = net.addSwitch('s14')  #R14
  s15 = net.addSwitch('s15')  #R15
  s16 = net.addSwitch('s16')  #R16
  s17 = net.addSwitch('s17')  #R17
  s18 = net.addSwitch('s18')  #R18
  s19 = net.addSwitch('s19')  #R19
  s20 = net.addSwitch('s20')  #R20
  s21 = net.addSwitch('s21')  #M1
  s22 = net.addSwitch('s22')  #M2
  s23 = net.addSwitch('s23')  #M3
  s24 = net.addSwitch('s24')  #M4
  s25 = net.addSwitch('s25')  #M5
  s26 = net.addSwitch('s26')  #A1
  s27 = net.addSwitch('s27')  #A2
  s28 = net.addSwitch('s28')  #A3
  s29 = net.addSwitch('s29')  #A4
  s30 = net.addSwitch('s30')  #C1
  s31 = net.addSwitch('s31')  #C2
  s32 = net.addSwitch('s32')  #C3
  s33 = net.addSwitch('s33')  #C4
  s34 = net.addSwitch('s34')  #I1 (Internet)


  # Adding nodes
  # h1 - h99 - Host / End-user
  # h100 - Video server
  # h1 = net.addHost('h1', ip='10.0.0.1', mac='00:04:00:00:00:01')
  # h2 = net.addHost('h2', ip='10.0.0.2', mac='00:04:00:00:00:02')
  # h99 = net.addHost('h99', ip='10.0.0.99', mac='00:04:00:00:00:99')

  #1.   DESTINATIONS
  #1.1. CREATING HOSTS
  #src1 = createHostAndManagerConf(net, 'src1', '10.0.0.249', '00:04:00:00:02:49')
  #src2 = createHostAndManagerConf(net, 'src2', '10.0.0.250', '00:04:00:00:02:50')
  cdn1 = createHostAndManagerConf(net, 'cdn1', '10.0.0.251', '00:04:00:00:02:51')
  cdn2 = createHostAndManagerConf(net, 'cdn2', '10.0.0.252', '00:04:00:00:02:52')
  cdn3 = createHostAndManagerConf(net, 'cdn3', '10.0.0.253', '00:04:00:00:02:53')
  ext1 = createHostAndManagerConf(net, 'ext1', '10.0.0.254', '00:04:00:00:02:54')
  
  #1.2. CREATING LINKS
  #linkSwitchToHost(net, src1, s4, 0, 99, False, linknodeg)
  #linkSwitchToHost(net, src2, s7, 0, 99, False, linknodeg)
  linkSwitchToHost(net, cdn1, s25, 0, 99, False, link100Mbps_1)
  linkSwitchToHost(net, cdn2, s29, 0, 99, False, link1Gbps_1)
  linkSwitchToHost(net, cdn3, s31, 0, 99, False, link1Gbps_1)
  linkSwitchToHost(net, ext1, s34, 0, 99, False, link1Gbps_30)

  #2.   SWITCH PROCESSING
  #2.1. CREATING HOSTS
  r1 = createHostAndManagerConf(net, 'r1', '10.0.0.201', '00:04:00:00:0F:01')
  r2 = createHostAndManagerConf(net, 'r2', '10.0.0.202', '00:04:00:00:0F:02')
  r3 = createHostAndManagerConf(net, 'r3', '10.0.0.203', '00:04:00:00:0F:03')
  r4 = createHostAndManagerConf(net, 'r4', '10.0.0.204', '00:04:00:00:0F:04')
  r5 = createHostAndManagerConf(net, 'r5', '10.0.0.205', '00:04:00:00:0F:05')
  r6 = createHostAndManagerConf(net, 'r6', '10.0.0.206', '00:04:00:00:0F:06')
  r7 = createHostAndManagerConf(net, 'r7', '10.0.0.207', '00:04:00:00:0F:07')
  r8 = createHostAndManagerConf(net, 'r8', '10.0.0.208', '00:04:00:00:0F:08')
  r9 = createHostAndManagerConf(net, 'r9', '10.0.0.209', '00:04:00:00:0F:09')
  r10 = createHostAndManagerConf(net, 'r10', '10.0.0.210', '00:04:00:00:0F:10')
  r11 = createHostAndManagerConf(net, 'r11', '10.0.0.211', '00:04:00:00:0F:11')
  r12 = createHostAndManagerConf(net, 'r12', '10.0.0.212', '00:04:00:00:0F:12')
  r13 = createHostAndManagerConf(net, 'r13', '10.0.0.213', '00:04:00:00:0F:13')
  r14 = createHostAndManagerConf(net, 'r14', '10.0.0.214', '00:04:00:00:0F:14')
  r15 = createHostAndManagerConf(net, 'r15', '10.0.0.215', '00:04:00:00:0F:15')
  r16 = createHostAndManagerConf(net, 'r16', '10.0.0.216', '00:04:00:00:0F:16')
  r17 = createHostAndManagerConf(net, 'r17', '10.0.0.217', '00:04:00:00:0F:17')
  r18 = createHostAndManagerConf(net, 'r18', '10.0.0.218', '00:04:00:00:0F:18')
  r19 = createHostAndManagerConf(net, 'r19', '10.0.0.219', '00:04:00:00:0F:19')
  r20 = createHostAndManagerConf(net, 'r20', '10.0.0.220', '00:04:00:00:0F:20')
  m1 = createHostAndManagerConf(net, 'm1', '10.0.0.221', '00:04:00:00:0F:21')
  m2 = createHostAndManagerConf(net, 'm2', '10.0.0.222', '00:04:00:00:0F:22')
  m3 = createHostAndManagerConf(net, 'm3', '10.0.0.223', '00:04:00:00:0F:23')
  m4 = createHostAndManagerConf(net, 'm4', '10.0.0.224', '00:04:00:00:0F:24')
  m5 = createHostAndManagerConf(net, 'm5', '10.0.0.225', '00:04:00:00:0F:25')
  a1 = createHostAndManagerConf(net, 'a1', '10.0.0.226', '00:04:00:00:0F:26')
  a2 = createHostAndManagerConf(net, 'a2', '10.0.0.227', '00:04:00:00:0F:27')
  a3 = createHostAndManagerConf(net, 'a3', '10.0.0.228', '00:04:00:00:0F:28')
  a4 = createHostAndManagerConf(net, 'a4', '10.0.0.229', '00:04:00:00:0F:29')
  c1 = createHostAndManagerConf(net, 'c1', '10.0.0.230', '00:04:00:00:0F:30')
  c2 = createHostAndManagerConf(net, 'c2', '10.0.0.231', '00:04:00:00:0F:31')
  c3 = createHostAndManagerConf(net, 'c3', '10.0.0.232', '00:04:00:00:0F:32')
  c4 = createHostAndManagerConf(net, 'c4', '10.0.0.233', '00:04:00:00:0F:33')
  i1 = createHostAndManagerConf(net, 'i1', '10.0.0.234', '00:04:00:00:0F:34')


  #2.2. CREATING LINKS
  linkSwitchToHost(net, r1, s1, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r2, s2, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r3, s3, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r4, s4, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r5, s5, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r6, s6, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r7, s7, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r8, s8, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r9, s9, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r10, s10, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r11, s11, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r12, s12, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r13, s13, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r14, s14, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r15, s15, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r16, s16, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r17, s17, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r18, s18, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r19, s19, 0, 100, True, linknodeg)
  linkSwitchToHost(net, r20, s20, 0, 100, True, linknodeg)
  linkSwitchToHost(net, m1, s21, 0, 100, True, linknodeg)
  linkSwitchToHost(net, m2, s22, 0, 100, True, linknodeg)
  linkSwitchToHost(net, m3, s23, 0, 100, True, linknodeg)
  linkSwitchToHost(net, m4, s24, 0, 100, True, linknodeg)
  linkSwitchToHost(net, m5, s25, 0, 100, True, linknodeg)
  linkSwitchToHost(net, a1, s26, 0, 100, True, linknodeg)
  linkSwitchToHost(net, a2, s27, 0, 100, True, linknodeg)
  linkSwitchToHost(net, a3, s28, 0, 100, True, linknodeg)
  linkSwitchToHost(net, a4, s29, 0, 100, True, linknodeg)
  linkSwitchToHost(net, c1, s30, 0, 100, True, linknodeg)
  linkSwitchToHost(net, c2, s31, 0, 100, True, linknodeg)
  linkSwitchToHost(net, c3, s32, 0, 100, True, linknodeg)
  linkSwitchToHost(net, c4, s33, 0, 100, True, linknodeg)
  linkSwitchToHost(net, i1, s34, 0, 100, True, linknodeg)
 
  #3. CREATING LINKS BETWEEN SWITCHES
  #Level 3.1 - RAN / Metro
  linkSwitchToSwitch(net, s1, s21, 31, 1, link100Mbps_6)
  linkSwitchToSwitch(net, s2, s21, 31, 2, link100Mbps_8)
  linkSwitchToSwitch(net, s3, s21, 31, 3, link100Mbps_6)
  linkSwitchToSwitch(net, s4, s21, 31, 4, link100Mbps_7)

  linkSwitchToSwitch(net, s5, s22, 31, 1, link100Mbps_4)
  linkSwitchToSwitch(net, s6, s22, 31, 2, link100Mbps_4)
  linkSwitchToSwitch(net, s7, s22, 31, 3, link100Mbps_4)
  linkSwitchToSwitch(net, s8, s22, 31, 4, link100Mbps_6)

  linkSwitchToSwitch(net, s9, s23, 31, 1, link100Mbps_9)
  linkSwitchToSwitch(net, s10, s23, 31, 2, link100Mbps_8)
  linkSwitchToSwitch(net, s11, s23, 31, 3, link100Mbps_4)
  linkSwitchToSwitch(net, s12, s23, 31, 4, link100Mbps_5)

  linkSwitchToSwitch(net, s13, s24, 31, 1, link100Mbps_8)
  linkSwitchToSwitch(net, s14, s24, 31, 2, link100Mbps_8)
  linkSwitchToSwitch(net, s15, s24, 31, 3, link100Mbps_7)
  linkSwitchToSwitch(net, s16, s24, 31, 4, link100Mbps_4)

  linkSwitchToSwitch(net, s17, s25, 31, 1, link100Mbps_4)
  linkSwitchToSwitch(net, s18, s25, 31, 2, link100Mbps_6)
  linkSwitchToSwitch(net, s19, s25, 31, 3, link100Mbps_7)
  linkSwitchToSwitch(net, s20, s25, 31, 4, link100Mbps_4)

  #Level 3.1.5 - Metro Ring
  linkSwitchToSwitch(net, s21, s22, 5, 5, link100Mbps_9)
  linkSwitchToSwitch(net, s22, s23, 6, 6, link100Mbps_6)
  linkSwitchToSwitch(net, s23, s24, 5, 5, link100Mbps_11)
  linkSwitchToSwitch(net, s24, s25, 6, 6, link100Mbps_5)
  linkSwitchToSwitch(net, s25, s21, 5, 6, link100Mbps_10) #Link to close ring

  #Level 3.2 - Metro / Access
  linkSwitchToSwitch(net, s22, s27, 7, 1, link1Gbps_20)
  linkSwitchToSwitch(net, s23, s28, 7, 1, link1Gbps_30)

  #Level 3.2.5 - Access ring
  linkSwitchToSwitch(net, s26, s27, 3, 3, link1Gbps_18)
  linkSwitchToSwitch(net, s27, s28, 2, 2, link1Gbps_20)
  linkSwitchToSwitch(net, s28, s29, 3, 3, link1Gbps_25)
  linkSwitchToSwitch(net, s29, s26, 2, 2, link1Gbps_23) #Link to close ring

  #Level 3.3 - Access / Core
  linkSwitchToSwitch(net, s26, s30, 4, 1, link1Gbps_20)
  linkSwitchToSwitch(net, s27, s30, 4, 2, link1Gbps_15)
  linkSwitchToSwitch(net, s28, s31, 4, 1, link1Gbps_25)
  linkSwitchToSwitch(net, s29, s31, 4, 2, link1Gbps_30)

  #Level 3.4 - Full-mesh Core
  linkSwitchToSwitch(net, s30, s31, 3, 3, link1Gbps_12)
  linkSwitchToSwitch(net, s30, s32, 4, 4, link1Gbps_20)
  linkSwitchToSwitch(net, s30, s33, 5, 5, link1Gbps_18)
  linkSwitchToSwitch(net, s31, s32, 5, 5, link1Gbps_23)
  linkSwitchToSwitch(net, s31, s33, 4, 4, link1Gbps_30)
  linkSwitchToSwitch(net, s32, s33, 3, 3, link1Gbps_15)

  #Level 3.5 - Core / Internet
  linkSwitchToSwitch(net, s32, s34, 1, 1, link1Gbps_25)
  linkSwitchToSwitch(net, s33, s34, 1, 2, link1Gbps_30)

  #4. SOURCES
  #4.1. CREATING HOSTS
  u001 = simpleCreateHost(net, 'u001', '10.0.0.1', '00:04:00:00:00:01')
  u002 = simpleCreateHost(net, 'u002', '10.0.0.2', '00:04:00:00:00:02')
  u003 = simpleCreateHost(net, 'u003', '10.0.0.3', '00:04:00:00:00:03')
  u004 = simpleCreateHost(net, 'u004', '10.0.0.4', '00:04:00:00:00:04')
  u005 = simpleCreateHost(net, 'u005', '10.0.0.5', '00:04:00:00:00:05')
  u006 = simpleCreateHost(net, 'u006', '10.0.0.6', '00:04:00:00:00:06')
  u007 = simpleCreateHost(net, 'u007', '10.0.0.7', '00:04:00:00:00:07')
  u008 = simpleCreateHost(net, 'u008', '10.0.0.8', '00:04:00:00:00:08')
  u009 = simpleCreateHost(net, 'u009', '10.0.0.9', '00:04:00:00:00:09')
  u010 = simpleCreateHost(net, 'u010', '10.0.0.10', '00:04:00:00:00:10')
  u011 = simpleCreateHost(net, 'u011', '10.0.0.11', '00:04:00:00:00:11')
  u012 = simpleCreateHost(net, 'u012', '10.0.0.12', '00:04:00:00:00:12')
  u013 = simpleCreateHost(net, 'u013', '10.0.0.13', '00:04:00:00:00:13')
  u014 = simpleCreateHost(net, 'u014', '10.0.0.14', '00:04:00:00:00:14')
  u015 = simpleCreateHost(net, 'u015', '10.0.0.15', '00:04:00:00:00:15')
  u016 = simpleCreateHost(net, 'u016', '10.0.0.16', '00:04:00:00:00:16')
  u017 = simpleCreateHost(net, 'u017', '10.0.0.17', '00:04:00:00:00:17')
  u018 = simpleCreateHost(net, 'u018', '10.0.0.18', '00:04:00:00:00:18')
  u019 = simpleCreateHost(net, 'u019', '10.0.0.19', '00:04:00:00:00:19')
  u020 = simpleCreateHost(net, 'u020', '10.0.0.20', '00:04:00:00:00:20')
  u021 = simpleCreateHost(net, 'u021', '10.0.0.21', '00:04:00:00:00:21')
  u022 = simpleCreateHost(net, 'u022', '10.0.0.22', '00:04:00:00:00:22')
  u023 = simpleCreateHost(net, 'u023', '10.0.0.23', '00:04:00:00:00:23')
  u024 = simpleCreateHost(net, 'u024', '10.0.0.24', '00:04:00:00:00:24')
  u025 = simpleCreateHost(net, 'u025', '10.0.0.25', '00:04:00:00:00:25')
  u026 = simpleCreateHost(net, 'u026', '10.0.0.26', '00:04:00:00:00:26')
  u027 = simpleCreateHost(net, 'u027', '10.0.0.27', '00:04:00:00:00:27')
  u028 = simpleCreateHost(net, 'u028', '10.0.0.28', '00:04:00:00:00:28')
  u029 = simpleCreateHost(net, 'u029', '10.0.0.29', '00:04:00:00:00:29')
  u030 = simpleCreateHost(net, 'u030', '10.0.0.30', '00:04:00:00:00:30')
  u031 = simpleCreateHost(net, 'u031', '10.0.0.31', '00:04:00:00:00:31')
  u032 = simpleCreateHost(net, 'u032', '10.0.0.32', '00:04:00:00:00:32')
  u033 = simpleCreateHost(net, 'u033', '10.0.0.33', '00:04:00:00:00:33')
  u034 = simpleCreateHost(net, 'u034', '10.0.0.34', '00:04:00:00:00:34')
  u035 = simpleCreateHost(net, 'u035', '10.0.0.35', '00:04:00:00:00:35')
  u036 = simpleCreateHost(net, 'u036', '10.0.0.36', '00:04:00:00:00:36')
  u037 = simpleCreateHost(net, 'u037', '10.0.0.37', '00:04:00:00:00:37')
  u038 = simpleCreateHost(net, 'u038', '10.0.0.38', '00:04:00:00:00:38')
  u039 = simpleCreateHost(net, 'u039', '10.0.0.39', '00:04:00:00:00:39')
  u040 = simpleCreateHost(net, 'u040', '10.0.0.40', '00:04:00:00:00:40')
  u041 = simpleCreateHost(net, 'u041', '10.0.0.41', '00:04:00:00:00:41')
  u042 = simpleCreateHost(net, 'u042', '10.0.0.42', '00:04:00:00:00:42')
  u043 = simpleCreateHost(net, 'u043', '10.0.0.43', '00:04:00:00:00:43')
  u044 = simpleCreateHost(net, 'u044', '10.0.0.44', '00:04:00:00:00:44')
  u045 = simpleCreateHost(net, 'u045', '10.0.0.45', '00:04:00:00:00:45')
  u046 = simpleCreateHost(net, 'u046', '10.0.0.46', '00:04:00:00:00:46')
  u047 = simpleCreateHost(net, 'u047', '10.0.0.47', '00:04:00:00:00:47')
  u048 = simpleCreateHost(net, 'u048', '10.0.0.48', '00:04:00:00:00:48')
  u049 = simpleCreateHost(net, 'u049', '10.0.0.49', '00:04:00:00:00:49')
  u050 = simpleCreateHost(net, 'u050', '10.0.0.50', '00:04:00:00:00:50')
  u051 = simpleCreateHost(net, 'u051', '10.0.0.51', '00:04:00:00:00:51')
  u052 = simpleCreateHost(net, 'u052', '10.0.0.52', '00:04:00:00:00:52')
  u053 = simpleCreateHost(net, 'u053', '10.0.0.53', '00:04:00:00:00:53')
  u054 = simpleCreateHost(net, 'u054', '10.0.0.54', '00:04:00:00:00:54')
  u055 = simpleCreateHost(net, 'u055', '10.0.0.55', '00:04:00:00:00:55')
  u056 = simpleCreateHost(net, 'u056', '10.0.0.56', '00:04:00:00:00:56')
  u057 = simpleCreateHost(net, 'u057', '10.0.0.57', '00:04:00:00:00:57')
  u058 = simpleCreateHost(net, 'u058', '10.0.0.58', '00:04:00:00:00:58')
  u059 = simpleCreateHost(net, 'u059', '10.0.0.59', '00:04:00:00:00:59')
  u060 = simpleCreateHost(net, 'u060', '10.0.0.60', '00:04:00:00:00:60')
  u061 = simpleCreateHost(net, 'u061', '10.0.0.61', '00:04:00:00:00:61')
  u062 = simpleCreateHost(net, 'u062', '10.0.0.62', '00:04:00:00:00:62')
  u063 = simpleCreateHost(net, 'u063', '10.0.0.63', '00:04:00:00:00:63')
  u064 = simpleCreateHost(net, 'u064', '10.0.0.64', '00:04:00:00:00:64')
  u065 = simpleCreateHost(net, 'u065', '10.0.0.65', '00:04:00:00:00:65')
  u066 = simpleCreateHost(net, 'u066', '10.0.0.66', '00:04:00:00:00:66')
  u067 = simpleCreateHost(net, 'u067', '10.0.0.67', '00:04:00:00:00:67')
  u068 = simpleCreateHost(net, 'u068', '10.0.0.68', '00:04:00:00:00:68')
  u069 = simpleCreateHost(net, 'u069', '10.0.0.69', '00:04:00:00:00:69')
  u070 = simpleCreateHost(net, 'u070', '10.0.0.70', '00:04:00:00:00:70')
  u071 = simpleCreateHost(net, 'u071', '10.0.0.71', '00:04:00:00:00:71')
  u072 = simpleCreateHost(net, 'u072', '10.0.0.72', '00:04:00:00:00:72')
  u073 = simpleCreateHost(net, 'u073', '10.0.0.73', '00:04:00:00:00:73')
  u074 = simpleCreateHost(net, 'u074', '10.0.0.74', '00:04:00:00:00:74')
  u075 = simpleCreateHost(net, 'u075', '10.0.0.75', '00:04:00:00:00:75')
  u076 = simpleCreateHost(net, 'u076', '10.0.0.76', '00:04:00:00:00:76')
  u077 = simpleCreateHost(net, 'u077', '10.0.0.77', '00:04:00:00:00:77')
  u078 = simpleCreateHost(net, 'u078', '10.0.0.78', '00:04:00:00:00:78')
  u079 = simpleCreateHost(net, 'u079', '10.0.0.79', '00:04:00:00:00:79')
  u080 = simpleCreateHost(net, 'u080', '10.0.0.80', '00:04:00:00:00:80')
  u081 = simpleCreateHost(net, 'u081', '10.0.0.81', '00:04:00:00:00:81')
  u082 = simpleCreateHost(net, 'u082', '10.0.0.82', '00:04:00:00:00:82')
  u083 = simpleCreateHost(net, 'u083', '10.0.0.83', '00:04:00:00:00:83')
  u084 = simpleCreateHost(net, 'u084', '10.0.0.84', '00:04:00:00:00:84')
  u085 = simpleCreateHost(net, 'u085', '10.0.0.85', '00:04:00:00:00:85')
  u086 = simpleCreateHost(net, 'u086', '10.0.0.86', '00:04:00:00:00:86')
  u087 = simpleCreateHost(net, 'u087', '10.0.0.87', '00:04:00:00:00:87')
  u088 = simpleCreateHost(net, 'u088', '10.0.0.88', '00:04:00:00:00:88')
  u089 = simpleCreateHost(net, 'u089', '10.0.0.89', '00:04:00:00:00:89')
  u090 = simpleCreateHost(net, 'u090', '10.0.0.90', '00:04:00:00:00:90')
  u091 = simpleCreateHost(net, 'u091', '10.0.0.91', '00:04:00:00:00:91')
  u092 = simpleCreateHost(net, 'u092', '10.0.0.92', '00:04:00:00:00:92')
  u093 = simpleCreateHost(net, 'u093', '10.0.0.93', '00:04:00:00:00:93')
  u094 = simpleCreateHost(net, 'u094', '10.0.0.94', '00:04:00:00:00:94')
  u095 = simpleCreateHost(net, 'u095', '10.0.0.95', '00:04:00:00:00:95')
  u096 = simpleCreateHost(net, 'u096', '10.0.0.96', '00:04:00:00:00:96')
  u097 = simpleCreateHost(net, 'u097', '10.0.0.97', '00:04:00:00:00:97')
  u098 = simpleCreateHost(net, 'u098', '10.0.0.98', '00:04:00:00:00:98')
  u099 = simpleCreateHost(net, 'u099', '10.0.0.99', '00:04:00:00:00:99')
  u100 = simpleCreateHost(net, 'u100', '10.0.0.100', '00:04:00:00:01:00')
  u101 = simpleCreateHost(net, 'u101', '10.0.0.101', '00:04:00:00:01:01')
  u102 = simpleCreateHost(net, 'u102', '10.0.0.102', '00:04:00:00:01:02')
  u103 = simpleCreateHost(net, 'u103', '10.0.0.103', '00:04:00:00:01:03')
  u104 = simpleCreateHost(net, 'u104', '10.0.0.104', '00:04:00:00:01:04')
  u105 = simpleCreateHost(net, 'u105', '10.0.0.105', '00:04:00:00:01:05')
  u106 = simpleCreateHost(net, 'u106', '10.0.0.106', '00:04:00:00:01:06')
  u107 = simpleCreateHost(net, 'u107', '10.0.0.107', '00:04:00:00:01:07')
  u108 = simpleCreateHost(net, 'u108', '10.0.0.108', '00:04:00:00:01:08')
  u109 = simpleCreateHost(net, 'u109', '10.0.0.109', '00:04:00:00:01:09')
  u110 = simpleCreateHost(net, 'u110', '10.0.0.110', '00:04:00:00:01:10')
  u111 = simpleCreateHost(net, 'u111', '10.0.0.111', '00:04:00:00:01:11')
  u112 = simpleCreateHost(net, 'u112', '10.0.0.112', '00:04:00:00:01:12')
  u113 = simpleCreateHost(net, 'u113', '10.0.0.113', '00:04:00:00:01:13')
  u114 = simpleCreateHost(net, 'u114', '10.0.0.114', '00:04:00:00:01:14')
  u115 = simpleCreateHost(net, 'u115', '10.0.0.115', '00:04:00:00:01:15')
  u116 = simpleCreateHost(net, 'u116', '10.0.0.116', '00:04:00:00:01:16')
  u117 = simpleCreateHost(net, 'u117', '10.0.0.117', '00:04:00:00:01:17')
  u118 = simpleCreateHost(net, 'u118', '10.0.0.118', '00:04:00:00:01:18')
  u119 = simpleCreateHost(net, 'u119', '10.0.0.119', '00:04:00:00:01:19')
  u120 = simpleCreateHost(net, 'u120', '10.0.0.120', '00:04:00:00:01:20')
  u121 = simpleCreateHost(net, 'u121', '10.0.0.121', '00:04:00:00:01:21')
  u122 = simpleCreateHost(net, 'u122', '10.0.0.122', '00:04:00:00:01:22')
  u123 = simpleCreateHost(net, 'u123', '10.0.0.123', '00:04:00:00:01:23')
  u124 = simpleCreateHost(net, 'u124', '10.0.0.124', '00:04:00:00:01:24')
  u125 = simpleCreateHost(net, 'u125', '10.0.0.125', '00:04:00:00:01:25')
  u126 = simpleCreateHost(net, 'u126', '10.0.0.126', '00:04:00:00:01:26')
  u127 = simpleCreateHost(net, 'u127', '10.0.0.127', '00:04:00:00:01:27')
  u128 = simpleCreateHost(net, 'u128', '10.0.0.128', '00:04:00:00:01:28')
  u129 = simpleCreateHost(net, 'u129', '10.0.0.129', '00:04:00:00:01:29')
  u130 = simpleCreateHost(net, 'u130', '10.0.0.130', '00:04:00:00:01:30')
  u131 = simpleCreateHost(net, 'u131', '10.0.0.131', '00:04:00:00:01:31')
  u132 = simpleCreateHost(net, 'u132', '10.0.0.132', '00:04:00:00:01:32')
  u133 = simpleCreateHost(net, 'u133', '10.0.0.133', '00:04:00:00:01:33')
  u134 = simpleCreateHost(net, 'u134', '10.0.0.134', '00:04:00:00:01:34')
  u135 = simpleCreateHost(net, 'u135', '10.0.0.135', '00:04:00:00:01:35')
  u136 = simpleCreateHost(net, 'u136', '10.0.0.136', '00:04:00:00:01:36')
  u137 = simpleCreateHost(net, 'u137', '10.0.0.137', '00:04:00:00:01:37')
  u138 = simpleCreateHost(net, 'u138', '10.0.0.138', '00:04:00:00:01:38')
  u139 = simpleCreateHost(net, 'u139', '10.0.0.139', '00:04:00:00:01:39')
  u140 = simpleCreateHost(net, 'u140', '10.0.0.140', '00:04:00:00:01:40')
  u141 = simpleCreateHost(net, 'u141', '10.0.0.141', '00:04:00:00:01:41')
  u142 = simpleCreateHost(net, 'u142', '10.0.0.142', '00:04:00:00:01:42')
  u143 = simpleCreateHost(net, 'u143', '10.0.0.143', '00:04:00:00:01:43')
  u144 = simpleCreateHost(net, 'u144', '10.0.0.144', '00:04:00:00:01:44')
  u145 = simpleCreateHost(net, 'u145', '10.0.0.145', '00:04:00:00:01:45')
  u146 = simpleCreateHost(net, 'u146', '10.0.0.146', '00:04:00:00:01:46')
  u147 = simpleCreateHost(net, 'u147', '10.0.0.147', '00:04:00:00:01:47')
  u148 = simpleCreateHost(net, 'u148', '10.0.0.148', '00:04:00:00:01:48')
  u149 = simpleCreateHost(net, 'u149', '10.0.0.149', '00:04:00:00:01:49')
  u150 = simpleCreateHost(net, 'u150', '10.0.0.150', '00:04:00:00:01:50')
  u151 = simpleCreateHost(net, 'u151', '10.0.0.151', '00:04:00:00:01:51')
  u152 = simpleCreateHost(net, 'u152', '10.0.0.152', '00:04:00:00:01:52')
  u153 = simpleCreateHost(net, 'u153', '10.0.0.153', '00:04:00:00:01:53')
  u154 = simpleCreateHost(net, 'u154', '10.0.0.154', '00:04:00:00:01:54')
  u155 = simpleCreateHost(net, 'u155', '10.0.0.155', '00:04:00:00:01:55')
  u156 = simpleCreateHost(net, 'u156', '10.0.0.156', '00:04:00:00:01:56')
  u157 = simpleCreateHost(net, 'u157', '10.0.0.157', '00:04:00:00:01:57')
  u158 = simpleCreateHost(net, 'u158', '10.0.0.158', '00:04:00:00:01:58')
  u159 = simpleCreateHost(net, 'u159', '10.0.0.159', '00:04:00:00:01:59')
  u160 = simpleCreateHost(net, 'u160', '10.0.0.160', '00:04:00:00:01:60')
  u161 = simpleCreateHost(net, 'u161', '10.0.0.161', '00:04:00:00:01:61')
  u162 = simpleCreateHost(net, 'u162', '10.0.0.162', '00:04:00:00:01:62')
  u163 = simpleCreateHost(net, 'u163', '10.0.0.163', '00:04:00:00:01:63')
  u164 = simpleCreateHost(net, 'u164', '10.0.0.164', '00:04:00:00:01:64')
  u165 = simpleCreateHost(net, 'u165', '10.0.0.165', '00:04:00:00:01:65')
  u166 = simpleCreateHost(net, 'u166', '10.0.0.166', '00:04:00:00:01:66')
  u167 = simpleCreateHost(net, 'u167', '10.0.0.167', '00:04:00:00:01:67')
  u168 = simpleCreateHost(net, 'u168', '10.0.0.168', '00:04:00:00:01:68')
  u169 = simpleCreateHost(net, 'u169', '10.0.0.169', '00:04:00:00:01:69')
  u170 = simpleCreateHost(net, 'u170', '10.0.0.170', '00:04:00:00:01:70')
  u171 = simpleCreateHost(net, 'u171', '10.0.0.171', '00:04:00:00:01:71')
  u172 = simpleCreateHost(net, 'u172', '10.0.0.172', '00:04:00:00:01:72')
  u173 = simpleCreateHost(net, 'u173', '10.0.0.173', '00:04:00:00:01:73')
  u174 = simpleCreateHost(net, 'u174', '10.0.0.174', '00:04:00:00:01:74')
  u175 = simpleCreateHost(net, 'u175', '10.0.0.175', '00:04:00:00:01:75')
  u176 = simpleCreateHost(net, 'u176', '10.0.0.176', '00:04:00:00:01:76')
  u177 = simpleCreateHost(net, 'u177', '10.0.0.177', '00:04:00:00:01:77')
  u178 = simpleCreateHost(net, 'u178', '10.0.0.178', '00:04:00:00:01:78')
  u179 = simpleCreateHost(net, 'u179', '10.0.0.179', '00:04:00:00:01:79')
  u180 = simpleCreateHost(net, 'u180', '10.0.0.180', '00:04:00:00:01:80')
  u181 = simpleCreateHost(net, 'u181', '10.0.0.181', '00:04:00:00:01:81')
  u182 = simpleCreateHost(net, 'u182', '10.0.0.182', '00:04:00:00:01:82')
  u183 = simpleCreateHost(net, 'u183', '10.0.0.183', '00:04:00:00:01:83')
  u184 = simpleCreateHost(net, 'u184', '10.0.0.184', '00:04:00:00:01:84')
  u185 = simpleCreateHost(net, 'u185', '10.0.0.185', '00:04:00:00:01:85')
  u186 = simpleCreateHost(net, 'u186', '10.0.0.186', '00:04:00:00:01:86')
  u187 = simpleCreateHost(net, 'u187', '10.0.0.187', '00:04:00:00:01:87')
  u188 = simpleCreateHost(net, 'u188', '10.0.0.188', '00:04:00:00:01:88')
  u189 = simpleCreateHost(net, 'u189', '10.0.0.189', '00:04:00:00:01:89')
  u190 = simpleCreateHost(net, 'u190', '10.0.0.190', '00:04:00:00:01:90')
  u191 = simpleCreateHost(net, 'u191', '10.0.0.191', '00:04:00:00:01:91')
  u192 = simpleCreateHost(net, 'u192', '10.0.0.192', '00:04:00:00:01:92')
  u193 = simpleCreateHost(net, 'u193', '10.0.0.193', '00:04:00:00:01:93')
  u194 = simpleCreateHost(net, 'u194', '10.0.0.194', '00:04:00:00:01:94')
  u195 = simpleCreateHost(net, 'u195', '10.0.0.195', '00:04:00:00:01:95')
  u196 = simpleCreateHost(net, 'u196', '10.0.0.196', '00:04:00:00:01:96')
  u197 = simpleCreateHost(net, 'u197', '10.0.0.197', '00:04:00:00:01:97')
  u198 = simpleCreateHost(net, 'u198', '10.0.0.198', '00:04:00:00:01:98')
  u199 = simpleCreateHost(net, 'u199', '10.0.0.199', '00:04:00:00:01:99')
  u200 = simpleCreateHost(net, 'u200', '10.0.0.200', '00:04:00:00:02:00')


  #4.2. CREATING LINKS
  linkSwitchToHost(net, u001, s1, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u002, s1, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u003, s1, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u004, s1, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u005, s1, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u006, s1, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u007, s1, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u008, s1, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u009, s1, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u010, s1, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u011, s2, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u012, s2, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u013, s2, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u014, s2, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u015, s2, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u016, s2, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u017, s2, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u018, s2, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u019, s2, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u020, s2, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u021, s3, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u022, s3, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u023, s3, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u024, s3, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u025, s3, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u026, s3, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u027, s3, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u028, s3, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u029, s3, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u030, s3, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u031, s4, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u032, s4, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u033, s4, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u034, s4, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u035, s4, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u036, s4, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u037, s4, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u038, s4, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u039, s4, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u040, s4, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u041, s5, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u042, s5, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u043, s5, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u044, s5, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u045, s5, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u046, s5, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u047, s5, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u048, s5, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u049, s5, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u050, s5, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u051, s6, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u052, s6, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u053, s6, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u054, s6, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u055, s6, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u056, s6, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u057, s6, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u058, s6, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u059, s6, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u060, s6, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u061, s7, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u062, s7, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u063, s7, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u064, s7, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u065, s7, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u066, s7, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u067, s7, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u068, s7, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u069, s7, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u070, s7, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u071, s8, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u072, s8, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u073, s8, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u074, s8, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u075, s8, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u076, s8, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u077, s8, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u078, s8, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u079, s8, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u080, s8, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u081, s9, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u082, s9, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u083, s9, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u084, s9, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u085, s9, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u086, s9, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u087, s9, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u088, s9, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u089, s9, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u090, s9, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u091, s10, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u092, s10, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u093, s10, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u094, s10, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u095, s10, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u096, s10, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u097, s10, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u098, s10, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u099, s10, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u100, s10, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u101, s11, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u102, s11, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u103, s11, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u104, s11, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u105, s11, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u106, s11, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u107, s11, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u108, s11, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u109, s11, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u110, s11, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u111, s12, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u112, s12, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u113, s12, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u114, s12, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u115, s12, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u116, s12, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u117, s12, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u118, s12, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u119, s12, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u120, s12, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u121, s13, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u122, s13, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u123, s13, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u124, s13, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u125, s13, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u126, s13, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u127, s13, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u128, s13, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u129, s13, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u130, s13, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u131, s14, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u132, s14, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u133, s14, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u134, s14, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u135, s14, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u136, s14, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u137, s14, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u138, s14, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u139, s14, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u140, s14, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u141, s15, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u142, s15, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u143, s15, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u144, s15, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u145, s15, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u146, s15, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u147, s15, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u148, s15, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u149, s15, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u150, s15, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u151, s16, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u152, s16, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u153, s16, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u154, s16, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u155, s16, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u156, s16, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u157, s16, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u158, s16, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u159, s16, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u160, s16, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u161, s17, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u162, s17, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u163, s17, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u164, s17, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u165, s17, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u166, s17, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u167, s17, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u168, s17, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u169, s17, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u170, s17, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u171, s18, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u172, s18, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u173, s18, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u174, s18, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u175, s18, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u176, s18, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u177, s18, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u178, s18, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u179, s18, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u180, s18, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u181, s19, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u182, s19, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u183, s19, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u184, s19, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u185, s19, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u186, s19, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u187, s19, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u188, s19, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u189, s19, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u190, s19, 0, 10, False, linknodeg)
  linkSwitchToHost(net, u191, s20, 0, 1, False, linknodeg)
  linkSwitchToHost(net, u192, s20, 0, 2, False, linknodeg)
  linkSwitchToHost(net, u193, s20, 0, 3, False, linknodeg)
  linkSwitchToHost(net, u194, s20, 0, 4, False, linknodeg)
  linkSwitchToHost(net, u195, s20, 0, 5, False, linknodeg)
  linkSwitchToHost(net, u196, s20, 0, 6, False, linknodeg)
  linkSwitchToHost(net, u197, s20, 0, 7, False, linknodeg)
  linkSwitchToHost(net, u198, s20, 0, 8, False, linknodeg)
  linkSwitchToHost(net, u199, s20, 0, 9, False, linknodeg)
  linkSwitchToHost(net, u200, s20, 0, 10, False, linknodeg)

  net.start()
  deployFlowRules()
  while True:
      time.sleep(60)
  #CLI( net )
  net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    evalTopo()
