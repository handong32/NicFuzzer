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
import argparse

CSERVER = "192.168.1.200"
CSERVER2 = "10.255.5.8"
ITR = 0
WTHRESH = 0
PTHRESH = 0
HTHRESH = 0
DTXMXSZRQ = 0
DCA = 0
RSC_DELAY = 0
MAX_DESC = 0
BSIZEPKT = 0
BSIZEHDR = 0
RXRING = 0
TXRING = 0

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
    global DCA
    global RSC_DELAY
    global MAX_DESC
    global BSIZEPKT
    global BSIZEHDR
    global RXRING
    global TXRING
    
    ### fix syntax highlighting in emacs???
    bs = 0
    
    '''
    Receive Side Scaling (RSC)
    '''
    # RSC Delay: The delay = (RSC Delay + 1) x 4 us = 4, 8, 12... 32 us.
    # 3 bits, so [0 - 7]
    RSC_DELAY = np.random.randint(1, 9)
    
    '''
    MAXDESC * SRRCTL.BSIZEPKT must not exceed 64 KB minus one, which is the
    maximum total length in the IP header and must be larger than the expected
    received MSS.

    Maximum descriptors per Large receive as follow:
    00b = Maximum of 1 descriptor per large receive.
    01b = Maximum of 4 descriptors per large receive.
    10b = Maximum of 8 descriptors per large receive.
    11b = Maximum of 16 descriptors per large receive
    '''
    MAX_DESC = np.random.randint(1, 4)


    '''
    SRRCTL.BSIZEPKT
    Receive Buffer Size for Packet Buffer.
    The value is in 1 KB resolution. Value can be from 1 KB to 16 KB. Default buffer size is
    2 KB. This field should not be set to 0x0. This field should be greater or equal to 0x2
    in queues where RSC is enabled.

    *** Linux default is at 3072
    
    MAXDESC * SRRCTL.BSIZEPKT must not exceed 64 KB minus one
    '''
    if MAX_DESC == 1:
        BSIZEPKT = np.random.randint(3, 16) * 1024
    elif MAX_DESC == 2:
        BSIZEPKT = np.random.randint(3, 8) * 1024
    else:
        BSIZEPKT = np.random.randint(3, 4) * 1024
        
    '''
    BSIZEHEADER

    Receive Buffer Size for Header Buffer.
    The value is in 64 bytes resolution. Value can be from 64 bytes to 1024 bytes

    *** Linux default is set at 0x4 * 64 Bytes = 256 Bytes
    '''
    # [4, 8, 12, 16] * 64 Bytes
    BSIZEHDR = np.random.randint(1, 5) * 4 * 64

    '''
    ITR Interval
    '''
    # ITR: (RSC_DELAY+2) us to 200 us in increments of 2
    ITR = np.random.randint((((RSC_DELAY+1) * 4)/2)+1, 101) * 2
    
    '''
    RDLEN
    '''
    c = np.random.randint(0, 3)
    if c == 0:
        RXRING = 512
    elif c == 1:
        RXRING = 4092
    else:
        RXRING = 8192

    '''
    TDLEN
    '''
    c = np.random.randint(0, 3)
    if c == 0:
        TXRING = 512
    elif c == 1:
        TXRING = 4092
    else:
        TXRING = 8192

    
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

    # [2, 40) in increments of 2
    # WTHRESH: Should not be higher than 1 when ITR == 0, else device basically crashes
    WTHRESH = np.random.randint(1, 20)
    
    #PTHRESH: WTHRESH + PTHRESH < 40
    PTHRESH = np.random.randint(1, (20 - WTHRESH)+1)
    
    # HTHRESH
    HTHRESH = np.random.randint(1, 20)

    WTHRESH *= 2
    PTHRESH *= 2
    HTHRESH *= 2
    
    '''
    DTXMXSZRQ
    The maximum allowed amount of 256 bytes outstanding requests. If the total
    size request is higher than the amount in the field no arbitration is done and no
    new packet is requested
    
    min: 0x10 * 256 = 4 KB
    max: 0xFFF * 256 = 1 MB
    '''
    c = np.random.randint(0, 5)
    if c == 0:
        DTXMXSZRQ = 16
    elif c == 1:
        DTXMXSZRQ = 1023
    elif c == 2:
        DTXMXSZRQ = 2046
    elif c == 3:
        DTXMXSZRQ = 3069
    elif c == 4:
        # 0xFFF
        DTXMXSZRQ = 4095

    '''
    DCA == 1, RX_DCA = OFF, TX_DCA = OFF
    DCA == 2, RX_DCA = ON, TX_DCA = OFF
    DCA == 3, RX_DCA = OFF, TX_DCA = ON
    DCA == 4, RX_DCA = ON, TX_DCA = ON
    '''
    DCA = np.random.randint(1,5)

    # RSC_DELAY
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 RSCDELAY", str(RSC_DELAY)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # MAXDESC
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 MAXDESC", str(MAX_DESC)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # BSIZEPKT
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 BSIZEPACKET", str(BSIZEPKT)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # BSIZEHDR
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 BSIZEHEADER", str(BSIZEHDR)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # RXRING
    p1 = Popen(["ssh", CSERVER2, "ethtool -G enp4s0f1 rx", str(RXRING)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # TXRING
    p1 = Popen(["ssh", CSERVER2, "ethtool -G enp4s0f1 tx", str(TXRING)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # ITR
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 rx-usecs", str(ITR)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
        
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 WTHRESH", str(WTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 PTHRESH", str(PTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 HTHRESH", str(HTHRESH)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # DTXMXSZRQ 
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 DTXMXSZRQ", str(DTXMXSZRQ)], stdout=PIPE, stderr=PIPE)
    p1.communicate()

    # DCA
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 DCA", str(DCA)], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    
    #print("RSC_DELAY=%d MAX_DESC=%d BSIZEPKT=%d BSIZEHDR=%d RXRING=%d TXRING=%d ITR=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d DCA=%d\n" % (RSC_DELAY, MAX_DESC, BSIZEPKT, BSIZEHDR, RXRING, TXRING, ITR, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, DCA))

    p1 = Popen(["ssh", CSERVER2, "ifdown enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    
    p1 = Popen(["ssh", CSERVER2, "ifup enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    for i in range(5):
        p1 = Popen(["ping", "-c 3", CSERVER], stdout=PIPE)
        output = p1.communicate()[0]
        if "3 received" in str(output):
            #print("3 received")
            return 1
        time.sleep(1)

    #print("ifdown enp4s0f1 && ifup enp4s0f1")
    #p1 = Popen(["ssh", CSERVER2, "ifdown enp4s0f1 && ifup enp4s0f1"], stdout=PIPE, stderr=PIPE)
    #time.sleep(2)
    print("enp40sf1 did not restart correctly")
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
    #runRemoteCommand (CSERVER2, "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ -x, taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+" -p 0 -r -I")

    runRemoteCommand (CSERVER2, "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ taskset -c 1 NPtcp -l "+msg_size+" -u "+msg_size+" -p 0 -r -I")
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
        ttime = 0.0
        watts = -1
        for l in str(output).split("\\n"):
            print(l.strip())
            f = list(filter(None, l.strip().split(' ')))
            if 'cycles' in l:
                ncycles = float(f[0].replace(',', ''))
            if 'instructions' in l:
                nins = float(f[0].replace(',', ''))
            if 'LLC' in l:
                cache_misses += float(f[0].replace(',', ''))
            if 'Joules' in l:
                joules += float(f[0])
            if 'seconds' in l:
                ttime = float(f[0])
        watts = joules/ttime
        return tput,nins,ncycles,watts,cache_misses,int(itrend)-int(itrstart)
    else:
        return tput,0,0,0,0,0

#print(updateNIC())
'''
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
    print("RSC_DELAY=%d MAX_DESC=%d BSIZEPKT=%d BSIZEHDR=%d RXRING=%d TXRING=%d ITR=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d DCA=%d TPUT=%d INSTRUCTIONS=%d CYCLES=%d LLC_MISS=%d WATTS=%d INTERRUPTS=%d" % (RSC_DELAY, MAX_DESC, BSIZEPKT, BSIZEHDR, RXRING, TXRING, ITR, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, DCA, int(tput), int(nins), int(ncycles), int(cache_misses), int(watts), nitr))
    
    #print("MSG=%d RXD=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d TPUT=%d INSTRUCTIONS=%d CYCLES=%d LLC_MISS=%d WATTS=%d INTERRUPTS=%d" % (msg, ITR/2, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, int(tput), int(nins), int(ncycles), int(cache_misses), int(watts), nitr))
    #print("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d" % (msg, ITR/2, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, int(tput), int(nins), int(ncycles), int(cache_misses), int(watts), nitr))
'''

#msg = np.random.randint(500, 20000)
msg = 10000
tput,nins,ncycles,watts,cache_misses,nitr = runStatic(str(msg))
print("TPUT=%f INSTRUCTIONS=%d CYCLES=%d LLC_MISS=%d WATTS=%f INTERRUPTS=%d" % (tput, int(nins), int(ncycles), int(cache_misses), watts, nitr))

