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
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    output = p1.communicate()[0].strip()
    for line in output.strip().split("\n"):
        if "Peak" in line:
            qps = float((line.split("=")[1]).strip())
            return qps
    
def runBenchStats():
    runRemoteCommand("chrt -r 1 perf stat -C 1,3,5,7,9,11,13,15 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ numactl --cpunodebind=1 --membind=1 memcached -u nobody -t 8 -m 16G -l "+MASTER+" -B binary")
    time.sleep(1)
    runLocalCommandOut("taskset -c 1 mutilate --binary -s "+MASTER+" --loadonly -K fb_key -V fb_value")
    runLocalCommand("taskset -c 3,5,7,9,11,13,15 mutilate -A --affinity -T 7")
    time.sleep(1)
    qps = runMutilateStats("taskset -c 1 mutilate --binary -B -s "+MASTER+" --noload -a localhost -K fb_key -V fb_value -i fb_ia -u 0.25 -c 8 -d 4 -C 8 --search=99:1000 -t 60")
    runRemoteCommandOut("pkill memcached")
    time.sleep(0.5)
    output = runRemoteCommandGet(MASTER, "cat perf.out")
    joules = 0.0
    ttime = 0.0
    for l in str(output).split("\n"):
        #print(l.strip())
        f = list(filter(None, l.strip().split(' ')))
        if 'Joules' in l:
            joules += float(f[0].replace(',', ''))
        if 'seconds' in l:
            ttime = float(f[0].replace(',', ''))
    watts = joules/ttime
    print("QPS=%.2f Watts=%.2f QPS/Watts=%.2f" % (qps, watts, qps/watts))
        
if __name__ == '__main__':
    #runBench()
    runBenchStats()
