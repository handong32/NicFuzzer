#!/bin/bash

taskset -c 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15 wrk -t16 -c512 -d30s http://192.168.1.$1:6666/index.html --latency
