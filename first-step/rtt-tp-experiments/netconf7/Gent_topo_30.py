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
  link10Gbps = dict(bw=200, delay='5ms') 
  linknodeg = dict()

 # link100Mbps_1 = dict(bw=1, delay='30ms') # ALTERAR AQUI
 # link100Mbps_1 = dict(bw=1, delay='30ms', loss=10) # ALTERAR AQUI
  link100Mbps_1 = dict(bw=90, delay='90ms') ##############################################################################################################################
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
  
  #1.2. CREATING LINKS
  #linkSwitchToHost(net, src1, s4, 0, 99, False, linknodeg)
  #linkSwitchToHost(net, src2, s7, 0, 99, False, linknodeg)
  linkSwitchToHost(net, cdn1, s1, 0, 99, False, link100Mbps_1)

  #2.   SWITCH PROCESSING
  #2.1. CREATING HOSTS


 

  #4. SOURCES
  #4.1. CREATING HOSTS
  u001 = simpleCreateHost(net, 'u001', '10.0.0.1', '00:04:00:00:00:01')


  #4.2. CREATING LINKS
  linkSwitchToHost(net, u001, s1, 0, 1, False, linknodeg)

  net.start()
  deployFlowRules()
  while True:
      time.sleep(60)
  #CLI( net )
  net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    evalTopo()
