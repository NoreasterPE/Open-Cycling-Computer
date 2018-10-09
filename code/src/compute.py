#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package compute
#  Module for handling calculations that require more than sensor data

import numbers
import sensor
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

        self.p_defaults.update(dict(slope=numbers.NAN,
                                    altitude_delta_cumulative=numbers.NAN,
                                    distance_delta_cumulative=numbers.NAN))
        self.p_raw.update(dict(self.p_defaults))
        self.p_formats.update(dict(slope='%.0f',
                                   altitude_delta_cumulative="%.3f",
                                   distance_delta_cumulative="%.3f"))
        self.p_units.update(dict(slope='%',
                                 altitude_delta_cumulative="m",
                                 distance_delta_cumulative="m"))
        self.p_units_allowed.update(dict(slope=["%", "m/m"]))
        self.p_raw_units.update(dict(slope="m/m",
                                     altitude_delta_cumulative="m",
                                     distance_delta_cumulative="m"))
        self.required = dict(bmp183_altitude_delta=numbers.NAN,
                             bmp183_distance_delta=numbers.NAN)

        self.reset_data()
        self.log.debug("Initialised.", extra=self.extra)

    ## Trigger calculation of slope on cumulative change of distance and altitude
    #  @param self The python object self
    def notification(self, required):
        self.log.debug("required {}".format(required), extra=self.extra)
        self.altitude_delta = self.required["bmp183_altitude_delta"]
        self.distance_delta = self.required["bmp183_distance_delta"]
        try:
            self.p_raw["altitude_delta_cumulative"] += self.altitude_delta
            self.p_raw["distance_delta_cumulative"] += self.distance_delta
            self.calculate_slope()
        except TypeError:
            self.log.debug("Data not suitable for calculationsi {}".format(required), extra=self.extra)
            pass

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            time.sleep(10)
        self.log.debug("Main loop finished", extra=self.extra)

    ## Calculate slope. Current values are matched with Bosch BMP183 sensor (0.18 m of resolution). To be changed if sensor is upgraded to BMP280
    #  @param self The python object self
    def calculate_slope(self):
        if self.p_raw["distance_delta_cumulative"] > 8.4:
            self.p_raw["slope"] = self.p_raw["altitude_delta_cumulative"] / self.p_raw["distance_delta_cumulative"]
        if abs(self.p_raw["slope"]) < 0.02:
            #If slope is less than 2% wait for more cumulative distance/altitude
            self.p_raw["slope"] = 0.0
        else:
            #If slope is less more 2%, use calculated value and reset cumulative variables
            self.log.debug("altitude_delta_cumulative: {}".format(self.p_raw["altitude_delta_cumulative"]), extra=self.extra)
            self.log.debug("distance_delta_cumulative: {}".format(self.p_raw["distance_delta_cumulative"]), extra=self.extra)
            self.p_raw["altitude_delta_cumulative"] = 0
            self.p_raw["distance_delta_cumulative"] = 0
        self.log.debug("slope: {}".format(self.p_raw["slope"]), extra=self.extra)
