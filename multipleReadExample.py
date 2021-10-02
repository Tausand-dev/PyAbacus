"""multipleReadExample
    
    Reads continuous samples from a Tausand Abacus device, using pyAbacus library.
    Implements error handling to self-recover.
    Writes measured data in a plain text file.
"""
import pyAbacus as abacus
import time

samples_to_read = 10 #change this parameter to set how many samples to read
my_sampling_time_ms = 1000 #change this parameter to set your sampling time. 1000=1s.

#define the desired channels to be read. Some examples:
channels_to_read_2ch = ['A','B','AB']   #for a 2 channel device
channels_to_read_4ch = ['A','B','C','AB','AC','custom_c1'] #custom_c1 corresponds to a multi-fold mesurement, to be configured, e.g. 'ABC'
channels_to_read_8ch = ['A','B','C','AB','AC','custom_c1', 'custom_c3', 'custom_c8'] #custom_cN corresponds to a multi-fold mesurement, to be configured, e.g. 'ABC'

print("******************************")
print("pyAbacus multiple read example")
print("******************************")
print("1. Find devices and establish a connection\n")

ports, n = abacus.findDevices() #required to scan devices before opening a connection

if n==0:
    print("\nNo valid devices were found. Closing.")
    
else:
    print("\nAvailable valid devices:")
    print(ports)

    mydevice = list(ports.keys())[0] #get first available device
    abacus.open(mydevice)	     #open connection with device

    #get and print some properties of the connected device:
    print("\nConnected to the following device:")
    idnstring = abacus.getIdn(mydevice)
    numchannels = abacus.getChannelsFromName(mydevice)
    resolution = abacus.getResolutionFromName(mydevice)
    physicalport = abacus.getPhysicalPort(mydevice)
    print("   device name =",mydevice)
    print("   device physical port =",physicalport)
    print("   device identifier string =",idnstring)
    print("   number of channels =",numchannels)
    print("   resolution =",resolution,"ns")

    ## select channels_to_read depending on the number of channels of the connected device    
    if numchannels == 8:
    	channels_to_read = channels_to_read_8ch
    elif numchannels == 4:
        channels_to_read = channels_to_read_4ch
    else:
        channels_to_read = channels_to_read_2ch

    #########
    print("\n2. Write and read new settings\n")
    #write settings, using pyAbacus setSetting function:
    abacus.setSetting(mydevice,"sampling", my_sampling_time_ms) #set sampling, in milliseconds (default: 1000ms)
    abacus.setSetting(mydevice,"coincidence_window", 50)    #set coincidence_window=50ns
    abacus.setSetting(mydevice,"delay_A", 0)	            #set delay_A=0ns
    abacus.setSetting(mydevice,"delay_B", 0)	            #set delay_B=0ns
    abacus.setSetting(mydevice,"sleep_A", 0)	            #set sleep_A=0ns
    abacus.setSetting(mydevice,"sleep_B", 0)	            #set sleep_B=0ns
    if numchannels == 4:
        abacus.setSetting(mydevice,"delay_C", 0)	        #set delay_C=0ns
        abacus.setSetting(mydevice,"sleep_C", 0)	        #set sleep_C=0ns
        #configure multi-fold coincidences ('custom_c1'):
        abacus.setSetting(mydevice,"config_custom_c1","ABC")    #must use 3 or 4 letters. Valid options: ABC, ABD, ACD, BCD, ABCD
    elif numchannels == 8:
    	abacus.setSetting(mydevice,"config_custom_c1","ADE")	#must use 3 or 4 letters. Valid options: any combination of letters from A to H in alphabetical order 
    	abacus.setSetting(mydevice,"config_custom_c3","EFH")
    	abacus.setSetting(mydevice,"config_custom_c8","BEGH")    	    	

    #read settings, using pyAbacus getAllSettings function:
    #a retry routine has been implemented, as an example to handle exceptions
    max_attempts=5
    for attempt in range(max_attempts):
        try:
            current_settings = abacus.getAllSettings(mydevice)
            print(current_settings)
        except abacus.CheckSumError:
            print("Data integrity error in getAllSettings: missing or wrong bits. Retry.")
            pass #retry
        except (abacus.serial.serialutil.SerialException,KeyError):
            print("Communication error in getAllSettings: device might be disconnected or turned off.")
        except:
            print("Unexpected error. Device connection closed.")
            abacus.close(mydevice)  #close connection with device
            raise
        else:
            break #done, continue
    
        

    #########
    print("\n3. Create file")
    #define constant strings:
    date_time_string = time.strftime("%Y-%m-%d_%H%M%S", time.localtime())
    column_headers = ["PC time","countersID"]+channels_to_read;
    file_name = "data_multipleReadExample_"+date_time_string+".txt"
    #create file and write headers:
    myfile = open(file_name, "a")
    print("File",file_name,"has been created")
    myfile.write('multipleReadExample\n')
    myfile.write('-------------------\n')
    myfile.write('Begin time: '+date_time_string+'\n')
    myfile.write('Device: '+mydevice+'\n')
    myfile.write('Settings: '+str(current_settings)+'\n')
    myfile.write("\n\n")
    myfile.write(str(column_headers))
    myfile.write("\n")

    #########
    print("\n4. Multiple read using pyAbacus waitAndGetValues function begins")
    full_data=[]
    print(column_headers)
    for sample in range(samples_to_read):
        print(sample+1,'/',samples_to_read,sep='',end=',')
        try:
            my_data, my_id = abacus.waitAndGetValues(mydevice,channels_to_read,print_on=True) #for debug purposes, turn print_on=True; by default is False.
            my_data.insert(0,my_id) #prepend my_id to my_data
            my_data.insert(0,round(time.time(),3)) #prepend current PC time to my_data
            print(my_data)
            full_data.append(my_data)
            myfile.write(str(my_data))
            myfile.write("\n")
        except abacus.CheckSumError:
            print("Data integrity error in waitAndGetValues: missing or wrong bits.")
        except (abacus.serial.serialutil.SerialException,KeyError):
            print("Communication error in waitAndGetValues: device might be disconnected or turned off.")
        except:
            print("Unexpected error. Device connection closed. File access closed.")
            abacus.close(mydevice)  #close connection with device
            myfile.close()          #close file
            raise        
        
    abacus.close(mydevice)  #close connection with device
    myfile.close()          #close file
    print("\nFull set of data is:")
    print(column_headers)
    print(full_data)
    print("\nExample done.")
