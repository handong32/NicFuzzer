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
export SEED=${SEED:='1'}

export SERVER=${SERVER:=192.168.1.200}

currdate=`date +%m_%d_%Y_%H_%M_%S`
if [[ -n $DEBUG ]]; then set -x; fi

function run
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
#		    ssh $SERVER "ethtool -G enp4s0f1 rx $rxq tx $txq"
		    success=1
#		    for testiter in `seq 0 1 $COUNT`;
#		    do
#			sleep 1
#			output=$(ping -c 3 192.168.1.200 | grep "3 received")
#			if [ ${#output} -ge 1 ]; then
#			    success=1
#			    break
#			fi
#		    done
		    
		    if [ $success -eq 1 ]; then
			ssh $SERVER pkill NPtcp
			pkill NPtcp
			sleep 1
			output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			sleep 1
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
		    #ssh $SERVER "ethtool -G enp4s0f1 rx $rxq tx $txq"
		    success=1
		    #for testiter in `seq 0 1 $COUNT`;
		    #do
		    #    sleep 1
		    #	output=$(ping -c 3 192.168.1.200 | grep "3 received")
		    #	if [ ${#output} -ge 1 ]; then
		    #	    success=1
		    #	    break
		    #	fi
		    #done
		    
		    if [ $success -eq 1 ]; then
			ssh $SERVER pkill NPtcp
			sleep 0.1
			pkill NPtcp
			sleep 0.1
			#if [ $OUTFILE -eq 1 ]; then
			    #output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,cache-misses,page-faults,power/energy-pkg/,power/energy-cores/,power/energy-ram/,syscalls:sys_enter_read,syscalls:sys_enter_write,'net:*','power:*' -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			#    output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,cache-misses,power/energy-pkg/,power/energy-ram/,'power:*' -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			#else
			output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
			#fi
			sleep 1
			intrstart=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
			taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n $NPITER -p 0 -r -I
			intrend=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
			intrtot=$((intrend-intrstart))
			
			#ncycles=$(ssh $SERVER cat perf.out | grep "cycles" | cut -d ',' -f1)
			#ninstructions=$(ssh $SERVER cat perf.out | grep "instructions" | cut -d ',' -f1)
		        #ncachemiss=$(ssh $SERVER cat perf.out | grep "cache-misses" | cut -d ',' -f1)
			#nllclmiss=$(ssh $SERVER cat perf.out | grep "LLC-load-misses" | cut -d ',' -f1)
			#nllcsmiss=$(ssh $SERVER cat perf.out | grep "LLC-store-misses" | cut -d ',' -f1)
			energypkg=$(ssh $SERVER cat perf.out | grep "energy-pkg" | cut -d ',' -f1)
			energyram=$(ssh $SERVER cat perf.out | grep "energy-ram" | cut -d ',' -f1)
		        #ncpuidle=$(ssh $SERVER cat perf.out | grep "cpu_idle" | cut -d ',' -f1)
		        #ncpufreq=$(ssh $SERVER cat perf.out | grep "cpu_frequency" | cut -d ',' -f1)
			totaltime=$(cat np.out | tr -s ' ' | cut -d ' ' -f 5)
			tput=$(cat np.out | tr -s ' ' | cut -d ' ' -f 3)
			
			#echo "$u $tput" | awk '{printf "min_time %.2f usec, time %.2f usec, ratio %.2f\n", ($1*8)/10000.0, ($1*8)/$2, (($1*8)/10000.0)/ (($1*8)/$2)}'
			echo "$tput" | awk '{printf "throughput %.2f\n", $1}'
			#echo "$ncycles" | awk '{printf "num_cycles %d\n", $1}'
			#echo "$ninstructions" | awk '{printf "num_instructions %d\n", $1}'
			#echo "$nllclmiss" | awk '{printf "LLC-load-misses %d\n", $1}'
			#echo "$nllcsmiss" | awk '{printf "LLC-store-misses %d\n", $1}'
			#echo "$nllclmiss $nllcsmiss" | awk '{printf "LLC_misses %d\n", $1+$2}'
			#echo "$nllclmiss $nllcsmiss $totaltime" | awk '{printf "Memory_Bandwidth %.2f MBps\n", ((($1+$2)*64)/1000000.0)/$3}'
			#echo "$energypkg $totaltime" | awk '{printf "RAPL_PKG_Power %.2f Watts\n", $1/$2}'
			#echo "$energyram $totaltime" | awk '{printf "RAPL_DRAM_Power %.2f Watts\n", $1/$2}'
			#echo "$intrtot" | awk '{printf "num_interrupts %d\n", $1}'
			echo "$energypkg $energyram $totaltime" | awk '{printf "Total_Power %.2f Watts\n", ($1+$2)/$3}'
			#echo "$ncpuidle" | awk '{printf "power:cpu_idle %.2f\n", $1}'
			#echo "$ncpufreq" | awk '{printf "power:cpu_frequency %.2f\n", $1}'
			
			
			if [ $OUTFILE -eq 1 ]; then
			    file="netpipe_data/$2/np_"$u\_$rxu\_$rxq\_$txq\_$1".log" 
			    cp np.out $file
			    scp $SERVER:~/perf.out "netpipe_data/$2/np_"$u\_$rxu\_$rxq\_$txq\_$1".perf"
			    echo "num_interrupt "$intrtot >> "netpipe_data/$2/np_"$u\_$rxu\_$rxq\_$txq\_$1".perf"
			    #echo "$tput" | awk '{printf "throughput %.2f\n", $1}' >> $file
			    #echo "$ncycles" | awk '{printf "num_cycles %d\n", $1}' >> $file
			    #echo "$ninstructions" | awk '{printf "num_instructions %d\n", $1}' >> $file
			    #echo "$nllclmiss" | awk '{printf "LLC-load-misses %d\n", $1}' >> $file
			    #echo "$nllcsmiss" | awk '{printf "LLC-store-misses %d\n", $1}' >> $file
			    #echo "$nllclmiss $nllcsmiss" | awk '{printf "LLC_misses %d\n", $1+$2}' >> $file
			    #echo "$nllclmiss $nllcsmiss $totaltime" | awk '{printf "Memory_Bandwidth %.2f MBps\n", ((($1+$2)*64)/1000000.0)/$3}' >> $file
			    #echo "$energypkg $totaltime" | awk '{printf "RAPL_PKG_Power %.2f Watts\n", $1/$2}' >> $file
			    #echo "$energyram $totaltime" | awk '{printf "RAPL_DRAM_Power %.2f Watts\n", $1/$2}' >> $file
			    #echo "$energypkg $energyram $totaltime" | awk '{printf "Total_Power %.2f Watts\n", ($1+$2)/$3}' >> $file
			    #echo "$intrtot" | awk '{printf "num_interrupts %d\n", $1}' >> $file
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
		#ssh $SERVER "ethtool -G enp4s0f1 rx $rxq tx $txq"
		success=1
		#for testiter in `seq 0 1 $COUNT`;
		#do
		#    sleep 1
		#    output=$(ping -c 3 192.168.1.200 | grep "3 received")
		#    if [ ${#output} -ge 1 ]; then
		#	success=1
		#       break
		#    fi
		#done

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

