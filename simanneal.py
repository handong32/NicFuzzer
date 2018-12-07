import subprocess
from subprocess import Popen, PIPE, call
import time
import sys
import getopt
import numpy as np

CNODE = "dell8"
SNODE = "dell10"
CIP = "192.168.1.1"
SIP = "192.168.1.2"
PARAMS = []
RXUSECS="16"
RXRING="2048"
TXRING="2048"
IPERFMSG="128K"

def initIperfParams():
    for i in range(0, 33, 2):
        PARAMS.append(str(i))

    PARAMS.append(str(1024))
    PARAMS.append(str(2048))
    PARAMS.append(str(4096))
    PARAMS.append(str(1024))
    PARAMS.append(str(2048))
    PARAMS.append(str(4096))
    print PARAMS

def initMCDParams():
    for i in range(0, 129, 2):
        PARAMS.append(str(i))

    PARAMS.append(str(1024))
    PARAMS.append(str(2048))
    PARAMS.append(str(4096))
    PARAMS.append(str(1024))
    PARAMS.append(str(2048))
    PARAMS.append(str(4096))
    print PARAMS

def resetEm2():
    call(["ssh", CNODE, "ifdown em2.302"])
    call(["ssh", CNODE, "ifup em2.302"])
    time.sleep(1)

def updateIperfConfig():
    global RXUSECS
    global RXRING
    global TXRING
    
    i = np.random.random_integers(len(PARAMS))-1

    if i <= 16:
        RXUSECS=PARAMS[i]
    elif i > 16 and i <= 19:
        RXRING=PARAMS[i]
    else:
        TXRING=PARAMS[i]

    #print "i=",i,"RXU=",RXUSECS,"RXRING=",RXRING,"TXRING=",TXRING

def updateMCDConfig():
    global RXUSECS
    global RXRING
    global TXRING
    
    i = np.random.random_integers(len(PARAMS))-1

    if i <= 64:
        RXUSECS=PARAMS[i]
    elif i > 64 and i <= 67:
        RXRING=PARAMS[i]
    else:
        TXRING=PARAMS[i]
    print "i=",i,"RXU=",RXUSECS,"RXRING=",RXRING,"TXRING=",TXRING
    
def updateNIC():
    p1 = Popen(["ssh", CNODE, "ethtool -C em2 rx-usecs", RXUSECS], stdout=PIPE, stderr=PIPE)
    tmp = p1.communicate()[0]
    
    p2 = Popen(["ssh", CNODE, "ethtool -G em2 rx", RXRING], stdout=PIPE, stderr=PIPE)
    tmp = p2.communicate()[0]
    
    p3 = Popen(["ssh", CNODE, "ethtool -G em2 tx", TXRING], stdout=PIPE, stderr=PIPE)
    tmp = p3.communicate()[0]
    
    resetEm2()
    
    for i in range(5):
        p4 = Popen(["ssh", CNODE, "ping -c 3", SIP], stdout=PIPE, stderr=PIPE)
        p5 = Popen(["grep", "3 received"], stdin=p4.stdout, stdout=PIPE, stderr=PIPE)
        output = p5.communicate()[0]
        #print output
        if len(output) > 0:
            return 1
        else:
            resetEm2()
    
    return 0
    
    
def runIperf():
    p1 = Popen(["ssh", CNODE, "taskset -c", "0", "iperf -s -N -p 5001 -P 1 -w", IPERFMSG], stdout=PIPE)
    time.sleep(1)
    p2 = Popen(["ssh", SNODE, "taskset -c", "0", "iperf -c", CIP ,"-N -p 5001 -P 1 -w", IPERFMSG], stdout=PIPE)
    p3 = Popen(["grep", "sec"], stdin=p2.stdout, stdout=PIPE)
    output = list(filter(None, (p3.communicate()[0]).split(' ')))
    return float(output[len(output)-2])
    
def iperf():
    updateConfig()
    ero = updateNIC()
    if ero == 1:
        #print "done updateNIC"
        return runIperf()
    else:
        return 0.0
    #print("RXUSECS=%s RXRING=%s TXRING=%s perf=%s" % (RXUSECS, RXRING, TXRING, perf))
        
    
def usage():
    print "runSA.py -i {iperf | netpipe | mcd}"

def killallMCD():
    for i in range(5):
        p1 = Popen(["ssh", SNODE, "ps aux"], stdout=PIPE)
        p2 = Popen(["grep", "mutilate"], stdin=p1.stdout, stdout=PIPE)
        output = p2.communicate()[0]
        if len(output) > 0:
            pid = list(filter(None, output.split(' ')))[1]
            p3 = Popen(["ssh", SNODE, "kill -9", pid], stdout=PIPE)
            tmp= p3.communicate()[0]
            break
        else:
            time.sleep(1)

    for i in range(5):
        p1 = Popen(["ssh", CNODE, "ps aux"], stdout=PIPE)
        p2 = Popen(["grep", "memcached"], stdin=p1.stdout, stdout=PIPE)
        output = p2.communicate()[0]
        if len(output) > 0:
            pid = list(filter(None, output.split(' ')))[1]
            p3 = Popen(["ssh", CNODE, "kill -9", pid], stdout=PIPE)
            tmp= p3.communicate()[0]
            break
        else:
            time.sleep(1)

