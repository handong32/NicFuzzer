#! /bin/bash
export RXU=${RXU:='8'}

currdate=`date +%m_%d_%Y_%H_%M_%S`

#set -x
ghzs="2.9 2.8 2.7 2.6 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 1.3 1.2"
coms="com1 com512"
#taskset -c 1 ./wrk -t1 -c1 -d1s -H "Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: example.com Host: example.com \n Host: test.go Host: example.com \n  Host: example.com \n  Host: example.com \n  Host: example.com \n Host: example.com \n Host: example.com Host: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.comHost: example.com Host: example.comHost: " http://192.168.1.230:6666/index.html --latency

function run
{
    for c in $coms;
    do
	for d in $ghzs;
	do
	    for r in `seq 136 -2 46`;
	    do	    
		timeout 120 python3 -u ./nodejs_bench.py --rapl $r --dvfs $d --com $c
	    done
	done
    done
}

function run2
{
    for i in `seq 10 100 900`; # 8
    do
	for d in $ghzs; # 17
	do
	    for r in `seq 136 -8 46`; # 9
	    do	    
		timeout 120 python3 -u ./nodejs_bench.py --rapl $r --dvfs $d --com "com512" --itr $i
	    done
	done
    done
}


$1
