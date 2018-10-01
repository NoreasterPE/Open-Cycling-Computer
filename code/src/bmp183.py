#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package bmp183
#  Module for handling Bosch BMP183 pressure sensor

import math
import numbers
import numpy
import sensor
import time


## Class for Bosch BMP183 pressure and temperature sensor with SPI interface as sold by Adafruit
class bmp183(sensor.sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'bmp183'}

    ## @var BMP183_REG
    # BMP183 registers
    BMP183_REG = {
        #@ Calibration data
        'CAL_AC1': 0xAA,
        'CAL_AC2': 0xAC,
        'CAL_AC3': 0xAE,
        'CAL_AC4': 0xB0,
        'CAL_AC5': 0xB2,
        'CAL_AC6': 0xB4,
        'CAL_B1': 0xB6,
        'CAL_B2': 0xB8,
        'CAL_MB': 0xBA,
        'CAL_MC': 0xBC,
        'CAL_MD': 0xBE,

        #@ Chip ID. Value fixed to 0x55. Useful to check if communication works
        'ID': 0xD0,
        'ID_VALUE': 0x55,

        #@ VER Undocumented
        'VER': 0xD1,

        #@ SOFT_RESET Write only. If set to 0xB6, will perform the same sequence as power on reset.
        'SOFT_RESET': 0xE0,

        #@ CTRL_MEAS Controls measurements
        'CTRL_MEAS': 0xF4,

        #@ DATA
        'DATA': 0xF6,
    }

    ## @var BMP183_CMD
    # BMP183 commands
    BMP183_CMD = {
        #@ Chip ID Value fixed to 0x55. Useful to check if communication works
        'ID_VALUE': 0x55,

        # SPI bit to indicate READ or WRITE operation
        'READWRITE': 0x80,

        # Read TEMPERATURE, Wait time 4.5 ms
        'TEMP': 0x2E,
        'TEMP_WAIT': 0.0045,

        # Read PRESSURE
        'PRESS': 0x34,  # 001

        # PRESSURE reading modes
        # Example usage: (PRESS || (OVERSAMPLE_2 << 4)
        'OVERSAMPLE_0': 0x0,  # ultra low power, no oversampling, wait time 4.5 ms
        'OVERSAMPLE_0_WAIT': 0.0045,
        'OVERSAMPLE_1': 0x1,  # standard, 2 internal samples, wait time 7.5 ms
        'OVERSAMPLE_1_WAIT': 0.0075,
        'OVERSAMPLE_2': 0x2,  # high resolution, 4 internal samples, wait time 13.5 ms
        'OVERSAMPLE_2_WAIT': 0.0135,
        'OVERSAMPLE_3': 0x3,  # ultra high resolution, 8 internal samples, Wait time 25.5 ms
        'OVERSAMPLE_3_WAIT': 0.0255,
    }

    ## The constructor
    #  @param self The python object self
    #  @param simulate Decides if bmp183 runs in simulation mode or real device mode.
    def __init__(self, simulate=False):
        # Run init for super class
        super().__init__()
        ## @var simulate
        #  Stores simulate parameter from constructor call
        self.simulate = simulate
        ## @var first_run
        #  Variable indicating first calculations. Deltas are calculated differently.
        self.first_run = True
        ## @var measurement_delay
        #  Time between measurements in [s]
        self.measurement_delay = 0.45
        ## @var temperature_max_delta
        #  Maximum allowed temperature difference between measurements. Normally temperature doesn't change too quickly
        #  so a sudden change means the measurement if invalid. It a new temperature value differs from the previous velu more than
        #  temperature_max_delta the measurement is ignored.
        self.temperature_max_delta = 10
        self.p_formats = dict(pressure="%.0f", pressure_min="%.0f", pressure_max="%.0f",
                              temperature="%.1f", temperature_min="%.1f", temperature_max="%.1f",
                              altitude="%.0f", altitude_delta="%0.2f")
        self.p_units = dict(pressure="hPa", pressure_min="hPa", pressure_max="hPa",
                            temperature="C", temperature_min="C", temperature_max="C",
                            altitude="m", altitude_delta="m")
        self.p_raw_units = dict(pressure="Pa", pressure_min="Pa", pressure_max="Pa",
                                temperature="C", temperature_min="C", temperature_max="C",
                                altitude="m", altitude_delta="m")
        self.required = dict(reference_altitude=numbers.NAN)
        self.reset_data()
        ## @var reference_altitude
        #  Home altitude. Used as reference altitude for calculation of pressure at sea level and subsequent altitude calculations.
        #  It is being set through the notification system - see \link notification \endlink function
        self.reference_altitude = numbers.NAN
        # Setup Raspberry PINS, as numbered on BOARD
        self.SCK = 32  # GPIO for SCK, other name SCLK
        self.SDO = 36  # GPIO for SDO, other name MISO
        self.SDI = 38  # GPIO for SDI, other name MOSI
        self.CS = 40  # GPIO for CS, other name CE

        # SCK frequency 1 MHz
        self.delay = 1 / 1000000.0
        if not self.simulate:
            self.set_up_gpio()
            # Check comunication / read ID
            ret = self.read_byte(self.BMP183_REG['ID'])
            if ret != self.BMP183_CMD['ID_VALUE']:
                self.log.error("Communication with bmp183 failed", extra=self.extra)
                self.connected = False
                raise IOError("Communication with bmp183 failed")
            else:
                self.connected = True
                self.read_calibration_data()
        # Proceed with initial pressure/temperature measurement
        self.measure_pressure()
        self.kalman_setup()
        self.log.debug("Initialised.", extra=self.extra)

    def get_raw_data(self):
        self.log.debug('get_raw_data called', extra=self.extra)
        #FIXME add name, addr, state
        return dict(time_stamp=self.time_stamp,
                    pressure=self.pressure,
                    temperature=self.temperature,
                    altitude=self.altitude,
                    altitude_delta=self.altitude_delta)

    def reset_data(self):
        ## @var temperature
        #  Measured temperature
        self.temperature = 0
        ## @var temperature_min
        #  Minimum measured temperature
        self.temperature_min = numbers.INF
        ## @var temperature_max
        #  Maximum measured temperature
        self.temperature_max = numbers.INF_MIN
        ## @var pressure
        #  Measured pressure after Kalman filter
        self.pressure = numbers.NAN
        ## @var pressure_min
        #  Minimum measured pressure
        self.pressure_min = numbers.INF
        ## @var pressure_max
        #  Maximum measured pressure
        self.pressure_max = numbers.INF_MIN
        ## @var pressure_unfiltered
        #  Actual pressure measured by the sensor
        self.pressure_unfiltered = 0
        ## @var altitude
        #  Altitude calculated based on reference altitude and current presure
        self.altitude = numbers.NAN
        ## @var altitude_delta
        #  Difference in altitude since last calculations
        self.altitude_delta = numbers.NAN

    ## Trigger calculation of pressure at the sea level on change of reference altitude
    #  @param self The python object self
    def notification(self, required):
        self.log.debug("required {}".format(required), extra=self.extra)
        self.reference_altitude = required["reference_altitude"]
        self.calculate_pressure_at_sea_level()

    def stop(self):
        super().stop()
        time.sleep(1)
        if not self.simulate:
            self.cleanup_gpio()
        self.log.debug("Stopped {}".format(__name__), extra=self.extra)

    def set_up_gpio(self):
        self.log.debug("set_up_gpio", extra=self.extra)
        import RPi.GPIO as GPIO
        # GPIO initialisation
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.SCK, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.CS, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.SDI, GPIO.OUT)
        GPIO.setup(self.SDO, GPIO.IN)

    def cleanup_gpio(self):
        self.log.debug("cleanup_gpio", extra=self.extra)
        import RPi.GPIO as GPIO
        GPIO.cleanup(self.SCK)
        GPIO.cleanup(self.CS)
        GPIO.cleanup(self.SDI)
        GPIO.cleanup(self.SDO)

    def read_byte(self, addr):
        # Read byte from SPI interface from address "addr"
        ret_value = self.spi_transfer(addr, 0, 1, 8)
        return ret_value

    def read_word(self, addr, extra_bits=0):
        # Read word from SPI interface from address "addr", option to extend
        # read by up to 3 bits
        ret_value = self.spi_transfer(addr, 0, 1, 16 + extra_bits)
        return ret_value

    def write_byte(self, addr, value):
        # Write byte of "value" to SPI interface at address "addr"
        self.spi_transfer(addr, value, 0, 8)

    def spi_transfer(self, addr, value, rw, length):
        import RPi.GPIO as GPIO
        # Bit banging at address "addr", "rw" indicates READ (1) or WRITE (1)
        # operation
        ret_value = 0
        if (rw == 0):
            spi_addr = addr & (~self.BMP183_CMD['READWRITE'])
        else:
            spi_addr = addr | self.BMP183_CMD['READWRITE']

        GPIO.output(self.CS, 0)
        time.sleep(self.delay)
        for i in range(8):
            bit = spi_addr & (0x01 << (7 - i))
            if (bit):
                GPIO.output(self.SDI, 1)
            else:
                GPIO.output(self.SDI, 0)
            GPIO.output(self.SCK, 0)
            time.sleep(self.delay)
            GPIO.output(self.SCK, 1)
            time.sleep(self.delay)

        if (rw == 1):
            for i in range(length):
                GPIO.output(self.SCK, 0)
                time.sleep(self.delay)
                bit = GPIO.input(self.SDO)
                GPIO.output(self.SCK, 1)
                ret_value = (ret_value << 1) | bit
                time.sleep(self.delay)

        if (rw == 0):
            for i in range(length):
                bit = value & (0x01 << (length - 1 - i))
                if (bit):
                    GPIO.output(self.SDI, 1)
                else:
                    GPIO.output(self.SDI, 0)
                GPIO.output(self.SCK, 0)
                time.sleep(self.delay)
                GPIO.output(self.SCK, 1)
                time.sleep(self.delay)
        GPIO.output(self.CS, 1)
        return ret_value

    def read_calibration_data(self):
        self.log.debug("read_calibration_data", extra=self.extra)
        # Read calibration data
        self.AC1 = numpy.int16(self.read_word(self.BMP183_REG['CAL_AC1']))
        self.AC2 = numpy.int16(self.read_word(self.BMP183_REG['CAL_AC2']))
        self.AC3 = numpy.int16(self.read_word(self.BMP183_REG['CAL_AC3']))
        self.AC4 = numpy.uint16(self.read_word(self.BMP183_REG['CAL_AC4']))
        self.AC5 = numpy.uint16(self.read_word(self.BMP183_REG['CAL_AC5']))
        self.AC6 = numpy.uint16(self.read_word(self.BMP183_REG['CAL_AC6']))
        self.B1 = numpy.int16(self.read_word(self.BMP183_REG['CAL_B1']))
        self.B2 = numpy.int16(self.read_word(self.BMP183_REG['CAL_B2']))
        # MB is not used
        self.MB = numpy.int16(self.read_word(self.BMP183_REG['CAL_MB']))
        self.MC = numpy.int16(self.read_word(self.BMP183_REG['CAL_MC']))
        self.MD = numpy.int16(self.read_word(self.BMP183_REG['CAL_MD']))

    def measure_temperature(self):
        # Start temperature measurement
        self.write_byte(self.BMP183_REG['CTRL_MEAS'], self.BMP183_CMD['TEMP'])
        # Wait
        time.sleep(self.BMP183_CMD['TEMP_WAIT'])
        # Read uncompensated temperature
        self.UT = numpy.int32(self.read_word(self.BMP183_REG['DATA']))
        self.calculate_temperature()

    def measure_pressure(self):
        if self.simulate:
            self.pressure_unfiltered = 101300
            self.temperature = 19.8
        elif self.connected:
            # Measure temperature - required for calculations
            self.measure_temperature()
            self.write_byte(self.BMP183_REG['CTRL_MEAS'], self.BMP183_CMD[
                            'PRESS'] | (self.BMP183_CMD['OVERSAMPLE_3'] << 4))
            # Wait for conversion
            time.sleep(self.BMP183_CMD['OVERSAMPLE_3_WAIT'])
            self.UP = numpy.int32(self.read_word(self.BMP183_REG['DATA'], 3))
            self.calculate_pressure()
        self.time_stamp = time.time()

    def calculate_pressure(self):
        # Calculate atmospheric pressure in [Pa]
        self.B6 = self.B5 - 4000
        X1 = (self.B2 * (self.B6 * self.B6 / 2 ** 12)) / 2 ** 11
        X2 = self.AC2 * self.B6 / 2 ** 11
        X3 = X1 + X2
        self.B3 = ((int(self.AC1 * 4 + X3) << self.BMP183_CMD['OVERSAMPLE_3']) + 2) / 4
        X1 = self.AC3 * self.B6 / 2 ** 13
        X2 = (self.B1 * (self.B6 * self.B6 / 2 ** 12)) / 2 ** 16
        X3 = ((X1 + X2) + 2) / 2 ** 2
        self.B4 = numpy.uint32(self.AC4 * (X3 + 32768) / 2 ** 15)
        self.B7 = (numpy.uint32(self.UP) - self.B3) * \
            (50000 >> self.BMP183_CMD['OVERSAMPLE_3'])
        p = numpy.uint32((self.B7 * 2) / self.B4)
        X1 = (p / 2 ** 8) * (p / 2 ** 8)
        X1 = int(X1 * 3038) / 2 ** 16
        X2 = int(-7357 * p) / 2 ** 16
        self.pressure_unfiltered = p + (X1 + X2 + 3791) / 2 ** 4

    def calculate_temperature(self):
        # Calculate temperature in [degC]
        X1 = (self.UT - self.AC6) * self.AC5 / 2 ** 15
        X2 = self.MC * 2 ** 11 / (X1 + self.MD)
        self.B5 = X1 + X2
        self.T = (self.B5 + 8) / 2 ** 4
        temperature = self.T / 10.0
        if not self.first_run:
            dtemperature = abs(temperature - self.temperature)
        else:
            dtemperature = 0
            self.first_run = False
        if dtemperature < self.temperature_max_delta:
            self.temperature = temperature

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            self.measure_pressure()
            if math.isnan(self.pressure_at_sea_level):
                self.calculate_pressure_at_sea_level()
            self.kalman_update()
            self.calculate_altitude()
            self.log.debug("pressure = {} [Pa], temperature = {} [C]".format(self.pressure, self.temperature), extra=self.extra)
            self.log.debug("altitude = {} [m], altitude_delta = {} [m]".format(self.altitude, self.altitude_delta), extra=self.extra)
            self.pressure_min = min(self.pressure_min, self.pressure)
            self.pressure_max = max(self.pressure_max, self.pressure)
            self.temperature_min = min(self.temperature_min, self.temperature)
            self.temperature_max = max(self.temperature_max, self.temperature)
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
        self.pressure = self.pressure_estimate

    ## Calculates pressure at sea level based on given reference altitude
    #  Saves calculated value to self.pressure_at_sea_level
    #  @param self The python object self
    #  @param reference_altitude Home altitudei
    def calculate_pressure_at_sea_level(self):
        self.log.debug("pressure: {}".format(self.pressure), extra=self.extra)
        if self.reference_altitude < 43300:
            self.pressure_at_sea_level = float(self.pressure / pow((1 - self.reference_altitude / 44330), 5.255))
        else:
            self.pressure_at_sea_level = numbers.NAN
            self.log.debug("Reference altitude over 43300: {}, refusing to calculate pressure at sea level".format(self.reference_altitude), extra=self.extra)
        self.log.debug("pressure_at_sea_level: {}".format(self.pressure_at_sea_level), extra=self.extra)

    ## Calculates altitude and altitude_delta based on pressure_at_sea_level and current pressure
    #  Saves calculated value to self.altitude and self.altitude_delta
    #  @param self The python object self
    def calculate_altitude(self):
        altitude_previous = self.altitude
        if self.pressure != 0:
            self.altitude = round(44330.0 * (1 - pow((self.pressure / self.pressure_at_sea_level), (1 / 5.255))), 2)
        self.altitude_delta = self.altitude - altitude_previous
        self.log.debug("altitude: {}, altitude_delta {}".format(self.altitude, self.altitude_delta), extra=self.extra)
