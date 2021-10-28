"""singleReadExample
    
    Finds Tausand Abacus devices, connects to the first found device, and reads counter values from device.
"""
import pyAbacus as abacus
ports , n = abacus.findDevices()    #required to scan devices before opening a connection
my_tausand = list(ports.keys())[0]  #get first available device
abacus.open(my_tausand)             #open connection with device
data = abacus.getAllCounters(my_tausand)    #read data
abacus.close(my_tausand)            #close connection with device
print(data)
