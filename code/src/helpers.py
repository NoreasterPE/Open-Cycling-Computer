#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## @package helpers
# Different helper classes used by pyplum and plugins

import math

class num():
    ## @var INF_MIN
    # helper variable, minus infinity
    INF_MIN = float("-inf")

    ## @var INF
    # helper variable, infinity
    INF = float("inf")

    ## @var NAN
    # helper variable, not-a-number
    NAN = float("nan")


    def sanitise(value):
        if value == '-0' or value == '-0.0':
            value = "0"
        try:
            if math.isinf(float(value)) or \
                    math.isnan(float(value)):
                value = '-'
        except (ValueError, TypeError):
            #Don't deal with invalid types or values
            pass
        return value


import ctypes as ct
import cairo

_initialized = False


def create_cairo_font_face_for_file(filename, faceindex=0, loadoptions=0):
    "given the name of a font file, and optional faceindex to pass to FT_New_Face" \
        " and loadoptions to pass to cairo_ft_font_face_create_for_ft_face, creates" \
        " a cairo.FontFace object that may be used to render text with that font."
    global _initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _ft_destroy_key
    global _surface

    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _initialized:
        # find shared objects
        _freetype_so = ct.CDLL("libfreetype.so.6")
        _cairo_so = ct.CDLL("libcairo.so.2")
        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ct.c_void_p, ct.c_int]
        _cairo_so.cairo_font_face_get_user_data.restype = ct.c_void_p
        _cairo_so.cairo_font_face_get_user_data.argtypes = (ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_font_face_set_user_data.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_set_font_face.argtypes = [ct.c_void_p, ct.c_void_p]
        _cairo_so.cairo_font_face_status.argtypes = [ct.c_void_p]
        _cairo_so.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
        _cairo_so.cairo_status.argtypes = [ct.c_void_p]
        # initialize freetype
        _ft_lib = ct.c_void_p()
        status = _freetype_so.FT_Init_FreeType(ct.byref(_ft_lib))
        if status != FT_Err_Ok:
            raise RuntimeError("Error %d initializing FreeType library." % status)
        # end if

        class PycairoContext(ct.Structure):
            _fields_ = \
                [
                    ("PyObject_HEAD", ct.c_byte * object.__basicsize__),
                    ("ctx", ct.c_void_p),
                    ("base", ct.c_void_p),
                ]
        # end PycairoContext

        _surface = cairo.ImageSurface(cairo.FORMAT_A8, 0, 0)
        _ft_destroy_key = ct.c_int()  # dummy address
        _initialized = True
    # end if

    ft_face = ct.c_void_p()
    cr_face = None
    try:
        # load FreeType face
        status = _freetype_so.FT_New_Face(_ft_lib, filename.encode("utf-8"), faceindex, ct.byref(ft_face))
        if status != FT_Err_Ok:
            raise RuntimeError("Error %d creating FreeType font face for %s" % (status, filename))
        # end if

        # create Cairo font face for freetype face
        cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
        status = _cairo_so.cairo_font_face_status(cr_face)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        # end if
        # Problem: Cairo doesn't know to call FT_Done_Face when its font_face object is
        # destroyed, so we have to do that for it, by attaching a cleanup callback to
        # the font_face. This only needs to be done once for each font face, while
        # cairo_ft_font_face_create_for_ft_face will return the same font_face if called
        # twice with the same FT Face.
        # The following check for whether the cleanup has been attached or not is
        # actually unnecessary in our situation, because each call to FT_New_Face
        # will return a new FT Face, but we include it here to show how to handle the
        # general case.
        if _cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(_ft_destroy_key)) is None:
            status = _cairo_so.cairo_font_face_set_user_data(cr_face,
                                                             ct.byref(_ft_destroy_key),
                                                             ft_face,
                                                             _freetype_so.FT_Done_Face)
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError("Error %d doing user_data dance for %s" % (status, filename))
            # end if
            ft_face = None  # Cairo has stolen my reference
        # end if

        # set Cairo font face into Cairo context
        cairo_ctx = cairo.Context(_surface)
        cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx
        _cairo_so.cairo_set_font_face(cairo_t, cr_face)
        status = _cairo_so.cairo_font_face_status(cairo_t)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        # end if

    finally:
        _cairo_so.cairo_font_face_destroy(cr_face)
        _freetype_so.FT_Done_Face(ft_face)
    # end try

    # get back Cairo font face as a Python object
    face = cairo_ctx.get_font_face()
    return face

