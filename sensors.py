#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import sys
import signal

import RPi.GPIO as GPIO
import spidev

from models import SensorReadings, db

enable_volume = False
volume_pin = 4 # the volume_counter pin

enable_moisture = True
moisture_channels = [(0, "front"),(1, "tomatos")]


spi = spidev.SpiDev()
spi.open(0,0)

# Function to read SPI data from MCP3008 chip
# Channel must be an integer 0-7
def read_channel(channel):
  adc = spi.xfer2([1,(8+channel)<<4,0])
  data = ((adc[1]&3) << 8) + adc[2]
  return data

def signal_handler(signal, frame):
    GPIO.cleanup()
    spi.close() 
    sys.exit(0)

GPIO.setmode(GPIO.BCM)
GPIO.setup(volume_pin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
signal.signal(signal.SIGINT, signal_handler) # SIGINT = interrupt by CTRL-C
signal.signal(signal.SIGTERM, signal_handler) # killed by systemd

import thread
import time

counter = 0
old_counter = 0

# Define a function for the thread
def count_volume(pin):
    global counter
    while True:
        GPIO.wait_for_edge(pin, GPIO.RISING)
        counter += 1
        GPIO.wait_for_edge(pin, GPIO.FALLING)

thread.start_new_thread( count_volume, (volume_pin,))


moisture_cache = {}
for ch, name in moisture_channels:
    moisture_cache[name] = [] 

moisture_interval = 10
cur_moisture_interval = 0

    
while True:
    if enable_volume:
        sr = SensorReadings(source="volume", value=counter-old_counter)
        db.session.add(sr)
        db.session.commit()
        #print("Volume: added: %s (all: %s)" % (counter-old_counter, counter))
        old_counter = counter

    if enable_moisture:
        cur_moisture_interval += 1

        # read in every minute, but only into a cache
        for channel, name in moisture_channels:
            value = read_channel(channel)
            moisture_cache[name].append(value)

        # only submit a moving avarage every Xmin
        # -> don't overfill the db... 
        if cur_moisture_interval > moisture_interval:
            for channel, name in moisture_channels:
                vals =  moisture_cache[name]
                moisture_cache[name] = []
                value = int(sum(vals)/len(vals))
                sr = SensorReadings(source=name, value=value)
                db.session.add(sr)
            db.session.commit()
            cur_moisture_interval = 0
            #print("%s: added: %s" % (name, value))
    time.sleep(60)

