# -*- coding: utf-8 -*-
"""readSpeedTestExample
    
    Repeat reading of counters and settings for a specified number of times, and returns statistics on the timing of execution of these reading functions: 
    * getAllCounters()
    * getAllSettings()
    
    Usage:
       Set the port variable in the corresponding value.
       Run.
    
    Created on Mon Jan 23 16:57:32 2023
"""

import pyAbacus as abacus
from time import time
import numpy as np

##User's parameters
port = 'COM4'    #indicate the port to connect with. E.g.: 'COM4'
samples = 1000   #how many times the read test should be made

##
#create empty arrays
tRdCounters=[]
tRdSettings=[]

my_tausand = abacus.open(port);             #open connection with device

print("Connected to: ",end='')
print(abacus.getIdn(my_tausand));

print("Read speed test. Progress=%5.1f" % ((0.0)), end='')
for a in range(samples):
    t0 = time() #start timer
    data = abacus.getAllCounters(my_tausand)    #read data
    tf = time() #end timer
    tRdCounters.append(tf-t0) #write lapsed time
    
    t0 = time() #start timer
    settings = abacus.getAllSettings(my_tausand)    #read settings
    tf = time() #end timer
    tRdSettings.append(tf-t0) #write lapsed time
    
    progress = float((a+1)*100.0/samples)
    print("\b\b\b\b\b", end='')
    print("%5.1f" % (progress), end='')

print("")
abacus.close(my_tausand)            #close connection with device

print("NumReads:  %d" % (a+1))
print("getAllCounters() statistics")
print("  Min:  %0.5f s" % (np.min(tRdCounters)))
print("  Max:  %0.5f s" % (np.max(tRdCounters)))
print("  Mean: %0.5f s" % (np.mean(tRdCounters)))
print("  StdD: %0.5f s" % (np.std(tRdCounters)))
print("getAllSettings() statistics")
print("  Min:  %0.5f s" % (np.min(tRdSettings)))
print("  Max:  %0.5f s" % (np.max(tRdSettings)))
print("  Mean: %0.5f s" % (np.mean(tRdSettings)))
print("  StdD: %0.5f s" % (np.std(tRdSettings)))