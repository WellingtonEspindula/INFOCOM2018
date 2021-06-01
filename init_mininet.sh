#!/usr/bin/env bash

sudo echo ""
echo "[INFO] Cleaning Running Managers..."
sudo killall /usr/netmetric/sbin/metricmanager
echo "[INFO] Cleaning previous mininet config..."
sudo mn -c
clear
echo "[INFO] Initializing controller..."
sudo ryu-manager Controller_DBR.py &
sleep 7s
clear
echo "[INFO] Initializing Topology..."
sudo python3 Topo_DBR.py
