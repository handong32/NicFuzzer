#!/bin/bash

taskset -c 1 wrk -t1 -c1 -d30s http://192.168.1.$1:6666/index.html --latency
