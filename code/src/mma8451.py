#! /usr/bin/python
## @package mma8451
#   Module for MMA8451 Triple-Axis Accelerometer w/ 14-bit ADC with I2C interface as sold by Adafruit'. Not yet used by the OCC

import smbus
import threading
import time


## Class for MMA8451 Triple-Axis Accelerometer w/ 14-bit ADC with I2C interface as sold by Adafruit'. Not yet used by the OCC
class mma8451(threading.Thread):
    DEVICE_ADDR = 29
    DEVICE_ID = 26
    REG_STATUS = 0
    REG_OUT_X_MSB = 1
    REG_OUT_X_LSB = 2
    REG_OUT_Y_MSB = 3
    REG_OUT_Y_LSB = 4
    REG_OUT_Z_MSB = 5
    REG_OUT_Z_LSB = 6
    REG_SYSMOD = 11
    REG_WHOAMI = 13
    REG_XYZ_DATA_CFG = 14
    REG_XYZ_HPF = 16
    REG_PL_STATUS = 16
    REG_PL_CFG = 17
    REG1_CTRL = 42
    REG2_CTRL = 43
    REG4_CTRL = 45
    REG5_CTRL = 46
    OFF_X = 47
    OFF_Y = 48
    OFF_Z = 49
    REG_XYZ_RANGE_8_G = 2
    REG_XYZ_RANGE_4_G = 1
    REG_XYZ_RANGE_2_G = 0
    REG1_ACTIVE = 1
    REG1_STANDBY = 16
    REG1_FAST_READ = 2
    REG1_LOW_NOISE = 4
    REG1_ODR = 56
    REG1_ODR_800_HZ = 0
    REG1_ODR_400_HZ = 8
    REG1_ODR_200_HZ = 16
    REG1_ODR_100_HZ = 24
    REG1_ODR_50_HZ = 32
    REG1_ODR_12_5_HZ = 40
    REG1_ODR_6_25HZ = 48
    REG1_ODR_1_56_HZ = 56
    REG1_ODR_RANGE = (REG1_ODR_800_HZ,
                      REG1_ODR_400_HZ,
                      REG1_ODR_200_HZ,
                      REG1_ODR_100_HZ,
                      REG1_ODR_50_HZ,
                      REG1_ODR_12_5_HZ,
                      REG1_ODR_6_25HZ,
                      REG1_ODR_1_56_HZ)
    REG2_AUTOSLEEP = 4
    REG2_RESET = 64
    REG2_SELF_TEXT = 128
    REG2_ACTIVE_OS_NORMAL = 0
    REG2_ACTIVE_OS_LNOISE_LPOWER = 1
    REG2_ACTIVE_OS_HIGH_RESOLUTION = 2
    REG2_ACTIVE_OS_LOW_POWER = 3
    REG2_SLEEP_OS_NORMAL = 0
    REG2_SLEEP_OS_LNOISE_LPOWER = 8
    REG2_SLEEP_OS_HIGH_RESOLUTION = 16
    REG2_SLEEP_OS_LOW_POWER = 24

    def __init__(self):
        super(mma8451, self).__init__()
        self.measurement_delay = 0.01
        self.bus = smbus.SMBus(1)
        self.check_id()
        self.write_byte_data(self.REG2_CTRL, self.REG2_RESET)
        while self.read_byte_data(self.REG2_CTRL) & self.REG2_RESET:
            pass

        self.write_byte_data(self.REG_XYZ_DATA_CFG, self.REG_XYZ_RANGE_2_G)
        self.step = 0.00025
        self.sensor_range = self.REG_XYZ_RANGE_2_G
        self.write_byte_data(
            self.REG2_CTRL, self.REG2_ACTIVE_OS_HIGH_RESOLUTION)
        self.write_byte_data(self.REG1_CTRL, self.REG1_LOW_NOISE)
        self.write_byte_data(self.REG1_CTRL, self.REG1_ACTIVE)
        self.acceleration = (0, 0, 0)

    def read_byte_data(self, register):
        ret = self.bus.read_byte_data(self.DEVICE_ADDR, register)
        time.sleep(self.measurement_delay)
        return ret

    def write_byte_data(self, register, value):
        self.bus.write_byte_data(self.DEVICE_ADDR, register, value)
        time.sleep(self.measurement_delay)

    def check_id(self):
        i = 1
        while i < 10:
            ret = self.read_byte_data(self.REG_WHOAMI)
            if ret == self.DEVICE_ID:
                return
            print 'ret=', ret, ' Expected:', self.DEVICE_ID, ' Sensor mmt8451 not found. Trying again [{}] in 1 s...'.format(i)
            time.sleep(1)
            i += 1

        raise Exception('Sensor MMA8451 not found')

    def read_raw_xyz(self):
        xm = self.read_byte_data(self.REG_OUT_X_MSB)
        xl = self.read_byte_data(self.REG_OUT_X_LSB)
        ym = self.read_byte_data(self.REG_OUT_Y_MSB)
        yl = self.read_byte_data(self.REG_OUT_Y_LSB)
        zm = self.read_byte_data(self.REG_OUT_Z_MSB)
        zl = self.read_byte_data(self.REG_OUT_Z_LSB)
        x = self.get_int_value(xm, xl)
        y = self.get_int_value(ym, yl)
        z = self.get_int_value(zm, zl)
        return (x, y, z)

    def read_xyz(self):
        _x, _y, _z = self.read_raw_xyz()
        x = _x * self.step
        y = _y * self.step
        z = _z * self.step
        return (x, y, z)

    def get_int_value(self, val_m, val_l):
        v = ((val_m << 8 | val_l) & 65533) >> 2
        if v & 8192:
            v = -16384 + v
        return v

    def set_high_pass_filter(self):
        self.bus.write_byte_data(
            self.DEVICE_ADDR, self.REG1_CTRL, self.REG1_STANDBY)
        self.bus.write_byte_data(
            self.DEVICE_ADDR, self.REG_XYZ_DATA_CFG, self.REG_XYZ_HPF)
        self.bus.write_byte_data(
            self.DEVICE_ADDR, self.REG1_CTRL, self.REG1_ACTIVE)
        return 0

    def set_range(self, value):
        if value == 2:
            sensor_range = self.REG_XYZ_RANGE_2_G
            self.step = 0.00025
        elif value == 4:
            sensor_range = self.REG_XYZ_RANGE_4_G
            self.step = 0.0005
        elif value == 8:
            sensor_range = self.REG_XYZ_RANGE_8_G
            self.step = 0.001
        else:
            raise Exception('MMA8451: Invalid range: {}'.format(value))
        self.bus.write_byte_data(self.DEVICE_ADDR, self.REG1_CTRL, 0)
        self.bus.write_byte_data(
            self.DEVICE_ADDR, self.REG_XYZ_DATA_CFG, sensor_range)
        self.bus.write_byte_data(
            self.DEVICE_ADDR, self.REG1_CTRL, self.REG1_ACTIVE)

    def get_data_rate_in_hz(self):
        r1 = self.read_byte_data(self.REG1_CTRL)
        r = r1 & self.REG1_ODR
        if r == self.REG1_ODR_1_56_HZ:
            rate = 1.56
        elif r == self.REG1_ODR_6_25HZ:
            rate = 6.26
        elif r == self.REG1_ODR_12_5_HZ:
            rate = 12.5
        elif r == self.REG1_ODR_50_HZ:
            rate = 50
        elif r == self.REG1_ODR_100_HZ:
            rate = 100
        elif r == self.REG1_ODR_200_HZ:
            rate = 200
        elif r == self.REG1_ODR_400_HZ:
            rate = 400
        elif r == self.REG1_ODR_800_HZ:
            rate = 800
        else:
            raise Exception(
                'MMA8451: Unknown output data rate returned by hardware: {}').format(r)
        return rate

    def set_data_rate(self, rate):
        if rate in self.REG1_ODR_RANGE:
            r1 = self.read_byte_data(self.REG1_CTRL)
            r1_new = r1 & ~self.REG1_ODR
            r1_new = r1_new | rate
            self.bus.write_byte_data(self.DEVICE_ADDR, self.REG1_CTRL, 0)
            self.bus.write_byte_data(self.DEVICE_ADDR, self.REG1_CTRL, r1_new)
        else:
            raise Exception(
                'MMA8451: Invalid output data rate: {}').format(rate)

    def calibrate(self):
        self.set_range(2)
        self.set_data_rate(self.REG1_ODR_200_HZ)
        _x, _y, _z = self.read_raw_xyz()
        x_offset = 255 & -1 * int(_x / 8.0 - 1)
        y_offset = 255 & -1 * int(_y / 8.0 - 1)
        z_offset = 255 & -1 * int((4096.0 - _z) / 8.0 - 1.0)
        self.write_byte_data(self.REG1_CTRL, self.REG1_STANDBY)
        self.write_byte_data(self.OFF_X, x_offset)
        self.write_byte_data(self.OFF_Y, y_offset)
        self.write_byte_data(self.OFF_Z, z_offset)
        self.write_byte_data(self.REG1_CTRL, self.REG1_ACTIVE)

    def run(self):
        self.running = True
        while self.running is True:
            self.acceleration = self.read_xyz()
            time.sleep(self.measurement_delay)

    def stop(self):
        self.running = False
