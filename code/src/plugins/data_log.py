#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package data_log
#  Module for handling ride parameters logging to file
import datetime
import logging
import num
import plugin
import pyplum
import threading
import time
import yaml


## Class for handling ride parameters logging
class data_log(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.pm = pyplum.pyplum()
        self.pm.register_parameter("data_log_period", self.extra["module_name"], value=1.0, raw_unit='s', store=True)
        self.pm.request_parameter("real_time", self.extra["module_name"])
        self.last_log_entry = 0.0
        self.pm.request_parameter("data_log_config", self.extra["module_name"])
        try:
            self.data_log_config = self.pm.parameters['data_log_config']['value']
        except KeyError:
            self.data_log_config = None
        self.log_initialised = False
        if self.data_log_config is not None:
            self.read_config()
            self.init_log()
        self.running = True
        threading.Timer(self.pm.parameters['data_log_period']['value'], self.add_entry).start()

    ## Function that reads config file with data_log format
    #  @param self The python object self
    def read_config(self):
        self.log.debug("read_config started", extra=self.extra)
        try:
            with open(self.data_log_config) as f:
                self.config_params = yaml.safe_load(f)
        except IOError:
            self.log.error("I/O Error when trying to parse rede log config file. Overwriting with copy of ride log base_config", extra=self.extra)
            from shutil import copyfile
            self.base_data_log_config = 'config/data_log_base_config.yaml'
            copyfile(self.base_data_log_config, self.data_log_config)
            self.data_log_config = self.base_data_log_config
            try:
                with open(self.data_log_config) as f:
                    self.config_params = yaml.safe_load(f)
            except IOError:
                #FIXME no hardcoded ride log yet
                self.log.critical("I/O Error when trying to parse overwritten config. Hardcoded format will be used!", extra=self.extra)

    ## Set up logging file and logging format.
    #  @param self The python object self
    def init_log(self):
        self.log.debug("init_log started", extra=self.extra)
        data_log_filename = "log/ride." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
        logging.getLogger('ride').setLevel(logging.INFO)

        data_log_format = ''
        self.ex = dict()
        self.parameter_format = dict()
        self.parameters = dict()
        for i in self.config_params['columns']:
            try:
                name = i['name']
            except KeyError:
                raise
            try:
                parameter = i['parameter']
            except KeyError:
                raise
            try:
                description = i['description']
            except KeyError:
                description = 'No description'
            try:
                string_format = i['format']
            except KeyError:
                string_format = '%.1f'

            data_log_format += '%(' + name + ')-12s,'
            self.parameter_format[name] = string_format
            self.parameters[name] = parameter
            self.ex[name] = description

        data_log_format = data_log_format.strip(',')

        data_log_handler = logging.handlers.RotatingFileHandler(data_log_filename)
        data_log_handler.setFormatter(logging.Formatter(data_log_format))
        logging.getLogger('ride').addHandler(data_log_handler)
        self.data_logger = logging.getLogger('ride')
        self.data_logger.info('', extra=self.ex)
        self.log_initialised = True
        self.log.debug("init_log finished", extra=self.extra)

    ## Notification handler, reacts to real_time and data_log_config changes
    #  @param self The python object self
    def notification(self):
        try:
            if self.pm.parameters['data_log_config']['value'] is not None:
                if self.pm.parameters['data_log_config']['value'] != self.data_log_config:
                    self.log.info("ride log config changed from {} to {}".format(self.data_log_config, self.pm.parameters['data_log_config']['value']), extra=self.extra)
                    self.data_log_config = self.pm.parameters['data_log_config']['value']
                    if self.data_log_config is not None:
                        self.read_config()
                    if not self.log_initialised:
                        self.init_log()
        except KeyError:
            pass

    ## Function responsible for formatting and adding entries to ride log
    #  @param self The python object self
    def add_entry(self):
        self.log.debug("Adding ride log entry", extra=self.extra)
        for name in self.ex:
            try:
                parameter = self.parameters[name]
                value = self.pm.parameters[parameter]["value"]
            except KeyError:
                self.log.debug("There is no {} in available paameters".format(name), extra=self.extra)
                continue
            string_format = self.parameter_format[name]
            if string_format == "hhmmss":
                try:
                    minutes, seconds = divmod(int(value), 60)
                    hours, minutes = divmod(minutes, 60)
                    value = "{:02.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds)
                except (TypeError, ValueError):
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
            self.ex[name] = num.sanitise(value)
        self.data_logger.info('', extra=self.ex)
        # Schedule next data entry event
        if self.running:
            threading.Timer(self.pm.parameters['data_log_period']['value'], self.add_entry).start()
