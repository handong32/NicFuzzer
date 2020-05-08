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
WTHRESH = 0
PTHRESH = 0
HTHRESH = 0
THRESHC = 0
DTXMXSZRQ = 0
DCA = 0
RSC_DELAY = 0
MAX_DESC = 0
BSIZEPKT = 0
BSIZEHDR = 0
RXRING = 0
TXRING = 0
RAPL = 136
ITRC = []
TYPE = 'etc'
TIME = 120
SEARCH = 0
VERBOSE = 0

'''
DVFS
0xc00 == 1.2GHz
0xd00 == 1.3GHz
.
.
.
.
0x1d00 == 2.9 GHz
'''
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

def runLocalCommandOut(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    p1.communicate()
    #print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(com):
    #print(com)
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE)
    p1.communicate()
    #print("\tssh "+SERVER, com, "->\n", p1.communicate()[0].strip())

def runLocalCommand(com):
    #print(com)
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(com):
    #print(com)
    p1 = Popen(["ssh", SERVER, com])

def runRemoteCommands(com, server):
    #print(com)
    p1 = Popen(["ssh", server, com])

def runRemoteCommandGet(com):
    #print(com)
    p1 = Popen(["ssh", SERVER, com], stdout=PIPE)
    return p1.communicate()[0].strip()

def init():
    r = runRemoteCommandGet("ls /dev/shm/")
    if len(r) == 0:
        runRemoteCommandOut("cp ~/dbtest /dev/shm/")
    
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
            
def runSilo():
    output = runRemoteCommandGet("pkill dbtest")
    
    output = runRemoteCommandGet("taskset -c 0-16 /dev/shm/dbtest --pmu --bench tpcc --runtime 30 --num-threads 15 --scale-factor 15")
    print("*** RAPL:", RAPL, " FREQ:", FREQ, end=" ")
    for l in str(output).split("\\n"):
            print(str(l.strip()), end=" ")
    print("\n")
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapl", help="Rapl power limit [46, 136]")
    parser.add_argument("--dvfs", help="Cpu frequency [1.2, 2.9 GHz]")
    
    args = parser.parse_args()
    if args.rapl:
        setRAPL(args.rapl)
    if args.dvfs:
        setDVFS(args.dvfs)
    
    init()
    runSilo()    
    
