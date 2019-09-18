#! /bin/bash
export RXU=${RXU:='8'}
export RXQ=${RXQ:='512'}
export TXQ=${TXQ:='512'}
export NITERS=${NITERS:='1'}
export SERVER=${SERVER:=192.168.1.200}
export OUTFILE=${OUTFILE:=0}
export MAXREQS=${MAXREQS:=20000}
export WARMUPREQS=${WARMUPREQS:=20000}
export QPS=${QPS:=2000}

currdate=`date +%m_%d_%Y_%H_%M_%S`

#set -x

function run
{
    if [ $OUTFILE -eq 1 ]; then
	mkdir -p "silo_data/$currdate"
	echo "Running $1 RXU=$RXU NITERS=$NITERS" > "silo_data/$currdate/command.txt"
    fi

    #for rxu in `seq 0 2 200`;
    for rxu in `seq 0 2 1`;
    do
	i="0"
	while [ $i -lt $NITERS ]
	do
	    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	    ssh $SERVER "pkill dbtest_server_networked"
	    pkill dbtest_client_networked
	    echo "**** ITER="$iter "RXU="$rxu "QPS="$QPS
	    #intrstart1=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
	    #intrstart3=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-3" | tr -s ' ' | cut -d ' ' -f 6 )
	    #intrstart5=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-5" | tr -s ' ' | cut -d ' ' -f 8 )
	    #intrstart7=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-7" | tr -s ' ' | cut -d ' ' -f 10 )
	    #intrstart9=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-9" | tr -s ' ' | cut -d ' ' -f 12 )
	    #intrstart11=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-11" | tr -s ' ' | cut -d ' ' -f 14 )
	    #intrstart13=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-13" | tr -s ' ' | cut -d ' ' -f 16 )
	    #intrstart15=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-15" | tr -s ' ' | cut -d ' ' -f 18 )

	    #ssh $SERVER "TBENCH_MAXREQS="$MAXREQS" TBENCH_WARMUPREQS="$WARMUPREQS" TBENCH_SERVER=192.168.1.200 TBENCH_SERVER_PORT=8080 chrt -r 1 numactl --cpunodebind=1 --membind=1 /root/tailbench-v0.9/silo/out-perf.masstree/benchmarks/dbtest_server_networked --bench tpcc --num-threads 8 --scale-factor 8 --retry-aborted-transactions --ops-per-worker 10000000" > silo_server.log 2>&1 &
	    ssh $SERVER "TBENCH_MAXREQS="$MAXREQS" TBENCH_WARMUPREQS="$WARMUPREQS" TBENCH_SERVER=192.168.1.200 TBENCH_SERVER_PORT=8080 chrt -r 1 numactl --cpunodebind=1 --membind=1 /root/tailbench-v0.9/silo/out-perf.masstree/benchmarks/dbtest_server_networked --bench tpcc --num-threads 1 --scale-factor 1 --retry-aborted-transactions --ops-per-worker 10000000" > silo_server.log 2>&1 &
	
	    sleep 1
	    TBENCH_QPS=${QPS} TBENCH_MINSLEEPNS=10000 TBENCH_SERVER=192.168.1.200 TBENCH_SERVER_PORT=8080 TBENCH_CLIENT_THREADS=8 chrt -r 1 numactl --cpunodebind=1 --membind=1 /root/github/tailbench-v0.9/silo/out-perf.masstree/benchmarks/dbtest_client_networked

	    if grep "failed" silo_server.log
	    then
		echo "failed, trying again"
	    else
		echo "success"
		i=$[$i+1]

		#intrend1=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
		#intrend3=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-3" | tr -s ' ' | cut -d ' ' -f 6 )
		#intrend5=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-5" | tr -s ' ' | cut -d ' ' -f 8 )
		#intrend7=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-7" | tr -s ' ' | cut -d ' ' -f 10 )
		#intrend9=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-9" | tr -s ' ' | cut -d ' ' -f 12 )
		#intrend11=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-11" | tr -s ' ' | cut -d ' ' -f 14 )
		#intrend13=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-13" | tr -s ' ' | cut -d ' ' -f 16 )
		#intrend15=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-15" | tr -s ' ' | cut -d ' ' -f 18 )

		#intrtot1=$((intrend1-intrstart1))
		#intrtot3=$((intrend3-intrstart3))
		#intrtot5=$((intrend5-intrstart5))
		#intrtot7=$((intrend7-intrstart7))
		#intrtot9=$((intrend9-intrstart9))
		#intrtot11=$((intrend11-intrstart11))
		#intrtot13=$((intrend13-intrstart13))
		#intrtot15=$((intrend15-intrstart15))

		./parselats.py lats.bin
	       	if [ $OUTFILE -eq 1 ]; then
		    mv lats.bin "silo_data/$currdate/silo_"$rxu\_$iter".bin"
		    #cp mutilate.log "silo_data/$currdate/silo_"$rxu\_$iter".log"
		    #scp $SERVER:~/perf.out "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot1",itr1" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot3",itr3" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot5",itr5" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot7",itr7" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot9",itr9" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot11",itr11" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot13",itr13" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		    #echo $intrtot15",itr15" >> "silo_data/$currdate/silo_"$rxu\_$iter".perf"
		fi
	    fi	    
	    sleep 1
	done
    done
}

$1
