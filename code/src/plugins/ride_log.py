#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ride_log
#  Module for handling ride parameters logging to file
from shutil import copyfile
import datetime
import logging
import numbers
import plugin
import plugin_manager
import time
import yaml


## Class for handling ride parameters logging
class ride_log(plugin.plugin):
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
        self.read_config()
        self.init_log()

    def init_log(self):
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
        self.pm = plugin_manager.plugin_manager()
        self.pm.request_parameter("real_time", self.extra["module_name"])
        self.last_log_entry = 0.0

    ## Function that reads config file with ride_log format
    #  @param self The python object self
    def read_config(self):
        self.log.debug("read_config started", extra=self.extra)
        #FIXME Replace with request parameter and an entry in the main config file
        self.config_file_path = 'config/ride_log_config.yaml'
        self.base_config_file_path = 'config/ride_log_base_config.yaml'
        try:
            with open(self.config_file_path) as f:
                self.config_params = yaml.safe_load(f)
        except IOError:
            self.log.error("I/O Error when trying to parse rede log config file. Overwriting with copy of ride log base_config", extra=self.extra)
            copyfile(self.base_config_file_path, self.config_file_path)
            self.config_file_path = self.config_file_path
            try:
                with open(self.config_file_path) as f:
                    self.config_params = yaml.safe_load(f)
            except IOError:
                self.log.critical("I/O Error when trying to parse overwritten config. Hardcoded format will be used!", extra=self.extra)

    def notification(self):
        if self.pm.parameters['real_time']['value'] is not None:
            if self.pm.parameters['real_time']['value'] - self.last_log_entry > self.RIDE_LOG_UPDATE:
                self.last_log_entry = self.pm.parameters['real_time']['value']
                self.add_entry()

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
                    value  = string_format % value
                except (ValueError, TypeError):
                    pass
            self.ex[p] = value
        self.ride_logger.info('', extra=self.ex)
