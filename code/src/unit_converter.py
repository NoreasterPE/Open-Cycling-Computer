#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package units
#  Package for converting units. When run independently shows a pseudo-test.


## Main unit converter class
#  Allows conversion of a value in source unit to target unit.
class unit_converter():

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        self.distance = {"m": 1.0, "km": 1000.0, "mi": 1609.344, "yd": 0.9144}
        self.temperature = {"C", "F"}
        self.speed = {"m/s": 1.0, "km/h": 0.2777778, "mi/h": 0.44704}
        self.mass = {"kg": 1.0, "st": 6.350293}
        self.slope = {"%", "m/m"}
        self.pressure = {"Pa": 1.0, "hPa": 100.0, "kPa": 1000.0}

    ## Main convert function. Returns value in target units
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert(self, value, source_unit, target_unit):
        if source_unit == target_unit:
            return value
        if ((source_unit in self.distance) and (target_unit in self.distance)):
            return self.convert_distance(value, source_unit, target_unit)
        if ((source_unit in self.temperature) and (target_unit in self.temperature)):
            return self.convert_temperature(value, source_unit, target_unit)
        if ((source_unit in self.speed) and (target_unit in self.speed)):
            return self.convert_speed(value, source_unit, target_unit)
        if ((source_unit in self.mass) and (target_unit in self.mass)):
            return self.convert_mass(value, source_unit, target_unit)
        if ((source_unit in self.slope) and (target_unit in self.slope)):
            return self.convert_slope(value, source_unit, target_unit)
        if ((source_unit in self.pressure) and (target_unit in self.pressure)):
            return self.convert_pressure(value, source_unit, target_unit)

    def convert_distance(self, value, source_unit, target_unit):
        return value * self.distance[source_unit] / self.distance[target_unit]

    ## Temperature conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_temperature(self, value, source_unit, target_unit):
        if source_unit == target_unit:
            result = value
        elif target_unit == "C":
            result = (value - 32) / 1.8
        elif target_unit == "F":
            result = (value * 1.8) + 32
        return result

    ## Speed conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_speed(self, value, source_unit, target_unit):
        return value * self.speed[source_unit] / self.speed[target_unit]

    ## Mass conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_mass(self, value, source_unit, target_unit):
        return value * self.mass[source_unit] / self.mass[target_unit]

    ## Slope conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_slope(self, value, source_unit, target_unit):
        if source_unit == target_unit:
            result = value
        elif target_unit == "%":
            result = 100 * value
        elif target_unit == "m/m":
            result = 0.01 * value
        return result

    ## Pressure conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_pressure(self, value, source_unit, target_unit):
        return value * self.pressure[source_unit] / self.pressure[target_unit]


if __name__ == '__main__':
    u = unit_converter()

    tC = 20  # C
    print("C: {} F: {}".format(tC, u.convert(tC, "C", "F")))

    tF = 68  # F
    print("F: {} C: {}".format(tF, u.convert(tF, "F", "C")))

    dist = 1854.3  # m
    print("m: {} km: {} mi: {} yd: {}".format(dist, u.convert(dist, "m", "km"), u.convert(dist, "m", "mi"), u.convert(dist, "m", "yd")))

    mass = 79.5  # kg
    print("kg: {} st: {}".format(mass, u.convert(mass, "kg", "st")))

    speed = 10  # m/s
    print("m/s: {} km/h: {} mi/hh: {}".format(speed, u.convert(speed, "m/s", "km/h"), u.convert(speed, "m/s", "mi/h")))

    slope = 0.013  # m/m
    print("m/m: {} %: {}".format(slope, u.convert(slope, "m/m", "%")))

    slope = 10  # %
    print("%: {} m/m: {}".format(slope, u.convert(slope, "%", "m/m")))

    pressure = 101013  # Pa
    print("Pa: {} hPa: {} kPa: {}".format(pressure, u.convert(pressure, "Pa", "hPa"), u.convert(pressure, "Pa", "kPa")))
