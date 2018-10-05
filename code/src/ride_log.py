#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ride_log
#  Module for handling ride parameters logging to file
from time import strftime
import logging


## Class for handling ride parameters logging
class ride_log():
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ride_log'}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        ride_log_filename = "log/ride." + strftime("%Y-%m-%d-%H:%M:%S") + ".log"
        logging.getLogger('ride').setLevel(logging.INFO)
        ride_log_handler = logging.handlers.RotatingFileHandler(ride_log_filename)
        #FIXME ridelog should be defined in config file
        ride_log_format = '%(time)-8s,%(dtime)-8s,%(speed)-8s,%(cadence)-8s,%(ble_hr_heart_rate)-5s,%(pressure)-8s,%(temperature)-8s,%(altitude)-8s,%(distance)-8s,%(slope)-8s'
        ride_log_handler.setFormatter(logging.Formatter(ride_log_format))
        logging.getLogger('ride').addHandler(ride_log_handler)
        self.ride_logger = logging.getLogger('ride')
        self.ride_logger.info('', extra={'time': "Time", 'dtime': "Delta", 'speed': "Speed",
                                         'cadence': "Cadence", 'ble_hr_heart_rate': "Heart RT",
                                         'pressure': "Pressure", 'temperature': "Temp",
                                         'altitude': "Altitude", 'distance': "Distance", 'slope': "Slope"})

    def add_entry(self, params):
        try:
            slp = params["compute_slope"]
        except KeyError:
            slp = "-"
        try:
            hrt = params["ble_hr_heart_rate"]
        except KeyError:
            hrt = "-"
        tme = params["timeon_hms"]
        spd = params["speed"]
        try:
            cde = params["ble_sc_cadence"]
        except KeyError:
            cde = "-"
        try:
            dte = params["time_delta"]
        except KeyError:
            dte = "-"
        try:
            pre = params["bmp183_pressure"]
        except KeyError:
            pre = "-"
        try:
            tem = params["bmp183_temperature"]
        except KeyError:
            tem = "-"
        try:
            alt = params["bmp183_altitude"]
        except KeyError:
            alt = "-"
        dst = params["distance"]
        self.ride_logger.info('', extra={'time': tme, 'dtime': dte, 'speed': spd, 'cadence': cde,
                                         'ble_hr_heart_rate': hrt, 'pressure': pre, 'temperature': tem,
                                         'altitude': alt, 'distance': dst, 'slope': slp})
