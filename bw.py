# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
                        
from flask import Flask, render_template, abort, flash, redirect, url_for, g

class fakeGPIO(object):
    OUT = 0
    IN = 1
    BCM = 11
    HIGH = 1
    LOW = 0
    state = None
    
    def __init__(self):
        self.state = {"mode": None, "setup":{}, "pinstate":{}}
    
    def check_mode(self):
        if not self.state["mode"]:
            raise RuntimeError("No Mode set")
    
    def check_out(self, pin):
        self.check_mode()
        if not pin in self.state["setup"] or self.state["setup"][pin] != self.OUT:
            raise RuntimeError("The GPIO channel has not been set up as an OUTPUT")

    def check_in(self, pin):
        self.check_mode()
        if not pin in self.state["setup"]:
            raise RuntimeError("You must setup() the GPIO channel first")

    def setmode(self, mode):
        self.state["mode"] = mode
       
    def setup(self, pin, mode):
        self.check_mode()
        self.state["setup"][pin] = mode
        # IN are always 0, but OUT can change with output()...
        self.state["pinstate"][pin] = 0
       
    def output(self, pin, value):
        self.check_out(pin)
        self.state["pinstate"][pin] = value

    def input(self, pin):
        self.check_in(pin)
        return self.state["pinstate"][pin]
    

class WateringSystemObject(object):
    """thin wrapper to access the object"""
    
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
    
    @property
    def type(self):
        return self.parent.get_type(self.name)

    @property
    def state(self):
        return self.parent.get_state(self.name)
        
    def setup(self):
        self.parent.setup(self.name)
    
    def enable(self):
        self.parent.enable(self.name)

    def disable(self):
        self.parent.disable(self.name)

        
class WateringSystem(object):

    def __init__(self, config, gpio=None):
        self._config = config
        self.inputs = []
        self.outputs = []
        
        if gpio is None:
            try:
                import RPi.GPIO as GPIO
                self._GPIO = GPIO
                self._GPIO_TYPE = "real"
            except ImportError:
                self._GPIO = fakeGPIO()
                self._GPIO_TYPE = "fake"
        else:
            self._GPIO = gpio
        
        self._GPIO.setmode(self._GPIO.BCM)
        
        for name in self._config:
            app.logger.debug("Configuring %s", name)
            obj = WateringSystemObject(name, self)
            obj.setup()
            setattr(self, name, obj)
            if obj.type == "out":
                self.outputs.append(obj)
            else:
                self.inputs.append(obj)
    
    def get_type(self, name):
        if not name in self._config:
            raise RuntimeError("Unknown object: {0}".format(name))
        cobj = self._config[name]
        return cobj["mode"]

    def get_state(self, name):
        if not name in self._config:
            raise RuntimeError("Unknown object: {0}".format(name))
        cobj = self._config[name]
        if cobj["mode"] == "out":
            # make sure we get "revered" states
            ret = self._GPIO.input(cobj["pin"]) == int(cobj["enable"])
            #ret = self._GPIO.input(cobj["pin"])
        else:
            ret = self._GPIO.input(cobj["pin"])
        return ret
    
    def set_state(self, name, state):
        if not name in self._config:
            raise RuntimeError("Unknown object: {0}".format(name))
        cobj = self._config[name]
        if not cobj["mode"] == "out":
            raise RuntimeError("Wrong mode for object: {0}".format(name))
        self._GPIO.output(cobj["pin"], cobj[state])
        app.logger.debug("changed state for %s (pin %s): %s", name, cobj["pin"], state)
    
    def enable(self, name):
        self.set_state(name, "enable")
    
    def disable(self, name):
        self.set_state(name, "disable")
    
    def setup(self, name):
        if not name in self._config:
            raise RuntimeError("Unknown object: {0}".format(name))
        cobj = self._config[name]
        GPIO_mode = self._GPIO.OUT if cobj["mode"] == "out" else self._GPIO.IN
        self._GPIO.setup(cobj["pin"], GPIO_mode)
        if cobj["mode"] == "out":
            self.disable(name)
    
    def cleanup(self):
        app.logger.debug("cleanup called")
        pass


app = Flask(__name__)
app.config.from_pyfile('application.cfg', silent=True)
#app.config.from_envvar('BALCONYWATERING_SETTINGS', silent=True)

_WS = None
def get_ws():
    global _WS
    if _WS is None:
        _WS = g._watering_system = WateringSystem(app.config.get("WATERING_OBJECTS"))
    return _WS

#@app.teardown_appcontext
def close_ws(exception):
    global _WS
    if _WS is not None:
        _WS.cleanup()

@app.route('/')
def index():
    """Just a generic index page to show."""
    return render_template('index.html', ws=get_ws())
    
@app.route('/enable/<ws_obj>')
def enable(ws_obj):
    """Enable the watering object"""
    try:
        get_ws().enable(ws_obj)
        flash("Enabled '{0}'".format(ws_obj))
    except RuntimeError as e:
        msg = 'Watering system: object "{0}" is not available or not changeable ({1})'
        flash(msg.format(ws_obj, e))
        app.logger.warning(msg, ws_obj, e)
    return redirect(url_for('index'))

    
@app.route('/disable/<ws_obj>')
def disable(ws_obj):
    """Enable the watering object"""
    try:
        get_ws().disable(ws_obj)
        flash("Disabled '{0}'".format(ws_obj))
    except RuntimeError as e:
        msg = 'Watering system: object "{0}" is not available or not changeable ({1})'
        flash(msg.format(ws_obj, e))
        app.logger.warning(msg, ws_obj, e)
    return redirect(url_for('index'))

    
if __name__ == "__main__":
    # import RPi.GPIO as GPIO
    app.run(host="0.0.0.0")
