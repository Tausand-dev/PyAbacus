import serial
import serial.tools.list_ports as find_ports

import time
from math import log10
from threading import Thread

from itertools import combinations

from .constants import TIMEOUT, BAUDRATE, START_COMMUNICATION, READ_VALUE, WRITE_VALUE, END_COMMUNICATION, BOUNCE_TIMEOUT
from .constants import CURRENT_OS, ABACUS_SERIALS, TEST_MESSAGE, TEST_ANSWER, COUNTERS_VALUES, SETTINGS
from .constants import ADDRESS_DIRECTORIES, ADDRESS_DIRECTORY_2CH, ADDRESS_DIRECTORY_8CH

from .constants import SAMPLING_VALUES
from .constants import DELAY_MINIMUM_VALUE, DELAY_MAXIMUM_VALUE, DELAY_STEP_VALUE
from .constants import SLEEP_MINIMUM_VALUE, SLEEP_MAXIMUM_VALUE, SLEEP_STEP_VALUE
from .constants import COINCIDENCE_WINDOW_MINIMUM_VALUE, COINCIDENCE_WINDOW_MAXIMUM_VALUE, COINCIDENCE_WINDOW_STEP_VALUE

from .exceptions import *
import pyAbacus.constants

def open(abacus_port):
    """
        Opens a session to a Tausand Abacus device
    """
    global ABACUS_SERIALS, ADDRESS_DIRECTORIES, DEVICES
    if abacus_port in ABACUS_SERIALS.keys():
        close(abacus_port)
    serial = AbacusSerial(DEVICES[abacus_port])
    ABACUS_SERIALS[abacus_port] = serial
    n = serial.getNChannels()
    if n == 2:
        ADDRESS_DIRECTORIES[abacus_port] = ADDRESS_DIRECTORY_2CH
        COUNTERS_VALUES[abacus_port] = CountersValues(2)
        SETTINGS[abacus_port] = Settings2Ch()
    elif n == 4:
        ADDRESS_DIRECTORIES[abacus_port] = ADDRESS_DIRECTORY_8CH
        COUNTERS_VALUES[abacus_port] = CountersValues(4)
        SETTINGS[abacus_port] = Settings4Ch()
    elif n == 8:
        ADDRESS_DIRECTORIES[abacus_port] = ADDRESS_DIRECTORY_8CH
        COUNTERS_VALUES[abacus_port] = CountersValues(8)
        SETTINGS[abacus_port] = Settings8Ch()

    #Set constants linked to device resolution. New on v1.1 (2020-04-23)
    name=serial.getIdn()
    if "AB19" in name:
        setConstantsByResolution(1) #resolution = 1ns; update constants
    elif "AB15" in name:
        setConstantsByResolution(2) #resolution = 2ns; update constants
    elif "AB10" in name:
        setConstantsByResolution(5) #resolution = 5ns; update constants        

def close(abacus_port):
    """
        Closes a Tausand Abacus device session
    """
    global ABACUS_SERIALS, ADDRESS_DIRECTORIES
    if abacus_port in ABACUS_SERIALS.keys():
        try:
            ABACUS_SERIALS[abacus_port].close()
        except Exception as e:
            print(e)
        del ABACUS_SERIALS[abacus_port]
    if abacus_port in ADDRESS_DIRECTORIES.keys():
        del ADDRESS_DIRECTORIES[abacus_port]

def getChannelsFromName(name):
    """Returns the number of input channels by reading the device name.

    For example, if name="Tausand Abacus AB1004", returns 4.
    
    Args:
        name: idn string of the device.

    Returns:
        integer, number of input channels in device.
        
    Raises:
        AbacusError: Not a valid abacus.
        
    """
    if pyAbacus.constants.DEBUG:
        print("Looking for channels in name: "+name)
    if "AB1002" in name:
        return 2
    elif "AB1004" in name:
        return 4
    elif "AB1008" in name:
        return 8
    #new devices AB150x and 190x. New on v1.1 (2020-04-22)
    elif "AB1502" in name:
        return 2
    elif "AB1504" in name:
        return 4
    elif "AB1508" in name:
        return 8
    elif "AB1902" in name:
        return 2
    elif "AB1904" in name:
        return 4
    elif "AB1908" in name:
        return 8
    else:
        raise(AbacusError("Not a valid abacus."))

def getResolutionFromName(name): #new on v1.1 (2020-06-20)
    """Returns the device resolution, in nanoseconds, by reading the device name.

    For example, if name="Tausand Abacus AB1004", a 5ns device, returns 5.
    For example, if name="Tausand Abacus AB1504", a 2ns device, returns 2.
    
    Args:
        name: idn string of the device.

    Returns:
        integer, number of input channels in device.
        
    Raises:
        AbacusError: Not a valid abacus.
        
    """
    if pyAbacus.constants.DEBUG:
        print("Looking for resolution in name: "+name)
    if "AB10" in name:    #AB1002, AB1004, AB1008
        return 5
    elif "AB15" in name:  #AB1502, AB1504, AB1508
        return 2
    elif "AB19" in name:  #AB1902, AB1904, AB1908
        return 1
    else:
        raise(AbacusError("Not a valid abacus."))
        return 5    

def writeSerial(abacus_port, command, address, data_16o32):
    """
	Low level function. Writes in the specified serial port an instruction built based on command, memory address and data.
    """
    global ABACUS_SERIALS

    serial = ABACUS_SERIALS[abacus_port]
    serial.writeSerial(command, address, data_16o32)

def readSerial(abacus_port):
    """
	Reads bytes available at the specified serial port.
    """
    global ABACUS_SERIALS
    return ABACUS_SERIALS[abacus_port].readSerial()

