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

def createHostAndManagerConf(net, hostName, hostIp, hostMac):
  #hostIp = hostIp.replace('.','\.')
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
  return net.addHost(hostName, ip=hostIp, mac=hostMac)

def addRule(switchName, reqIp, portOut):
  routeParam = 'priority=1024,ip,nw_dst=' + reqIp + ',actions=output:' + portOut
  print(routeParam)
  p = Popen(['ovs-ofctl', 'add-flow', switchName, routeParam, '-O OpenFlow13']) 

def deploySwitchesToHostsRules():
  #Output rules from switches to its own hosts
  addRule('s1', '10.0.0.201', '5')
  addRule('s2', '10.0.0.202', '5')
  addRule('s3', '10.0.0.203', '3')
  addRule('s4', '10.0.0.204', '3')
  addRule('s5', '10.0.0.205', '3')
  addRule('s6', '10.0.0.206', '3')
  addRule('s7', '10.0.0.207', '3')
  addRule('s8', '10.0.0.208', '3')
  addRule('s9', '10.0.0.209', '5')
  addRule('s10', '10.0.0.210', '4')
  addRule('s11', '10.0.0.211', '4')
  addRule('s12', '10.0.0.212', '5')
  addRule('s13', '10.0.0.213', '8')
  addRule('s14', '10.0.0.214', '8')
  addRule('s15', '10.0.0.215', '4')
  addRule('s16', '10.0.0.216', '5')

  addRule('s16', '10.0.0.99', '1')
  addRule('s1', '10.0.0.1', '1')
  addRule('s2', '10.0.0.2', '1')
  #Creating links between switches
  #Level 1 - RAN / end-user
  #(s1, s3)
  addRule('s1', '10.0.0.203', '2')
  addRule('s3', '10.0.0.201', '1')

  #(s1, s4)
  addRule('s1', '10.0.0.204', '3')
  addRule('s4', '10.0.0.201', '1')

  #(s1, s5)
  addRule('s1', '10.0.0.205', '4')
  addRule('s5', '10.0.0.201', '1')

  #(s2, s6)
  addRule('s2', '10.0.0.206', '2')
  addRule('s6', '10.0.0.202', '1')

  #(s2, s7)
  addRule('s2', '10.0.0.207', '3')
  addRule('s7', '10.0.0.202', '1')

  #(s2, s8)
  addRule('s2', '10.0.0.208', '4')
  addRule('s8', '10.0.0.202', '1')

  #(s3, s9)
  addRule('s3', '10.0.0.209', '2')
  addRule('s9', '10.0.0.203', '1')

  #(s4, s9)
  addRule('s4', '10.0.0.209', '2')
  addRule('s9', '10.0.0.204', '2')

  #(s5, s10)
  addRule('s5', '10.0.0.210', '2')
  addRule('s10', '10.0.0.205', '1')

  #(s6, s11)
  addRule('s6', '10.0.0.211', '2')
  addRule('s11', '10.0.0.206', '1')

  #(s7, s12)
  addRule('s7', '10.0.0.212', '2')
  addRule('s12', '10.0.0.207', '1')

  #(s8, s12)
  addRule('s8', '10.0.0.212', '2')
  addRule('s12', '10.0.0.208', '2')
 
  #Level 2 - Access
  #(s9, s13)
  addRule('s9', '10.0.0.213', '3')
  addRule('s13', '10.0.0.209', '1')

  #(s9, s14)
  addRule('s9', '10.0.0.214', '4')
  addRule('s14', '10.0.0.209', '1')

  #(s10, s13)
  addRule('s10', '10.0.0.213', '2')
  addRule('s13', '10.0.0.210', '2')

  #(s10, s14)
  addRule('s10', '10.0.0.214', '3')
  addRule('s14', '10.0.0.210', '2')

  #(s11, s13)
  addRule('s11', '10.0.0.213', '2')
  addRule('s13', '10.0.0.211', '3')

  #(s11, s14)
  addRule('s11', '10.0.0.214', '3')
  addRule('s14', '10.0.0.211', '3')

  #(s12, s13)
  addRule('s12', '10.0.0.213', '3')
  addRule('s13', '10.0.0.212', '4')

  #(s12, s14)
  addRule('s12', '10.0.0.214', '4')
  addRule('s14', '10.0.0.212', '4')

  #Level 3 - Core
  #(s13, s14)
  addRule('s13', '10.0.0.214', '5')
  addRule('s14', '10.0.0.213', '5')

  #(s13, s15)
  addRule('s13', '10.0.0.215', '6')
  addRule('s15', '10.0.0.213', '1')

  #(s13, s16)
  addRule('s13', '10.0.0.216', '7')
  addRule('s16', '10.0.0.213', '2')

  #(s14, s15)
  addRule('s14', '10.0.0.215', '6')
  addRule('s15', '10.0.0.214', '2')

  #(s14, s16)
  addRule('s14', '10.0.0.216', '7')
  addRule('s16', '10.0.0.214', '3')
  
  #(s15, s16)
  addRule('s15', '10.0.0.216', '3')
  addRule('s16', '10.0.0.215', '4')

