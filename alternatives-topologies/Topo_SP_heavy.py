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
from functools import partial

def evalTopo():
  "Service Provider Topology"
  #switch = partial ( OVSSwitch, protocols="OpenFlow13" )
  #switch = partial ( OVSSwitch, protocols="sp" )
  net = Mininet( topo=None, controller=RemoteController, switch=OVSKernelSwitch, link=TCLink )

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

  # Adding nodes
  # h1 - h99 - Host / End-user
  # h100 - Video server
  h1 = net.addHost('h1', ip='10.0.0.1', mac='00:04:00:00:00:01')
  h2 = net.addHost('h2', ip='10.0.0.2', mac='00:04:00:00:00:02')
  h99 = net.addHost('h99', ip='10.0.0.99', mac='00:04:00:00:00:99')

  # 29 Links
  # Creating links between hosts and switches
  net.addLink(h1, s1)
  net.addLink(h2, s2)
  net.addLink(h99, s16)

  #Creating links between switches
  #Level 1 - RAN / end-user
  net.addLink(s1, s3)
  net.addLink(s1, s4)
  net.addLink(s1, s5)
  net.addLink(s2, s6)
  net.addLink(s2, s7)
  net.addLink(s2, s8)

  net.addLink(s3, s9)
  net.addLink(s4, s9)
  net.addLink(s5, s10)
  net.addLink(s6, s11)
  net.addLink(s7, s12)
  net.addLink(s8, s12)
 
  #Level 2 - Access
  net.addLink(s9, s13)
  net.addLink(s9, s14)
  net.addLink(s10, s13, **linkopts1 )
  net.addLink(s10, s14)
  net.addLink(s11, s13)
  net.addLink(s11, s14, **linkopts1 )
  net.addLink(s12, s13)
  net.addLink(s12, s14)


  #Level 3 - Core
  net.addLink(s13, s14)
  net.addLink(s13, s15)
  net.addLink(s13, s16)
  net.addLink(s14, s15)
  net.addLink(s14, s16)
  net.addLink(s15, s16)


  net.start()

  CLI( net )

  net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    evalTopo()
