#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package units
#  Package for converting units. When run independently shows a pseudo-test.
#  This is not a general unit converter as it always converts from default units used by ride_parameters module.


## Main units class
#  Allows conversion of a value in source unit to target unit. Source unit is always the same as default unit from ride_parameters. I.e. for temperature it's degree Celsius, for mass it's kilogram, etc.
class units():

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        pass

    ## Main convert function. Returns value in target units
    #  @param self The python object self
    #  @param value value in source units. Source units are default units from ride_parameters module
    #  @param target_unit target unit
    def convert(self, value, target_unit):
        conversions = {'F': self.temp_C_to_F(value),
                       'K': self.temp_C_to_K(value),
                       "km/h": self.speed_ms_to_kmh(value),
                       "mi/h": self.speed_ms_to_mph(value),
                       "st": self.mass_kg_to_st(value),
                       "lb": self.mass_kg_to_lb(value),
                       "km": self.dist_m_to_km(value),
                       "mi": self.dist_m_to_mi(value),
                       "yd": self.dist_m_to_yd(value),
                       "%": self.m_m_to_percent(value),
                       "hPa": self.pressure_Pa_to_hPa(value),
                       'C': value,
                       "Pa": value,
                       "kg": value,
                       "s": value,
                       "RPM": value,
                       "BPM": value,
                       "m/s": value,
                       "m/m": value,
                       "m": value,
                       "": value}
        return conversions[target_unit]

    ## Celsius to Farrenheit conversion
    #  @param self The python object self
    #  @param temp temperature in Celsius
    def temp_C_to_F(self, temp):
        tF = temp * 1.8 + 32
        return tF

    ## Celsius to Kelvin conversion
    #  @param self The python object self
    #  @param temp temperature in Celsius
    def temp_C_to_K(self, temp):
        tK = 273.15 + temp
        return tK

    ## meters per second to kilometers per second conversion
    #  @param self The python object self
    #  @param speed in meters per second
    def speed_ms_to_kmh(self, speed):
        s_kmh = speed * 3.6
        return s_kmh

    ## meters per second to miles per second conversion
    #  @param self The python object self
    #  @param speed in meters per second
    def speed_ms_to_mph(self, speed):
        s_mph = speed * 2.23694
        return s_mph

    ## kilograms to stones conversion
    #  @param self The python object self
    #  @param mass in kilograns
    def mass_kg_to_st(self, mass):
        m_st = mass * 0.15747
        # m_lb = (mass - (m_st / 0.15747)) * 2.2046
        # return (m_st, m_lb)
        return m_st

    ## kilograms to pounds conversion
    #  @param self The python object self
    #  @param mass in kilograns
    def mass_kg_to_lb(self, mass):
        m_lb = mass * 2.2046
        return m_lb

    ## meters to kilometers conversion
    #  @param self The python object self
    #  @param distance in meters
    def dist_m_to_km(self, dist):
        d_km = dist / 1000
        return d_km

    ## meters to miles conversion
    #  @param self The python object self
    #  @param distance in meters
    def dist_m_to_mi(self, dist):
        d_mi = dist / 1609.344
        return d_mi

    ## meters to yards conversion
    #  @param self The python object self
    #  @param distance in meters
    def dist_m_to_yd(self, dist):
        d_yd = dist / 0.9144
        return d_yd

    ## unitless to percent conversion
    #  @param self The python object self
    #  @param unitless value
    def m_m_to_percent(self, value):
        v = 100 * value
        return v

    ## Pascal to hectopascal conversion
    #  @param self The python object self
    #  @param value in Pascals
    def pressure_Pa_to_hPa(self, value):
        v = value / 100.0
        return v


if __name__ == '__main__':
    u = units()

    tC = 20  # C
    print("C {} F {} K {}".format(tC, u.convert(tC, "F"), u.convert(tC, "K")))

    dist = 1854.3
    print("m {} km {} mi {} yd {}".format(dist, u.convert(dist, "km"), u.convert(dist, "mi"), u.convert(dist, "yd")))

    mass = 79.5
    print("kg {} lb {}".format(mass, u.convert(mass, "lb")))

    speed = 10
    print("m/s {} km/h {} mph {}".format(speed, u.convert(speed, "km/h"), u.convert(speed, "mi/h")))

    slope = 0.013
    print("m/m {} % {}".format(slope, u.convert(slope, "%")))
    pressure = 101013
    print("Pa {} hPa {}".format(pressure, u.convert(pressure, "hPa")))
