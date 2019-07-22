#! /bin/bash

export RXU=${RXU:='8'}
export RXQ=${RXQ:='512'}
export TXQ=${TXQ:='512'}
export NITERS=${NITERS:='1'}
export SERVER=${SERVER:=192.168.1.200}
export OUTFILE=${OUTFILE:=0}

currdate=`date +%m_%d_%Y_%H_%M_%S`

if [ $OUTFILE -eq 1 ]; then
    mkdir -p "mcd_data/$currdate"
    echo "Running $1 RXU=$RXU NITERS=$NITERS" > "mcd_data/$currdate/command.txt"
fi

for iter in `seq 1 1 $NITERS`;
do
    for rxu in `seq 0 4 5`;
    do
	echo "iter="$iter "rxu="$rxu
	python -u memtier_bench.py $rxu
	
	if [ $OUTFILE -eq 1 ]; then
	    cp memtier.json "mcd_data/$currdate/mcd_"$rxu\_$iter".json"
	    scp $SERVER:~/perf.out "mcd_data/$currdate/mcd_"$rxu\_$iter".perf"
	fi
	sleep 1
    done
done


