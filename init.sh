#!/usr/bin/env bash

echo "[INFO] Cleaning previous mininet config..."
sudo mn -c
clear
echo "[INFO] Initializing controller..."
sudo ryu-manager Controller_DBR.py &
sleep 3s
clear
echo "[INFO] Initializing Topology..."
sudo python3 Topo_DBR.py
