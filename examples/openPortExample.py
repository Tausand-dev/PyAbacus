"""openPortExample
    
    Show how to start communication with a Tausand Abacus devices using two simple methods: 1) By specifying the port name a device is plugged into.    2) By finding Tausand Abacus devices that are plugged in and connecting to the first found device
    Finally, after comminucation is established, the counters values are read read.
"""
import pyAbacus as abacus

# FIRST METHOD
print('\nFIRST METHOD\n')
# The simplest way to start communication with a Tausand device is by calling the function open, assuming you know what port your device is plugged into:
#my_tausand = abacus.open("COM3") # For Windows use a string "COMX" where X is the number of the port
my_tausand = abacus.open("/dev/ttyACM0") # For Mac or Linux use "/dev/ttyXXXXXXX", where ttyXXXXXXX represents the name of the port
data = abacus.getAllCounters(my_tausand)
abacus.close(my_tausand)
print(data) 

# SECOND METHOD
print('\nSECOND METHOD\n')
# If you don't know the ports' names, you can also start communication by calling find devices(), choosing one of the ports, and calling open():
ports , n = abacus.findDevices()    #required to scan devices before opening a connection
my_tausand = list(ports.keys())[0]  #get first available device
abacus.open(my_tausand)             #open connection with device
data = abacus.getAllCounters(my_tausand)    #read data
abacus.close(my_tausand)            #close connection with device
print(data)
