#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package sensor
#  Abstract base class for all sensors.
import logging
import threading

M = {'module_name': 'a_sensor'}


## Abstract base class for sensors
class sensor(threading.Thread):

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
        # Name of the heart rate sensor
        self.name = None

        ## @var running
        # Variable controlling main loop. Should be set to True when starting the loop.
        self.running = False

    def run(self):
        self.log.debug('Starting the main loop for {}'.format(M["module_name"]), extra=M)
        self.running = True
        while self.running:
            pass
            # Copy the above code to a real sensor code and replace pass with whatewer the sensor needs to provide data

    def get_prefix(self):
        return M["module_name"]

    def get_raw_data(self):
        self.log.debug('get_raw_data called', extra=M)
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
        self.log.debug('Stop started for {}'.format(M["module_name"]), extra=M)
        self.running = False

    def __del__(self):
        self.stop()