def evalTopo():
  "Service Provider Topology"
  switch = partial ( OVSSwitch, protocols="OpenFlow13" )
  #switch = partial ( OVSSwitch, protocols="sp" )
  net = Mininet( topo=None, controller=RemoteController, switch=switch, autoStaticArp=True, link=TCLink )

  net.addController( 'c0', RemoteController, ip="127.0.0.1", port=6633 )

  linkopts1 = dict(bw=1, delay='150ms' )
  linkopts2 = dict(bw=2, delay='80ms' )
  linkopts3 = dict(bw=10, delay='30ms' )
  #net.addLink(Host1,   Switch1,    **linkopts )
  # Adding switches
  s1 = net.addSwitch('s1')
  s2 = net.addSwitch('s2')
  s3 = net.addSwitch('s3')
  s4 = net.addSwitch('s4')
  s5 = net.addSwitch('s5')
  s6 = net.addSwitch('s6')
  s7 = net.addSwitch('s7')
  s8 = net.addSwitch('s8')
  s9 = net.addSwitch('s9')
  s10 = net.addSwitch('s10')
  s11 = net.addSwitch('s11')
  s12 = net.addSwitch('s12')
  s13 = net.addSwitch('s13')
  s14 = net.addSwitch('s14')
  s15 = net.addSwitch('s15')
  s16 = net.addSwitch('s16')

  print(s15.name)
  # Adding nodes
  # h1 - h99 - Host / End-user
  # h100 - Video server
  # h1 = net.addHost('h1', ip='10.0.0.1', mac='00:04:00:00:00:01')
  # h2 = net.addHost('h2', ip='10.0.0.2', mac='00:04:00:00:00:02')
  # h99 = net.addHost('h99', ip='10.0.0.99', mac='00:04:00:00:00:99')

  h1 = createHostAndManagerConf(net, 'h1', '10.0.0.1', '00:04:00:00:00:01')
  h2 = createHostAndManagerConf(net, 'h2', '10.0.0.2', '00:04:00:00:00:02')
  h99 = createHostAndManagerConf(net, 'h99', '10.0.0.99', '00:04:00:00:00:99')

  a1 = createHostAndManagerConf(net, 'a1', '10.0.0.201', '00:04:00:00:0F:01')
  a2 = createHostAndManagerConf(net, 'a2', '10.0.0.202', '00:04:00:00:0F:02')
  a3 = createHostAndManagerConf(net, 'a3', '10.0.0.203', '00:04:00:00:0F:03')
  a4 = createHostAndManagerConf(net, 'a4', '10.0.0.204', '00:04:00:00:0F:04')
  a5 = createHostAndManagerConf(net, 'a5', '10.0.0.205', '00:04:00:00:0F:05')
  a6 = createHostAndManagerConf(net, 'a6', '10.0.0.206', '00:04:00:00:0F:06')
  a7 = createHostAndManagerConf(net, 'a7', '10.0.0.207', '00:04:00:00:0F:07')
  a8 = createHostAndManagerConf(net, 'a8', '10.0.0.208', '00:04:00:00:0F:08')
  a9 = createHostAndManagerConf(net, 'a9', '10.0.0.209', '00:04:00:00:0F:01')
  a10 = createHostAndManagerConf(net, 'a10', '10.0.0.210', '00:04:00:00:0F:10')
  a11 = createHostAndManagerConf(net, 'a11', '10.0.0.211', '00:04:00:00:0F:11')
  a12 = createHostAndManagerConf(net, 'a12', '10.0.0.212', '00:04:00:00:0F:12')
  a13 = createHostAndManagerConf(net, 'a13', '10.0.0.213', '00:04:00:00:0F:13')
  a14 = createHostAndManagerConf(net, 'a14', '10.0.0.214', '00:04:00:00:0F:14')
  a15 = createHostAndManagerConf(net, 'a15', '10.0.0.215', '00:04:00:00:0F:15')
  a16 = createHostAndManagerConf(net, 'a16', '10.0.0.216', '00:04:00:00:0F:16')


  #a1 = net.addHost('a1', ip='10.0.0.201', mac='00:04:00:00:0F:01')
  #a2 = net.addHost('a2', ip='10.0.0.202', mac='00:04:00:00:0F:02')
  #a3 = net.addHost('a3', ip='10.0.0.203', mac='00:04:00:00:0F:03')
  #a4 = net.addHost('a4', ip='10.0.0.204', mac='00:04:00:00:0F:04')
  #a5 = net.addHost('a5', ip='10.0.0.205', mac='00:04:00:00:0F:05')
  #a6 = net.addHost('a6', ip='10.0.0.206', mac='00:04:00:00:0F:06')
  #a7 = net.addHost('a7', ip='10.0.0.207', mac='00:04:00:00:0F:07')
  #a8 = net.addHost('a8', ip='10.0.0.208', mac='00:04:00:00:0F:08')
  #a9 = net.addHost('a9', ip='10.0.0.209', mac='00:04:00:00:0F:09')
  #a10 = net.addHost('a10', ip='10.0.0.210', mac='00:04:00:00:0F:10')
  #a11 = net.addHost('a11', ip='10.0.0.211', mac='00:04:00:00:0F:11')
  #a12 = net.addHost('a12', ip='10.0.0.212', mac='00:04:00:00:0F:12')
  #a13 = net.addHost('a13', ip='10.0.0.213', mac='00:04:00:00:0F:13')
  #a14 = net.addHost('a14', ip='10.0.0.214', mac='00:04:00:00:0F:14')
  #a15 = net.addHost('a15', ip='10.0.0.215', mac='00:04:00:00:0F:15')
  #a16 = net.addHost('a16', ip='10.0.0.216', mac='00:04:00:00:0F:16')


  # 29 Links
  # Creating links between hosts and switches
  net.addLink(h1, s1, 0, 1)
  net.addLink(h2, s2, 0, 1)
  net.addLink(h99, s16, 0, 1)

  #Aux links, to enable switches processing
  net.addLink(a1, s1, 0, 5)
  net.addLink(a2, s2, 0, 5)
  net.addLink(a3, s3, 0, 3)
  net.addLink(a4, s4, 0, 3)
  net.addLink(a5, s5, 0, 3)
  net.addLink(a6, s6, 0, 3)
  net.addLink(a7, s7, 0, 3)
  net.addLink(a8, s8, 0, 3)
  net.addLink(a9, s9, 0, 5)
  net.addLink(a10, s10, 0, 4)
  net.addLink(a11, s11, 0, 4)
  net.addLink(a12, s12, 0, 5)
  net.addLink(a13, s13, 0, 8)
  net.addLink(a14, s14, 0, 8)
  net.addLink(a15, s15, 0, 4)
  net.addLink(a16, s16, 0, 5)

  #Creating links between switches
  #Level 1 - RAN / end-user
  net.addLink(s1, s3, 2, 1, **linkopts1)
  net.addLink(s1, s4, 3, 1, **linkopts2)
  net.addLink(s1, s5, 4, 1)
  net.addLink(s2, s6, 2, 1)
  net.addLink(s2, s7, 3, 1)
  net.addLink(s2, s8, 4, 1, **linkopts3)

  net.addLink(s3, s9, 2, 1)
  net.addLink(s4, s9, 2, 2)
  net.addLink(s5, s10, 2, 1)
  net.addLink(s6, s11, 2, 1)
  net.addLink(s7, s12, 2, 1)
  net.addLink(s8, s12, 2, 2)
 
  #Level 2 - Access
  net.addLink(s9, s13, 3, 1, **linkopts1)
  net.addLink(s9, s14, 4, 1)
  net.addLink(s10, s13, 2, 2)
  net.addLink(s10, s14, 3, 2, **linkopts3)
  net.addLink(s11, s13, 2, 3)
  net.addLink(s11, s14, 3, 3)
  net.addLink(s12, s13, 3, 4)
  net.addLink(s12, s14, 4, 4, **linkopts2)


  #Level 3 - Core
  net.addLink(s13, s14, 5, 5)
  net.addLink(s13, s15, 6, 1)
  net.addLink(s13, s16, 7, 2, **linkopts1)
  net.addLink(s14, s15, 6, 2)
  net.addLink(s14, s16, 7, 3)
  net.addLink(s15, s16, 3, 4)

  net.start()
  deploySwitchesToHostsRules()
  CLI( net )
  net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    evalTopo()
