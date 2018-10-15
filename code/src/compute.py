#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package compute
#  Module for handling calculations that require more than sensor data

#import numbers
import sensor
import sensors
import time


## Compute module, handles all cross sensor calculations. I.e. slope calculation can be done with data from altimeter and speed sensor.
class compute(sensor.sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'compute'}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()

        self.s = sensors.sensors()
        self.s.register_parameter("slope", self.extra["module_name"], raw_unit="m/m", unit="%", units_allowed=["m/m", "%"])
        self.s.register_parameter("speed", self.extra["module_name"], raw_unit="m/s", unit="km/h", units_allowed=["m/s", "km/h", "mi/h"])
        self.s.register_parameter("start_time", self.extra["module_name"], raw_unit="s")
        self.s.parameters["start_time"]["value"] = time.time()
        self.s.register_parameter("session_time", self.extra["module_name"], raw_unit="s")
        self.s.parameters["session_time"]["value"] = 0.0
        self.s.request_parameter("odometer", self.extra["module_name"])
        self.odometer = None
        self.odometer_delta_cumulative = 0.0
        self.odometer_delta = 0.0
        self.s.request_parameter("altitude", self.extra["module_name"])
        self.altitude = None
        self.altitude_delta_cumulative = 0.0
        self.s.request_parameter("wheel_revolution_time", self.extra["module_name"])
        self.wheel_revolution_time = None
        self.reset_data()
        self.log.debug("Initialised.", extra=self.extra)

    ## Trigger calculation of slope on cumulative change of distance and altitude
    #  @param self The python object self
    def notification(self):
        self.log.debug("notification received", extra=self.extra)
        previous_altitude = self.altitude
        self.altitude = self.s.parameters["altitude"]["value"]
        try:
            self.altitude_delta = self.altitude - previous_altitude
        except TypeError:
            self.altitude_delta = 0.0
        previous_wheel_rev_time = self.wheel_revolution_time
        self.wheel_revolution_time = self.s.parameters["wheel_revolution_time"]["value"]
        try:
            self.wheel_revolution_time_delta = self.wheel_revolution_time - previous_wheel_rev_time
            self.altitude_delta_cumulative += self.altitude_delta
            self.odometer_delta_cumulative += self.odometer_delta
            self.calculate_slope()
        except TypeError:
            pass

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            self.s.parameters["session_time"]["value"] = time.time() - self.s.parameters["start_time"]["value"]
            time.sleep(0.1)
        self.log.debug("Main loop finished", extra=self.extra)

    ## Calculate slope. Current values are matched with Bosch BMP183 sensor (0.18 m of resolution). To be changed if sensor is upgraded to BMP280
    #  @param self The python object self
    def calculate_slope(self):
        if self.odometer_delta_cumulative > 8.4:
            self.s.parameters["slope"]["value"] = self.altitude_delta_cumulative / self.odometer_delta_cumulative
        if abs(self.s.parameters["slope"]["value"]) < 0.02:
            #If slope is less than 2% wait for more cumulative distance/altitude
            self.s.parameters["slope"]["value"] = 0.0
        else:
            #If slope is less more 2%, use calculated value and reset cumulative variables
            self.log.debug("altitude_delta_cumulative: {}".format(self.altitude_delta_cumulative), extra=self.extra)
            self.log.debug("odometer_delta_cumulative: {}".format(self.odometer_delta_cumulative), extra=self.extra)
            self.altitude_delta_cumulative = 0.0
            self.odometer_delta_cumulative = 0.0
        self.log.debug("slope: {}".format(self.s.parameters["slope"]["value"]), extra=self.extra)
