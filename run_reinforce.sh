#! /bin/bash

set -x

for t in `seq 0 1 600`;
do
	python3 -u reinforce_netpipe_single_reward.py
done
