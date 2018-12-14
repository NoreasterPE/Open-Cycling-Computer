#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ds18b20
#  Module for handling DS18B20 1-wire teperature sensor'

import glob
import time

from helpers import num
import plugin
import pyplum


class ds18b20(plugin.plugin):
    'Class for DS18B20 1-wire teperature sensor. It uses any sensor from /sys/bus/w1/devices/28-00*/w1_slave, so medify the code if you have more than one sensor'
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self):
        # Run init for super class
        super().__init__()
        ## @var measurement_delay
        #  Time between measurements in [s]
        self.measurement_delay = 1.0

        ## @var pm
        #  Pythom PLUgin Manager instance
        self.pm = pyplum.pyplum()
        self.pm.register_parameter("cheese_temperature", self.extra["module_name"], raw_unit="C", unit="C", units_allowed=["C", "F"], store=False)
        ## @var temperature
        #  Temperature as reported by the sensor.
        self.temperature = num.NAN
        self.log.debug("Initialised.", extra=self.extra)

    def measure(self):
        # Typical reading
        # 73 01 4b 46 7f ff 0d 10 41 : crc=41 YES
        # 73 01 4b 46 7f ff 0d 10 41 t=23187
        for sensor in glob.glob("/sys/bus/w1/devices/28-00*/w1_slave"):
            with open(sensor, 'r') as f:
                data = f.read()
                f.close()
            if "YES" in data:
                (discard, sep, reading) = data.partition(' t=')
                t = float(reading) / 1000.0
                self.temperature = "{:.1f}".format(t)
            else:
                self.temperature = '999.9'

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            if self.pm.parameters['data_log_period']['value'] != 5:
                self.pm.parameters["data_log_period"]['value'] = 5
            self.measure()
            self.pm.parameters['cheese_temperature']['value'] = self.temperature
            self.log.debug("ds18b20 temperature: {}".format(self.temperature), extra=self.extra)
            time.sleep(self.measurement_delay)
        self.log.debug("Main loop finished", extra=self.extra)
