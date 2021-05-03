#!/usr/bin/env bash

sudo mn -c
sudo ryu-manager Controller_DBR.py &
sleep 20s
sudo python3 Topo_ DBR.sh