def runMCD():
    p1 = Popen(["ssh", CNODE, "taskset -c", "0", "memcached -u nobody -t 1 -m 8G -l", CIP ,"-B binary"], stdout=PIPE)
    time.sleep(1)
    p2 = Popen(["ssh", SNODE, "./mutilate/mutilate --binary -s", CIP ,"--loadonly -K fb_key -V fb_value"], stdout=PIPE)
    tmp = p2.communicate()[0]
    
    p3 = Popen(["ssh", SNODE, "taskset -c 1-15 ./mutilate/mutilate -A --affinity -T 15"], stdout=PIPE)
    time.sleep(1)
    p4 = Popen(["ssh", SNODE, "taskset -c 0 ./mutilate/mutilate --binary --noload -B -s", CIP ,"-a localhost -K fb_key -V fb_value -i fb_ia -u 0.25 -c 8 -d 4 -C 8 -Q 1000 -t 5 --scan=10000:200000:10000"], stdout=PIPE)
    lines = p4.communicate()[0].split('\n')
    sla1 = 0
    sla2 = 0
    tput1 = 0
    tput2 = 0
    
    for l in lines:
        print l
        if "read" in l:
            fil = list(filter(None, l.split(' ')))
            sla = float(fil[8])
            if sla < 500:
                sla1 = int(sla)
                tput1 = int(float(fil[9]))
            elif sla >= 500:
                sla2 = int(sla)
                tput2 = int(float(fil[9]))
                break
    
    p1.kill()
    p3.kill()
    killallMCD()
    ratio = (tput2 - tput1) / (sla2 - sla1)
    projectedtput = tput1 + ((500 - sla1) * ratio)
    return projectedtput
    #print sla1, tput1, sla2, tput2, projectedtput
    
def mcd():
    print 'as'
    runMCD()
    
def netpipe():
    print "b"

def f(x):
    return (x*x*x) - (60*x*x) + 900*x + 100

def randomf(x):
    i = np.random.random_integers(5)-1
    if (x >> i) & 0x1:
        return ~(0x1 << i) & x
    else:
        return (0x1 << i) | x

def anneal2(n_iter=1, annealing_rate=0.95, annealing_constant_steps=1, restarts=True, restart_steps=20):
    init_temp_scale = 0.5
    global RXUSECS
    global RXRING
    global TXRING
    
    rxu = RXUSECS
    rxr = RXRING
    txr = TXRING
    updateNIC()
    cost = runIperf()
    temperature = cost * init_temp_scale
    
    current_iter = 0
    while current_iter < n_iter:
        if current_iter % annealing_constant_steps == 0:
            temperature *= annealing_rate
            print("Step=%d RXUSECS=%s RXRING=%s TXRING=%s Cost=%f Temp=%f" % (current_iter, RXUSECS, RXRING, TXRING, cost, temperature))
            
        new_cost = iperf()
        if new_cost > cost:
            rxu = RXUSECS
            rxr = RXRING
            txr = TXRING
            cost = new_cost
        else:
            threshold = np.exp((new_cost - cost)/temperature)
            if np.random.random() < threshold:
                rxu = RXUSECS
                rxr = RXRING
                txr = TXRING
                cost = new_cost

        if restarts:
            if current_iter%restart_steps==0:
                temperature = cost * init_temp_scale
        current_iter += 1
    
    print ("BEST: RXUSECS=%s RXRING=%s TXRING=%s Cost=%f" % (rxu, rxr, txr, cost))
    
def anneal(num, n_iter=500, annealing_rate=0.95, annealing_constant_steps=1, restarts=True, restart_steps=100):
    init_temp_scale = 0.5
    keepnum = num
    cost = f(keepnum)
    temperature = cost * init_temp_scale
    
    current_iter = 0
    while current_iter < n_iter:
        if current_iter % annealing_constant_steps == 0:
            temperature *= annealing_rate
            print("Step = %d: Num = %d: Cost = %d: Temp=%f" % (current_iter, keepnum, cost, temperature))

        newnum = randomf(keepnum)
        new_cost = f(newnum)
        if new_cost > cost:
            cost = new_cost
            keepnum = newnum
        else:
            threshold = np.exp((new_cost - cost)/temperature)
            if np.random.random() < threshold:
                cost = new_cost
                keepnum = newnum
                
        if restarts:
            if current_iter%restart_steps==0:
                temperature = cost * init_temp_scale

        current_iter += 1

    print "num", keepnum, "cost", cost
    
def main(argv):    
    itype = ''
    try:
        opts, args = getopt.getopt(argv, "i:h")
    except getopt.GetoptError as err:
        usage()
        sys.exit()
    if len(argv) == 0:
        usage()
        sys.exit()
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-i"):
            itype = arg
    print "Running", itype
    if itype == "iperf":
        initIperfParams()
        #iperf()
        anneal2()
    elif itype == "netpipe":
        netpipe()
    elif itype == "mcd":
        initMCDParams()
        mcd()
    else:
        print 'Unknown', itype
        #initMCDParams()
        #for i in range(0, 100):
        #    updateMCDConfig()

if __name__ == '__main__':
    main(sys.argv[1:])


    
