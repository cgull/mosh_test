#!/usr/bin/python

"CS244 Assignment 3: MOSH"

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg
from mininet.util import dumpNodeConnections
from mininet.cli import CLI

import subprocess
from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
import termcolor as T
from argparse import ArgumentParser

import sys
import os
from util.monitor import monitor_qlen
from util.helper import stdev


# Number of samples to skip for reference util calibration.
CALIBRATION_SKIP = 10
#CALIBRATION_SKIP = 5

# Number of samples to grab for reference util calibration.
CALIBRATION_SAMPLES = 30
#CALIBRATION_SAMPLES = 15

# Set the fraction of the link utilization that the measurement must exceed
# to be considered as having enough buffering.
TARGET_UTIL_FRACTION = 0.98
#TARGET_UTIL_FRACTION = 0.95

# Fraction of input bandwidth required to begin the experiment.
# At exactly 100%, the experiment may take awhile to start, or never start,
# because it effectively requires waiting for a measurement or link speed
# limiting error.
START_BW_FRACTION = 0.9


# Number of samples to take in get_rates() before returning.
NSAMPLES = 3
#NSAMPLES = 2

# Time to wait between samples, in seconds, as a float.
SAMPLE_PERIOD_SEC = 1.0
#SAMPLE_PERIOD_SEC = 0.5

# Time to wait for first sample, in seconds, as a float.
SAMPLE_WAIT_SEC = 3.0
#SAMPLE_WAIT_SEC = 2.0

# Delay in milliseconds.  Will be changed based on test tech.
DELAY = 200.0

# Bandwidth in MB/s.  Will be changed based on test tech.
BANDWIDTH = 5.0

# Drop rate.  Will be changed based on test tech.
DROP_RATE = 0.0

# Jitter factor. Will change based on test tech.
JITTER_FACTOR = 0.5

# Tech to use.  MOSH or SSH.
MOSH_PATH = "/usr/bin/mosh"
SSH_PATH = "/usr/bin/ssh"
TECH_PATH = ""


def cprint(s, color, cr=True):
    """Print in color
       s: string to print
       color: color to use"""
    if cr:
        print T.colored(s, color)
    else:
        print T.colored(s, color),


# Parse arguments

parser = ArgumentParser(description="Mosh Testing")
parser.add_argument('--tech', '-t',
                    dest="tech",
                    type=str,
                    action="store",
                    help="Broadband technology",
                    required=True)

parser.add_argument('--dir', '-d',
                    dest="dir",
                    type=str,
                    action="store",
                    help="Directory to store outputs",
                    default="results",
                    required=True)
                    
parser.add_argument('--prog', '-p',
                    dest="prog",
                    type=str,
                    action="store",
                    help="Program to run (MOSH or SSH)",
                    required=True)

# Expt parameters
args = parser.parse_args()

if not os.path.exists(args.dir):
    os.makedirs(args.dir)

lg.setLogLevel('info')

# Topology to be instantiated in Mininet
class StarTopo(Topo):
    "Star topology for Buffer Sizing experiment"

    def build(self, tech="3G", prog="MOSH"):
          
        # TODO: Fill in the following function to Create the experiment
        # topology Set appropriate values for bandwidth, delay, and queue
        # size.
        
        if (prog == "MOSH"):
            TECH_PATH = MOSH_PATH
        else:
            TECH_PATH = SSH_PATH
        
        
        h_server = self.addHost('server')
        h_client = self.addHost('client')
        self.addLink(h_server, h_client, bw=BANDWIDTH, delay=(str(DELAY) + "ms"), loss=DROP_RATE, jitter=(str(DELAY * JITTER_FACTOR) + "ms"))
        
        return

def start_tcpprobe():
    "Install tcp_probe module and dump to file"
    print "Starting TCP Probe"
    os.system("rmmod tcp_probe 2>/dev/null; modprobe tcp_probe;")
    Popen("cat /proc/net/tcpprobe > %s/tcp_probe.txt" %
          args.dir, shell=True)

def stop_tcpprobe():
    os.system("killall -9 cat; rmmod tcp_probe &>/dev/null;")

def count_connections():
    "Count current connections in iperf output file"
    out = args.dir + "/iperf_server.txt"
    lines = Popen("grep connected %s | wc -l" % out,
                  shell=True, stdout=PIPE).communicate()[0]
    return int(lines)

def set_q(iface, q):
    "Change queue size limit of interface"
    cmd = ("tc qdisc change dev %s parent 5:1 "
           "handle 10: netem limit %s" % (iface, q))
    #os.system(cmd)
    subprocess.check_output(cmd, shell=True)

def set_speed(iface, spd):
    "Change htb maximum rate for interface"
    cmd = ("tc class change dev %s parent 5:0 classid 5:1 "
           "htb rate %s burst 15k" % (iface, spd))
    os.system(cmd)

def get_txbytes(iface):
    f = open('/proc/net/dev', 'r')
    lines = f.readlines()
    for line in lines:
        if iface in line:
            break
    f.close()
    if not line:
        raise Exception("could not find iface %s in /proc/net/dev:%s" %
                        (iface, lines))
    # Extract TX bytes from:
    #Inter-|   Receive                                                |  Transmit
    # face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    # lo: 6175728   53444    0    0    0     0          0         0  6175728   53444    0    0    0     0       0          0
    return float(line.split()[9])

