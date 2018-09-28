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
        self.p_formats = dict()
        self.p_units = dict()
        self.p_raw_units = dict()

        self.connected = False
        threading.Thread.__init__(self)
        self.reset_data()

        ## @var name
        # Name of the sensor
        self.name = None

        ## @var running
        # Variable controlling main loop. Should be set to True when starting the loop.
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

    def is_connected(self):
        return self.connected

    def stop(self):
        self.log.debug("Stop started", extra=self.extra)
        self.running = False

    def __del__(self):
        self.stop()