def dataStreamToDataArrays(input_string, chunck_size = 3):
    """Builds data from string read on serial port.

    Args:
        input_string: stream of bytes to convert. Should have the appropriate format, as given by a Tausand Abacus device.

        | chunck_size : integer, number of bytes per single data row.
        |   -  Use chunck_size=3 for devices with inner 16-bit registers e.g. Tausand Abacus AB1002, where byte streams are: {address,MSB,LSB}.
        |   -  Use chunck_size=5 for devices with inner 32-bit registers e.g. Tausand Abacus AB1004, where byte streams are: {address,MSB,2nd-MSB,2nd-LSB,LSB}.

    Returns:
        Two lists of integer values: addresses, data.

    Raises:
        AbacusError: Input string is not valid chunck size must either be 3 or 5.

    """
    input_string, n = input_string
    test = sum(input_string[2:]) & 0xFF # 8 bit
    if test != 0xFF:
        raise(CheckSumError())
    # if test == 0xFF:
    chuncks = input_string[2 : -1] # (addr & MSB & LSB)^n
    if chunck_size == 3:
        chuncks = [chuncks[i:i + 3] for i in range(0, n-3, 3)]
        addresses = [chunck[0] for chunck in chuncks]
        data = [(chunck[1] << 8) | (chunck[2]) for chunck in chuncks]
    elif chunck_size == 5:
        chuncks = [chuncks[i:i + 5] for i in range(0, n-5, 5)]
        addresses = [chunck[0] for chunck in chuncks]
        data = [(chunck[1] << 8 * 3) | (chunck[2] << 8 * 2) | (chunck[3] << 8 * 1) | (chunck[4]) for chunck in chuncks]
    else:
        raise(AbacusError("Input string is not valid chunck size must either be 3 or 5."))
    return addresses, data
    # else:
    #     if pyAbacus.constants.DEBUG: print("CheckSumError")
    #     return [], []

def dataArraysToCounters(abacus_port, addresses, data):
    """Saves in local memory the values of device's counters.

    Args:
        abacus_port: device port.

        addresses: list of integers with device's register addresses.

        data: list of integers with device's register values.

    Returns:
        List of counter values as registered within the device.

    """
    global COUNTERS_VALUES
    for i in range(len(addresses)):
        COUNTERS_VALUES[abacus_port].setValueFromArray(addresses[i], data[i])
    return COUNTERS_VALUES[abacus_port]

def dataArraysToSettings(abacus_port, addresses, data):
    """Saves in local memory the values of device's settings.

    Args:
        abacus_port: device port.

        addresses: list of integers with device's register addresses.

        data: list of integers with device's register values.

    Returns:
        List of settings as registered within the device.

    """
    global SETTINGS
    for i in range(len(addresses)):
        SETTINGS[abacus_port].setValueFromArray(addresses[i], data[i])
    return SETTINGS[abacus_port]

def getAllCounters(abacus_port):
    """Reads all counters from a Tausand Abacus device.

    With a single call, this function reads all the counters within the device, including single-channel counters, 2-fold coincidence counters and multi-fold coincidence counters.

    Example:

        counters, counters_id = getAllCounters('COM3')

        Reads data from the device in port 'COM3', and might return for example,

        | counters = COUNTERS VALUES: 37
        |    A: 1023
        |    B: 1038
        |    AB: 201

        meaning that this is the 37th measurement made by the device, and the measurements were 1023 counts in A, 1038 counts in B, and 201 coincidences between A and B.

    Args:
        abacus_port: device port.

    Returns:
        CountersValues class object including counter values as registered within the device, and the sequential number of the reading.

    """
    global COUNTERS_VALUES
    n = ABACUS_SERIALS[abacus_port].getNChannels()
    counters = COUNTERS_VALUES[abacus_port]
    if n == 2:
        writeSerial(abacus_port, READ_VALUE, 24, 6)
        data = readSerial(abacus_port)
        array, datas = dataStreamToDataArrays(data)
        dataArraysToCounters(abacus_port, array, datas)
    else:
        multiple_a = []
        multiple_d = []
        addresses_and_nchannels = [(0, 4), (9, 3), (18, 2), (27, 0), (96, 0)]
        for info in addresses_and_nchannels:
            writeSerial(abacus_port, READ_VALUE, *info)
            data = readSerial(abacus_port)
            array, datas = dataStreamToDataArrays(data, chunck_size = 5)
            multiple_a += array
            multiple_d += datas
        dataArraysToCounters(abacus_port, multiple_a, multiple_d)
    return COUNTERS_VALUES[abacus_port], getCountersID(abacus_port)

def getFollowingCounters(abacus_port, counters):
    """
    """
    global COUNTERS_VALUES
    if len(counters) > 0:
        n = ABACUS_SERIALS[abacus_port].getNChannels()
        counter = COUNTERS_VALUES[abacus_port]
        address = ADDRESS_DIRECTORIES[abacus_port]
        if n == 2:
            counters = ["counts_%s_LSB"%c for c in counters]
            multiple_a = []
            multiple_d = []
            for c in counters:
                writeSerial(abacus_port, READ_VALUE, address[c], 2)
                data = readSerial(abacus_port)
                array, datas = dataStreamToDataArrays(data)
                multiple_a += array
                multiple_d += datas
            dataArraysToCounters(abacus_port, multiple_a, multiple_d)
        else:
            single_double = ["counts_%s"%c for c in counters if len(c) < 3]
            multiple = ["custom_c%d"%(i + 1) for i in range(len(counters) - len(single_double))]
            counters = single_double + multiple
            multiple_a = []
            multiple_d = []
            for c in counters:
                writeSerial(abacus_port, READ_VALUE, address[c], 0)
                data = readSerial(abacus_port)
                array, datas = dataStreamToDataArrays(data, chunck_size = 5)
                multiple_a += array
                multiple_d += datas
            dataArraysToCounters(abacus_port, multiple_a, multiple_d)
    return COUNTERS_VALUES[abacus_port], getCountersID(abacus_port)

