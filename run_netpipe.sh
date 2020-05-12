#! /bin/bash
export RXU=${RXU:='8'}

currdate=`date +%m_%d_%Y_%H_%M_%S`

#set -x
ghzs="2.9 2.8 2.7 2.6 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 1.3 1.2"
msgs="64 1024 8192 65536 524288"
itrs="2 10 20 60"
rapls="136 86 46"

function set_dynamic
{
    set -x
    set -e
    
    ssh 10.255.5.8 ethtool -C enp4s0f1 rx-usecs 1
    sleep 1
    ssh 10.255.5.8 ip link set enp4s0f1 down
    sleep 1
    ssh 10.255.5.8 ip link set enp4s0f1 up
    sleep 1

    ssh 10.255.5.11 ethtool -C enp4s0f1 rx-usecs 1
    sleep 1
    ssh 10.255.5.11 ip link set enp4s0f1 down
    sleep 1
    ssh 10.255.5.11 ip link set enp4s0f1 up
    sleep 1
}

function set_static
{
    set -x
    set -e
    
    ssh 10.255.5.8 ethtool -C enp4s0f1 rx-usecs 2
    sleep 1
    ssh 10.255.5.8 ip link set enp4s0f1 down
    sleep 1
    ssh 10.255.5.8 ip link set enp4s0f1 up
    sleep 1

    ssh 10.255.5.11 ethtool -C enp4s0f1 rx-usecs 2
    sleep 1
    ssh 10.255.5.11 ip link set enp4s0f1 down
    sleep 1
    ssh 10.255.5.11 ip link set enp4s0f1 up
    sleep 1    
}

function run
{
    set_dynamic

    # warm up
    timeout 120 python3 -u ./netpipe_bench.py --dvfs 2.9 --rapl 136 --msg 1024 --iter 100000

    for r in $rapls;
    do
	for d in $ghzs;
	do
	    timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 64 --iter 200000 --rapl $r
	    sleep 1
	    timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 1024 --iter 200000 --rapl $r
	    sleep 1
	    timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 8192 --iter 100000 --rapl $r
	    sleep 1
	    timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 65536 --iter 50000 --rapl $r
	    sleep 1
	    timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 524288 --iter 50000 --rapl $r
	    sleep 1
	done
    done

    set_static

    # warm up
    timeout 120 python3 -u ./netpipe_bench.py --dvfs 2.9 --rapl 136 --msg 1024 --iter 100000 --itr 12

    for r in $rapls;
    do
	for d in $ghzs;
	do
	    for i in $itrs;
	    do
		timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 64 --iter 200000 --itr $i --rapl $r
		sleep 1
		timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 1024 --iter 200000 --itr $i --rapl $r
		sleep 1
		timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 8192 --iter 100000 --itr $i --rapl $r
		sleep 1
		timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 65536 --iter 50000 --itr $i --rapl $r
		sleep 1
		timeout 120 python3 -u ./netpipe_bench.py --dvfs $d --msg 524288 --iter 20000 --itr $i --rapl $r
		sleep 1
	    done
	done
    done
}

$1
