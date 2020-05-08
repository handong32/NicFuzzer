#! /bin/bash
export RXU=${RXU:='8'}

currdate=`date +%m_%d_%Y_%H_%M_%S`

#set -x
ghzs="2.9 2.8 2.7 2.6 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 1.3 1.2"
coms="com1 com512"

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


$1
