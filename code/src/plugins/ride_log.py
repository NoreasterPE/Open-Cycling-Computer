#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ride_log
#  Module for handling ride parameters logging to file
import datetime
import logging
import plugin
import pyplum
import time
import yaml


## Class for handling ride parameters logging
class ride_log(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## @var RIDE_LOG_UPDATE
    # Period of time in s between ride log update events.
    RIDE_LOG_UPDATE = 0.9

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.pm = pyplum.pyplum()
        self.pm.request_parameter("real_time", self.extra["module_name"])
        self.last_log_entry = 0.0
        self.pm.request_parameter("ride_log_config", self.extra["module_name"])
        try:
            self.ride_log_config = self.pm.parameters['ride_log_config']['value']
        except KeyError:
            elf.ride_log_config = None
        self.log_initialised = False
        if self.ride_log_config is not None:
            self.read_config()
            self.init_log()

    ## Function that reads config file with ride_log format
    #  @param self The python object self
    def read_config(self):
        self.log.debug("read_config started", extra=self.extra)
        try:
            with open(self.ride_log_config) as f:
                self.config_params = yaml.safe_load(f)
        except IOError:
            self.log.error("I/O Error when trying to parse rede log config file. Overwriting with copy of ride log base_config", extra=self.extra)
            from shutil import copyfile
            self.base_ride_log_config = 'config/ride_log_base_config.yaml'
            copyfile(self.base_ride_log_config, self.ride_log_config)
            self.ride_log_config = self.base_ride_log_config
            try:
                with open(self.ride_log_config) as f:
                    self.config_params = yaml.safe_load(f)
            except IOError:
                #FIXME no hardcoded ride log yet
                self.log.critical("I/O Error when trying to parse overwritten config. Hardcoded format will be used!", extra=self.extra)

    ## Set up logging file and logging format.
    #  @param self The python object self
    def init_log(self):
        self.log.debug("init_log started", extra=self.extra)
        ride_log_filename = "log/ride." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
        logging.getLogger('ride').setLevel(logging.INFO)

        ride_log_format = ''
        self.ex = dict()
        self.parameter_format = dict()
        for i in self.config_params['parameters']:
            ride_log_format += '%(' + i['name'] + ')-12s,'
            try:
                self.parameter_format[i['name']] = i['format']
            except KeyError:
                self.parameter_format[i['name']] = '%.1f'
            self.ex[i['name']] = i['description']
            self.parameter_format
        ride_log_format = ride_log_format.strip(',')

        ride_log_handler = logging.handlers.RotatingFileHandler(ride_log_filename)
        ride_log_handler.setFormatter(logging.Formatter(ride_log_format))
        logging.getLogger('ride').addHandler(ride_log_handler)
        self.ride_logger = logging.getLogger('ride')
        self.ride_logger.info('', extra=self.ex)
        self.log_initialised = True
        self.log.debug("init_log finished", extra=self.extra)

    ## Notification handler, reacts to real_time and ride_log_config changes
    #  @param self The python object self
    def notification(self):
        try:
            if self.pm.parameters['ride_log_config']['value'] is not None:
                if self.pm.parameters['ride_log_config']['value'] != self.ride_log_config:
                    self.log.info("ride log config changed from {} to {}".format(self.ride_log_config, self.pm.parameters['ride_log_config']['value']), extra=self.extra)
                    self.ride_log_config = self.pm.parameters['ride_log_config']['value']
                    if self.ride_log_config is not None:
                        self.read_config()
                    if not self.log_initialised:
                        self.init_log()
        except KeyError:
            pass
        try:
            if self.pm.parameters['real_time']['value'] is not None:
                if self.pm.parameters['real_time']['value'] - self.last_log_entry > self.RIDE_LOG_UPDATE:
                    self.last_log_entry = self.pm.parameters['real_time']['value']
                    self.add_entry()
        except KeyError:
            pass

    ## Function responsible for formatting and adding entries to ride log
    #  @param self The python object self
    def add_entry(self):
        self.log.debug("Adding ride log entry", extra=self.extra)
        for p in self.ex:
            value = self.pm.parameters[p]["value"]
            string_format = self.parameter_format[p]
            if string_format == "hhmmss":
                try:
                    minutes, seconds = divmod(int(value), 60)
                    hours, minutes = divmod(minutes, 60)
                    value = "{:02.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds)
                except TypeError:
                    pass
            elif string_format == "time":
                try:
                    value = datetime.datetime.fromtimestamp(int(value)).strftime('%H:%M:%S')
                except (TypeError, ValueError):
                    pass
            elif string_format == "date":
                try:
                    value = datetime.datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
            else:
                try:
                    value = string_format % value
                except (ValueError, TypeError):
                    pass
            self.ex[p] = value
        self.ride_logger.info('', extra=self.ex)
