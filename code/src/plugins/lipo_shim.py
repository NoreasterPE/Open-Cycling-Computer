#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package lipo_shim
#  Module for handling Pimoroni LiPo shim

import plugin
import pyplum
import time
import RPi.GPIO


#  Module for handling Pimoroni LiPo shim
class lipo_shim(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}
    battery_low_overlay_image = 'images/ol_battery_low_warning.png'
    READ_PERIOD = 10

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()

        self.pm.register_parameter("battery_low", self.extra["module_name"], value=False, store=False)
        self.battery_low = False

        RPi.GPIO.setmode(RPi.GPIO.BOARD)
        RPi.GPIO.setup(7, RPi.GPIO.IN, pull_up_down=RPi.GPIO.PUD_UP)
        self.battery_low = bool(RPi.GPIO.input(7))

        self.last_read = time.time()
        self.log.debug("Initialised.", extra=self.extra)

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            if time.time() - self.last_read > self.READ_PERIOD:
                self.last_read = time.time()
                self.battery_low = not(bool(RPi.GPIO.input(7)))
                if self.battery_low:
                    self.log.debug('Battery status: low', extra=self.extra)
                else:
                    self.log.debug('Battery status: OK', extra=self.extra)
                self.pm.parameters['battery_low']['value'] = self.battery_low
                if self.pm.event_queue is not None and self.battery_low:
                    self.pm.event_queue.put(('show_overlay', self.battery_low_overlay_image))
            time.sleep(1.0)
        self.log.debug("Main loop finished", extra=self.extra)
