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

# credit: unutbu for this function
# http://stackoverflow.com/questions/2566412/find-nearest-value-in-numpy-array
def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return array[idx]

if __name__ == '__main__':
    # arg list
    # 1 - ssh data file
    # 2 - mosh data file
    
    if len(sys.argv) != 4:
        raise("error, incorrect argument formatting!")
        
    ssh_data_file = sys.argv[1]
    mosh_data_file = sys.argv[2]
    test_tech = sys.argv[3]
    
    with open(ssh_data_file) as f:
        ssh_content = f.readlines()
        
    ssh_all_floats = []
    for line in ssh_content:
        val = line.split(" ")[1]
        if "0." in val:
            ssh_all_floats.append(float(val))
    
    
    ssh_values, ssh_base = np.histogram(ssh_all_floats, bins=20000)
    #evaluate the cumulative
    ssh_cumulative = np.cumsum(ssh_values)
    
    ssh_max_val = max(ssh_cumulative)
    ssh_data = []
    for val in ssh_cumulative:
        ssh_data.append(val*100.0/ssh_max_val)
        
    # plot the cumulative function
    ssh_line = plt.plot(ssh_base[:-1], ssh_data, c='blue', linestyle="dotted", linewidth=2.0, label="SSH")
    
    ssh_median = np.median(np.array(ssh_all_floats))
    ssh_mean_x = np.mean(np.array(ssh_all_floats))
    ssh_mean_x_closest = find_nearest(np.array(ssh_base[:-1]), ssh_mean_x)
    index_of_closest = np.nonzero(ssh_base[:-1] == ssh_mean_x_closest)[0][0]
    ssh_mean_y = ssh_data[index_of_closest]
    plt.plot(ssh_median, 50, 'o')
    plt.annotate("Median:\n%.1f ms" % (ssh_median*1000), xy=(ssh_median, 50),
            xytext=(ssh_median + 0.01, 46.5),
            textcoords='data',
            horizontalalignment='left',
            verticalalignment='bottom',)
            
    plt.plot(ssh_mean_x, ssh_mean_y, 'o')
    plt.annotate("Mean:\n%.1f ms" % (ssh_mean_x*1000), xy=(ssh_mean_x, ssh_mean_y),
            xytext=(ssh_mean_x + 0.01, ssh_mean_y + 5),
            textcoords='data',
            horizontalalignment='left',
            verticalalignment='bottom',)
    
    with open(mosh_data_file) as f:
        mosh_content = f.readlines()
        
    mosh_all_floats = []
    for line in mosh_content:
        val = line.split(" ")[1]
        if "0." in val:
            mosh_all_floats.append(float(val))
    
    
    mosh_values, mosh_base = np.histogram(mosh_all_floats, bins=20000)
    #evaluate the cumulative
    mosh_cumulative = np.cumsum(mosh_values)
    
    mosh_max_val = max(mosh_cumulative)
    mosh_data = []
    for val in mosh_cumulative:
        mosh_data.append(val*100.0/mosh_max_val)
        
    # plot the cumulative function
    mosh_line = plt.plot(mosh_base[:-1], mosh_data, c='red', linewidth=2.0, label="Mosh")
    
    mosh_median = np.median(np.array(mosh_all_floats))
    mosh_mean_x = np.mean(np.array(mosh_all_floats))
    mosh_mean_x_closest = find_nearest(np.array(mosh_base[:-1]), mosh_mean_x)
    index_of_closest = np.nonzero(mosh_base[:-1] == mosh_mean_x_closest)[0][0]
    mosh_mean_y = mosh_data[index_of_closest]
    
    plt.plot(mosh_median, 50, 'o')
    plt.annotate("Median:\n%.1f ms" % (mosh_median*1000), xy=(mosh_median, 50),
            xytext=(mosh_median + 0.01, 46.5),
            textcoords='data',
            horizontalalignment='left',
            verticalalignment='bottom',)
            
    plt.plot(mosh_mean_x, mosh_mean_y, 'o')
    plt.annotate("Mean:\n%.1f ms" % (mosh_mean_x*1000), xy=(mosh_mean_x, mosh_mean_y),
            xytext=(mosh_mean_x + 0.01, mosh_mean_y + 5),
            textcoords='data',
            horizontalalignment='left',
            verticalalignment='bottom',)
    
    plt.xlabel('Keystroke response time (seconds)')
    plt.ylabel('Percentage')
    plt.title(test_tech)
    plt.xlim([-.003,0.6])
    plt.ylim([0,100])
    plt.legend(loc = 1);
    plt.grid(b=True, which='major', color='gray', linestyle='-')
    
    
    
    plt.savefig(test_tech + ".png")
