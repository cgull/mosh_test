import matplotlib
matplotlib.use('Agg')
import itertools
import matplotlib.pyplot as plt
import math
import sys
import numpy as np
import os
 
#import matplotlib as m
#if os.uname()[0] == "Darwin":
#    m.use("MacOSX")
#else:
#    m.use("Agg")


if __name__ == '__main__':
    # arg list
    # 1 - dir with data files
    # 2 - tech (i.e. 3G, Wifi, etc)
    
    if len(sys.argv) != 3:
        raise("error, incorrect argument formatting!")
        
    test_dir = sys.argv[1]
    test_tech = sys.argv[2]
    
    with open(test_dir + "/" + "ssh-stderr-out.txt") as f:
        content = f.readlines()
        
    all_floats = []
    for line in content:
        val = line.split(" ")[1]
        if "0." in val:
            all_floats.append(float(val))
    
    
    values, base = np.histogram(all_floats, bins=100)
    #evaluate the cumulative
    cumulative = np.cumsum(values)
    
    max_val = max(cumulative)
    data = []
    for val in cumulative:
        data.append(val*100.0/max_val)
        
    # plot the cumulative function
    plt.plot(base[:-1], data, c='blue')
    plt.xlabel('Keystroke response time (seconds)')
    plt.ylabel('Percentage')
    plt.savefig(test_dir + "/" + test_tech + ".png")