def get_rates(iface, nsamples=NSAMPLES, period=SAMPLE_PERIOD_SEC,
              wait=SAMPLE_WAIT_SEC):
    """Returns the interface @iface's current utilization in Mb/s.  It
    returns @nsamples samples, and each sample is the average
    utilization measured over @period time.  Before measuring it waits
    for @wait seconds to 'warm up'."""
    # Returning nsamples requires one extra to start the timer.
    nsamples += 1
    last_time = 0
    last_txbytes = 0
    ret = []
    sleep(wait)
    while nsamples:
        nsamples -= 1
        txbytes = get_txbytes(iface)
        now = time()
        elapsed = now - last_time
        #if last_time:
        #    print "elapsed: %0.4f" % (now - last_time)
        last_time = now
        # Get rate in Mbps; correct for elapsed time.
        rate = (txbytes - last_txbytes) * 8.0 / 1e6 / elapsed
        if last_txbytes != 0:
            # Wait for 1 second sample
            ret.append(rate)
        last_txbytes = txbytes
        print '.',
        sys.stdout.flush()
        sleep(period)
    return ret

def avg(s):
    "Compute average of list or string of values"
    if ',' in s:
        lst = [float(f) for f in s.split(',')]
    elif type(s) == str:
        lst = [float(s)]
    elif type(s) == list:
        lst = s
    return sum(lst)/len(lst)

def median(l):
    "Compute median from an unsorted list of values"
    s = sorted(l)
    if len(s) % 2 == 1:
        return s[(len(l) + 1) / 2 - 1]
    else:
        lower = s[len(l) / 2 - 1]
        upper = s[len(l) / 2]
        return float(lower + upper) / 2

def format_floats(lst):
    "Format list of floats to three decimal places"
    return ', '.join(['%.3f' % f for f in lst])

def ok(fraction):
    "Fraction is OK if it is >= args.target"
    return fraction >= args.target

def format_fraction(fraction):
    "Format and colorize fraction"
    if ok(fraction):
        return T.colored('%.3f' % fraction, 'green')
    return T.colored('%.3f' % fraction, 'red', attrs=["bold"])

def test_response_time(net):
    h_server = net.get('server')
    h_client = net.get('client')
    
    
    print "h_server IP = " + str(h_server.IP())
    print "h_client IP = " + str(h_client.IP())
    #CLI(net);
    
    h_server.cmd("/usr/sbin/sshd -D&")
    
    print "Running SSH Test"
               
    ssh_cmd = '%s %s ssh ubuntu@%s -i %s -o %s \'"%s %s"\' > %s 2> %s' % \
             ("/home/ubuntu/cs244/mosh_test/term-replay-client", \
              "term_trace_1", \
              str(h_server.IP()), \
              "./private_test_key", \
              "StrictHostKeyChecking=no", \
              "cd /home/ubuntu/cs244/mosh_test/; ./term-replay-server", \
              "term_trace_1", \
              args.dir + "/ssh-std-out.txt", \
              args.dir + "/ssh-stderr-out.txt")
               
    print "ssh_cmd2\n\n"
    print ssh_cmd
    
    h_client.cmd(ssh_cmd)
    pass

# TODO: Fill in the following function to verify the latency
# settings of your topology

def verify_latency(net):
    "Verify link latency"
    # use ping to figure out the latency and verify it matches what we expect
    h_server = net.get('server')
    h_client = net.get('client')
    RTT = float(h_client.cmd("ping -c %d %s | tail -1| awk -F '/' '{print $5}'" % (NSAMPLES, str(h_server.IP()))))

    RTT_fail = abs(RTT - DELAY * 2) >  DELAY * 2 * JITTER_FACTOR
    
    print "RTT is: %.1f" % RTT
    print "DELAY is %.1f" % DELAY

    if (RTT_fail):
        print "System latency not within 10%% of desired delay"
        sys.exit(1)

    print "System latency verified"
    return

# TODO: Fill in the following function to verify the bandwidth
# settings of your topology

def verify_bandwidth(net):
    print "Verifying link bandwidths..."
    h_server = net.get('server')
    h_client = net.get('client')
    host_list = [h_server, h_client]
    # use iperf in mininet to get the bandwidth
    [ expBW, cBW, sBW ] = net.iperf(host_list, 'UDP', '%sM' % (BANDWIDTH), None, 10);
    outBW = sBW.split(' ')[0]
    if (abs(float(BANDWIDTH) - float(outBW)) > (JITTER_FACTOR * BANDWIDTH)):
        print "Bottleneck bandwidth not within 10%% of desired bandwidth"
        sys.exit(1)

    print "System bandwidth verified"
    return

def main():
    "Create network and run Buffer Sizing experiment"

    start = time()
    # Reset to known state
    topo = StarTopo(tech=args.tech, prog=args.prog)
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    dumpNodeConnections(net.hosts)
    net.pingAll()

    # TODO: verify latency and bandwidth of links in the topology you
    # just created.
    verify_latency(net)
    
    verify_bandwidth(net)

    cprint("Starting experiment", "green")

    # TODO: change the interface for which queue size is adjusted
    # might be eth2
    test_response_time(net)

    # Store output.  It will be parsed by run.sh after the entire
    # sweep is completed.  Do not change this filename!
    #output = "%d %s %.3f\n" % (total_flows, ret, ret * 1500.0)
    #open("%s/result.txt" % args.dir, "w").write(output)


    net.stop()
    Popen("killall -9 top bwm-ng tcpdump cat mnexec", shell=True).wait()
    end = time()
    cprint("Test took %.3f seconds" % (end - start), "yellow")

if __name__ == '__main__':
    try:
        main()
    except:
        print "-"*80
        print "Caught exception.  Cleaning up..."
        print "-"*80
        import traceback
        traceback.print_exc()
        os.system("killall -9 top bwm-ng tcpdump cat mnexec iperf; mn -c")

