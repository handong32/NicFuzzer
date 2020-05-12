import math
import random
import subprocess
from subprocess import Popen, PIPE, call
import time
from datetime import datetime
import sys
import os
import getopt
import numpy as np
import itertools
import argparse

SERVER = "192.168.1.230"

ITR = 666
RAPL = 136
MSG = "1024"
ITER = "10000"

dvfs_dict = {
    "1.2" : "0xc00",
    "1.3" : "0xd00",
    "1.4" : "0xe00",
    "1.5" : "0xf00",
    "1.6" : "0x1000",
    "1.7" : "0x1100",
    "1.8" : "0x1200",
    "1.9" : "0x1300",
    "2.0" : "0x1400",
    "2.1" : "0x1500",
    "2.2" : "0x1600",
    "2.3" : "0x1700",
    "2.4" : "0x1800",
    "2.5" : "0x1900",
    "2.6" : "0x1a00",
    "2.7" : "0x1b00",
    "2.8" : "0x1c00",
    "2.9" : "0x1d00",
}

FREQ = dvfs_dict["2.9"]

def runRemoteCommand(server, com):
    p1 = Popen(["ssh", server, com])

def runRemoteCommandGet(server, com):
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE, stderr=PIPE)
    return p1.communicate()[0].strip()

def init():
    r = runRemoteCommandGet("192.168.1.230", "ls /dev/shm/")
    if len(r) == 0:
        runRemoteCommandGet("192.168.1.230", "cp ~/NPtcp_static /dev/shm/")

    r = runRemoteCommandGet("192.168.1.11", "ls /dev/shm/")
    if len(r) == 0:
        runRemoteCommandGet("192.168.1.11", "cp ~/NPtcp_static /dev/shm/")
    
def setRAPL(v):
    global RAPL
    p1 = Popen(["ssh", SERVER, "/root/uarch-configure/rapl-read/rapl-power-mod", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    RAPL = int(v)

def setDVFS(v):
    global FREQ
    p1 = Popen(["ssh", SERVER, "wrmsr -a 0x199", dvfs_dict[v]], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    FREQ = v

def setITR(v):
    global ITR
    p1 = Popen(["ssh", "10.255.5.8", "ethtool -C enp4s0f1 rx-usecs", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    p1 = Popen(["ssh", "10.255.5.11", "ethtool -C enp4s0f1 rx-usecs", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    ITR = int(v)

def runBench(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE, stderr=PIPE)
    stdout, stderr = p1.communicate()
    #print(stdout)
    #print(stderr)
    res = ""
    if 'Mbps' in str(stdout):
        res = str(stdout).strip().split('-->')[1]
        print("stdout ", res)
        #t = s.split('Mbps')[0]
        #return 0.0
        #return float(t.strip())
    elif 'Mbps' in str(stderr):
        res = str(stderr).strip().split('-->')[1]
        print("stderr ", res)
        
    if len(res) > 0:
        tmp = list(filter(None, res.strip().split(' ')))
        return tmp[0], tmp[3], tmp[5]
    
def runNP():    
    output = runRemoteCommandGet("192.168.1.230", "pkill NPtcp_static")
    time.sleep(1)
    output = runRemoteCommandGet("192.168.1.11", "pkill NPtcp_static")
    time.sleep(1)
    
    runRemoteCommand("192.168.1.230", "perf stat -C 1 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/ -x , taskset -c 1 /dev/shm/NPtcp_static -l "+MSG+" -u "+MSG+" -p 0 -r -I")
    time.sleep(1)
    tput, lat, secs = runBench("ssh 192.168.1.11 taskset -c 1 /dev/shm/NPtcp_static -h 192.168.1.230 -l "+MSG+" -u "+MSG+" -n "+ITER+" -p 0 -r -I")    

    # just to be sure, kill netpipe server
    runRemoteCommandGet("192.168.1.230", "pkill NPtcp_static")
    
    nodeOut = runRemoteCommandGet("192.168.1.230", "cat perf.out")
    joules = 0.0
    for l in str(nodeOut).split("\\n"):
        if 'Joules' in l.strip():
            tmp = list(filter(None, l.strip().split(',')))
            joules = float(tmp[0])
            break
        #print(l.strip())
  
    print("*** "," ITR:", ITR, " RAPL:", RAPL, " FREQ:", FREQ, " MSG:", MSG, " ITER:", ITER, " TPUT:", tput, " LATENCY:", lat, " TIME:", secs, " Joules:", joules)
 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapl", help="Rapl power limit [46, 136]")
    parser.add_argument("--dvfs", help="Cpu frequency [1.2, 2.9 GHz]")
    parser.add_argument("--iter", help="iteration count")
    parser.add_argument("--msg", help="message size")
    parser.add_argument("--itr", help="Static interrupt delay [10, 1000]")
    
    args = parser.parse_args()
    if args.rapl:
        setRAPL(args.rapl)
    if args.dvfs:
        setDVFS(args.dvfs)
    if args.itr:
        setITR(args.itr)
    if args.iter:
        ITER = args.iter
    if args.msg:
        MSG = args.msg
        
    init()
    runNP()
