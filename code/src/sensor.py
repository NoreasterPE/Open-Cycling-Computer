#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package sensor
#  Abstract base class for all sensors.
import logging
import threading


## Abstract base class for sensors
class sensor(threading.Thread):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'a_sensor'}

    def __init__(self):
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')
        threading.Thread.__init__(self)

        self.p_formats = dict()
        self.p_units = dict()
        self.p_raw_units = dict()
        ## @var params_required
        # List of params required by the sensor to work properly
        self.required = list()

        ## @var connected
        # Variable indicating it the sensor hardware is currently connected
        self.connected = False
        self.reset_data()

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
            pass
            # Copy the above code to a real sensor code and replace pass with whatewer the sensor needs to provide data
        self.log.debug("Main loop finished", extra=self.extra)

    def get_prefix(self):
        return self.extra["module_name"]

    def get_raw_data(self):
        self.log.debug('get_raw_data called', extra=self.extra)
        return dict(name=self.name,
                    time_stamp=self.time_stamp)

    def reset_data(self):
        pass

    def get_raw_units(self):
        return self.p_raw_units

    def get_units(self):
        return self.p_units

    def get_formats(self):
        return self.p_formats

    ## Return list of parameters required be a sensor to fully work. I.e. pressure sensor might need home altitude to calculate current altitude
    #  @param self The python object self
    def get_required(self):
        return self.required

    ## Useb by module "sensors" to notify about change of a reqired parameter. Overwrite with code that needs to be executed on change of the parameters.
    #  @param self The python object self
    #  @param reqired Dict with new values for require parameters
    def notification(self, required):
        pass

    def is_connected(self):
        return self.connected

    def stop(self):
        self.log.debug("Stop started", extra=self.extra)
        self.running = False

    def __del__(self):
        self.stop()
