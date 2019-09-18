import subprocess
from subprocess import Popen, PIPE, call
import time
import sys
import os
import getopt
#import numpy as np

MASTER = "10.255.5.9"
NODES = ["10.255.3.8", "10.255.3.5" , "10.255.3.6", "10.255.3.11", "10.255.5.10", "10.255.5.11", "10.255.5.2", "10.255.5.5"]

def runMutilate():
    print "runMutilate"
    for node in NODES:
        print "Node:", node
        p1 = Popen(["ssh", node, "mutilate -A --affinity -T 16"])
        time.sleep(2)
        
def runCommand(com):
    for node in NODES:
        print "Node:", node
        p1 = Popen(["ssh", node, com], stdout=PIPE)
        print "\t", com, "->", p1.communicate()[0].strip()

def powerCycle(n):
    p1 = Popen(["hil", "node", "power", "cycle", n])
    time.sleep(240)
    p2 = Popen(["ssh", MASTER, "ping -c 3 192.168.1.200"], stdout=PIPE)
    p3 = Popen(["grep", "3 received"], stdin=p2.stdout, stdout=PIPE)
    output = p3.communicate()[0]
    if len(output) > 0:
        print n, "has rebooted"
    else:
        print n, " has not successfully rebooted. Exiting benchmark ..."
        sys.exit()

def preloadMemory():
    for i in range(0, 16):
        p1 = Popen(["ssh", MASTER, "mutilate --binary -s 192.168.1.200 --loadonly -K fb_key -V fb_value"], stdout=PIPE)
        p1.communicate()
        time.sleep(1)

def runMutilateBench(com):
    print "runMutilateBench", com
    p1 = Popen(["ssh", MASTER, com], stdout=PIPE)
    output = p1.communicate()[0].split("\n")
    for l in output:
        print l
    time.sleep(1)

def runTest(num):
    for i in range(0, num):
        print "**** RUN", i, "**********"
        
        runCommand("pkill mutilate")
        time.sleep(1)
        
        runMutilate()
        time.sleep(1)
        
        runCommand("pgrep mutilate")
        time.sleep(1)
        
        powerCycle("neu-5-8")
        preloadMemory()
        time.sleep(1)
        
        runMutilateBench("taskset -c 0 mutilate --binary --noload -B -s 192.168.1.200 -a 192.168.1.22 -a 192.168.1.23 -a 192.168.1.24 -a 192.168.1.25 -a 192.168.1.26 -a 192.168.1.27 -a 192.168.1.28 -a 192.168.1.29 -K fb_key -V fb_value -i fb_ia -u 0.25 -c 8 -d 4 -C 8 -Q 1000 -t 60 --scan=100000:1200000:100000")
        
    
def main(argv):
    options, remainder = getopt.getopt(sys.argv[1:], 'r:c:m')
    for opt, arg in options:
        if opt in ('-c'):    
            runCommand(arg)
        if opt in ('-r'):    
            runTest(int(arg))
        elif opt in ('-m'):    
            runMutilate()
    
if __name__ == '__main__':
    main(sys.argv[1:])
