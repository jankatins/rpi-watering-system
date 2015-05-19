#!/usr/bin/env python
# coding=utf8
import os
import logging

IN = "in"
OUT = "out"
HIGH = 1
LOW = 0

if os.name == 'nt':
    state = {"exported":[], "setup":{}, "pinstate":{}}

    def check_exported(pin):
        if not str(pin) in state["exported"]:
            raise RuntimeError("Not exported: %s" % pin)
       
    def check_out(pin):
        check_exported(pin)
        if not pin in state["setup"] or state["setup"][pin] != OUT:
            raise RuntimeError("The GPIO channel has not been set up as an OUTPUT")

    def check_in(pin):
        check_exported(pin)
        if not pin in state["setup"]:
            raise RuntimeError("You must setup() the GPIO channel first")
        
    def export_pins(pins):
        pins = str(pins)
        state["exported"].extend(pins.split())
        logging.getLogger().debug("exported pins %s", pins)


    def unexport_pins(pins):
        pins = str(pins).split()
        try:
            for pin in pins:
                state["exported"].remove(pin)
                logging.getLogger().debug("unexported pin %s", pin)
        except:
            raise RuntimeError("GPIO %s is not found, so skipping unexport gpio" % (str(pins), ))


    def setpindirection(pin_no, pin_direction):
        state["setup"][pin_no] = pin_direction
        # IN are always 0, but OUT can change with output()...
        state["pinstate"][pin_no] = 0



    def writepin(pin_no, pin_value):
        check_out(pin_no)
        state["pinstate"][pin_no] = pin_value


    def readpin(pin_no):
        check_in(pin_no)
        return state["pinstate"][pin_no]


else:
    def export_pins(pins):
        try:
            f = open("/sys/class/gpio/export", "w")
            f.write(str(pins))
            f.close()
        except IOError:
            raise RuntimeError(
                "GPIO %s already Exists, so skipping export gpio" % (str(pins), ))
        except:
            raise RuntimeError("ERR: export_pins()")


    def unexport_pins(pins):
        try:
            f = open("/sys/class/gpio/unexport", "w")
            f.write(str(pins))
            f.close()
        except IOError:
            raise RuntimeError(
                "GPIO %s is not found, so skipping unexport gpio" % (str(pins), ))
        except:
            raise RuntimeError("ERR: unexport_pins()")


    def setpindirection(pin_no, pin_direction):
        try:
            gpiopin = "gpio%s" % (str(pin_no), )
            pin = open("/sys/class/gpio/" + gpiopin + "/direction", "w")
            pin.write(pin_direction)
            pin.close()
        except:
            raise RuntimeError("ERR: setpindirection()")


    def writepin(pin_no, pin_value):
        try:
            gpiopin = "gpio%s" % (str(pin_no), )
            pin = open("/sys/class/gpio/" + gpiopin + "/value", "w")
            if pin_value == 1:
                pin.write("1")
            else:
                pin.write("0")
            pin.close()
        except:
            raise RuntimeError("ERR: writepins()")


    def readpin(pin_no):
        try:
            gpiopin = "gpio%s" % (str(pin_no), )
            pin = open("/sys/class/gpio/" + gpiopin + "/value", "r")
            value = pin.read()
            logging.getLogger().debug("The value on the PIN %s is : %s", str(pin_no), str(value))
            pin.close()
            return int(value)
        except:
            raise RuntimeError("ERR: readpins()")

if __name__ == '__main__':
    from time import sleep
    export_pins(32)
    setpindirection(32, "out")

    while(1):
        writepin(32, 1)
        sleep(1)
        writepin(32, 0)
        sleep(1)
