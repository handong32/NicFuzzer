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

CSERVER = "192.168.1.200"
CSERVER2 = "10.255.5.8"
ITR = 0
WTHRESH = 0
PTHRESH = 0
HTHRESH = 0
DTXMXSZRQ = 0

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

def updateNIC():
    global ITR
    global WTHRESH
    global HTHRESH
    global PTHRESH
    global DTXMXSZRQ
    
    # ITR: 6 us to 120 us in increments of 2
    ITR = np.random.randint(3, 61) * 2

    '''
    Notes about THRESH, PTHRESH, WTHRESH

    Transmit descriptor fetch setting is programmed in the TXDCTL[n] register per
    In order to reduce transmission latency, it is recommended to set the PTHRESH value
    as high as possible while the HTHRESH and WTHRESH as low as possible (down to
    zero).

    In order to minimize PCIe overhead the PTHRESH should be set as low as possible
    while HTHRESH and WTHRESH should be set as high as possible.

    The sum of PTHRESH plus WTHRESH must not be greater than the on-chip descriptor
    buffer size (40)

    When the WTHRESH equals zero, descriptors are written back for those
    descriptors with the RS bit set. When the WTHRESH value is greater than
    zero, descriptors are accumulated until the number of accumulated descriptors equals
    the WTHRESH value, then these descriptors are written back. Accumulated
    descriptor write back enables better use of the PCIe bus and memory bandwidth.

    PTHRESH: Pre-Fetch Threshold The on-chip descriptor buffer becomes almost empty while there are enough
    descriptors in the host memory.
         - The on-chip descriptor buffer is defined as almost empty if it contains less descriptors
           then the threshold defined by PTHRESH
         - The transmit descriptor contains enough descriptors if it includes more ready
           descriptors than the threshold defined by TXDCTL[n].HTHRESH

    Controls when a prefetch of descriptors is considered. This threshold refers to the
    number of valid, unprocessed transmit descriptors the 82599 has in its on-chip buffer. If
    this number drops below PTHRESH, the algorithm considers pre-fetching descriptors from
    host memory. However, this fetch does not happen unless there are at least HTHRESH
    valid descriptors in host memory to fetch. HTHRESH should be given a non-zero value each time PTHRESH is used.
    '''

    # WTHRESH: Should not be higher than 1 when ITR == 0, else device basically crashes
    WTHRESH = np.random.randint(1, 40)
    
    #PTHRESH: WTHRESH + PTHRESH < 40
    #PTHRESH = 40 - WTHRESH
    PTHRESH = np.random.randint(1, (40 - WTHRESH))
    
    # HTHRESH
    HTHRESH = np.random.randint(1, 40)

    '''
    DTXMXSZRQ
    The maximum allowed amount of 256 bytes outstanding requests. If the total
    size request is higher than the amount in the field no arbitration is done and no
    new packet is requested
    '''
    DTXMXSZRQ = np.random.randint(1, 4096)
    
    #print("RXD=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d\n" % (ITR/2, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH))
    
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 rx-usecs", str(ITR)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    #print(p1.communicate())
        
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 WTHRESH", str(WTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    #print(p1.communicate())
    
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 PTHRESH", str(PTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    #print(p1.communicate())
    
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 HTHRESH", str(HTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    #print(p1.communicate())

    # DTXMXSZRQ 
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 DTXMXSZRQ", str(DTXMXSZRQ)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    #print(p1.communicate())

    time.sleep(1)
    for i in range(5):
        p1 = Popen(["ping", "-c 3", CSERVER], stdout=PIPE)
        output = p1.communicate()[0]
        if "3 received" in str(output):
            #print("3 received")
            return 1
        time.sleep(1)

    print("ifdown enp4s0f1 && ifup enp4s0f1")
    p1 = Popen(["ssh", CSERVER2, "ifdown enp4s0f1 && ifup enp4s0f1"], stdout=PIPE, stderr=PIPE)
    time.sleep(2)

    return 0

def runBench(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE, stderr=PIPE)
    #time.sleep(1)
    stdout, stderr = p1.communicate()
    #print(len(stdout))
    #print(stdout)
    #print("")
    #print(len(stderr))
    #print(stderr)
    if 'Mbps' in str(stderr):
        s = str(stderr).strip().split('-->')[1]
        t = s.split('Mbps')[0]
        return float(t.strip())
    else:
        return -1.0
    
def runStatic(msg_size):
    runRemoteCommand(CSERVER, "pkill NPtcp")
    time.sleep(0.5)
    runLocalCommand("pkill NPtcp")
    time.sleep(0.5)
    itrstart = runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-1 | tr -s ' ' | cut -d ' ' -f 4")
    runRemoteCommand (CSERVER2, "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ -x, taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+" -p 0 -r -I")
    #runRemoteCommand(CSERVER, "taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+" -p 0 -r -I")
    time.sleep(1)
    tput = runBench("taskset -c 1 NPtcp -h "+CSERVER+" -l "+msg_size+" -u "+msg_size+" -T 2 -p 0 -r -I")
    if tput > 0:
        itrend = runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-1 | tr -s ' ' | cut -d ' ' -f 4")
        time.sleep(0.5)
        output = runRemoteCommandGet(CSERVER2, "cat perf.out")
        nins = 0
        ncycles = 0
        cache_misses = 0
        joules = 0
        watts = 0
        for l in str(output).split("\\n"):
            f = list(filter(None, l.strip().split(',')))
            if 'instructions' in l:
                nins = float(f[0])
            if 'cycles' in l:
                ncycles = float(f[0])
            if 'LLC' in l:
                cache_misses += float(f[0])
            if 'Joules' in l:
                joules += float(f[0])
        watts = joules/2.0
        return tput,nins,ncycles,watts,cache_misses,int(itrend)-int(itrstart)
    else:
        return tput,0,0,0,0,0
    
if updateNIC() == 1:
    npu = np.random.random_sample()
    msg = np.random.randint(500, 20000)
    if npu <= 0.2:
        msg = np.random.randint(500, 10000)
    elif npu > 0.2 and npu <= 0.4:
        msg = np.random.randint(10000, 20000)
    elif npu > 0.4 and npu <= 0.5:
        msg = np.random.randint(20000, 30000)
    elif npu > 0.5 and npu <= 0.6:
        msg = np.random.randint(30000, 50000)
    elif npu > 0.6 and npu <= 0.7:
        msg = np.random.randint(50000, 100000)
    elif npu > 0.7 and npu <= 0.8:
        msg = np.random.randint(100000, 150000)
    elif npu > 0.8 and npu <= 0.9:
        msg = np.random.randint(150000, 200000)
    else:
        msg = np.random.randint(500, 500000)
            
    #tput = runStatic(str(msg))
    tput,nins,ncycles,watts,cache_misses,nitr = runStatic(str(msg))
    print("MSG=%d RXD=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d TPUT=%d INSTRUCTIONS=%d CYCLES=%d LLC_MISS=%d WATTS=%d INTERRUPTS=%d" % (msg, ITR/2, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, int(tput), int(nins), int(ncycles), int(cache_misses), int(watts), nitr))
    print("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d" % (msg, ITR/2, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, int(tput), int(nins), int(ncycles), int(cache_misses), int(watts), nitr))







    