##  Class providing scalar version of Kalman filter. 
class kalman():
    'Class for Kalman filter helper'
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self, Q=None, R=None, P=None, P_previous=None, K=None):
        # FIXME Add detailed comments
        # R is the measurement noise covariance (sensor noise), Q is the process noise covariance
        # P, P_previous and K are self tuning
        if Q is not None:
            #self.Q = 0.02
            self.Q = Q
        else:
            self.Q = 0.02
        # Estimate of measurement variance, sensor noise
        if R is not None:
            #self.R = 1.0
            self.R = R
        else:
            self.R = 1.0
        # Error
        if P is not None:
            #self.P = 0.245657137142
            self.P = P
        else:
            self.P = 0.245657137142
        # First previous error
        if P_previous is not None:
            #self.P_previous = 0.325657137142
            self.P_previous = P_previous
        else:
            self.P_previous = 0.325657137142
        # First gain
        if K is not None:
            #self.K = 0.245657137142
            self.K = K
        else:
            self.K = 0.245657137142

    def set_initial_value(self, value_unfiltered):
        # First estimate
        self.value_estimate = value_unfiltered
        # First previous estimate
        self.value_estimate_previous = value_unfiltered
        # Value unfiltered aka raw measurement
        self.value_unfiltered = value_unfiltered

    def update_unfiltered_value(self, value_unfiltered):
        # Value unfiltered aka raw measurement
        self.value_unfiltered = value_unfiltered

    def update(self):
        # FIXME Add detailed commants
        z = self.value_unfiltered
        # Save previous value
        self.value_estimate_previous = self.value_estimate
        # Save previous error
        self.P_previous = self.P + self.Q
        # Calculate current gain
        self.K = self.P_previous / (self.P_previous + self.R)
        # Calculate new estimate
        self.value_estimate = self.value_estimate_previous + self.K * (z - self.value_estimate_previous)
        # Calculate new error estimate
        self.P = (1 - self.K) * self.P_previous


