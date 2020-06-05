import pyAbacus as abacus

print("********************")
print("pyAbacus example")
print("********************")
print("1. Find devices and establish a connection\n")

ports, n = abacus.findDevices()
print(ports)

port = list(ports.values())[0] #get first available device

abacus.open(port)			#open connection with device
#abacus.getAllCounters(port)		#read all counter's data from device
#abacus.setSetting(port,"sampling", 5)	#set a single setting in device

print("\n********************")
print("2. Read device settings\n")

#Example of reading all device settings
settings = abacus.getAllSettings(port)
print("Settings read from device, using getAllSettings method:")
print("   settings =",settings)

#Examples reading single settings
value = abacus.getSetting(port,"delay_A")
print("current delay_A=",value,"ns")
value = abacus.getSetting(port,"delay_B")
print("current delay_B=",value,"ns")
value = abacus.getSetting(port,"sleep_A")
print("current sleep_A=",value,"ns")
value = abacus.getSetting(port,"sleep_B")
print("current sleep_B=",value,"ns")
value = abacus.getSetting(port,"coincidence_window")
print("current coincidence_window=",value,"ns")
value = abacus.getSetting(port,"sampling")
print("current sampling=",value,"ms")

print("\n********************")
print("3. Write device settings\n")

#Example of writing a new setting value
abacus.setSetting(port,"sampling", 1300)	    #set sampling=5ms
value = abacus.getSetting(port,"sampling")  #read sampling
print("current sampling=",value,"ms")

abacus.setSetting(port,"delay_B", 20)	    #set delay_B=20ns
value = abacus.getSetting(port,"delay_B")
print("current delay_B=",value,"ns")

print("\n********************")
print("4. Read measurements from device\n")

#Example of reading measurements from counters
counters, counters_id = abacus.getAllCounters(port)
print("Measurements read from device, using getAllCounters method:")
print("   counters_id =",counters_id)
print("   counters =",counters)
print("   counts in A:                    counters.A =",counters.A)
print("   coincidences between A and B:   counters.AB =",counters.AB)

abacus.close(port)			#close connection with device