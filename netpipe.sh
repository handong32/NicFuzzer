#! /bin/bash

export DEBUG=${DEBUG:=}
export PROC=${PROC:=1}
export COUNT=${COUNT:=5}
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
    rxusec='43'
    #qiter='128 512 1024 2048 4096 6144'
    qiter='128'
    #uu='3072 4099 7567'
    uu='3072'
    printf "NETPIPE TESTS\n"

    for rxu in $rxusec;
    do
	mkdir -p $2"/rxu"$rxu/$1
    done

    for u in $uu;
    do
	for rxu in $rxusec;
	do
	    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	    for rxq in $qiter;
	    do
		for txq in $qiter;
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
			taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n 1000 -p 0 -r -I
			cp np.out $2"/rxu"$rxu/$1/netpipe_$rxq\_$txq\_$u.log 
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

function gather() {
    for iter in `seq 1 1 100`;
    do	
	#echo run "run"$iter "tmp"
	run "run"$iter "linux_default"
    done
}

function gather_linux_default() {
    mkdir -p gather_linux_default/$currdate
    uu='3072'
    
    for iter in `seq 1 1 1`;
    do
	for u in $uu;
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
		output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
		sleep 2
		taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n 1000 -p 0 -r -I
		cp np.out gather_linux_default/$currdate/$u\_$iter.log 
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
else
    $1
fi

