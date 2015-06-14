import gpios
import logging
from datetime import datetime

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
        self._state = {}
        self.inputs = []
        self.outputs = []
        self.log = []
                       
        for name in self._config:
            logging.getLogger().debug("Configuring %s", name)
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
            # make sure we get "reversed" states
            ret = gpios.readpin(cobj["pin"]) == int(cobj["enable"])
            #ret = self._GPIO.input(cobj["pin"])
        else:
            ret = gpios.readpin(cobj["pin"])
        return ret
    
    def set_state(self, name, state):
        if not name in self._config:
            raise RuntimeError("Unknown object: {0}".format(name))
        cobj = self._config[name]
        if not cobj["mode"] == "out":
            raise RuntimeError("Wrong mode for object: {0}".format(name))
        gpios.writepin(cobj["pin"], cobj[state])
        if not self._state.get(name) or self._state[name]['state'] != state:
                self._state[name] = {'state': state, 'last_changed':datetime.utcnow()}
        logging.getLogger().debug("changed state for %s (pin %s): %s", name, cobj["pin"], state)
    
    def enable(self, name, stack = None):
        if stack and name in stack:
             logging.getLogger().error("Cycle detected while enabling '%s': %s", name, stack)
        depends = self._config[name].get("depends", None)
        if depends:
             if stack:
                  stack.append(name)
             else:
                  stack = [name]
             self.enable(depends, stack=[name])
        self.set_state(name, "enable")
    
    def disable(self, name, stack=None):
        if stack and name in stack:
             logging.getLogger().error("Cycle detected while enabling '%s': %s", name, stack)
        self.set_state(name, "disable")
        depends = self._config[name].get("depends", None)
        if depends:
             if stack:
                  stack.append(name)
             else:
                  stack = [name]
             self.disable(depends, stack=[name])
    
    def setup(self, name):
        if not name in self._config:
            raise RuntimeError("Unknown object: {0}".format(name))
        cobj = self._config[name]
        GPIO_mode = gpios.OUT if cobj["mode"] == "out" else gpios.IN
        try:
            gpios.export_pins(cobj["pin"])
        except RuntimeError as e:
            logging.getLogger().info("Pin for %s (pin %s) was already exported. This might be a problem with other apps on your rpi!", name, cobj["pin"])
        gpios.setpindirection(cobj["pin"], GPIO_mode)
        if cobj["mode"] == "out":
            self.disable(name)
    
    def cleanup(self):
        logging.getLogger().debug("cleanup called")
        pass


