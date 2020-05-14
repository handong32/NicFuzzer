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

ITR = "Dynamic"
RAPL = 136

com_dict = {
    "com1" : 'ssh 192.168.1.11 taskset -c 1 /dev/shm/wrk -t1 -c1 -d30s http://192.168.1.230:6666/index.html --latency',
    "com512" : "ssh 192.168.1.11 taskset -c 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 /dev/shm/wrk -t16 -c512 -d30s http://192.168.1.230:6666/index.html --latency",
    'com1_1024' : 'ssh 192.168.1.11 taskset -c 1 /dev/shm/wrk -t1 -c1 -d30s -H "Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: example.com Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: " http://192.168.1.230:6666/index.html --latency',
    'com512_1024' : 'ssh 192.168.1.11 taskset -c 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 /dev/shm/wrk -t16 -c512 -d30s -H "Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: example.com Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: " http://192.168.1.230:6666/index.html --latency'
}

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
COM = com_dict['com1']

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
        runRemoteCommandOut("cp ~/node /dev/shm/")
        runRemoteCommandOut("cp ~/hello_http.js /dev/shm/")        
    
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
    p1 = Popen(["ssh", SERVER, "ethtool -C enp4s0f1 rx-usecs", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(0.5)
    
def runWrk():
    time.sleep(2)
    output = runRemoteCommandGet("pkill node")
    time.sleep(2)
    
    runRemoteCommand("perf stat -C 1 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/ -x , taskset -c 1 /dev/shm/node /dev/shm/hello_http.js")
    time.sleep(0.5)    

    com = com_dict[COM]
    
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    wrkOut = p1.communicate()[0].strip()
    req = 0
    for l in str(wrkOut).split("\\n"):
        if "requests in" in l.strip():
            tmp = list(filter(None, l.strip().split(' ')))
            req = int(tmp[0])            
        print(l.strip())

    output = runRemoteCommandGet("pkill node")
    nodeOut = runRemoteCommandGet("cat perf.out")

    joules = 0.0
    for l in str(nodeOut).split("\\n"):
        if 'Joules' in l.strip():
            tmp = list(filter(None, l.strip().split(',')))
            joules = float(tmp[0])
        print(l.strip())

    
    print("*** ", COM, " ITR:", ITR, " RAPL:", RAPL, " FREQ:", FREQ, " Requests: ", req, " Joules: ", joules)
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--rapl", help="Rapl power limit [46, 136]")
    parser.add_argument("--dvfs", help="Cpu frequency [1.2, 2.9 GHz]")
    parser.add_argument("--com", help="com1 == -t1 -c1, com512 == -t16 -c512, com1_1024 == 1024 bytes")
    parser.add_argument("--itr", help="Static interrupt delay [10, 1000]")
    
    args = parser.parse_args()
    if args.rapl:
        setRAPL(args.rapl)
    if args.dvfs:
        setDVFS(args.dvfs)
    if args.com:
        COM = args.com
    if args.itr:
        setITR(args.itr)
        ITR=args.itr
        
    init()
    runWrk()