def getAllSettings(abacus_port):
    """Reads all settings from a Tausand Abacus device.

    With a single call, this function reads all the settings within the device, including sampling time, coincidence window, delay per channel and sleep time per channel.

    Example:
        settings = getAllSettings('COM3')

        Reads settings from the device in port 'COM3', and might return for example,

        |  delay_A (ns): 0
        |  delay_B (ns): 20
        |  sleep_A (ns): 0
        |  sleep_B (ns): 0
        |  coincidence_window (ns): 10
        |  sampling (ms): 1300

    Args:
        abacus_port: device port.

    Returns:
	Settings2ch, Settings4ch or Settings8ch class object including all setting values as registered within the device.
    """
    global SETTINGS
    def get(abacus_port, first, last, chunck_size):
        writeSerial(abacus_port, READ_VALUE, first, last - first + 1)
        data = readSerial(abacus_port)
        array, datas = dataStreamToDataArrays(data, chunck_size)
        dataArraysToSettings(abacus_port, array, datas)

    tp =  type(SETTINGS[abacus_port])

    if tp is Settings2Ch:
        first = ADDRESS_DIRECTORY_2CH["delay_A_ns"]
        last = ADDRESS_DIRECTORY_2CH["coincidence_window_s"]
        get(abacus_port, first, last, 3)
    elif tp is Settings4Ch:
        first = ADDRESS_DIRECTORY_8CH["delay_A"]
        last = ADDRESS_DIRECTORY_8CH["delay_D"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["sleep_A"]
        last = ADDRESS_DIRECTORY_8CH["sleep_D"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["sampling"]
        last = ADDRESS_DIRECTORY_8CH["coincidence_window"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["config_custom_c1"]
        get(abacus_port, first, first, 5)
    elif tp is Settings8Ch:
        first = ADDRESS_DIRECTORY_8CH["delay_A"]
        last = ADDRESS_DIRECTORY_8CH["delay_H"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["sleep_A"]
        last = ADDRESS_DIRECTORY_8CH["sleep_H"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["sampling"]
        last = ADDRESS_DIRECTORY_8CH["coincidence_window"]
        get(abacus_port, first, last, 5)
        first = ADDRESS_DIRECTORY_8CH["config_custom_c1"]
        last = ADDRESS_DIRECTORY_8CH["config_custom_c8"]
        get(abacus_port, first, last, 5)

    return SETTINGS[abacus_port]

def getSetting(abacus_port, setting):
    """Get a single configuration setting within a Tausand Abacus.

    Args:
        abacus_port: device port

        setting: name of the setting to be written. Valid strings are: "sampling", "coincidence_window", "delay_N", "sleep_N", where "N" refers to a channel (A,B,C,D,...).

    Returns:
        value for the setting. For "sampling", value in ms; for other settings, value in ns.

    """
    global SETTINGS

    settings = SETTINGS[abacus_port]
    if type(settings) is Settings2Ch:
        addr, val = settings.getAddressAndValue(setting + "_ns")
        writeSerial(abacus_port, READ_VALUE, addr, 4)

    else:
        addr, val = settings.getAddressAndValue(setting)
        writeSerial(abacus_port, READ_VALUE, addr, 0)

    data = readSerial(abacus_port)
    if ABACUS_SERIALS[abacus_port].getNChannels() == 2:
        array, datas = dataStreamToDataArrays(data)
    else:
        array, datas = dataStreamToDataArrays(data, chunck_size = 5)
    dataArraysToSettings(abacus_port, array, datas)

    return SETTINGS[abacus_port].getSetting(setting)

def getIdn(abacus_port):
    """Reads the identifier string model (IDN) from a Tausand Abacus.

    Example:
        myidn = getIdn('COM3')

        | might return 
        |     myidn = "Tausand Abacus AB1002"

    Args:
        abacus_port: device port.

    Returns:
        IDN string.
    """
    global ABACUS_SERIALS
    return ABACUS_SERIALS[abacus_port].getIdn()

def getCountersID(abacus_port):
    """Reads the *counters_id* (consecutive number of measurements) in a Tausand Abacus.

    When a new configuration is set, *counters_id=0*, indicating no valid data is available.

    Each time a new set of valid measurements is available, *counters_id* increments 1 unit.

    *counters_id* overflows at 1 million, starting over at *counters_id=1*.

    Args:
        abacus_port: device port.

    Returns:
        integer, *counters_id* value.
    
    """
    global COUNTERS_VALUES, ADDRESS_DIRECTORIES

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORIES[abacus_port]["dataID"], 0)
    data = readSerial(abacus_port)
    if ABACUS_SERIALS[abacus_port].getNChannels() == 2:
        array, datas = dataStreamToDataArrays(data)
    else:
        array, datas = dataStreamToDataArrays(data, chunck_size = 5)
    if datas:
        COUNTERS_VALUES[abacus_port].setCountersID(datas[0])
    return COUNTERS_VALUES[abacus_port].getCountersID()

def getTimeLeft(abacus_port):
    """Reads the remaining time for the next measurement to be ready, in ms.

    Args:
        abacus_port: device port

    Returns:
        integer, in ms, of time left for next measurement.

    """
    global COUNTERS_VALUES, ADDRESS_DIRECTORIES

    writeSerial(abacus_port, READ_VALUE, ADDRESS_DIRECTORIES[abacus_port]["time_left"], 0)
    data = readSerial(abacus_port)
    if ABACUS_SERIALS[abacus_port].getNChannels() == 2:
        array, datas = dataStreamToDataArrays(data)
    else:
        array, datas = dataStreamToDataArrays(data, chunck_size = 5)
    COUNTERS_VALUES[abacus_port].setTimeLeft(datas[0])
    return COUNTERS_VALUES[abacus_port].getTimeLeft()

def setSetting(abacus_port, setting, value):
    """Sets a configuration setting within a Tausand Abacus.

    Example:
        setSetting('COM3' , 'sampling' , 1300)

        sets the sampling time to 1300 ms to a device in port 'COM3'.

    Args:
        abacus_port: device port

        setting: name of the setting to be written. Valid strings are: "sampling", "coincidence_window", "delay_N", "sleep_N", where "N" refers to a channel (A,B,C,D,...).

        value: new value for the setting. For "sampling", value in ms; for other settings, value in ns.

    """
    global SETTINGS
    settings = SETTINGS[abacus_port]
    settings.setSetting(setting, value)

    if type(settings) is Settings2Ch:
        suffix = ["_ns", "_us", "_ms", "_s"]
        for s in suffix:
            addr, val = settings.getAddressAndValue(setting + s)
            writeSerial(abacus_port, WRITE_VALUE, addr, val)
    else:
        addr, val = settings.getAddressAndValue(setting)
        writeSerial(abacus_port, WRITE_VALUE, addr, val)

def setAllSettings(abacus_port, new_settings):
    """
    """
    global SETTINGS
    if type(new_settings) is Settings2Ch:
        SETTINGS[abacus_port] = new_settings
        for setting in SETTINGS[abacus_port].addresses.values():
            addr, val = SETTINGS[abacus_port].getAddressAndValue(setting)
            writeSerial(abacus_port, WRITE_VALUE, addr, val)
    else:
        raise(Exception("New settings are not a valid type."))

def waitForAcquisitionComplete(abacus_port, print_on = False, max_try=6, max_wait_s=10): #new on v1.1.1 (2021-02-28)
    """Waits for a new set of valid data to be available within a Tausand Abacus.

    Args:
        abacus_port: device port

        print_on: bool When True, prints information of the waiting process

        max_try: positive integer number, indicating the maximum trials to recover a communication issue

        max_wait_s: timeout maximum number of seconds to wait. Once this time is reached, the function ends.

    Returns:
        0  if wait has suceeded.        
        -1 if timeout has been reached.

    """
    begin_time = time.time()
    id_start = 0
    id_new = 0
    time_to_wait_ms = 0

    #max_try must be a positive integer
    max_try = int(max_try)
    if max_try < 1:
        max_try = 1

    #max_wait_s must be positive
    if max_wait_s < 0:
        max_wait_s = 0 #'0' means 'do not wait'

    #Step 1: get initial ID
    for attempt in range(max_try):    #retry up to 'max_try' times
        try:
            id_start = getCountersID(abacus_port)
        except CheckSumError:
            pass #data integrity error found: retry
        except (serial.serialutil.SerialException,KeyError):
            #serial communication error found: retry
            close(abacus_port)
            try:
                open(abacus_port)   #self recovery for lost communication
            except:
                pass
        except:
            raise
        else:
            break #done, continue
    if attempt == (max_try-1): #if number of attempts reached max_try
        if print_on:
            print("Communication error after",max_try,"attempts.")

    new_and_valid_id = False
    while (new_and_valid_id == False):
        #Step 2: get time to wait
        for attempt in range(max_try):    #retry up to 'max_try' times
            try:
                time_to_wait_ms = getTimeLeft(abacus_port)   
            except CheckSumError:
                pass #data integrity error found: retry
            except (serial.serialutil.SerialException,KeyError):
                #serial communication error found: retry
                close(abacus_port)
                try:
                    open(abacus_port)   #self recovery for lost communication
                except:
                    pass
            except:
                raise
            else:
                break #done, continue
        if attempt == (max_try-1): #if number of attempts has reached max_try
            if print_on:
                print("Communication error after",max_try,"attempts.")
            
        #Step 3: wait up to 500ms
        if time_to_wait_ms > 500:
            time_to_wait_ms = 500
        time.sleep(time_to_wait_ms/1000)
        if print_on:
            print(".", end='')

        #Step 4: read new ID
        for attempt in range(max_try):    #retry up to 'max_try' times
            try:
                id_new = getCountersID(abacus_port)
            except CheckSumError:
                pass #data integrity error found: retry
            except (serial.serialutil.SerialException,KeyError):
                #serial communication error found: retry
                close(abacus_port)
                try:
                    open(abacus_port)   #self recovery for lost communication
                except:
                    pass
            except:
                raise
            else:
                break #done, continue
        if attempt == (max_try-1): #if number of attempts has reached max_try
            if print_on:
                print("Communication error after",max_try,"attempts.")
            
        #Step 5: validation
        if id_new == 0:
            id_start = 0  #this case avoids to wait double for id=1 after id=0
        new_and_valid_id = (id_new > 0) and (id_start != id_new)

        #Step 6: max timeout validation
        if (time.time() - begin_time) > max_wait_s:
            if print_on:
                print(f'Waited {time.time() - begin_time:.2f}s,',f'max_wait={max_wait_s:.2f}s reached.',"Function waitForAcquisitionComplete ends.")
            return -1

    if print_on:
        print(f'Waited {time.time() - begin_time:.2f}s.',"Now data ID",id_new,"is available")
    return 0

def waitAndGetValues(abacus_port,channels,print_on = False, max_try=6, max_wait_s=10):#new on v1.1.1 (2021-02-28)
    """Waits and reads a new set of valid data from a Tausand Abacus.

    Example:
        counters, counter_id = waitAndGetValues('COM3',{'A','B','AC'})

        Waits for a new set of valid data to be available, related to the sampling time of the device.
        Then, reads the values of counts in A, B and the coincidences of AC, of the device connected in port COM3.
        Returns the requested counters within an array, for example
        | counters = [1023,1038,201]
        | counter_id = 37
        meaning that this is the 37th measurement made by the device, and the measurements were 1023 counts in A, 1038 counts in B, and 201 coincidences between A and C.

    Args:
        abacus_port: device port

        channels: list of upper case characters indicating the channel to be read. e.g. 'A' for singles in input A, 'AB' for coincidences between inputs A and B.

        print_on: bool When True, prints information of the waiting process

        max_try: positive integer number, indicating the maximum trials to recover a communication issue

        max_wait_s: timeout maximum number of seconds to wait. Once this time is reached, the function ends.

    Returns:
        counters, counters_id

        Set of read data, and their corresponding ID
        
        counters: array of integer values of counts in the selected channels

        counters_id: ID (consecutive number of measurements) field from a set of measurements.

    """
    waitForAcquisitionComplete(abacus_port,print_on = print_on, max_try=max_try, max_wait_s=max_wait_s)
    for attempt in range(max_try):    #retry up to 'maxretry' times
        try:
            counters, counters_id = getAllCounters(abacus_port)
            values = counters.getValues(channels)
            return values, counters_id
        except CheckSumError:
            pass #data integrity error found: retry
        except (serial.serialutil.SerialException,KeyError):
            #serial communication error found: retry
            close(abacus_port)
            try:
                open(abacus_port)   #self recovery for lost communication
            except:
                pass
        except:
            raise
        else:
            break #done, continue
    if attempt == (max_try-1): #if number of attempts reached max_try
        print("Communication error after",max_try,"attempts.")

    return [], -1

def findDevices(print_on = True):
    """Returns a list of connected and available devices that match with a Tausand Abacus.

    Scans all serial ports, and asks each of them their descriptions. When a device responds with a valid string, e.g. "Tausand Abacus AB1002", the port is inlcuded in the final answer. The constant DEVICES is updated with the dictionary of valid devices.

    Args:
        print_on: bool When True, prints devices information.

    Returns:
        ports, len(ports)
        List of valid ports, and its length.
        ports is a dictionary where the keys are the identifier strings of the devices (e.g. "Tausand Abacus AB1004"), and the values are the corresponding pyserial port (e.g. 'COM8', or '/dev/ttyACM0').
    """
    global CURRENT_OS, DEVICES
    ports_objects = list(find_ports.comports())
    ports = {}
    keys = []
    for i in range(len(ports_objects)):
        port = ports_objects[i]
        attrs = ["device", "name", "description", "hwid", "vid", "pid",
         "serial_number", "location", "manufacturer", "product", "interface"]

        if print_on:
            for attr in attrs:
                print(attr + ":", eval("port.%s"%attr))
        try:
            serial = AbacusSerial(port.device)
            idn = serial.getIdn()
            if CURRENT_OS in {"win32","cygwin","msys"}: #modified on v1.1
                #in windows, COM port serves as unique identifier of device
                keys = list(renameDuplicates(keys + [idn+" ("+port.device+")"])) #key assignment: 'Tausand Abacus ABxxxx (COMx)'
            else: #linux
                #in linux, serial number serves as unique identifier of device
                if port.serial_number is None: #new on 2021-06-28
					#if no serial number exist, assign only by IDN string
                    keys = list(renameDuplicates(keys + [idn])) #key assignment: 'Tausand Abacus ABxxxx'
                else:
					#if a serial number exist, add it to the description
                    keys = list(renameDuplicates(keys + [idn+" (S/N:"+port.serial_number+")"])) #key assignment: 'Tausand Abacus ABxxxx (S/N: serial_number)'
            ports[keys[-1]] = port.device #value assignment: 'COMx' or '/dev/ttyxxx'
            serial.close()
        except AbacusError:
            pass
        except Exception as e:
            print(port.device, e)
    DEVICES = ports
    return ports, len(ports)

def getPhysicalPort(abacus_port): #new on v1.1 (2020-06-23)
    """
	Reads the physical port at the specified serial port.
    """
    global ABACUS_SERIALS
    return ABACUS_SERIALS[abacus_port].port

def renameDuplicates(old):
    """
    """
    seen = {}
    for x in old:
        if x in seen:
            seen[x] += 1
            yield "%s-%d" % (x, seen[x])
        else:
            seen[x] = 0
            yield x

def customBinaryToLetters(number):
    binary = bin(number)[2:]
    n = len(binary)
    if n < 8: binary = '0' * (8 - n) + binary
    letters = [chr(i + ord('A')) for i in range(8) if binary[i] == '1']
    return ''.join(letters)

def customLettersToBinary(letters):
    valid = [chr(i + ord('A')) for i in range(8)]
    numbers = ['1' if valid[i] in letters else '0' for i in range(8)]
    number = int('0b' + ''.join(numbers), base = 2)
    return number

def setConstantsByResolution(resolution_ns): #new on v1.1 (2020-04-23)
    global COINCIDENCE_WINDOW_MINIMUM_VALUE,COINCIDENCE_WINDOW_STEP_VALUE,DELAY_STEP_VALUE,SLEEP_STEP_VALUE
    if not resolution_ns in [1,2,5]:
        raise(BaseError("%d ns is not a valid resolution (1, 2, 5)."%resolution_ns))
    else:
        #update local variables linked to device resolution
        COINCIDENCE_WINDOW_MINIMUM_VALUE = resolution_ns
        COINCIDENCE_WINDOW_STEP_VALUE = resolution_ns
        DELAY_STEP_VALUE = resolution_ns
        SLEEP_STEP_VALUE = resolution_ns
        #update constants in pyAbacus library
        pyAbacus.constants.COINCIDENCE_WINDOW_MINIMUM_VALUE = COINCIDENCE_WINDOW_MINIMUM_VALUE
        pyAbacus.constants.COINCIDENCE_WINDOW_STEP_VALUE = COINCIDENCE_WINDOW_STEP_VALUE
        pyAbacus.constants.DELAY_STEP_VALUE = DELAY_STEP_VALUE
        pyAbacus.constants.SLEEP_STEP_VALUE = SLEEP_STEP_VALUE
    if pyAbacus.constants.DEBUG:
        print("Constant values linked to device resolution:")
        print("  COINCIDENCE_WINDOW_MINIMUM_VALUE:",COINCIDENCE_WINDOW_MINIMUM_VALUE)
        print("  COINCIDENCE_WINDOW_STEP_VALUE:",COINCIDENCE_WINDOW_STEP_VALUE)
        print("  DELAY_STEP_VALUE:",DELAY_STEP_VALUE)
        print("  SLEEP_STEP_VALUE:",SLEEP_STEP_VALUE)

class CountersValues(object):
    """Keeps a set of measurements from counters within a device.
    """
    def __init__(self, n_channels):
        if not n_channels in [2, 4, 8]:
            raise(BaseError("%d is not a valid number of channels (2, 4, 8)."%n_channels))
        letters = [chr(ord('A') + i) for i in range(n_channels)]
        channels = []
        for i in range(1, 3): # n_channels + 1
            for item in combinations("".join(letters), i):
                item = "".join(item)
                channels.append(item)

        self.n_channels = n_channels
        self.channels_letters = channels

        if n_channels == 2:
            for c in channels:
                setattr(self, "%s_LSB"%c, 0)
                setattr(self, "%s_MSB"%c, 0)
        else:
            for c in channels:
                setattr(self, "%s"%c, 0)

        self.addresses = {}

        if n_channels == 2:
            directory = ADDRESS_DIRECTORY_2CH
        else:
            directory = ADDRESS_DIRECTORY_8CH

        for key in list(directory.keys()):
            for c in channels:
                txt = "counts_%s"%c
                if n_channels == 2:
                    if ("%s_LSB"%txt == key) or ("%s_MSB"%txt == key): pass
                    else: continue
                else:
                    if txt != key: continue
                addr = directory[key]
                self.addresses[addr] = key.replace("counts_", "")

        self.numeric_addresses = self.addresses.copy()

        if n_channels == 2:
            self.addresses[30] = 'dataID'
            self.addresses[31] = 'time_left'

        else:
            self.addresses[83] = 'dataID'
            self.addresses[84] = 'time_left'
            self.addresses[96] = 'custom_c1'
            if n_channels > 4:
                self.addresses[83] = 'dataID'
                self.addresses[84] = 'time_left'
                self.addresses[97] = 'custom_c2'
                self.addresses[98] = 'custom_c3'
                self.addresses[99] = 'custom_c4'
                self.addresses[100] = 'custom_c5'
                self.addresses[101] = 'custom_c6'
                self.addresses[102] = 'custom_c7'
                self.addresses[103] = 'custom_c8'

        self.counters_id = 0
        self.time_left = 0 #: in ms

    def setValueFromArray(self, address, value):
        """
        """
        setattr(self, self.addresses[address], value)

    def getValue(self, channel):
        """Gets a value of a single channel.

        Example:
            mycounters.getValue('A')

        Args:
            channel: upper case characters indicating the channel to be read. e.g. 'A' for singles in input A, 'AB' for coincidences between inputs A and B.

        Returns:
            integer value of counts in the selected channel
        """
        if self.n_channels == 2:
            msb = getattr(self, "%s_MSB" % channel) << 16
            lsb = getattr(self, "%s_LSB" % channel)

            return msb | lsb
        else:
            return getattr(self, "%s" % channel)

    def getValues(self, channels):
        """Gets an array of values of several channels.

        Example:
            mycounters.getValues({'A','B','AB'})

        Args:
            channels: list of upper case characters indicating the channel to be read. e.g. 'A' for singles in input A, 'AB' for coincidences between inputs A and B.

        Returns:
            array of integer values of counts in the selected channels
        """
	
        return [self.getValue(c) for c in channels]

    def getValuesFormatted(self, channels):
        """
        """
        values = ["%d"%v for v in self.getValues(channels)]
        return "(%d) "%self.getCountersID() + ", ".join(values)

    def getCountersID(self):
        """Gets the *counters_id* (consecutive number of measurements) field from a set of measurements.
        """
        return self.counters_id

    def setCountersID(self, id):
        """
        """
        self.counters_id = id

    def getTimeLeft(self):
        """Gets the *time_left* (time in ms for next measurement to be available) field from a set of measurements.
        """
        return self.time_left

    def setTimeLeft(self, time):
        """
        """
        self.time_left = time # ms

    def getNumericAddresses(self):
        """
        """
        return self.numeric_addresses

    def __repr__(self):
        values = ["\t%s: %d"%(i, self.getValue(i)) for i in self.channels_letters]
        text = "COUNTERS VALUES: %d\n"%self.getCountersID() + "\n".join(values)
        return text

class SettingsBase(object):
    def __init__(self):
        self.addresses = {}

    def setValueFromArray(self, address, value):
        """
        """
        setattr(self, self.addresses[address], value)

    def valueCheck(self, value, min, max, step):
        """
        """
        if (value >= min) and (value <= max) and (value % step == 0):
            return True
        else: return False

    def verifySetting(self, setting, value):
        """
        """
        if "delay" in setting:
            if not self.valueCheck(value, DELAY_MINIMUM_VALUE, \
                DELAY_MAXIMUM_VALUE, DELAY_STEP_VALUE):
                txt = "(%d <= %d delay (ns) <= %d) with steps of: %d"%(DELAY_MINIMUM_VALUE, \
                value, DELAY_MAXIMUM_VALUE, DELAY_STEP_VALUE)
                raise(InvalidValueError(txt))

        elif "sleep" in setting:
            if not self.valueCheck(value, SLEEP_MINIMUM_VALUE, \
                SLEEP_MAXIMUM_VALUE, SLEEP_STEP_VALUE):
                txt = "(%d <= %d sleep (ns) <= %d) with steps of: %d"%(SLEEP_MINIMUM_VALUE, \
                value, SLEEP_MAXIMUM_VALUE, SLEEP_STEP_VALUE)
                raise(InvalidValueError(txt))

        elif "coincidence_window" in setting: 
            if COINCIDENCE_WINDOW_MINIMUM_VALUE == 1 and value >= 10 and value % 2 != 0:
            # 15-07-2021 For increasing values starting at 10, the steps should be even for devices
            #            with 1ns resolution. Therefore, odd values shouldn't be allowed.
                txt = "Trying to set odd value for coincidence window (ns) in a range with even steps that starts with even number"
                raise(InvalidValueError(txt))
            elif not self.valueCheck(value, COINCIDENCE_WINDOW_MINIMUM_VALUE, \
                COINCIDENCE_WINDOW_MAXIMUM_VALUE, COINCIDENCE_WINDOW_STEP_VALUE):
                txt = " (%d <= %d coincidence window (ns) <= %d) with steps of: %d"%(COINCIDENCE_WINDOW_MINIMUM_VALUE, \
                value, COINCIDENCE_WINDOW_MAXIMUM_VALUE, COINCIDENCE_WINDOW_STEP_VALUE)
                raise(InvalidValueError(txt))

        elif "sampling" in setting:
            if not int(value) in SAMPLING_VALUES:
                sampling = ", ".join(["%d"%i for i in SAMPLING_VALUES])
                txt = ", sampling time must be one of the following: %s (ms)"%sampling
                raise(InvalidValueError(txt))

    def __repr__(self):
        values = ["\t%s"%(self.getSettingStr(c)) for c in self.channels]
        text = "SETTINGS[abacus_port]:\n" + "\n".join(values)
        return text

class Settings48Ch(SettingsBase):
    """
        4 and 8 channel devices use as time base a second. Nevertheless 2 channel uses ns for all timers with the exception of the sampling time (ms).
    """
    def __init__(self):
        super(Settings48Ch, self).__init__()

    def initAddreses(self):
        """
        """
        for c in self.channels:
            setattr(self, c, 0)

        keys = list(ADDRESS_DIRECTORY_8CH.keys())
        for c in self.channels:
            if c in keys:
                addr = ADDRESS_DIRECTORY_8CH[c]
                self.addresses[addr] = c

    def getChannels(self):
        """
        """
        return self.channels

    def setSetting(self, setting, value):
        """
            For all timers: value is in nanoseconds, for sampling in ms.
        """
        if 'custom' in setting:
            bits = customLettersToBinary(value)
        else:
            if setting == "sampling":
                if self.valueCheck(value, min(SAMPLING_VALUES), \
                    max(SAMPLING_VALUES), 1):
                    c, e = self.valueToExponentRepresentation(value / 1000)
                else:
                    raise(InvalidValueError("Sampling value of %d is not valid."%value))
            else:
                self.verifySetting(setting, value)
                c, e = self.valueToExponentRepresentation(value / int(1e9))
            bits = self.exponentsToBits(c, e)
        setattr(self, setting, bits)

    def getSetting(self, timer):
        """
            For all timers: returns nanoseconds, for sampling returns ms.
        """
        bits = getattr(self, timer)
        if 'custom' in timer:
            return customBinaryToLetters(bits)
        else:
            value = self.fromBitsToValue(bits)
            if timer == "sampling":
                return round(value * 1000) #improved in v1.1.1 to return int using python's round
            return round(value * int(1e9)) #improved in v1.1.1 to return int using python's round

    def getAddressAndValue(self, timer):
        """
        """
        return ADDRESS_DIRECTORY_8CH[timer], getattr(self, timer)

    def getSettingStr(self, timer):
        """
        """
        value = self.getSetting(timer)
        unit = "ns"
        if timer == "sampling": unit = "ms"
        if 'config_custom' in timer:
            return "%s: %s"%(timer, value)
        return "%s (%s): %d"%(timer, unit, value)

    def fromBitsToValue(self, bits):
        """
        """
        e = bits >> 12
        c = bits & 0xFFF
        return self.exponentRepresentationToValue(c, e)

    def exponentRepresentationToValue(self, c, e):
        """
        """
        return int(c) * 10 ** (int(e) - 10)

    def valueToExponentRepresentation(self, number):
        """
        """
        if number == 0:
            return 0, 0
        else:
            r = log10(number) + 10
            e = int(r)
            c = round(10 ** (r - e), 2)
            if (c < 10):
                e -= 1
                c *= 10
            c = int(c)
            if (e > 12) or (e < 0) or (c < 10) or (c > 99):
                raise(InvalidValueError(". %.1e is a value outside range."%number))
            n = self.exponentRepresentationToValue(c, e)
            if abs(n - number) < 1e-10:
                return c, e
            else:
                raise(InvalidValueError(". Only two signficant figures are posible %f"%number))

    def exponentsToBits(self, c, e):
        """
        """
        e = e << 12
        c = c & 0xFFF
        return e | c

class Settings2Ch(SettingsBase):
    """
    """
    def __init__(self):
        super(Settings2Ch, self).__init__()

        names = []
        self.channels = ['delay_A', 'delay_B', 'sleep_A', 'sleep_B', 'coincidence_window', 'sampling']
        for c in self.channels:
            names += ["%s_ns"%c, "%s_us"%c, "%s_ms"%c, "%s_s"%c]
        for c in names:
            setattr(self, c, 0)

        for key in list(ADDRESS_DIRECTORY_2CH.keys()):
            for c in self.channels:
                if c in key:
                    addr = ADDRESS_DIRECTORY_2CH[key]
                    self.addresses[addr] = key

    def setSetting(self, setting, value):
        """
        """
        self.verifySetting(setting, value)
        if "sampling" in setting:
            setattr(self, setting + "_ns", 0)
            setattr(self, setting + "_us", 0)
            setattr(self, setting + "_ms", value % 1000)
            setattr(self, setting + "_s", value // 1000)

        else:
            setattr(self, setting + "_ns", value % 1000)
            value = value // 1000
            setattr(self, setting + "_us", value % 1000)
            value = value // 1000
            setattr(self, setting + "_ms", value % 1000)
            setattr(self, setting + "_s", value // 1000)

    def getSetting(self, timer):
        """
        """
        ns = getattr(self, "%s_ns" % timer)
        us = getattr(self, "%s_us" % timer)
        ms = getattr(self, "%s_ms" % timer)
        s = getattr(self, "%s_s" % timer)
        if timer == "sampling": # ms
            return int(ms + s*1e3)
        else: # ns
            return int(ns + (us * 1e3) + (ms * 1e6) + (s * 1e9))

    def getAddressAndValue(self, timer):
        """
        """
        return ADDRESS_DIRECTORY_2CH[timer], getattr(self, timer)

    def getSettingStr(self, timer):
        """
        """
        value = self.getSetting(timer)
        unit = "ns"
        if timer == "sampling": unit = "ms"
        return "%s (%s): %d"%(timer, unit, value)

class Settings4Ch(Settings48Ch):
    """
        4 and 8 channel devices use as time base a second. Nevertheless 2 channel uses ns for all timers with the exception of the sampling time (ms).
    """
    def __init__(self):
        super(Settings4Ch, self).__init__()
        self.channels = ['delay_A', 'delay_B', 'delay_C', 'delay_D',
                        'sleep_A', 'sleep_B', 'sleep_C', 'sleep_D',
                        'coincidence_window', 'sampling', 'config_custom_c1']

        self.initAddreses()

class Settings8Ch(Settings48Ch):
    """
        4 and 8 channel devices use as time base a second. Nevertheless 2 channel uses ns for all timers with the exception of the sampling time (ms).
    """
    def __init__(self):
        super(Settings8Ch, self).__init__()
        self.channels = ['delay_A', 'delay_B', 'delay_C', 'delay_D',
                        'delay_E', 'delay_F', 'delay_G', 'delay_H',
                        'sleep_A', 'sleep_B', 'sleep_C', 'sleep_D',
                        'sleep_E', 'sleep_F', 'sleep_G', 'sleep_H',
                        'coincidence_window', 'sampling', 'config_custom_c1',
                        'config_custom_c2', 'config_custom_c3', 'config_custom_c4',
                        'config_custom_c5', 'config_custom_c6', 'config_custom_c7',
                         'config_custom_c8']

        self.initAddreses()

class AbacusSerial(serial.Serial):
    """
        Builds a serial port from pyserial.
    """
    def __init__(self, port):
        super(AbacusSerial, self).__init__(port, baudrate = BAUDRATE, timeout = TIMEOUT)
        self.idn = ""
        self.flush()
        if self.testDevice():
            self.n_channels = getChannelsFromName(self.getIdn())
            if pyAbacus.constants.DEBUG:
                print(port, "answered: %s"%self.getIdn())
                print(port, "number of channels: %d"%self.n_channels)
        else:
            if pyAbacus.constants.DEBUG:
                print(port, "answered: %s"%self.getIdn())
            self.close()
            raise(AbacusError("Not a valid abacus."))

    def flush(self):
        """
        """
        self.flushInput()
        self.flushOutput()

    def findIdn(self):
        """
        Requests the device for its string identificator (IDN) using serial port.
        """
        self.write(TEST_MESSAGE)
        self.idn = self.read(21).decode()
        time.sleep(1)
        return self.idn

    def getIdn(self):
        """
	Gets the device string identificator (IDN) from local memory.
        """
        return self.idn

    def testDevice(self):
        """
        """
        ans = self.findIdn()
        if TEST_ANSWER in ans: return True
        return False

    def writeSerial(self, command, address, data_16o32):
        """
        """
        if self.n_channels == 2:
            msb = (data_16o32 >> 8) & 0xFF
            lsb = data_16o32 & 0xFF
            message = [START_COMMUNICATION, command, address, msb, lsb, END_COMMUNICATION]
        else:
            bits = [(data_16o32 >> 8 * i) & 0xFF for i in range(3, -1, -1)]
            message = [START_COMMUNICATION, command, address] + bits + [END_COMMUNICATION]
        if pyAbacus.constants.DEBUG:
            print('writeSerial:', message)
        self.write(message)

    def readSerial(self):
        """
        """
        try:
            if self.read()[0] == 0x7E:
                numbytes = self.read()[0]
                bytes_read = list(self.read(numbytes))
                checksum = self.read()[0]
                message = [0x7E, numbytes] +  bytes_read + [checksum], numbytes + 3
                if pyAbacus.constants.DEBUG: print('readSerial:', message)
                return message
        except IndexError:
            pass
        if pyAbacus.constants.DEBUG:
            print("Error on readSerial")
        return [], 0

    def getNChannels(self):
        """Gets the number of input channels in the device.
        """
        return self.n_channels

class Stream(object):
    """
    """
    def __init__(self, abacus_port, counters, output_function = print):
        self.abacus_port = abacus_port
        self.counters = counters
        self.output_function = output_function
        self.stream_on = False
        self.exceptions = []
        self.all = False
        if len(counters) == ABACUS_SERIALS[abacus_port].getNChannels():
            self.all = True

    def threadFunc(self):
        # try:
        if self.all: counters, id = getAllCounters(self.abacus_port)
        else: counters, id = getFollowingCounters(self.abacus_port, self.counters)
        if id != 0:
            values = counters.getValuesFormatted(self.counters)
            self.output_function(values)

        while self.stream_on:
            # try:
            left = getTimeLeft(self.abacus_port)
            if self.all: counters, id2 = getAllCounters(self.abacus_port)
            else: counters, id2 = getFollowingCounters(self.abacus_port, self.counters)
            if id == id2:
                time.sleep(left / 1000)
                if self.all: counters, id = getAllCounters(self.abacus_port)
                else: counters, id = getFollowingCounters(self.abacus_port, self.counters)
            else: id = id2
            values = counters.getValuesFormatted(self.counters)
            self.output_function(values)
        # except Exception as e:
        #     self.exceptions.append(e)

    def start(self):
        """
        """
        self.stream_on = True
        self.thread = Thread(target = self.threadFunc, daemon = True)
        self.thread.start()

    def stop(self):
        """
        """
        self.stream_on = False

    def setCounters(self, counters):
        """
        """
        self.counters = counters