## Unit converter class
#  Allows conversion of a value from a source unit to a target unit.
class unit_converter():

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        self.distance = {"m": 1.0, "km": 1000.0, "mi": 1609.344, "yd": 0.9144, "ft": 0.3048, "in": 0.0254, "cm": 0.01, "mm": 0.001}
        self.temperature = {"C", "F"}
        self.speed = {"m/s": 1.0, "km/h": 0.2777778, "mi/h": 0.44704}
        self.mass = {"kg": 1.0, "st": 6.350293, "lb": 0.4535924}
        self.slope = {"%", "m/m"}
        self.pressure = {"Pa": 1.0, "hPa": 100.0, "kPa": 1000.0, "mmHg": 133.322, "inHg":3386.375258}

    ## Main convert function. Returns value in target units
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert(self, value, source_unit, target_unit):
        if source_unit == target_unit:
            return value
        if value is None:
            return value
        if source_unit is None or target_unit is None:
            return None
        try:
            value = float(value)
        except TypeError:
            print("Can't convert value: {} to float".format(value))
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
        result = num.NAN
        try:
            result = value * self.distance[source_unit] / self.distance[target_unit]
        except TypeError:
            print("Failed to convert distance value {}, source unit: {}, target_unit: {}".format(value, source_unit, target_unit))
        return result

    ## Temperature conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_temperature(self, value, source_unit, target_unit):
        result = num.NAN
        try:
            if source_unit == target_unit:
                result = value
            elif target_unit == "C":
                result = (value - 32) / 1.8
            elif target_unit == "F":
                result = (value * 1.8) + 32
        except TypeError:
            print("Failed to convert temperature value {}, source unit: {}, target_unit: {}".format(value, source_unit, target_unit))
        return result

    ## Speed conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_speed(self, value, source_unit, target_unit):
        result = num.NAN
        try:
            result = value * self.speed[source_unit] / self.speed[target_unit]
        except TypeError:
            print("Failed to convert speed value {}, source unit: {}, target_unit: {}".format(value, source_unit, target_unit))
        return result

    ## Mass conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_mass(self, value, source_unit, target_unit):
        result = num.NAN
        try:
            result = value * self.mass[source_unit] / self.mass[target_unit]
        except TypeError:
            print("Failed to convert mass value {}, source unit: {}, target_unit: {}".format(value, source_unit, target_unit))
        return result

    ## Slope conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_slope(self, value, source_unit, target_unit):
        result = num.NAN
        try:
            if source_unit == target_unit:
                result = value
            elif target_unit == "%":
                result = 100 * value
            elif target_unit == "m/m":
                result = 0.01 * value
        except TypeError:
            print("Failed to convert slope value {}, source unit: {}, target_unit: {}".format(value, source_unit, target_unit))
        return result

    ## Pressure conversion
    #  @param self The python object self
    #  @param value value in source units
    #  @param source_unit source unit
    #  @param target_unit target unit
    def convert_pressure(self, value, source_unit, target_unit):
        result = num.NAN
        try:
            result = value * self.pressure[source_unit] / self.pressure[target_unit]
        except TypeError:
            print("Failed to convert mass value {}, source unit: {}, target_unit: {}".format(value, source_unit, target_unit))
        return result


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

    mass = 79.5  # kg
    print("kg: {} lb: {}".format(mass, u.convert(mass, "kg", "lb")))

    speed = 10  # m/s
    print("m/s: {} km/h: {} mi/h: {}".format(speed, u.convert(speed, "m/s", "km/h"), u.convert(speed, "m/s", "mi/h")))

    slope = 0.013  # m/m
    print("m/m: {} %: {}".format(slope, u.convert(slope, "m/m", "%")))

    slope = 10  # %
    print("%: {} m/m: {}".format(slope, u.convert(slope, "%", "m/m")))

    pressure = 101013  # Pa
    print("Pa: {} hPa: {} kPa: {}".format(pressure, u.convert(pressure, "Pa", "hPa"), u.convert(pressure, "Pa", "kPa")))



## wheel class
#  Helper module providing wheel size based on tyre size/width.
class wheel:

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        #FIXME move to csv file, add more wheels
        self.wheel_circ = {}
        self.wheel_circ['700X18C'] = 2.070
        self.wheel_circ['700X19C'] = 2.080
        self.wheel_circ['700X20C'] = 2.086
        self.wheel_circ['700X23C'] = 2.096
        self.wheel_circ['700X25C'] = 2.105
        self.wheel_circ['700X28C'] = 2.136
        self.wheel_circ['700X30C'] = 2.146
        self.wheel_circ['700X32C'] = 2.155
        self.wheel_circ['700X35C'] = 2.168
        self.wheel_circ['700X38C'] = 2.180
        self.wheel_circ['700X40C'] = 2.200
        self.wheel_circ['700X42C'] = 2.224
        self.wheel_circ['700X44C'] = 2.235
        self.wheel_circ['700X45C'] = 2.242
        self.wheel_circ['700X47C'] = 2.268

    ## Helper function returning wheel size in meters
    #  @param self The python object self
    #  @param name String describing wheel, i.e. 700x25C
    def get_circumference(self, name):
            return self.wheel_circ[name.upper()]

    ## Helper function returning all allowed values for wheel size
    #  @param self The python object self
    def get_allowed_values(self):
        return ('700X18C', '700X19C', '700X20C', '700X23C', '700X25C', '700X28C', '700X30C', '700X32C',
                '700X35C', '700X38C', '700X40C', '700X42C', '700X44C', '700X45C', '700X47C')
