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

iface=s0-eth1

#for tech in 3G 4GLTE WIFI 3G_FLAKY 4GLTE_FLAKY WIFI_FLAKY; do
#  for prog in MOSH SSH; do

for tech in 3G; do
for prog in SSH; do
  	dir=$rootdir/$tech

  	python mosh_test.py --dir $dir --tech $tech --prog $prog
    python plot_cdf.py $dir $tech

	#python $plotpath/plot_queue.py -f $dir/qlen_$iface.txt -o $dir/q.png
	#python $plotpath/plot_tcpprobe.py -f $dir/tcp_probe.txt -o $dir/cwnd.png --histogram
  done
done

#cat $rootdir/*/result.txt | sort -n -k 1
#python plot-results.py --dir $rootdir -o $rootdir/result.png
echo "Started at" $start
echo "Ended at" `date`
