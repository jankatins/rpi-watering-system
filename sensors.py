#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import RPi.GPIO as GPIO
import datetime
import sys
import signal


from models import SensorReadings, db

mygpiopin = 4 # the volume_counter pin

def signal_handler(signal, frame):
    GPIO.cleanup()
    sys.exit(0)

GPIO.setmode(GPIO.BCM)
GPIO.setup(mygpiopin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
signal.signal(signal.SIGINT, signal_handler) # SIGINT = interrupt by CTRL-C
signal.signal(signal.SIGTERM, signal_handler) # killed by systemd

import thread
import time

counter = 0

# Define a function for the thread
def count_volume(pin):
    global counter
    while True:
        GPIO.wait_for_edge(pin, GPIO.RISING)
        counter += 1
        GPIO.wait_for_edge(pin, GPIO.FALLING)

thread.start_new_thread( count_volume, (mygpiopin,))

old_counter = 0
    
while True:
    sr = SensorReadings(source="volume", value=counter-old_counter)
    db.session.add(sr)
    db.session.commit()
    print("added: %s (all: %s)" % (counter-old_counter, counter))
    old_counter = counter
    time.sleep(60)

