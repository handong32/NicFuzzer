#! /bin/bash

export RXU=${RXU:='8'}
export RXQ=${RXQ:='512'}
export TXQ=${TXQ:='512'}
export NITERS=${NITERS:='1'}
export SERVER=${SERVER:=192.168.1.200}
export OUTFILE=${OUTFILE:=0}

currdate=`date +%m_%d_%Y_%H_%M_%S`

function run5
{
    for i in `seq 1 1 $NITERS`;
    do
	for d in $RXU;
	do
	    ssh $SERVER "pkill memcached"
	    pkill mutilate
	    sleep 1
	    timeout 600 python3 -u mutilate_bench.py $d
	done
    done
}

function run4
{
    ssh $SERVER "pkill memcached"
    pkill mutilate
    sleep 1
    timeout 600 python3 -u mutilate_bench.py $1
}

function run3
{
    while true; do
	ssh $SERVER "pkill memcached"
	pkill mutilate
	sleep 1
	timeout 600 python3 -u mutilate_bench.py
	sleep 1
    done
}

function run2
{
    ssh $SERVER "pkill memcached"
    pkill mutilate
    sleep 1
    timeout 600 python3 -u mutilate_bench.py
}

function run
{
    if [ $OUTFILE -eq 1 ]; then
	echo $currdate
	mkdir -p "mcd_data/$currdate"
	echo "Running $1 RXU=$RXU NITERS=$NITERS" > "mcd_data/$currdate/command.txt"
    fi

    for iter in `seq 2 1 $NITERS`;
    do
	for rxu in $RXU;
	do
	    echo $rxu
	    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	    sleep 0.2
	    
	    ssh $SERVER "pkill memcached"
	    pkill mutilate
	    sleep 1
	    echo "**** ITER="$iter "RXU="$rxu
	    intrstart1=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
	    intrstart3=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-3" | tr -s ' ' | cut -d ' ' -f 6 )
	    intrstart5=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-5" | tr -s ' ' | cut -d ' ' -f 8 )
	    intrstart7=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-7" | tr -s ' ' | cut -d ' ' -f 10 )
	    intrstart9=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-9" | tr -s ' ' | cut -d ' ' -f 12 )
	    intrstart11=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-11" | tr -s ' ' | cut -d ' ' -f 14 )
	    intrstart13=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-13" | tr -s ' ' | cut -d ' ' -f 16 )
	    intrstart15=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-15" | tr -s ' ' | cut -d ' ' -f 18 )
	    python -u mutilate_bench.py
	    intrend1=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
	    intrend3=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-3" | tr -s ' ' | cut -d ' ' -f 6 )
	    intrend5=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-5" | tr -s ' ' | cut -d ' ' -f 8 )
	    intrend7=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-7" | tr -s ' ' | cut -d ' ' -f 10 )
	    intrend9=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-9" | tr -s ' ' | cut -d ' ' -f 12 )
	    intrend11=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-11" | tr -s ' ' | cut -d ' ' -f 14 )
	    intrend13=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-13" | tr -s ' ' | cut -d ' ' -f 16 )
	    intrend15=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-15" | tr -s ' ' | cut -d ' ' -f 18 )

	    intrtot1=$((intrend1-intrstart1))
	    intrtot3=$((intrend3-intrstart3))
	    intrtot5=$((intrend5-intrstart5))
	    intrtot7=$((intrend7-intrstart7))
	    intrtot9=$((intrend9-intrstart9))
	    intrtot11=$((intrend11-intrstart11))
	    intrtot13=$((intrend13-intrstart13))
	    intrtot15=$((intrend15-intrstart15))
	    
	    if [ $OUTFILE -eq 1 ]; then
		cp mutilate.log "mcd_data/$currdate/mcd_"$rxu\_$iter".log"
		scp $SERVER:~/perf.out "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot1",itr1" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot3",itr3" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot5",itr5" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot7",itr7" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot9",itr9" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot11",itr11" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot13",itr13" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
		echo $intrtot15",itr15" >> "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
	    fi
	    sleep 1
	done
    done
}

$1 $2
