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

def runMutilate(com, dirr, i, delay):
    p1 = Popen(list(filter(None, com.strip().split(' '))), stdout=PIPE)
    output = p1.communicate()[0].strip().split('\n')
    ll = list(filter(None, output[1].strip().split(' ')))
    f = open(dirr+"/"+delay+"_"+str(i)+".log", "w")
    f.write(str(ll[8])+"\n")
    f.close()

def runLoop(dirr, i, delay, goal):
    runRemoteCommandOut("pkill memcached")
    runLocalCommandOut("pkill mutilate")
    time.sleep(1)
    runRemoteCommand("taskset -c 1 memcached -u nobody -t 1 -m 8G -l "+MASTER+" -B binary")
    time.sleep(1)
    runLocalCommandOut("taskset -c 1 mutilate --binary -s "+MASTER+" --loadonly -K fb_key -V fb_value")
    time.sleep(1)
    runLocalCommand("taskset -c 2-15 mutilate -A --affinity -T 14")
    time.sleep(1)
    runMutilate("taskset -c 1 mutilate --binary --noload -B -s "+MASTER+" -a localhost -K fb_key -V fb_value -i fb_ia -u 0.25 -c 8 -d 4 -C 8 -Q 1000 -t 30 -q "+str(goal), dirr, i, delay)
    time.sleep(1)

def main(argv):
    lu = 0
    uu = 0
    su = 0
    txq = 512
    rxq = 512
    niters = 1
    goal = 10000
    linux = 0
    options, remainder = getopt.getopt(sys.argv[1:], 'x:r:t:i:g:l:')
    for opt, arg in options:
        if opt in ('-x'):    
            lu = int(arg.strip().split(',')[0])
            uu = int(arg.strip().split(',')[1])
            su = int(arg.strip().split(',')[2])
        if opt in ('-r'):    
            rxq = int(arg)
        if opt in ('-t'):    
            txq = int(arg)
        if opt in ('-i'):    
            niters = int(arg)
        if opt in ('-g'):    
            goal = int(arg)
        if opt in ('-l'):    
            linux = int(arg)
    today = datetime.now()
    
    dirr=str(today.month)+"_"+str(today.day)+"_"+str(today.year)+"_"+str(today.hour)+"_"+str(today.minute)+"_"+str(today.second)
    cm=dirr+" delay=[" +str(lu)+","+str(uu)+","+str(su)+ "]"+ " RXQ="+str(rxq)+ " TXQ="+str(txq)+ " ITERS="+ str(niters)+ " GOAL RPS="+ str(goal)+" Linux="+str(linux)
    print(cm)
    #print(dirr, "delay=[",lu, uu, su, "]", "RXQ=",rxq, "TXQ=",txq, "ITERS=", niters, "GOAL RPS=", goal)
    
    runLocalCommandOut("mkdir -p "+dirr)
    f = open(dirr+"/command.txt", "w")
    f.write(cm+"\n")
    f.close()

    if linux == 0:
        for delay in range(lu, uu, su):    
            runRemoteCommandOut("ethtool -C enp4s0f1 rx-usecs "+str(delay))
            time.sleep(1)
            for i in range(1, niters+1):
                runLoop(dirr, i, str(delay), goal)
    else:
        for i in range(1, niters+1):
            runLoop(dirr, i, "linux", goal)
            
if __name__ == '__main__':
    main(sys.argv[1:])
