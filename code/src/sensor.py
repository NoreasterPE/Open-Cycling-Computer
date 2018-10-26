#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package sensor
#  Abstract base class for all sensors.
import logging
import threading
import numbers
import time


## Abstract base class for sensors
class sensor(threading.Thread):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'a_sensor'}

    def __init__(self):
        super().__init__()
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')

        ## @var params_required
        # Dict with params required by the sensor to work properly
        self.required = dict()

        ## @var connected
        # Variable indicating it the sensor hardware is currently connected
        self.connected = False
        #self.reset_data()

        ## @var name
        # Name of the sensor
        self.name = None

        ## @var running
        # Variable controlling the main loop. Should be set to True when starting the loop.
        self.running = False

    def run(self):
        self.log.debug("Starting the main loop", extra=self.extra)
        self.running = True
        while self.running:
            time.sleep(10)
            # Copy the above code to a real sensor code and replace sleep with whatewer the sensor needs to provide data
        self.log.debug("Main loop finished", extra=self.extra)

    ## Resets all parameters to the default values
    #  @param self The python object self
    def reset_data(self):
        pass

    ## Useb by module "sensors" to notify about change of a reqired parameter. Overwrite with code that needs to be executed on change of the parameters.
    #  @param self The python object self
    #  @param reqired Dict with new values for require parameters
    def notification(self):
        pass

    def is_connected(self):
        return self.connected

    def stop(self):
        self.log.debug("Stop started", extra=self.extra)
        self.running = False
