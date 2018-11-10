#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package pimoroni_lipo_shim
#  Module for handling Pimoroni LiPo shim

import plugin
import pyplum
import time
import RPi.GPIO


#  Module for handling Pimoroni LiPo shim
class pimoroni_lipo_shim(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()

        self.pm = pyplum.pyplum()
        self.pm.register_parameter("battery_low", self.extra["module_name"], value=False, store=False)
        RPi.GPIO.setmode(RPi.GPIO.BOARD)
        RPi.GPIO.setup(7, RPi.GPIO.IN)
        self.last_read = time.time()
        self.log.debug("Initialised.", extra=self.extra)

    ## Notification handler
    #  @param self The python object self
    def notification(self):
        pass

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            if time.time() - self.last_read > 10:
                self.last_read = time.time()
                battery_low = bool(RPi.GPIO.input(7))
                self.log.debug("Battery low: {}.".format(battery_low), extra=self.extra)
                self.pm.parameters['battery_low']['value'] = battery_low
        self.log.debug("Main loop finished", extra=self.extra)
