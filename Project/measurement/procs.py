import os
import re
import signal
import subprocess
import time
from typing import Optional

from Project.common.constants import MININET_M, MAX_THREADS, NETMETRIC_MANAGER, NETMETRIC_AGENT

manager_processes: list[int] = []
agent_processes: list[int] = []


def run_agent(agent_hostname: str, uuid: str, schedule_file: str):
    """
        Run Agent process and returns its pid
    """
    global agent_processes
    command = f"{MININET_M} {agent_hostname} {NETMETRIC_AGENT} -c -f {schedule_file} -w -l 1000 -u " \
              f"100 -u {uuid} "
    agent_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    agent_processes.append(agent_process.pid)
    agent_process.wait(100000)
    agent_processes.remove(agent_process.pid)


def start_managers(managers: list[str] = None):
    if managers is None:
        managers = ["man1", "man2", "man3", "man4"]

    print("Starting managers...")
    # signal.signal(signal.SIGINT, interruption_handler)
    for manager in managers:
        run_manager(manager)
    print("Started manager... Let's wait them to wake up")
    time.sleep(5)
    print("Ok, Managers should be awake now. Let's get start the measurements!")


def run_manager(manager_hostname: str) -> int:
    """
        Run Manager process and returns its pid
    """
    global manager_processes
    pid_manager_port_busy = is_manager_busy(manager_hostname)
    print(f"Is manager {manager_hostname} busy: {pid_manager_port_busy is not None}")
    while pid_manager_port_busy is not None:
        print(f"Waiting for manager {manager_hostname} free the port up...")
        kill_proc(pid_manager_port_busy)
        time.sleep(5)
        pid_manager_port_busy = is_manager_busy(manager_hostname)
    command = f"taskset -c {run_manager.core} {MININET_M} {manager_hostname} {NETMETRIC_MANAGER} -c &"
    print(command)
    manager_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    manager_processes.append(manager_process.pid)
    time.sleep(1)
    run_manager.core = run_manager.core + 1 if run_manager.core < (MAX_THREADS - 1) else 0
    return manager_process.pid


run_manager.core = 0


def is_manager_busy(manager: str) -> Optional[int]:
    """
    Returns if a manager port is busy (metricmanager already load), the process' pid
    """
    manager_port = "12055"
    netstat_results = subprocess.Popen(f"{MININET_M} {manager} netstat -anp", shell=True, stdout=subprocess.PIPE).stdout
    netstat_results = netstat_results.read().decode().split('\n')[2:]  # Separates lines
    for result in netstat_results:
        formatted_result = [r for r in result.replace(' \t', '').split(' ') if r != '']
        if len(formatted_result) >= 7 and formatted_result[3].find(manager_port) != -1:
            pid_busy_port = re.match(r'(\d+)/\w+', formatted_result[6])
            if pid_busy_port is not None:
                return int(re.match(r'(\d+)/\w+', formatted_result[6]).group(1))
    return None


def kill_all_managers():
    global manager_processes
    for proc in manager_processes:
        kill_proc(proc)


def kill_proc(pid: int):
    os.killpg(pid, signal.SIGTERM)
