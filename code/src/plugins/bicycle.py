#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package bicycle
#  Module for handling bicycle parameters like session_distance or slope

import math
import num
import plugin
import pyplum
import time
import wheel


## Bicycle  module, handles all bicycle related parameters
class bicycle(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()

        self.pm = pyplum.pyplum()
        self.pm.register_parameter("slope", self.extra["module_name"], value=num.NAN, raw_unit="m/m", unit="%", units_allowed=["m/m", "%"])
        self.pm.register_parameter("speed", self.extra["module_name"], value=num.NAN, raw_unit="m/s", unit="km/h", units_allowed=["m/s", "km/h", "mi/h"], store=True)
        self.pm.parameters["speed"]["time_stamp"] = 0.0
        self.pm.register_parameter("session_distance", self.extra["module_name"], value=0.0, raw_unit="m", unit="km", units_allowed=["m", "km", "mi"])
        self.pm.register_parameter("session_odometer_start", self.extra["module_name"], value=num.NAN, raw_unit="m")
        self.pm.register_parameter("gear_ratio", self.extra["module_name"], value=num.NAN)
        self.w = wheel.wheel()
        self.pm.register_parameter("wheel_size", self.extra["module_name"], value=num.NAN, raw_unit="m", value_list=self.w.get_allowed_values(), store=True)
        self.pm.request_parameter("wheel_size", self.extra["module_name"])
        self.wheel_size = num.NAN
        self.pm.request_parameter("cadence", self.extra["module_name"])
        self.cadence = num.NAN
        self.pm.register_parameter("wheel_circumference", self.extra["module_name"], value=num.NAN, raw_unit="m", units_allowed=['mm', 'cm', 'm', 'in'], store=True)
        self.pm.request_parameter("wheel_circumference", self.extra["module_name"])
        self.wheel_circumference = num.NAN
        self.pm.register_parameter("rider_weight", self.extra["module_name"], units_allowed=['kg', 'lb', 'st'], store=True)
        self.pm.request_parameter("odometer", self.extra["module_name"])
        self.odometer = None
        self.odometer_delta_cumulative = 0.0
        self.odometer_delta = 0.0
        self.pm.request_parameter("altitude", self.extra["module_name"])
        self.altitude = None
        self.altitude_delta_cumulative = 0.0
        self.pm.request_parameter("wheel_revolution_time", self.extra["module_name"])
        self.wheel_revolution_time = None
        self.pm.request_parameter("wheel_size", self.extra["module_name"])
        self.wheel_size = None
        self.reset_data()
        self.log.debug("Initialised.", extra=self.extra)

    ## Trigger calculation of slope on cumulative change of distance and altitude
    #  @param self The python object self
    def notification(self):
        # Set initial session odometer value
        if 'session_odometer_start' in self.pm.parameters:
            if self.pm.parameters["session_odometer_start"]["value"] is not None:
                if math.isnan(self.pm.parameters["session_odometer_start"]["value"]):
                    self.pm.parameters["session_odometer_start"]["value"] = self.odometer

        # Handle wheel_size change
        if self.wheel_size != self.pm.parameters['wheel_size']['value']:
            self.log.debug("wheel_size changed from {} to {}.".format(self.wheel_size, self.pm.parameters['wheel_size']['value']), extra=self.extra)
            self.wheel_size = self.pm.parameters['wheel_size']['value']
            try:
                self.pm.parameters['wheel_circumference']['value'] = self.w.get_circumference(self.wheel_size)
            except KeyError:
                #FIXME That should give user feedback that something went wrong
                self.log.critical("Unknown wheel_circumference for wheel_size {}.".format(self.wheel_size), extra=self.extra)

        # Handle wheel_circumference change
        if self.wheel_circumference != self.pm.parameters['wheel_circumference']['value']:
            self.log.debug("wheel_circumference changed from {} to {}.".format(self.wheel_circumference, self.pm.parameters['wheel_circumference']['value']), extra=self.extra)
            self.wheel_circumference = self.pm.parameters['wheel_circumference']['value']
            #FIXME Reverse check wheel helper for wheel_size or just set it to 'User'?
            #FIXME Make wheel module a plugin?

        # Speed calculation
        if self.wheel_revolution_time != self.pm.parameters["wheel_revolution_time"]["value"]:
            self.wheel_revolution_time = self.pm.parameters["wheel_revolution_time"]["value"]
            self.pm.parameters["speed"]["value"] = self.wheel_circumference / self.wheel_revolution_time
            self.pm.parameters["speed"]["value_max"] = max(self.pm.parameters["speed"]["value_max"], self.pm.parameters["speed"]["value"])
            self.speed_time_stamp = time.time()
            self.pm.parameters["speed"]["time_stamp"] = self.speed_time_stamp

        # Expiry speed after 2 s
        if time.time() - self.speed_time_stamp > 2.0:
            self.pm.parameters["speed"]["value"] = 0.0
            self.speed_time_stamp = time.time()
            self.pm.parameters["speed"]["time_stamp"] = self.speed_time_stamp

        # Calculate altitude change
        if self.altitude != self.pm.parameters["altitude"]["value"]:
            previous_altitude = self.altitude
            self.altitude = self.pm.parameters["altitude"]["value"]
            try:
                self.altitude_delta = self.altitude - previous_altitude
            except TypeError:
                self.altitude_delta = 0.0

        # Calculate odometer change
        if self.odometer != self.pm.parameters["odometer"]["value"]:
            previous_odometer = self.odometer
            self.odometer = self.pm.parameters["odometer"]["value"]
            try:
                self.odometer_delta = self.odometer - previous_odometer
            except TypeError:
                self.odometer_delta = 0.0
            try:
                self.pm.parameters["session_distance"]["value"] = self.odometer - self.pm.parameters["session_odometer_start"]["value"]
            except (TypeError, ValueError):
                pass

        # Calculate gear ratio
        if self.cadence != self.pm.parameters["cadence"]["value"]:
            self.cadence = self.pm.parameters["cadence"]["value"]
            try:
                self.pm.parameters["gear_ratio"]["value"] = self.wheel_revolution_time / (self.cadence / 60.0)
            except (TypeError, ZeroDivisionError):
                self.pm.parameters["gear_ratio"]["value"] = num.NAN

        # Calculate slope
        if self.odometer_delta > 0.0:
            try:
                self.altitude_delta_cumulative += self.altitude_delta
                self.odometer_delta_cumulative += self.odometer_delta
                self.calculate_slope()
            except TypeError:
                pass

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            # 3 s expiry to slope reset
            if time.time() - self.pm.parameters["slope"]["time_stamp"] > 3.0:
                self.pm.parameters["slope"]["value"] = 0.0
            time.sleep(0.1)
        self.log.debug("Main loop finished", extra=self.extra)

    ## Calculate slope. Current values are matched with Bosch BMP183 sensor (0.18 m of resolution). To be changed if sensor is upgraded to BMP280
    #  @param self The python object self
    def calculate_slope(self):
        t = time.time()
        if self.odometer_delta_cumulative > 2.0:
            self.pm.parameters["slope"]["value"] = self.altitude_delta_cumulative / self.odometer_delta_cumulative
            self.pm.parameters["slope"]["time_stamp"] = t
            self.log.debug("slope: {}".format(self.pm.parameters["slope"]["value"]), extra=self.extra)
        if abs(self.pm.parameters["slope"]["value"]) < 0.02:
            #If slope is less than 2% wait for more cumulative distance/altitude
            self.pm.parameters["slope"]["value"] = 0.0
            self.pm.parameters["slope"]["time_stamp"] = t
        else:
            #If slope is less more 2%, use calculated value and reset cumulative variables
            self.log.debug("altitude_delta_cumulative: {}".format(self.altitude_delta_cumulative), extra=self.extra)
            self.log.debug("odometer_delta_cumulative: {}".format(self.odometer_delta_cumulative), extra=self.extra)
            self.altitude_delta_cumulative = 0.0
            self.odometer_delta_cumulative = 0.0
