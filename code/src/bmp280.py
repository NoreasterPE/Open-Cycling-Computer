#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package bmp280
#  Module for handling Bosch BMP280 pressureAand temperature sensor

import RPi.GPIO as GPIO
import math
import numbers
import numpy
import sensor
import sensors
import time


class bmp280(sensor.sensor):
    'Class for Bosch BMP280 pressure and temperature sensor with SPI/I2C interfaces as sold by Adafruit. Currently only SPI is supported'
    # Setup Raspberry PINS, as numbered on BOARD, modify to match your setup!
    SCK = 32  # GPIO for SCK, other name SCLK
    SDO = 36  # GPIO for SDO, other name MISO
    SDI = 38  # GPIO for SDI, other name MOSI
    CS = 40  # GPIO for CS, other name CE

    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'bmp280'}

    # BMP280 registers
    BMP280_REG = {
        #@ Calibration data
        'DIG_T1_LSB': 0x88,
        'DIG_T1_MSB': 0x89,
        'DIG_T2_LSB': 0x8A,
        'DIG_T2_MSB': 0x8B,
        'DIG_T3_LSB': 0x8C,
        'DIG_T3_MSB': 0x8D,
        'DIG_P1_LSB': 0x8E,
        'DIG_P1_MSB': 0x8F,
        'DIG_P2_LSB': 0x90,
        'DIG_P2_MSB': 0x91,
        'DIG_P3_LSB': 0x92,
        'DIG_P3_MSB': 0x93,
        'DIG_P4_LSB': 0x94,
        'DIG_P4_MSB': 0x95,
        'DIG_P5_LSB': 0x96,
        'DIG_P5_MSB': 0x97,
        'DIG_P6_LSB': 0x98,
        'DIG_P6_MSB': 0x99,
        'DIG_P7_LSB': 0x9A,
        'DIG_P7_MSB': 0x9B,
        'DIG_P8_LSB': 0x9C,
        'DIG_P8_MSB': 0x9D,
        'DIG_P9_LSB': 0x9E,
        'DIG_P9_MSB': 0x9F,

        #@ Chip ID. Useful to check if communication works
        'ID': 0xD0,

        #@ SOFT_RESET Write only. If set to 0xB6, will perform the same sequence as power on reset.
        'SOFT_RESET': 0xE0,

        #@ STATUS Status of the device, 2 bits only
        # Bit 3 - 1 when conversion is running and 0 when the results have been transferred
        # Bit 0 - 1 when the NVM (Non-Volatile Memory) data are being copied to image registers, 0 when finished
        'STATUS': 0xF3,

        #@ CTRL_MEAS Controls measurements.
        # Bit 7,6,5 temperature oversamplig
        # Bit 4,3,2 pressure oversamplig
        # Bit 1,0   power mode
        # Oversampling:
        # 000 - skipped
        # 001 - oversampling x1
        # 010 - oversampling x2
        # 011 - oversampling x4
        # 100 - oversampling x8
        # 101, 110, 111 - oversampling x16
        # Power mode:
        # 00 - sleep mode
        # 01 and 10 - forced mode (single measurement and back to sleep)
        # 11 - normal mode

        'CTRL_MEAS': 0xF4,

        #@ CONFIG
        # Bit 7,6,5 Controls t-standby in normal mode
        # 000 - 0.5 ms
        # 001 - 62.5 ms
        # 010 - 125 ms
        # 011 - 255 ms
        # 100 - 500 ms
        # 101 - 1000 ms
        # 110 - 2000 ms
        # 111 - 4000 ms
        # Bit 4,3,2 Controls time constant of the IIR filter
        # FIXME, Use filter
        # Bit 0     Enables 3-wire SPI interface when set to 1
        'CONFIG': 0xF5,

        #@ DATA_START
        # Start of data block in BMP280 memory (the same as PRESS_MSB)
        'DATA_START': 0xF7,

        #@ PRESSURE
        'PRES_MSB': 0xF7,
        'PRES_LSB': 0xF8,
        'PRES_XLSB': 0xF9,

        #@ TEMPERATURE
        'TEMP_MSB': 0xFA,
        'TEMP_LSB': 0xFB,
        'TEMP_XLSB': 0xFC,
    }

    # BMP280 commands
    BMP280_VAL = {
        #@ Chip ID Value fixed to 0x58. Useful to check if communication works
        'ID_VALUE': 0x58,

        # SPI bit to indicate READ or WRITE operation
        'READWRITE': 0x80,

        # Length of data field in bits.
        #@ FIELD_LENGTH
        'FIELD_LENGTH': 24,

        # Number of field in BMP280 memory. First field is pressure, second temperature. Block read is recommended to keep data consistency
        #@ FIELD_NUMBER
        'FIELD_NUMBER': 2,

        # Oversampling, applied to pressure and temperature
        'OVERSAMPLING_0': 0x000,
        'OVERSAMPLING_1': 0x001,
        'OVERSAMPLING_2': 0x010,
        'OVERSAMPLING_4': 0x011,
        'OVERSAMPLING_8': 0x100,
        'OVERSAMPLING_16': 0x101,

        'PRES_OVERSAMPLING_SHIFT': 2,
        'TEMP_OVERSAMPLING_SHIFT': 5,

        # Power modes
        'POWER_MODE_SLEEP': 0x00,
        'POWER_MODE_FORCED': 0x01,
        'POWER_MODE_NORMAL': 0x11,

        #'OVERSAMPLE_0_WAIT': 0.0045,
        #'OVERSAMPLE_1_WAIT': 0.0075,
        #'OVERSAMPLE_2_WAIT': 0.0135,
        #'OVERSAMPLE_3_WAIT': 0.0255,
    }

    def __init__(self):
        # Run init for super class
        super().__init__()
        self. _hw_init()
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

    def _hw_init(self):
        # SCK frequency 1 MHz
        self.delay = 1 / 1000000.0
        # GPIO initialisation
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.SCK, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.CS, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.SDI, GPIO.OUT)
        GPIO.setup(self.SDO, GPIO.IN)
        self._read_calibration_data()
        self.configure()

        # Check comunication / read ID
        ret = self._read_byte(self.BMP280_REG['ID'])
        if ret[0] != self.BMP280_VAL['ID_VALUE']:
                print("BMP280 returned {} instead of {}. Expect problems.".format(ret, self.BMP280_VAL['ID_VALUE']))

    ## Trigger calculation of pressure at the sea level on change of reference altitude
    #  @param self The python object self
    def notification(self):
        self.log.debug("notification received", extra=self.extra)
        self.calculate_pressure_at_sea_level()

    def configure(self, pressure_oversampling=16, temperature_oversampling=2, power_mode="NORMAL"):
        #FIXME make it internal and add convinience functions "ultra_low_power", "low_power", "standard_resolution" etc
        try:
            control_byte = self.BMP280_VAL['OVERSAMPLING_' + format(temperature_oversampling)] << self.BMP280_VAL['PRES_OVERSAMPLING_SHIFT']
        except KeyError:
            raise Exception('BMP280: Invalid temperature oversampling: {}. Allowed values: 0 (skip), 1, 2, 4, 8 and 16'.format(temperature_oversampling))
        try:
            control_byte |= self.BMP280_VAL['OVERSAMPLING_' + format(pressure_oversampling)] << self.BMP280_VAL['PRES_OVERSAMPLING_SHIFT']
        except KeyError:
            raise Exception('BMP280: Invalid pressure oversampling: {}. Allowed values: 0 (skip), 1, 2, 4, 8 and 16'.format(pressure_oversampling))
        try:
            control_byte |= self.BMP280_VAL['POWER_MODE_' + format(power_mode)]
        except KeyError:
            raise Exception('BMP280: Invalid power mode: {}. Allowed values: \'SLEEP\', \'FORCED\' and \'NORMAL\''.format(power_mode))
        #FIXME wait time depends on oversampling

        self._write_byte(self.BMP280_REG['CTRL_MEAS'], control_byte)

    def cleanup_gpio(self):
        # GPIO clean up
        GPIO.cleanup(self.SCK)
        GPIO.cleanup(self.CS)
        GPIO.cleanup(self.SDI)
        GPIO.cleanup(self.SDO)

    def _read_byte(self, addr):
        ret = self._spi_read(addr)
        return ret

    def _write_byte(self, addr, value):
        # Write byte of "value" to SPI interface at address "addr"
        self._spi_write(addr, value, 8)

    def _spi_write(self, addr, value, length):
        # Bit banging at address "addr"
        # Write value at addr, "length" is length of value in bits
        spi_addr = addr & (~self.BMP280_VAL['READWRITE'])

        GPIO.output(self.CS, 0)
        time.sleep(self.delay)
        # Write address
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

        # Write data
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

    def _spi_read(self, addr, block_length=1, chunk_length=8):
        # Bit banging at address "addr"
        # Reads block_length of chunks, each chunk has length in bits chunk_length
        # To read 4 bytes use block_lenght=4, chunk_length=8
        # To read 2 32 bit words use block_lenght=2, chunk_length=32
        ret_value = list()
        spi_addr = addr | self.BMP280_VAL['READWRITE']

        GPIO.output(self.CS, 0)
        time.sleep(self.delay)
        for i in range(8):
            # Write single bit to SPI
            bit = spi_addr & (0x01 << (7 - i))
            if (bit):
                    GPIO.output(self.SDI, 1)
            else:
                    GPIO.output(self.SDI, 0)
            # Flip the SCK
            GPIO.output(self.SCK, 0)
            time.sleep(self.delay)
            GPIO.output(self.SCK, 1)
            time.sleep(self.delay)

        #FIXME
        time.sleep(0.2)

        for i in range(block_length):
            chunk_value = 0
            for j in range(chunk_length):
                # Set SCK low
                GPIO.output(self.SCK, 0)
                time.sleep(self.delay)
                # Read bit
                bit = GPIO.input(self.SDO)
                # Set SCK high
                GPIO.output(self.SCK, 1)
                #Put together the read value
                chunk_value = (chunk_value << 1) | bit
                time.sleep(self.delay)
            ret_value.append(chunk_value)
        GPIO.output(self.CS, 1)
        return ret_value

    def _read_calibration_data(self):
        # Read calibration data
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_T1_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_T1_MSB'])[0])
        self.T1 = numpy.uint16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_T2_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_T2_MSB'])[0])
        self.T2 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_T3_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_T3_MSB'])[0])
        self.T3 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P1_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P1_MSB'])[0])
        self.P1 = numpy.uint16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P2_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P2_MSB'])[0])
        self.P2 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P3_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P3_MSB'])[0])
        self.P3 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P4_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P4_MSB'])[0])
        self.P4 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P5_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P5_MSB'])[0])
        self.P5 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P6_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P6_MSB'])[0])
        self.P6 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P7_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P7_MSB'])[0])
        self.P7 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P8_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P8_MSB'])[0])
        self.P8 = numpy.int16(MSB << 8 | LSB)
        LSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P9_LSB'])[0])
        MSB = numpy.uint8(self._read_byte(self.BMP280_REG['DIG_P9_MSB'])[0])
        self.P9 = numpy.int16(MSB << 8 | LSB)

    def _read_data_block(self):
        # Reads block of data containing raw pressure and temperature measurements
        data = self._spi_read(self.BMP280_REG['DATA_START'], self.BMP280_VAL['FIELD_NUMBER'], self.BMP280_VAL['FIELD_LENGTH'])
        # Last 4 bits are always 0, but are transmitted anyway, strip them
        data[0] = data[0] >> 4
        data[1] = data[1] >> 4
        return data

    def measure(self):
        #FIXME set up IIR filter
        self.configure()
        data = self._read_data_block()
        self.log.debug("data: {}".format(data), extra=self.extra)
        self._raw_pressure = numpy.int32(data[0])
        self._raw_temperture = numpy.int32(data[1])
        self.calculate_temperature()
        self.calculate_pressure()
        self.log.debug("pressure_unfiltered: {}".format(self.pressure_unfiltered), extra=self.extra)
        self.log.debug("temperature: {}".format(self.temperature), extra=self.extra)

    def calculate_pressure(self):
        # Calculate atmospheric pressure in [Pa]
        v1 = self.t_fine / 2 - 64000
        v2 = (v1 * v1 * self.P6) / 32768
        v2 = v2 + v1 * self.P5 * 2
        v2 = v2 / 4 + self.P4 * 65536
        v1 = (self.P3 * v1 * v1 / 524288 + self.P2 * v1) / 524288
        v1 = (1 + v1 / 32768) * self.P1
        p = 1048576 - self._raw_pressure
        p = ((p - v2 / 4096.0) * 6250.0) / v1
        v1 = self.P9 * p * p / 2147483648
        v2 = p * self.P8 / 32768
        self.pressure_unfiltered = p + (v1 + v2 + self.P7) / 16

    def calculate_temperature(self):
        #Calculate temperature in [degC]. It has to be performed before pressure calculations at least once.
        v1 = (self._raw_temperture / 16384 - self.T1 / 1024) * self.T2
        v2 = ((self._raw_temperture / 131072 - self.T1 / 8192) * (self._raw_temperture / 131072 - self.T1 / 8192)) * self.T3
        self.t_fine = v1 + v2
        self.temperature = self.t_fine / 5120
        self.s.parameters["temperature"]["value"] = float(self.temperature)

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

    def stop(self):
        super().stop()
        time.sleep(1)
        self.cleanup_gpio()
        self.log.debug("Stopped {}".format(__name__), extra=self.extra)
