#! /bin/bash

export DEBUG=${DEBUG:=}
export PROC=${PROC:=1}
export COUNT=${COUNT:=5}
export RXU=${RXU:='10'}
export RXQ=${RXQ:='512'}
export TXQ=${TXQ:='512'}
export MSGS=${MSGS:='1024'}
export MSGL=${MSGL:='1024'}
export MSGU=${MSGU:='2024'}
export NITERS=${NITERS:=10}
export NPITER=${NPITER:=1000}
export OUTFILE=${OUTFILE:=0}
export DORAND=${DORAND:=0}

export SERVER=${SERVER:=192.168.1.200}

currdate=`date +%m_%d_%Y_%H_%M_%S`
if [[ -n $DEBUG ]]; then set -x; fi

function run
{
    success=0
    #qiter='128 256 512 1024 1152 1280 1536 2048 2176 2304 2560 3072 3200 3328 3584 4096'
    #qiter='128 256 512 1024 2048 3072 4096 5120 6144 7168'
    #rxusec='10 30 50 70 90 110 130 150'
    #rxusec='10 15 20'
    #qiter='128 512 1024 2048 4096 6144'
    #uu='3072 4099 7567'
    printf "NETPIPE TESTS\n"

    for u in $MSGS;
    do
	for rxu in $RXU;
	do
	    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	    for rxq in $RXQ;
	    do
		for txq in $TXQ;
		do
		    printf "CONFIG: RX-RING:%d TX-RING:%d RXU:%d\n" $rxq $txq $rxu
		    ssh $SERVER "ethtool -G enp4s0f1 rx $rxq tx $txq"
		    success=0
		    for testiter in `seq 0 1 $COUNT`;
		    do
			sleep 1
			output=$(ping -c 3 192.168.1.200 | grep "3 received")
			if [ ${#output} -ge 1 ]; then
			    success=1
			    break
			fi
		    done
		    
		    if [ $success -eq 1 ]; then
			ssh $SERVER pkill NPtcp
			pkill NPtcp
			output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			sleep 2
			taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n $NPITER -p 0 -r -I
			if [ $OUTFILE -eq 1 ]; then
			    cp np.out "netpipe_data/$2/np_"$u\_$rxu\_$rxq\_$txq\_$1".log"
			fi
			sleep 1
		    else
			echo "CONFIG FAILED"
			echo " "
		    fi	        
		done
	    done
	done
    done    
}

function runPerf
{
    success=0
    printf "NETPIPE TESTS\n"

    for u in $MSGS;
    do
	for rxu in $RXU;
	do
	    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	    for rxq in $RXQ;
	    do
		for txq in $TXQ;
		do
		    printf "CONFIG: RX-RING:%d TX-RING:%d RXU:%d\n" $rxq $txq $rxu
		    ssh $SERVER "ethtool -G enp4s0f1 rx $rxq tx $txq"
		    success=0
		    for testiter in `seq 0 1 $COUNT`;
		    do
			sleep 1
			output=$(ping -c 3 192.168.1.200 | grep "3 received")
			if [ ${#output} -ge 1 ]; then
			    success=1
			    break
			fi
		    done
		    
		    if [ $success -eq 1 ]; then
			ssh $SERVER pkill NPtcp
			pkill NPtcp
			#perf stat -a -e cycles,instructions,cache-misses,cache-references,power/energy-cores/,power/energy-pkg/,power/energy-ram/ -I 100 -x , taskset -c 1 NPtcp -l 3072 -u 3072 -p 0 -r -I
			if [ $OUTFILE -eq 1 ]; then
			    #output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,cache-misses,page-faults,power/energy-pkg/,power/energy-cores/,power/energy-ram/,syscalls:sys_enter_read,syscalls:sys_enter_write,'net:*' -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			    output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -o perf.out -e power/energy-pkg/,power/energy-ram/ -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			else
			    output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -e power/energy-pkg/,power/energy-ram/ -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			    #output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -e cycles,instructions,cache-misses,page-faults,power/energy-pkg/,power/energy-cores/,power/energy-ram/,syscalls:sys_enter_read,syscalls:sys_enter_write,'net:*' -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			fi
			sleep 1
			taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n $NPITER -p 0 -r -I
			if [ $OUTFILE -eq 1 ]; then
			    cp np.out "netpipe_data/$2/np_"$u\_$rxu\_$rxq\_$txq\_$1".log"
			    scp $SERVER:~/perf.out "netpipe_data/$2/np_"$u\_$rxu\_$rxq\_$txq\_$1".perf"
			fi
			sleep 1
		    else
			echo "CONFIG FAILED"
			echo " "
		    fi	        
		done
	    done
	done
    done    
}

function runRand {
    success=0
    printf "NETPIPE TESTS\n"

    for rxu in $RXU;
    do
	ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	for rxq in $RXQ;
	do
	    for txq in $TXQ;
	    do
		printf "CONFIG: RX-RING:%d TX-RING:%d RXU:%d\n" $rxq $txq $rxu
		ssh $SERVER "ethtool -G enp4s0f1 rx $rxq tx $txq"
		success=0
		for testiter in `seq 0 1 $COUNT`;
		do
		    sleep 1
		    output=$(ping -c 3 192.168.1.200 | grep "3 received")
		    if [ ${#output} -ge 1 ]; then
			success=1
			break
		    fi
		done

		if [ $success -eq 1 ]; then
		    ssh $SERVER pkill NPtcp
		    pkill NPtcp
		    output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $MSGL -u $MSGU -p 0 -r -I -x") &
		    sleep 2
		    taskset -c 1 NPtcp -h $SERVER -l $MSGL -u $MSGU -n $NPITER -p 0 -r -I -x
		    if [ $OUTFILE -eq 1 ]; then
			cp np.out "netpipe_data/$2/np_"$MSGL\_$MSGU\_$rxu\_$rxq\_$txq\_$1".log"
		    fi
		    sleep 1
		else
		    echo "CONFIG FAILED"
		    echo " "
		fi
	    done
	done
    done
}

function gather() {
    echo $currdate
    for iter in `seq 1 1 $NITERS`;
    do	
	#echo "run" $iter $currdate
	run $iter $currdate
    done
}

function gatherPerf() {
    echo $currdate
    for iter in `seq 1 1 $NITERS`;
    do	
	runPerf $iter $currdate
    done
}

function gatherRand() {
    echo $currdate
    for iter in `seq 1 1 $NITERS`;
    do	
	runRand $iter $currdate
    done
}    


function gather_linux_default() {
    echo $currdate
    
    if [ $OUTFILE -eq 1 ]; then
    	mkdir -p gather_linux_default/$currdate
    fi
    
    for iter in `seq 1 1 $NITERS`;
    do
	for u in $MSGS;
	do
	    success=0
	    for testiter in `seq 0 1 $COUNT`;
	    do
		sleep 1
		output=$(ping -c 3 192.168.1.200 | grep "3 received")
		if [ ${#output} -ge 1 ]; then
		    success=1
		    break
		fi
	    done
	    
	    if [ $success -eq 1 ]; then
		ssh $SERVER pkill NPtcp
		pkill NPtcp

		if [ $DORAND -eq 1 ]; then
		    output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $MSGL -u $MSGU -p 0 -r -I -x") &
		    sleep 2
		    taskset -c 1 NPtcp -h $SERVER -l $MSGL -u $MSGU -n $NPITER -p 0 -r -I -x
		else
		    output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
		    sleep 2
		    taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n $NPITER -p 0 -r -I
		fi
		
		if [ $OUTFILE -eq 1 ]; then
		    cp np.out gather_linux_default/$currdate/$u\_$iter.log
		fi
		sleep 1
	    else
		echo "CONFIG FAILED"
		echo " "
	    fi
	done
    done
}

function run2() {
    success=0
    rxu=$1
    rxq=$2
    txq=$3
    numiter=$4
    lu=$5
    uu=$6

    echo "RXUSEC="$rxu "RXQ="$rxq "TXQ="$txq "NUMITER="$numiter
    
    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
    sleep 1
    
    printf "CONFIG: RX-RING:%d TX-RING:%d\n" $rxq $txq
    ssh $SERVER "ethtool -G enp4s0f1 rx $rxq tx $txq"
    success=0
    for testiter in `seq 0 1 $COUNT`;
    do
	sleep 3
	output=$(ping -c 3 192.168.1.200 | grep "3 received")
	if [ ${#output} -ge 1 ]; then
	    success=1
	    break
  	fi
    done

    if [ $success -eq 1 ]; then
	for testiter in `seq 0 1 $numiter`;
	do
	    pkill NPtcp
	    ssh $SERVER pkill NPtcp
	    sleep 1
	    output1=$(ssh $SERVER "NPtcp -l $lu -u $uu -r -p 0 -I") &
	    sleep 1
	    NPtcp -h 192.168.1.200 -l $lu -u $uu -p 0 -n 1000 -r -I 
	    sleep 1
	done
    else
	echo "CONFIG FAILED"
	echo " "
    fi    
}

if [ "$1" = "run2" ]; then
    $1 $2 $3 $4 $5 $6 $7
elif [ "$1" = "gather_linux_default" ]; then
    $1
elif [ "$1" = "gather" ]; then
    echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGS=$MSGS"
    
    if [ $OUTFILE -eq 1 ]; then
	mkdir -p "netpipe_data/$currdate"
	echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGS=$MSGS" > "netpipe_data/$currdate/command.txt"
    fi
    $1
elif [ "$1" = "gatherPerf" ]; then
    echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGS=$MSGS"

    if [ $OUTFILE -eq 1 ]; then
	mkdir -p "netpipe_data/$currdate"
	echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGS=$MSGS" > "netpipe_data/$currdate/command.txt"
    fi
    $1
elif [ "$1" = "gatherRand" ]; then
    echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGL=$MSGL MSGU=$MSGU"

    if [ $OUTFILE -eq 1 ]; then
	mkdir -p "netpipe_data/$currdate"
	echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGL=$MSGL MSGU=$MSGU" > "netpipe_data/$currdate/command.txt"
    fi
    $1
else
    echo "unknown command"
fi

