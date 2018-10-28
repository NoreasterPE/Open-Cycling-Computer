#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package bmp280
#  Module for handling Bosch BMP280 pressureAand temperature sensor

import kalman
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

        self.s = sensors.sensors()
        self.s.register_parameter("pressure", self.extra["module_name"], raw_unit="Pa", unit="hPa", units_allowed=["hPa", "kPa"])
        self.s.register_parameter("pressure_nof", self.extra["module_name"], raw_unit="Pa", unit="hPa", units_allowed=["hPa", "kPa"])
        self.s.register_parameter("mean_sea_level_pressure", self.extra["module_name"], raw_unit="Pa", unit="hPa", units_allowed=["hPa", "kPa"])
        self.s.register_parameter("temperature", self.extra["module_name"], raw_unit="C", unit="C", units_allowed=["C", "F"])
        self.s.register_parameter("altitude", self.extra["module_name"], raw_unit="m", unit="m", units_allowed=["m"])
        self.s.request_parameter("reference_altitude", self.extra["module_name"])
        self.s.request_parameter("mean_sea_level_pressure", self.extra["module_name"])
        ## @var pressure_unfiltered
        #  Pressure as reported by the sensor. Might be IIR filtered, depending on the sensor configureaion
        self.pressure_unfiltered = numbers.NAN
        ## @var reference_altitude
        #  Reference altitude used to calculate current altitude
        self.reference_altitude = numbers.NAN
        self.ignore_reference_altitude_change = False
        ## @var mean_sea_level_pressure
        #  Mean sea-level pressure. Calculations are based on reference altitude or might be set by the user as MSLP METAR
        self.mean_sea_level_pressure = numbers.NAN
        self.measure()
        # Initialise Kalman filter
        self.kalman = kalman.kalman(Q=0.02, R=1.0)
        self.kalman.set_initial_value(self.pressure_unfiltered)
        self.log.debug("Initialised.", extra=self.extra)

    ## Trigger calculation of pressure at the sea level on change of reference altitude
    #  @param self The python object self
    def notification(self):
        # User editer mean_sea_level_pressure, use it and calculate reference_altitude
        if self.s.parameters["mean_sea_level_pressure"]["value"] != self.mean_sea_level_pressure:
            self.log.debug("mean_sea_level_pressure changed to {}".format(self.s.parameters['mean_sea_level_pressure']['value']), extra=self.extra)
            self.mean_sea_level_pressure = self.s.parameters["mean_sea_level_pressure"]["value"]
            ra = self.calculate_altitude(self.s.parameters['pressure']['value'])
            if ra is not None and not math.isnan(ra):
                # reference_altitude recalculation triggers notification, so ignore the next event
                self.ignore_reference_altitude_change = True
                self.s.parameters['reference_altitude']['value'] = ra
            self.log.debug("reference_altitude recalculated to: {}".format(self.s.parameters['reference_altitude']['value']), extra=self.extra)
        elif self.s.parameters["reference_altitude"]["value"] != self.reference_altitude:
            self.log.debug("reference_altitude changed to {}".format(self.s.parameters['reference_altitude']['value']), extra=self.extra)
            if not self.ignore_reference_altitude_change:
                self.reference_altitude = self.s.parameters["reference_altitude"]["value"]
                self.calculate_mean_sea_level_pressure()
                self.log.debug("mean_sea_level_pressure recalculated to: {}".format(self.s.parameters['mean_sea_level_pressure']['value']), extra=self.extra)
            else:
                self.ignore_reference_altitude_change = False

    def measure(self):
        # Reades pressure and temperature from the kernel driver
        # FIXME Hardware checks
        try:
            with open('/sys/bus/iio/devices/iio:device0/in_pressure_input', 'r') as press:
                # self.pressure_unfiltered is required for test files
                self.pressure_unfiltered = float(press.read()) * 1000.0
            with open('/sys/bus/iio/devices/iio:device0/in_temp_input', 'r') as temp:
                # self.temperature is required for test files
                self.temperature = float(temp.read()) / 1000.0
                self.s.parameters["temperature"]["value"] = self.temperature
        except (FileNotFoundError, OSError) as e:
            # FileNotFoundError: [Errno 2] No such file or directory: '/sys/bus/iio/devices/iio:device0/in_pressure_input'
            # OSError: [Errno 121] Remote I/O error
            self.log.critical("eading from bmp280 caused exception: {}".format(e), extra=self.extra)

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            self.measure()
            if self.mean_sea_level_pressure is not None:
                if math.isnan(self.mean_sea_level_pressure):
                    self.calculate_mean_sea_level_pressure()
            self.kalman.update_unfiltered_value(self.pressure_unfiltered)
            self.kalman.update()
            # self.pressure is required for test files
            self.pressure = self.kalman.value_estimate
            self.s.parameters["pressure"]["value"] = self.pressure
            self.s.parameters["pressure_nof"]["value"] = self.pressure_unfiltered
            self.s.parameters['altitude']['value'] = self.calculate_altitude(self.s.parameters['pressure']['value'])
            self.log.debug("pressure = {} [Pa], temperature = {} [C]".format(self.s.parameters["pressure"]["value"], self.s.parameters["temperature"]["value"]), extra=self.extra)
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

    ## Calculates pressure at sea level based on given reference altitude
    #  Saves calculated value to self.mean_sea_level_pressure
    #  @param self The python object self
    #  @param reference_altitude Home altitudei
    def calculate_mean_sea_level_pressure(self):
        self.log.debug("pressure: {}".format(self.s.parameters["pressure"]["value"]), extra=self.extra)
        try:
            ref_alt = float(self.s.parameters["reference_altitude"]["value"])
        except (ValueError, TypeError):
            ref_alt = 0.0
            self.log.error("Reference altitude : {}, can't convert to float. Using 0 m".format(self.s.parameters["reference_altitude"]["value"]), extra=self.extra)
        except (KeyError):
            ref_alt = 0.0
            self.log.debug("Reference altitude doesn't exist, using 0 0 m", extra=self.extra)
        try:
            if ref_alt < 43300.0:
                try:
                    self.mean_sea_level_pressure = float(self.s.parameters["pressure"]["value"] / pow((1 - ref_alt / 44330), 5.255))
                except TypeError:
                    self.mean_sea_level_pressure = numbers.NAN
            else:
                self.log.debug("Reference altitude over 43300: {}, can't calculate pressure at sea level".format(ref_alt), extra=self.extra)
                self.mean_sea_level_pressure = numbers.NAN
        except TypeError:
            pass
        self.s.parameters['mean_sea_level_pressure']['value'] = self.mean_sea_level_pressure
        self.log.debug("mean_sea_level_pressure: {}".format(self.mean_sea_level_pressure), extra=self.extra)

    ## Calculates altitude based on mean_sea_level_pressure and given pressure
    #  Saves calculated value to self.s.parameters["altitude]"
    #  @param self The python object self
    def calculate_altitude(self, pressure):
        altitude = numbers.NAN
        try:
            if pressure != 0:
                altitude = round(44330.0 * (1 - pow((pressure / self.mean_sea_level_pressure), (1 / 5.255))), 2)
        except TypeError:
            pass
        self.log.debug("calculate_altitude  altitude: {} [m]".format(altitude), extra=self.extra)
        return altitude
