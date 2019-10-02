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

MASTER = "192.168.1.200"
CSERVER = "192.168.1.200"
CSERVER2 = "10.255.5.8"
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


def runLocalCommandOut(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    p1.communicate()
    #print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(com):
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)
    p1.communicate()
    #print("\tssh "+MASTER, com, "->\n", p1.communicate()[0].strip())

def runLocalCommand(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(com):
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)        

def runRemoteCommandGet(server, com):
    p1 = Popen(["ssh", server, com], stdout=PIPE)
    return p1.communicate()[0].strip()

def setITR(v):
    global ITR
    p1 = Popen(["ssh", CSERVER2, "ethtool -C enp4s0f1 rx-usecs", v], stdout=PIPE, stderr=PIPE)
    p1.communicate()    
    time.sleep(0.5)
    ITR = int(v)

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
    global THRESHC
    
    ### fix syntax highlighting in emacs???
    bs = 0
    
    '''
    Receive Side Scaling (RSC)
    '''
    # RSC Delay: The delay = (RSC Delay + 1) x 4 us = 4, 8, 12... 32 us.
    # 3 bits, so [0 - 7]
    # select 4: 4, 8, 16, 32 | 1, 2, 4, 8
    RSC_DELAY = np.random.randint(1, 5)
    if RSC_DELAY == 3:
        RSC_DELAY=4
    elif RSC_DELAY == 4:
        RSC_DELAY = 8
    
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
    # select 3: 1, 2, 3
    MAX_DESC = np.random.randint(1, 4)

    '''
    SRRCTL.BSIZEPKT
    Receive Buffer Size for Packet Buffer.
    The value is in 1 KB resolution. Value can be from 1 KB to 16 KB. Default buffer size is
    2 KB. This field should not be set to 0x0. This field should be greater or equal to 0x2
    in queues where RSC is enabled.

    *** Linux default is at 3072
    
    MAXDESC * SRRCTL.BSIZEPKT must not exceed 64 KB minus one

    if MAX_DESC == 1:
        BSIZEPKT = 12 * 1024 #np.random.randint(3, 16) * 1024
    elif MAX_DESC == 2:
        BSIZEPKT = 6 * 1024#np.random.randint(3, 8) * 1024
    else:
        BSIZEPKT = 3 * 1024 #np.random.randint(3, 4) * 1024
    '''
    BSIZEPKT = 3 * 1024
    
    '''
    BSIZEHEADER

    Receive Buffer Size for Header Buffer.
    The value is in 64 bytes resolution. Value can be from 64 bytes to 1024 bytes

    *** Linux default is set at 0x4 * 64 Bytes = 256 Bytes
    '''
    # select 3: [4, 8, 12] * 64 Bytes
    BSIZEHDR = np.random.randint(1, 4) * 4 * 64

    '''
    ITR Interval
    '''
    # ITR: (RSC_DELAY+2) us to 200 us in increments of 10
    #ITR = np.random.randint((((RSC_DELAY+1) * 4)/2)+1, 101) * 2
    itr_delay_us = RSC_DELAY*4
    itr_start = (itr_delay_us/10) + 1
    #print("itr_start", itr_start)
    ITR = np.random.randint(itr_start, 16) * 10
    
    '''
    RDLEN
    '''
    c = np.random.randint(0, 2)
    if c == 0:
        RXRING = 512
        TXRING = 512
    else:
        RXRING = 4092
        TXRING = 4092

    '''
    TDLEN
    '''
    #c = np.random.randint(0, 2)
    #if c == 0:
    #    TXRING = 512
    #else:
    #    TXRING = 4092
    
    '''
    Notes about THRESH, PTHRESH, WTHRESH

    Transmit descriptor fetch setting is programmed in the TXDCTL[n] register per
    In order to reduce transmission latency, it is recommended to set the PTHRESH value
    as high as possible while the HTHRESH and WTHRESH as low as possible (down to
    zero).

    In order to minimize PCIe overhead the PTHRESH should be set as low as possible
    while HTHRESH and WTHRESH should be set as high as possible.

    The sum of PTHRESH plus WTHRESH must not be greater than the onchip descriptor
    buffer size (40)

    When the WTHRESH equals zero, descriptors are written back for those
    descriptors with the RS bit set. When the WTHRESH value is greater than
    zero, descriptors are accumulated until the number of accumulated descriptors equals
    the WTHRESH value, then these descriptors are written back. Accumulated
    descriptor write back enables better use of the PCIe bus and memory bandwidth.

    PTHRESH: Pre Fetch Threshold The on chip descriptor buffer becomes almost empty while there are enough
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
    '''
    WTHRESH = np.random.randint(1, 20)
    
    #PTHRESH: WTHRESH + PTHRESH < 40
    PTHRESH = np.random.randint(1, (20 - WTHRESH)+1)
    
    # HTHRESH
    HTHRESH = np.random.randint(1, 20)

    WTHRESH *= 2
    PTHRESH *= 2
    HTHRESH *= 2
    '''
    '''
    In order to reduce transmission latency, it is recommended to set the PTHRESH value
    as high as possible while the HTHRESH and WTHRESH as low as possible (down to
    zero).

    In order to minimize PCIe overhead the PTHRESH should be set as low as possible
    while HTHRESH and WTHRESH should be set as high as possible.

    The sum of PTHRESH plus WTHRESH must not be greater than the on chip descriptor
    buffer size (40)
    '''
    THRESHC = np.random.randint(0, 3)

    if THRESHC == 0:
        '''
        CPU cache line optimization Assume  N equals the CPU cache line divided by 16 descriptor size.
        Then in order to align descriptors prefetch to CPU cache line in most cases it is advised to
        set PTHRESH to the onchip descriptor buffer size minus N and HTHRESH to N. In order to align 
        descriptor write back to the CPU cache line it is advised to set WTHRESH to either N or even 2 times N.
        Note that partial cache line writes might significantly degrade performance. Therefore, it is highly recommended to follow this advice.
        
        getconf LEVEL1_DCACHE_LINESIZE == CPU cache line size 64
        on chip descriptor size == 16
        
        N = 64 / 16 = 4
        PTHRESH = 16 4 == 12
        HTHRESH == 4
        WTHRESH == 4 or 8
        '''

        PTHRESH = 12
        HTHRESH = 4
        WTHRESH = 4
    elif THRESHC == 1:
        '''
        Minimizing PCIe overhead: As an example, setting PTHRESH to the on-chip descriptor buffer size minus 16 and HTHRESH to 16 
        minimizes the PCIe request and header overhead to 20% of the bandwidth required for the descriptor fetch.
        '''
        PTHRESH = 0
        HTHRESH = 16
        WTHRESH = 16
    elif THRESHC == 2:
        '''
        Minimizing transmission latency from tail update: Setting PTHRESH to the on chip 
        descriptor buffer size minus N, previously defined, while HTHRESH and WTHRESH to zero.
        '''
        PTHRESH = 12
        HTHRESH = 0
        WTHRESH = 0
    
    '''
    DTXMXSZRQ
    The maximum allowed amount of 256 bytes outstanding requests. If the total
    size request is higher than the amount in the field no arbitration is done and no
    new packet is requested
    
    min: 0x10 * 256 = 4 KB
    max: 0xFFF * 256 = 1 MB
    '''
    c = np.random.randint(0, 3)
    if c == 0:
        # default
        DTXMXSZRQ = 16
    elif c == 1:
        DTXMXSZRQ = 2046
    elif c == 2:
        # 0xFFF
        DTXMXSZRQ = 4095

    '''
    DCA == 1, RX_DCA = OFF, TX_DCA = OFF
    DCA == 2, RX_DCA = ON, TX_DCA = OFF
    DCA == 3, RX_DCA = OFF, TX_DCA = ON
    DCA == 4, RX_DCA = ON, TX_DCA = ON
    '''
    dcac = np.random.randint(0, 2)
    if dcac == 0:
        DCA = 1
    else:
        DCA = 4

    #print("RSC_DELAY=%d MAX_DESC=%d BSIZEPKT=%d BSIZEHDR=%d RXRING=%d TXRING=%d ITR=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d DCA=%d\n" % (RSC_DELAY, MAX_DESC, BSIZEPKT, BSIZEHDR, RXRING, TXRING, ITR, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, DCA))
    #return

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
    
    p1 = Popen(["ssh", CSERVER2, "ifdown enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)
    
    p1 = Popen(["ssh", CSERVER2, "ifup enp4s0f1"], stdout=PIPE, stderr=PIPE)
    p1.communicate()
    time.sleep(1)

    #print("RSC_DELAY=%d MAX_DESC=%d BSIZEPKT=%d BSIZEHDR=%d RXRING=%d TXRING=%d ITR=%d DTXMXSZRQ=%d WTHRESH=%d PTHRESH=%d HTHRESH=%d DCA=%d" % (RSC_DELAY, MAX_DESC, BSIZEPKT, BSIZEHDR, RXRING, TXRING, ITR, DTXMXSZRQ, WTHRESH, PTHRESH, HTHRESH, DCA), end='')
    
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

def runMutilate(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    output = p1.communicate()[0].strip()
    #print(output)
    f = open("mutilate.log", "w")
    f.write(output)
    f.close()
    
def runBench():
    #runRemoteCommandOut("pkill memcached")
    #runLocalCommandOut("pkill mutilate")
    runRemoteCommand("chrt -r 1 perf stat -C 1,3,5,7,9,11,13,15 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ numactl --cpunodebind=1 --membind=1 memcached -u nobody -t 8 -m 16G -l "+MASTER+" -B binary")
    time.sleep(1)
    runLocalCommandOut("taskset -c 1 mutilate --binary -s "+MASTER+" --loadonly -K fb_key -V fb_value")
    runLocalCommand("taskset -c 3,5,7,9,11,13,15 mutilate -A --affinity -T 7")
    time.sleep(1)
    runMutilate("taskset -c 1 mutilate --binary -B -s "+MASTER+" --noload -a localhost -K fb_key -V fb_value -i fb_ia -u 0.25 -c 8 -d 4 -C 8 --search=99:500 -t 30")
    runRemoteCommandOut("pkill memcached")

def runMutilateStats(com):
    try:
        p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
        output = p1.communicate()[0].strip()
        #print(len(output), output)
        if len(output) > 10:
            for line in str(output).strip().split("\\n"):
                #print(line.strip())
                if "Peak" in line:
                    qps = float((line.split("=")[1]).strip())
                    return qps
        else:
            return -1.0
    except Exception as e:
        print("An error occurred in runMutilateStats ", type(e), e)
        return -1.0
    
def runBenchStats():
    sitr1 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-1 | tr -s ' ' | cut -d ' ' -f 4"))
    sitr3 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-3 | tr -s ' ' | cut -d ' ' -f 6"))
    sitr5 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-5 | tr -s ' ' | cut -d ' ' -f 8"))
    sitr7 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-7 | tr -s ' ' | cut -d ' ' -f 10"))
    sitr9 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-9 | tr -s ' ' | cut -d ' ' -f 12"))
    sitr11 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-11 | tr -s ' ' | cut -d ' ' -f 14"))
    sitr13 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-13 | tr -s ' ' | cut -d ' ' -f 16"))
    sitr15 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-15 | tr -s ' ' | cut -d ' ' -f 18"))
    #runRemoteCommand("chrt -r 1 perf stat -C 1,3,5,7,9,11,13,15 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ numactl --cpunodebind=1 --membind=1 memcached -u nobody -t 8 -m 16G -l "+MASTER+" -B binary")
    runRemoteCommand("chrt -r 1 perf stat -C 1,3,5,7,9,11,13,15 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ numactl --cpunodebind=1 --membind=1 memcached -u nobody -t 8 -m 16G -l "+MASTER+" -B binary")
    time.sleep(1)
    runLocalCommandOut("taskset -c 1 mutilate --binary -s "+MASTER+" --loadonly -K fb_key -V fb_value")
    #runLocalCommandOut("taskset -c 1 mutilate --binary -s "+MASTER+" --loadonly --keysize=19 --valuesize=2")
    runLocalCommand("taskset -c 3,5,7,9,11,13,15 mutilate -A --affinity -T 7")
    time.sleep(1)
    qps = runMutilateStats("taskset -c 1 mutilate --binary -B -s "+MASTER+" --noload -a localhost -K fb_key -V fb_value -i fb_ia -u 0.25 -c 8 -d 4 -C 8 --search=99:500 -t 30")
    #qps = runMutilateStats("taskset -c 1 mutilate --binary -B -s "+MASTER+" --noload -a localhost -K fb_key -V fb_value -i fb_ia -u 0.25 -c 14 -d 7 -C 14 --search=99:1000 -t 30")
    #qps = runMutilateStats("taskset -c 1 mutilate --binary -B -s "+MASTER+" --noload -a localhost  --keysize=19 --valuesize=2 -u 0.002 -c 8 -d 4 -C 8 --search=99:500 -t 30")
    runRemoteCommandOut("pkill memcached")
    if qps > 0.0:
        time.sleep(0.1)
        eitr1 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-1 | tr -s ' ' | cut -d ' ' -f 4"))
        eitr3 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-3 | tr -s ' ' | cut -d ' ' -f 6"))
        eitr5 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-5 | tr -s ' ' | cut -d ' ' -f 8"))
        eitr7 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-7 | tr -s ' ' | cut -d ' ' -f 10"))
        eitr9 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-9 | tr -s ' ' | cut -d ' ' -f 12"))
        eitr11 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-11 | tr -s ' ' | cut -d ' ' -f 14"))
        eitr13 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-13 | tr -s ' ' | cut -d ' ' -f 16"))
        eitr15 = int(runRemoteCommandGet(CSERVER2, "cat /proc/interrupts | grep -m 1 enp4s0f1-TxRx-15 | tr -s ' ' | cut -d ' ' -f 18"))
        itr1 = eitr1 - sitr1
        itr3 = eitr3 - sitr3
        itr5 = eitr5 - sitr5
        itr7 = eitr7 - sitr7
        itr9 = eitr9 - sitr9
        itr11 = eitr11 - sitr11
        itr13 = eitr13 - sitr13
        itr15 = eitr15 - sitr15
        
        output = runRemoteCommandGet(MASTER, "cat perf.out")
        cycles = 0
        instructions = 0
        llc_load = 0
        llc_store = 0
        energy_pkg = 0.0
        energy_ram = 0.0
        ttime = 0.0
        watts = 0.0
        ipc = 0.0
        avg_itr = 0.0
        for l in str(output).split("\\n"):
            #print(l.strip())
            f = list(filter(None, l.strip().split(' ')))
            if 'cycles' in l:
                cycles = int(f[0].replace(',', ''))
            if 'instructions' in l:
                instructions = int(f[0].replace(',', ''))
            if 'load-misses' in l:
                llc_load = int(f[0].replace(',', ''))
            if 'store-misses' in l:
                llc_store = int(f[0].replace(',', ''))
            if 'energy-pkg' in l:
                energy_pkg = float(f[0].replace(',', ''))
            if 'energy-ram' in l:
                energy_ram = float(f[0].replace(',', ''))
            if 'seconds' in l:
                ttime = float(f[0].replace(',', ''))
        watts = (energy_pkg+energy_ram)/ttime
        ipc = instructions/float(cycles)
        avg_itr = (itr1+itr3+itr5+itr7+itr9+itr11+itr13+itr15) / 8.0
        print("RSC_DELAY=%d MAX_DESC=%d BSIZEHDR=%d RXRING=%d TXRING=%d ITR=%d DTXMXSZRQ=%d THRESHC=%d DCA=%d QPS=%.2f CYCLES=%d INSTRUCTIONS=%d LLC_LOAD_MISSES=%d LLC_STORE_MISSES=%d NRG_PKG=%.2f NRG_RAM=%.2f TIME=%.2f ITR1=%d ITR3=%d ITR5=%d ITR7=%d ITR9=%d ITR11=%d ITR13=%d ITR15=%d WATTS=%.2f QPS/WATT=%.2f LLC_MISSES=%d IPC=%.5f AVG_ITR_PER_CORE=%.2f" % (RSC_DELAY, MAX_DESC, BSIZEHDR, RXRING, TXRING, ITR, DTXMXSZRQ, THRESHC, DCA, qps, cycles, instructions, llc_load, llc_store, energy_pkg, energy_ram, ttime, itr1, itr3, itr5, itr7, itr9, itr11, itr13, itr15, watts, qps/watts, llc_load+llc_store, ipc, avg_itr))
        #print("WATTS=%.2f" % ((energy_pkg+energy_ram) / ttime))
if __name__ == '__main__':
    if len(sys.argv) == 2:
        setITR(sys.argv[1])
        runBenchStats()
    else:
        #runBenchStats()
        if updateNIC() == 1:
            runBenchStats()

'''        
if len(sys.argv) == 2:
    setITR(sys.argv[1])
    tput,nins,ncycles,watts,cache_misses,ttime,nitr = runRand(str(512), str(24576), str(20000))
    ##tput,nins,ncycles,watts,cache_misses,ttime,nitr = runRand(str(512), str(524288), str(4000))
    print("ITR=%d TPUT=%f INSTRUCTIONS=%d CYCLES=%d LLC_MISS=%d WATTS=%f INTERRUPTS=%d TIME(s)=%f" % (int(sys.argv[1]), tput, int(nins), int(ncycles), int(cache_misses), watts, nitr, ttime))
else:
    tput,nins,ncycles,watts,cache_misses,ttime,nitr = runRand(str(512), str(24576), str(20000))
    #tput,nins,ncycles,watts,cache_misses,ttime,nitr = runRand(str(512), str(524288), str(4000))
    print("DefaultLinux=1 TPUT=%f INSTRUCTIONS=%d CYCLES=%d LLC_MISS=%d WATTS=%f INTERRUPTS=%d TIME(s)=%f" % (tput, int(nins), int(ncycles), int(cache_misses), watts, nitr, ttime))
'''
