import subprocess
from subprocess import Popen, PIPE, call
import time
from datetime import datetime
import sys
import os
import getopt

MASTER = "192.168.1.200"

def runLocalCommandOut(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    print("\t"+com, "->\n", p1.communicate()[0].strip())
    
def runRemoteCommandOut(com):
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)
    print("\tssh "+MASTER, com, "->\n", p1.communicate()[0].strip())

def runLocalCommand(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    
def runRemoteCommand(com):
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)        

def runMutilate(com):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    output = p1.communicate()[0].strip()
    print(output)
    f = open("mutilate.log", "w")
    f.write(output)
    f.close()
    
def runBench():
    #runRemoteCommandOut("pkill memcached")
    #runLocalCommandOut("pkill mutilate")
    runRemoteCommand("chrt -r 1 perf stat -C 1,3,5,7,9,11,13,15 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ -x, numactl --cpunodebind=1 --membind=1 memcached -u nobody -t 8 -m 16G -l "+MASTER+" -B binary")
    time.sleep(1)
    runLocalCommandOut("taskset -c 1 mutilate --binary -s "+MASTER+" --loadonly -K fb_key -V fb_value")
    runLocalCommand("taskset -c 3,5,7,9,11,13,15 mutilate -A --affinity -T 7")
    time.sleep(1)
    runMutilate("taskset -c 1 mutilate --binary -B -s "+MASTER+" -a localhost -K fb_key -V fb_value -i fb_ia -u 0.25 -c 8 -d 4 -C 8 --search=99:500 -t 60")
    runRemoteCommandOut("pkill memcached")

if __name__ == '__main__':
    runBench()
