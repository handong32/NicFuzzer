import subprocess
from subprocess import Popen, PIPE, call
import time
from datetime import datetime
import sys
import os
import getopt
#import numpy as np

MASTER = "192.168.1.200"

def runLocalCommandOut(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    print "\t"+com, "->\n", p1.communicate()[0].strip()
    
def runRemoteCommandOut(com):
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)
    print "\tssh "+MASTER, com, "->\n", p1.communicate()[0].strip()

def runLocalCommand(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(com):
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)        

def runMemtier(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    output = p1.communicate()[0].strip().split('\n')
    for line in output:
        if "Totals" in line:
            print(line)

def main(rxu):
    runRemoteCommandOut("pkill memcached")
    runLocalCommandOut("pkill memtier_benchmark")
    runRemoteCommandOut("ethtool -C enp4s0f1 rx-usecs "+str(rxu))
    #chrt -r 1 perf stat -C 1,3,5,7,9,11,13,15 -e power/energy-pkg/,power/energy-ram/ -x, numactl --cpunodebind=1 --membind=1 memcached -u nobody -t 8 -m 16G -l 192.168.1.200 -B binary
    runRemoteCommand("chrt -r 1 perf stat -C 1,3,5,7,9,11,13,15 -D 1000 -o perf.out -e power/energy-pkg/,power/energy-ram/ -x, numactl --cpunodebind=1 --membind=1 memcached -u nobody -t 8 -m 16G -l "+MASTER+" -B binary")
    time.sleep(1)

    s = datetime.now()
    #runMemtier("memtier_benchmark -s "+MASTER+" -p 11211 -t 8 -R --ratio=1:1 -P memcache_binary --hide-histogram --test-time=28 --json-out-file=memtier.json")
    runMemtier("chrt -r 1 numactl --cpunodebind=1 --membind=1 memtier_benchmark -s "+MASTER+" -p 11211 -t 8 --random-data --data-size-range=4-204 --data-size-pattern=S --key-minimum=200 --key-maximum=400 --ratio=1:1 -P memcache_binary --test-time=28 --json-out-file=memtier.json")
    e = datetime.now()
    duration = (e - s).total_seconds()
    runRemoteCommandOut("pkill memcached")
    runRemoteCommandOut('echo "'+str(duration)+',sec" >> perf.out')
    
if __name__ == '__main__':
    main(int(sys.argv[1]))
