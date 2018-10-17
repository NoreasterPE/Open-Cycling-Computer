#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ride_log
#  Module for handling ride parameters logging to file
import time
import logging
import numbers
import sensors
import sched


## Class for handling ride parameters logging
class ride_log():
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ride_log'}

    ## @var RIDE_LOG_UPDATE
    # Period of time in s between ride log update events.
    RIDE_LOG_UPDATE = 1.0

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')

        ride_log_filename = "log/ride." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
        logging.getLogger('ride').setLevel(logging.INFO)
        ride_log_handler = logging.handlers.RotatingFileHandler(ride_log_filename)
        #FIXME ridelog should be defined in config file
        ride_log_format = '%(time)-8s,%(speed)-8s,%(cadence)-8s,%(heart_rate)-5s,%(pressure)-8s,%(temperature)-8s,%(altitude)-8s,%(odometer)-8s,%(slope)-8s'
        ride_log_handler.setFormatter(logging.Formatter(ride_log_format))
        logging.getLogger('ride').addHandler(ride_log_handler)
        self.ride_logger = logging.getLogger('ride')
        self.ride_logger.info('', extra={'time': "Time", 'speed': "Speed", 'cadence': "Cadence",
                                         'heart_rate': "Heart RT", 'pressure': "Pressure", 'temperature': "Temp",
                                         'altitude': "Altitude", 'odometer': "Odometer", 'slope': "Slope"})
        self.s = sensors.sensors()
        ## @var event_scheduler
        self.event_scheduler = sched.scheduler(time.time, time.sleep)

    def schedule_update_event(self):
        self.log.debug("schedule_update_event started", extra=self.extra)
        self.add_entry()
        if not self.stopping:
            #Setting up next update event
            self.event_scheduler.enter(self.RIDE_LOG_UPDATE, 1, self.schedule_update_event)
            t = self.event_scheduler.run(blocking=False)
            self.log.debug("Event scheduler, next event in: {0:.3f}".format(t), extra=self.extra)
        self.log.debug("schedule_update_event finished", extra=self.extra)

    def stop(self):
        self.stopping = True

    def start(self):
        self.stopping = False
        self.log.debug("Setting up event scheduler", extra=self.extra)
        #self.event_scheduler.enter(self.RIDE_LOG_UPDATE, 1, self.schedule_update_event)
        self.schedule_update_event()
        self.log.debug("Start finished", extra=self.extra)

    def add_entry(self):
        self.log.debug("Adding ride log entry", extra=self.extra)
        try:
            tme = numbers.sanitise(self.s.parameters["real_time"]["value"])
            hrt = numbers.sanitise(self.s.parameters["heart_rate"]["value"])
            spd = numbers.sanitise(self.s.parameters["speed"]["value"])
            cde = numbers.sanitise(self.s.parameters["cadence"]["value"])
            pre = numbers.sanitise(self.s.parameters["pressure"]["value"])
            tem = numbers.sanitise(self.s.parameters["temperature"]["value"])
            alt = numbers.sanitise(self.s.parameters["altitude"]["value"])
            odo = numbers.sanitise(self.s.parameters["odometer"]["value"])
            slp = numbers.sanitise(self.s.parameters["slope"]["value"])

            self.ride_logger.info('', extra={'time': tme, 'speed': spd, 'cadence': cde,
                                             'heart_rate': hrt, 'pressure': pre, 'temperature': tem,
                                             'altitude': alt, 'odometer': odo, 'slope': slp})
        except KeyError:
            self.log.debug("Not all parameters for ride log are ready, waiting...", extra=self.extra)
        self.log.debug("Adding ride log entry finished", extra=self.extra)
