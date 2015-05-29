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
trace=term_trace_4

iface=s0-eth1

for tech in 3G_FLAKY 3G 4G_LTE 4G_LTE_FLAKY WIFI; do
  dir=$rootdir/$tech
  for prog in SSH MOSH; do
    python mosh_test.py --dir $dir --tech $tech --prog $prog  --trace $trace --user $SUDO_USER --testdir $(pwd)/
  done  
  python plot_cdf.py $dir/ssh-stderr-out.txt $dir/mosh-stderr-out.txt $tech
done

echo "Started at" $start
echo "Ended at" `date`
