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

# Number of samples to take in verify latency
NSAMPLES = 5

# Delay in milliseconds.  Will be changed based on test tech.
DELAY = 200.0

# Bandwidth in MB/s.  Will be changed based on test tech.
BANDWIDTH = 5.0

# Drop rate.  Will be changed based on test tech.
DROP_RATE = 0.0

# Jitter factor. Will change based on test tech.
JITTER_FACTOR = 0.5



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
                    
parser.add_argument('--trace', '-r',
                    dest="trace",
                    type=str,
                    action="store",
                    help="Trace file to use",
                    required=True)
                    
parser.add_argument('--user', '-u',
                    dest="user",
                    type=str,
                    action="store",
                    help="Login username",
                    required=True)

parser.add_argument('--testdir', '-td',
                    dest="testdir",
                    type=str,
                    action="store",
                    help="Directory of test script and key files",
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
        
        global BANDWIDTH
        global DELAY
        global JITTER_FACTOR
        global DROP_RATE
        
        if tech == "4G_LTE":
            BANDWIDTH = 26.0
            DELAY = 44.5
            JITTER_FACTOR = .11
            DROP_RATE = 0.0
        elif tech == "4G_LTE_FLAKY":
            BANDWIDTH = 3.0
            DELAY = 67.5
            JITTER_FACTOR = 0.30
            DROP_RATE = 0.063  
        elif tech == "3G":
            BANDWIDTH = 3.0
            DELAY = 61.5
            JITTER_FACTOR = 0.24
            DROP_RATE = 0.013
        elif tech == "3G_FLAKY":
            BANDWIDTH = 0.9
            DELAY = 74.5
            JITTER_FACTOR = 0.40
            DROP_RATE = 0.087
        elif tech == "WIFI":
            BANDWIDTH = 68
            DELAY = 4.0
            JITTER_FACTOR = 0.38
            DROP_RATE = 0.0         
        
        h_server = self.addHost('server')
        h_client = self.addHost('client')
        self.addLink(h_server, h_client, bw=BANDWIDTH, delay=(str(DELAY) + "ms"), loss=DROP_RATE, jitter=(str(DELAY * JITTER_FACTOR) + "ms"))
        
        return

def test_response_time(net):
    h_server = net.get('server')
    h_client = net.get('client')
    
    
    print "h_server IP = " + str(h_server.IP())
    print "h_client IP = " + str(h_client.IP())
    #CLI(net);
    
    h_server.cmd("/usr/sbin/sshd -D&")
    
    print "Running " + args.prog + " Test with tech " + str(args.tech)

    cmd_invocation = '%s %s' % \
                     (args.testdir + "term-replay-client", \
                      str(args.trace))

    target_host = '%s@%s' % \
                  (str(args.user), \
                   str(h_server.IP()))

    ssh_flags = '-i %s -o %s' % ("./private_test_key", \
                                 "StrictHostKeyChecking=no")

    ssh_cmd = '%s ssh %s %s \'"%s %s"\' > %s 2> %s' % \
             (cmd_invocation, \
              target_host, \
              str(ssh_flags), \
              "cd " + args.testdir + "; ./term-replay-server", \
              str(args.trace), \
              args.dir + "/ssh-std-out.txt", \
              args.dir + "/ssh-stderr-out.txt")
               
#    mosh_cmd = '%s mosh %s --ssh=\'"ssh %s"\' \'"%s %s"\' > %s 2> %s' % \
#              (cmd_invocation, \
#              target_host, \
#               str(ssh_flags), \
#               "cd " + args.testdir + "; ./term-replay-server", \
#               str(args.trace), \
#               args.dir + "/mosh-std-out.txt", \
#               args.dir + "/mosh-stderr-out.txt")

    iptables_setp_cmd_a = 'sudo iptables -I INPUT 1 --proto udp -j ACCEPT'
    iptables_setp_cmd_b = 'sudo iptables -I OUTPUT 1 --proto udp -j ACCEPT'

    mosh_cmd = '%s "mosh --bind-server=any --ssh=\\\"ssh %s\\\" -- %s sh -c \\\"%s %s\\\"" > %s 2> %s' % \
               (cmd_invocation, \
                str(ssh_flags), \
                target_host, \
                "cd " + args.testdir + "; ./term-replay-server", \
                str(args.trace), \
                args.dir + "/mosh-std-out.txt", \
                args.dir + "/mosh-stderr-out.txt")

    CLI(net)

    if (args.prog == "SSH"):
        print "ssh_cmd\n\n"
        print ssh_cmd
        h_client.cmd(ssh_cmd)
    elif (args.prog == "MOSH"):
        print "mosh_cmd\n\n"
        print mosh_cmd
        h_client.cmd(iptables_setp_cmd_a, shell=True)
        h_client.cmd(iptables_setp_cmd_b, shell=True)
        h_server.cmd(iptables_setp_cmd_a, shell=True)
        h_server.cmd(iptables_setp_cmd_b, shell=True)
        hc_proc = h_client.popen(mosh_cmd, shell=True)
        while(hc_proc.poll() == None):
            sleep(1)
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
        print "System latency not within %.0f%% of desired delay" % (JITTER_FACTOR * 100)
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
        print "Bottleneck bandwidth not within %.0f%% of desired bandwidth" % (JITTER_FACTOR * 100)
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

