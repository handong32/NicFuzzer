import math
import random
import subprocess
from subprocess import Popen, PIPE, call
import time
from datetime import datetime
import sys
import os
import getopt
import pickle
import numpy as np
import itertools
import zmq

CSERVER = "192.168.1.200"
CSERVER2 = "10.255.5.8" 

context = zmq.Context()
sock = context.socket(zmq.PAIR)
sock.connect("tcp://localhost:5563")

def runLocalCommandOut(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(server, com):
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    print("\tssh "+server, com, "->\n", p1.communicate()[0].strip())

def runRemoteCommandGet(server, com):
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    return p1.communicate()[0].strip()
    
def runLocalCommand(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(server, com):
    p1 = Popen(["ssh", server, com], stdout=PIPE)

def updateITR(ITR):
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 rx-usecs", str(ITR)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    
def runBench(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE, stderr=PIPE)
    stdout, stderr = p1.communicate()
    if 'Mbps' in str(stderr):
        s = str(stderr).strip().split('-->')[1]
        t = s.split('Mbps')[0]
        return float(t.strip())
    else:
        return -1.0

def runStatic(msg_size):
    runRemoteCommand(CSERVER, "taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+" -p 0 -r -I")
    time.sleep(1)
    tput = runBench("taskset -c 1 NPtcp -h "+CSERVER+" -l "+msg_size+" -u "+msg_size+" -T 2 -p 0 -r -I")
    time.sleep(0.5)
    runRemoteCommand(CSERVER, "pkill NPtcp")
    time.sleep(0.5)
    runLocalCommand("pkill NPtcp")
    time.sleep(0.5)
    return tput

sock.send("hi")
itr = sock.recv()
if int(itr) > 0 and int(itr) < 202:
    #itr = 40
    updateITR(itr)
    msg = 10000
    tput = runStatic(str(msg))
    #print(tput)
    sock.send(str(tput))
else:
    
    sock.send(str(abs(int(itr)) * -9999.99))
