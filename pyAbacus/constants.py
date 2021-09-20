#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

CURRENT_OS = sys.platform #: Current operative system

ADDRESS_DIRECTORY_2CH = {'delay_A_ns': 0,
           'delay_A_us': 1,
           'delay_A_ms': 2,
           'delay_A_s': 3,
           'delay_B_ns': 4,
           'delay_B_us': 5,
           'delay_B_ms': 6,
           'delay_B_s': 7,
           'sleep_A_ns': 8,
           'sleep_A_us': 9,
           'sleep_A_ms': 10,
           'sleep_A_s': 11,
           'sleep_B_ns': 12,
           'sleep_B_us': 13,
           'sleep_B_ms': 14,
           'sleep_B_s': 15,
           'sampling_ns': 16,
           'sampling_us': 17,
           'sampling_ms': 18,
           'sampling_s': 19,
           'coincidence_window_ns': 20,
           'coincidence_window_us': 21,
           'coincidence_window_ms': 22,
           'coincidence_window_s': 23,
           'counts_A_LSB': 24,
           'counts_A_MSB': 25,
           'counts_B_LSB': 26,
           'counts_B_MSB': 27,
           'counts_AB_LSB': 28,
           'counts_AB_MSB': 29,
           'dataID': 30,
           'time_left': 31} #: Memory addresses

ADDRESS_DIRECTORY_8CH = {'counts_A': 0,
           'counts_AB': 1,
           'counts_AC': 2,
           'counts_AD': 3,
           'counts_AE': 4,
           'counts_AF': 5,
           'counts_AG': 6,
           'counts_AH': 7,
           # 8
           'counts_B': 9,
           'counts_BC': 10,
           'counts_BD': 11,
           'counts_BE': 12,
           'counts_BF': 13,
           'counts_BG': 14,
           'counts_BH': 15,
           # 16
           # 17
           'counts_C': 18,
           'counts_CD': 19,
           'counts_CE': 20,
           'counts_CF': 21,
           'counts_CG': 22,
           'counts_CH': 23,
           # 24
           # 25
           # 26
           'counts_D': 27,
           'counts_DE': 28,
           'counts_DF': 29,
           'counts_DG': 30,
           'counts_DH': 31,
           # 32
           # 33
           # 34
           # 35
           'counts_E': 36,
           'counts_EF': 37,
           'counts_EG': 38,
           'counts_EH': 39,
           # 40
           # 41
           # 42
           # 43
           # 44
           'counts_F': 45,
           'counts_FG': 46,
           'counts_FH': 47,
           # 48
           # 49
           # 50
           # 51
           # 52
           # 53
           'counts_G': 54,
           'counts_GH': 55,
           # 56
           # 57
           # 58
           # 59
           # 60
           # 61
           # 62
           'counts_H': 63,
           'delay_A': 64,
           'delay_B': 65,
           'delay_C': 66,
           'delay_D': 67,
           'delay_E': 68,
           'delay_F': 69,
           'delay_G': 70,
           'delay_H': 71,
           'sleep_A': 72,
           'sleep_B': 73,
           'sleep_C': 74,
           'sleep_D': 75,
           'sleep_E': 76,
           'sleep_F': 77,
           'sleep_G': 78,
           'sleep_H': 79,
           'sampling': 80,
           'coincidence_window': 81,
           'dataID': 83,
           'time_left': 84,
           # 85
           # 86
           # 87
           'config_custom_c1': 88,
           'config_custom_c2': 89,
           'config_custom_c3': 90,
           'config_custom_c4': 91,
           'config_custom_c5': 92,
           'config_custom_c6': 93,
           'config_custom_c7': 94,
           'config_custom_c8': 95,
           'custom_c1': 96,
           'custom_c2': 97,
           'custom_c3': 98,
           'custom_c4': 99,
           'custom_c5': 100,
           'custom_c6': 101,
           'custom_c7': 102,
           'custom_c8': 103,
           }
           # 'measure_number': 30,
           # 'time_to_next_sample': 31} #: Memory addresses

# ADDRESS_DIRECTORY = ADDRESS_DIRECTORY_2CH

ADDRESS_DIRECTORIES = {}

READ_VALUE = 0x0e #: Reading operation signal
WRITE_VALUE = 0x0f #: Writing operation signal
START_COMMUNICATION = 0x02 #: Begin message signal
END_COMMUNICATION = 0x04 #: End of message
MAXIMUM_WRITING_TRIES = 20 #: Number of tries done to write a value


COINCIDENCE_WINDOW_MINIMUM_VALUE = 5 #: Minimum coincidence window time value (ns).
COINCIDENCE_WINDOW_MAXIMUM_VALUE = 10000 #: Maximum coincidence window time value (ns).
COINCIDENCE_WINDOW_STEP_VALUE = 5 #: Increase ratio on the coincidence window time value (ns).
COINCIDENCE_WINDOW_DEFAULT_VALUE = 10 #: Default coincidence window time value (ns).

DELAY_MINIMUM_VALUE = 0 #: Minimum delay time value (ns).
DELAY_MAXIMUM_VALUE = 100 #: Maximum delay time value (ns).
DELAY_STEP_VALUE = 5 #: Increase ratio on the delay time value (ns).
DELAY_DEFAULT_VALUE = 0 #: Default delay time value (ns).

SLEEP_MINIMUM_VALUE = 0 #: Minimum sleep time value (ns).
SLEEP_MAXIMUM_VALUE = 100 #: Maximum sleep time value (ns).
SLEEP_STEP_VALUE = 5 #: Increase ratio on the sleep time value (ns).
SLEEP_DEFAULT_VALUE = 0 #: Default sleep time value (ns).

coeff = [1, 2, 5]
SAMPLING_VALUES = [int(c*10**i) for i in range(6) for c in coeff] + [int(1e6)] #: From (1, 2, 5) ms to 1000 s
SAMPLING_DEFAULT_VALUE = 1000 #: Default sampling time value (ms)

SETTINGS = {} #: Global settings variable
COUNTERS_VALUES = {} #: Global counters values variable

BAUDRATE = 115200 #: Default baudrate for the serial port communication
TIMEOUT = 0.5 #: Maximum time without answer from the serial port
BOUNCE_TIMEOUT = 1 #: Number of times a specific transmition is tried

TEST_MESSAGE = "*IDN?".encode()
TEST_ANSWER = "Tausand Abacus"

DEVICES = {}
ABACUS_SERIALS = {}

status_message = None

DEBUG = False
