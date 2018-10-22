#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package bmp280
#  Module for handling Bosch BMP280 pressureAand temperature sensor

import math
import numbers
import sensor
import sensors
import time


class bmp280(sensor.sensor):
    'Class for Bosch BMP280 pressure and temperature sensor with SPI/I2C interfaces as sold by Adafruit. Currently only SPI is supported'
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'bmp280'}

    def __init__(self):
        # Run init for super class
        super().__init__()
        ## @var first_run
        #  Variable indicating first calculations. Deltas are calculated differently.
        self.first_run = True
        ## @var measurement_delay
        #  Time between measurements in [s]
        self.measurement_delay = 1.0
        ## @var temperature_max_delta
        #  Maximum allowed temperature difference between measurements. Normally temperature doesn't change too quickly
        #  so a sudden change means the measurement if invalid. It a new temperature value differs from the previous velu more than
        #  temperature_max_delta the measurement is ignored.
        self.temperature_max_delta = 10

        self.s = sensors.sensors()
        self.s.register_parameter("pressure", self.extra["module_name"], raw_unit="Pa", unit="hPa", units_allowed=["hPa", "kPa"])
        self.s.register_parameter("pressure_nof", self.extra["module_name"], raw_unit="Pa", unit="hPa", units_allowed=["hPa", "kPa"])
        self.s.register_parameter("temperature", self.extra["module_name"], raw_unit="C", unit="C", units_allowed=["C", "F"])
        self.s.register_parameter("altitude", self.extra["module_name"], raw_unit="m", unit="m", units_allowed=["m"])
        self.s.request_parameter("reference_altitude", self.extra["module_name"])
        ## @var pressure_unfiltered
        #  Pressure as reported by the sensor. Might be IIR filtered, depending on the sensor configureaion
        self.pressure_unfiltered = numbers.NAN
        ## @var altitude_delta
        #  Change of altitude since last measurement
        self.altitude_delta = numbers.NAN
        ## @var pressure_at_sea_level
        #  Mean sea-level pressure. Calculations are based on reference altitude
        self.pressure_at_sea_level = numbers.NAN
        self.measure()
        self.kalman_setup()
        self.log.debug("Initialised.", extra=self.extra)

    ## Trigger calculation of pressure at the sea level on change of reference altitude
    #  @param self The python object self
    def notification(self):
        self.log.debug("notification received", extra=self.extra)
        self.calculate_pressure_at_sea_level()

    def measure(self):
        # Reades pressure and temperature from the kernel driver
        # FIXME Hardware checks
        with open('/sys/bus/iio/devices/iio:device0/in_pressure_input', 'r') as press:
            self.pressure_unfiltered = float(press.read()) * 1000.0
        with open('/sys/bus/iio/devices/iio:device0/in_temp_input', 'r') as temp:
            self.s.parameters["temperature"]["value"] = float(temp.read()) / 1000.0

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            self.measure()
            if math.isnan(self.pressure_at_sea_level):
                self.calculate_pressure_at_sea_level()
            self.kalman_update()
            self.calculate_altitude()
            self.log.debug("pressure = {} [Pa], temperature = {} [C]".format(self.s.parameters["pressure"]["value"], self.s.parameters["temperature"]["value"]), extra=self.extra)
            self.log.debug("altitude = {} [m]".format(self.s.parameters["altitude"]["value"]), extra=self.extra)
            try:
                self.s.parameters["pressure"]["value_min"] = min(self.s.parameters["pressure"]["value"], self.s.parameters["pressure"]["value_min"])
                self.s.parameters["pressure"]["value_max"] = max(self.s.parameters["pressure"]["value"], self.s.parameters["pressure"]["value_max"])
                self.s.parameters["temperature"]["value_min"] = min(self.s.parameters["temperature"]["value"], self.s.parameters["temperature"]["value_min"])
                self.s.parameters["temperature"]["value_max"] = max(self.s.parameters["temperature"]["value"], self.s.parameters["temperature"]["value_max"])
                # Some variables are not initialised when run in test mode, so ignore the error
            except TypeError:
                pass
            time.sleep(self.measurement_delay)
        self.log.debug("Main loop finished", extra=self.extra)

    def kalman_setup(self):
        # FIXME Add detailed comments
        # FIXME that will depend on max descend/ascend speed.  calculate from max +/- 1.5m/s
        # R makes no difference, R/Q is what matters
        # P and K are self tuning
        self.Q = 0.02
        # First estimate
        self.pressure_estimate = self.pressure_unfiltered
        # Error
        self.P = 0.245657137142
        # First previous estimate
        self.pressure_estimate_previous = self.pressure_unfiltered
        # First previous error
        self.P_previous = 0.325657137142
        # First gain
        self.K = 0.245657137142
        # Estimate of measurement variance, sensor noise
        self.R = 1.0

    def kalman_update(self):
        # FIXME Add detailed commants
        z = self.pressure_unfiltered
        # Save previous value
        self.pressure_estimate_previous = self.pressure_estimate
        # Save previous error
        self.P_previous = self.P + self.Q
        # Calculate current gain
        self.K = self.P_previous / (self.P_previous + self.R)
        # Calculate new estimate
        self.pressure_estimate = self.pressure_estimate_previous + \
            self.K * (z - self.pressure_estimate_previous)
        # Calculate new error estimate
        self.P = (1 - self.K) * self.P_previous
        self.s.parameters["pressure"]["value"] = self.pressure_estimate
        self.s.parameters["pressure_nof"]["value"] = self.pressure_unfiltered

    ## Calculates pressure at sea level based on given reference altitude
    #  Saves calculated value to self.pressure_at_sea_level
    #  @param self The python object self
    #  @param reference_altitude Home altitudei
    def calculate_pressure_at_sea_level(self):
        self.log.debug("pressure: {}".format(self.s.parameters["pressure"]["value"]), extra=self.extra)
        try:
            ref_alt = float(self.s.parameters["reference_altitude"]["value"])
        except (ValueError):
            ref_alt = 0.0
            self.log.error("Reference altitude : {}, can't convert to float. Using 0 m".format(self.s.parameters["reference_altitude"]["value"]), extra=self.extra)
        except (KeyError):
            ref_alt = 0.0
            self.log.debug("Reference altitude doesn't exist, using 0 0 m", extra=self.extra)
        try:
            if ref_alt < 43300.0:
                try:
                    self.pressure_at_sea_level = float(self.s.parameters["pressure"]["value"] / pow((1 - ref_alt / 44330), 5.255))
                except TypeError:
                    self.pressure_at_sea_level = numbers.NAN
            else:
                self.log.debug("Reference altitude over 43300: {}, can't calculate pressure at sea level".format(ref_alt), extra=self.extra)
                self.pressure_at_sea_level = numbers.NAN
        except TypeError:
            pass
        self.log.debug("pressure_at_sea_level: {}".format(self.pressure_at_sea_level), extra=self.extra)

    ## Calculates altitude and altitude_delta based on pressure_at_sea_level and current pressure
    #  Saves calculated value to self.s.parameters["altitude]" and sel.altitude_delta
    #  @param self The python object self
    def calculate_altitude(self):
        altitude_previous = self.s.parameters["altitude"]["value"]
        if self.s.parameters["pressure"]["value"] != 0:
            self.s.parameters["altitude"]["value"] = round(44330.0 * (1 - pow((self.s.parameters["pressure"]["value"] / self.pressure_at_sea_level), (1 / 5.255))), 2)
        try:
            self.altitude_delta = self.s.parameters["altitude"]["value"] - altitude_previous
        except TypeError:
            self.altitude_delta = numbers.NAN
        self.log.debug("altitude: {}, altitude_delta {}".format(self.s.parameters["altitude"]["value"], self.altitude_delta), extra=self.extra)
