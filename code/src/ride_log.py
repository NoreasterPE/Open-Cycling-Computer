#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ride_log
#  Module for handling ride parameters logging to file
import time
import logging
import numbers
import sensor
import sensors


## Class for handling ride parameters logging
class ride_log(sensor.sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ride_log'}

    ## @var RIDE_LOG_UPDATE
    # Period of time in s between ride log update events.
    RIDE_LOG_UPDATE = 0.9

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')

        ride_log_filename = "log/ride." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
        logging.getLogger('ride').setLevel(logging.INFO)
        ride_log_handler = logging.handlers.RotatingFileHandler(ride_log_filename)
        #FIXME ridelog should be defined in config file
        ride_log_format = '%(time)-12s,%(speed)-12s,%(cadence)-12s,%(heart_rate)-5s,%(pressure)-12s,%(pressure_nof)-12s,%(temperature)-12s,%(altitude)-12s,%(odometer)-12s,%(slope)-12s'
        ride_log_handler.setFormatter(logging.Formatter(ride_log_format))
        logging.getLogger('ride').addHandler(ride_log_handler)
        self.ride_logger = logging.getLogger('ride')
        self.ride_logger.info('', extra={'time': "Time", 'speed': "Speed", 'cadence': "Cadence",
                                         'heart_rate': "Heart RT", 'pressure': "Pressure", 'pressure_nof': "Pressure nof", 'temperature': "Temp",
                                         'altitude': "Altitude", 'odometer': "Odometer", 'slope': "Slope"})
        self.s = sensors.sensors()
        self.s.request_parameter("real_time", self.extra["module_name"])
        self.last_log_entry = 0.0

    def notification(self):
        self.log.debug("notification received", extra=self.extra)
        if self.s.parameters['real_time']['value'] is not None:
            if self.s.parameters['real_time']['value'] - self.last_log_entry > self.RIDE_LOG_UPDATE:
                self.last_log_entry = self.s.parameters['real_time']['value']
                self.add_entry()

    def add_entry(self):
        self.log.debug("Adding ride log entry", extra=self.extra)
        try:
            tme = numbers.sanitise(self.s.parameters["real_time"]["value"])
            hrt = numbers.sanitise(self.s.parameters["heart_rate"]["value"])
            spd = numbers.sanitise(self.s.parameters["speed"]["value"])
            cde = numbers.sanitise(self.s.parameters["cadence"]["value"])
            pre = numbers.sanitise(self.s.parameters["pressure"]["value"])
            prn = numbers.sanitise(self.s.parameters["pressure_nof"]["value"])
            tem = numbers.sanitise(self.s.parameters["temperature"]["value"])
            alt = numbers.sanitise(self.s.parameters["altitude"]["value"])
            odo = numbers.sanitise(self.s.parameters["odometer"]["value"])
            slp = numbers.sanitise(self.s.parameters["slope"]["value"])

            self.ride_logger.info('', extra={'time': tme, 'speed': spd, 'cadence': cde,
                                             'heart_rate': hrt, 'pressure': pre, 'pressure_nof': prn, 'temperature': tem,
                                             'altitude': alt, 'odometer': odo, 'slope': slp})
        except KeyError:
            self.log.debug("Not all parameters for ride log are ready, waiting...", extra=self.extra)
        self.log.debug("Adding ride log entry finished", extra=self.extra)