function runRandLimit {
    success=0
    printf "NETPIPE runRandLimit\n"

    for rxu in $RXU;
    do
	ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	printf "CONFIG: RX-RING:%d TX-RING:%d RXU:%d\n" $rxq $txq $rxu
	success=1
	
	if [ $success -eq 1 ]; then
	    ssh $SERVER pkill NPtcp
	    pkill NPtcp
	    output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $MSGL -u $MSGU -Y $SEED -p 0 -r -I -x") &
	    sleep 2
	    taskset -c 1 NPtcp -h $SERVER -l $MSGL -u $MSGU -n $NPITER -Y $SEED -p 0 -r -I -x
	    if [ $OUTFILE -eq 1 ]; then
		cp np.out "netpipe_data/$2/np_"$MSGL\_$MSGU\_$rxu\_$rxq\_$txq\_$1".log"
	    fi
	    sleep 1
	else
	    echo "CONFIG FAILED"
	    echo " "
	fi
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

function ttest() {
    for iter in `seq 1 1 $NITERS`;
    do
	for rxu in $RXU;
	do
	    ssh $SERVER "ethtool -C enp4s0f1 rx-usecs $rxu"
	    echo "RXU = "$rxu
	    for u in `seq 70 5 1500`;
	    do	    
		ssh $SERVER pkill NPtcp
		sleep 0.1
		pkill NPtcp
		sleep 0.1
		output1=$(ssh $SERVER "perf stat -C 1 -D 1000 -o perf.out -e cycles,instructions,LLC-load-misses,LLC-store-misses,power/energy-pkg/,power/energy-ram/ -x, taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
		sleep 1
		intrstart=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
		taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n $NPITER -p 0 -r -I
		intrend=$(ssh $SERVER cat /proc/interrupts | grep -m 1 "enp4s0f1-TxRx-1" | tr -s ' ' | cut -d ' ' -f 4 )
		intrtot=$((intrend-intrstart))

		if [ $OUTFILE -eq 1 ]; then
		    file="netpipe_data/$currdate/np_"$u\_$rxu\_$RXQ\_$TXQ\_$iter".log" 
		    cp np.out $file
		    scp $SERVER:~/perf.out "netpipe_data/$currdate/np_"$u\_$rxu\_$RXQ\_$TXQ\_$iter".perf"
		    echo "num_interrupt,,"$intrtot >> "netpipe_data/$currdate/np_"$u\_$rxu\_$RXQ\_$TXQ\_$iter".perf"
		fi
		sleep 0.5
	    done
	done
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

function gatherRandLimit() {
    echo $currdate
    for iter in `seq 1 1 $NITERS`;
    do	
	runRandLimit $iter $currdate
    done
}

function reinforce() {
   for iter in `seq 1 1 $NITERS`;
   do	
       python3 -u reinforce_netpipe.py
       sleep 5
       ssh $SERVER pkill NPtcp
       pkill NPtcp
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

function gather_linux_default2() {
    echo $currdate
    
#    touch gather_linux_default/default2.ref
    
    for u in `seq 90000 1 666666`;
    do
	echo $u
	ssh $SERVER pkill NPtcp
	pkill NPtcp
	output1=$(ssh $SERVER "taskset -c 1 NPtcp -l $u -u $u -p 0 -r -I") &
	sleep 1
	taskset -c 1 NPtcp -h $SERVER -l $u -u $u -n 100 -p 0 -r -I
	cat np.out >> gather_linux_default/default.ref
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
elif [ "$1" = "gather_linux_default2" ]; then
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
elif [ "$1" = "gatherRandLimit" ]; then
    echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGL=$MSGL MSGU=$MSGU"

    if [ $OUTFILE -eq 1 ]; then
	mkdir -p "netpipe_data/$currdate"
	echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGL=$MSGL MSGU=$MSGU" > "netpipe_data/$currdate/command.txt"
    fi
    $1    
elif [ "$1" = "reinforce" ]; then
    $1
elif [ "$1" = "ttest" ]; then
    echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS"
    if [ $OUTFILE -eq 1 ]; then
	mkdir -p "netpipe_data/$currdate"
	echo "Running $1 RXU=$RXU NPITER=$NPITER RXQ=$RXQ TXQ=$TXQ NITERS=$NITERS MSGS=$MSGS" > "netpipe_data/$currdate/command.txt"
    fi
    $1
else
    echo "unknown command"
fi

