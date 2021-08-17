#!/usr/env python3.9
import multiprocessing
from pathlib import Path

# Hardware Consts
MAX_THREADS = multiprocessing.cpu_count()

# Unix Consts
HOME_DIR = Path.home()

# Mininet Consts
MININET_DIR = f"{HOME_DIR}/mininet"
MININET_M = f"{MININET_DIR}/util/m"

# Controller Routes Consts
CONTROLLER_API_HOSTNAME = "localhost"
CONTROLLER_API_PORT = 8080
