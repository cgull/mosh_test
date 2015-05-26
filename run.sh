#!/bin/bash

# Exit on any failure
set -e

# Check for uninitialized variables
set -o nounset

ctrlc() {
	killall -9 python
	mn -c
	exit
}

trap ctrlc SIGINT

start=`date`
exptid=`date +%b%d-%H:%M`

rootdir=mosh_test-$exptid
plotpath=util
trace=term_trace_1

iface=s0-eth1

for tech in 3G 3G_FLAKY 4G_LTE 4G_LTE_FLAKY WIFI; do
for prog in SSH MOSH; do
  	dir=$rootdir/$tech
  	python mosh_test.py --dir $dir --tech $tech --prog $prog  --trace $trace --user $SUDO_USER --testdir $(pwd)/
    python plot_cdf.py $dir $tech

done  
done

echo "Started at" $start
echo "Ended at" `date`
