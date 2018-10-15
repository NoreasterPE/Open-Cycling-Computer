#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ride_parameters
#  Module for handling all ride parameters. This is the main module responsible for pulling all data together and preparing values for displaying, logging and saving.
from time import strftime
import unit_converter
import logging
import time
import sched
import ride_log


## @var RIDE_PARAMETERS_UPDATE
# Period of time in m between ride parameters update events.
RIDE_PARAMETERS_UPDATE = 1.0


## Class for handling all ride parameters
class ride_parameters():
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ride_param'}

    ## The constructor
    #  @param self The python object self
    #  @param occ OCC instance
    #  @param simulate Decides if ride_parameters runs in simulation mode or real device mode.
    def __init__(self, occ, simulate=False):
        ## @var l
        # System logger handle
        self.log = logging.getLogger('system')
        ## @var stopping
        # Variable indicating is stopping is in progress
        self.stopping = False
        ## @var ride_log
        # Ride logger handle
        self.ride_log = ride_log.ride_log()
        ## @var uc
        # Units converter
        self.uc = unit_converter.unit_converter()
        ## @var event_scheduler
        # Event scheduler triggering parameters update and writing ride log entry
        self.event_scheduler = sched.scheduler(time.time, time.sleep)
        self.log.info("Initialising sensors", extra=self.extra)
        ## @var sensors
        # Handle of sensors instance
        self.sensors = occ.sensors

        self.suffixes = ("_hms")

        # Params of the ride ready for rendering.
        self.params = dict(
            # Editor params
            editor_index=0, variable=None,
            variable_description=None, variable_raw_value=None, variable_unit=None, variable_value=None)

        self.log.debug("Setting up event scheduler", extra=self.extra)
        self.event_scheduler.enter(RIDE_PARAMETERS_UPDATE, 1, self.schedule_update_event)

    def schedule_update_event(self):
        self.log.debug("Calling update values from event scheduler", extra=self.extra)
        self.ride_log.add_entry(self.params)
        if not self.stopping:
            #Setting up next update event
            self.event_scheduler.enter(RIDE_PARAMETERS_UPDATE, 1, self.schedule_update_event)
            t = self.event_scheduler.run(blocking=False)
            self.log.debug("Event scheduler, next event in: {0:.3f}".format(t), extra=self.extra)

    def stop(self):
        self.stopping = True
        self.log.debug("Stop started", extra=self.extra)
        self.log.debug("Stopping sensors thread", extra=self.extra)
        self.sensors.stop()
        self.log.debug("Stop finished", extra=self.extra)

    def __del__(self):
        self.stop()

    def set_raw_param(self, param_name, value):
        self.log.debug("Setting {} to {} (raw)".format(param_name, value), extra=self.extra)
        self.p_raw[param_name] = value

    def set_param(self, param_name, value):
        self.log.debug("Setting {} to {} ".format(param_name, value), extra=self.extra)
        self.params[param_name] = value

    def get_param(self, param):
        value = None
        try:
            if param.endswith("_units"):
                value = self.get_unit(param[:-6])
            elif param in self.params:
                value = self.params[param]
        except KeyError:
            self.log.error("No unit for {}".format(param), extra=self.extra)
        finally:
            return value

    def get_unit(self, param_name):
        suffixes = ("_min", "_max", "_avg")
        p = self.strip_end(param_name, suffixes)
        if p.endswith("_units"):
            p = self.strip_end(p, "_units")
        try:
            unit = self.p_units[p]
        except KeyError:
            unit = None
        self.log.debug("Unit for {} / {} is {}".format(param_name, p, unit), extra=self.extra)

    def get_internal_unit(self, param_name):
        suffixes = ("_min", "_max", "_avg")
        p = self.strip_end(param_name, suffixes)
        if p.endswith("_units"):
            units = None
        else:
            try:
                units = self.p_raw_units[p]
            except KeyError:
                units = None
        return units

    def update_params(self):
        self.update_rtc()
        self.params["utc"] = self.p_raw["utc"]

    def strip_end(self, param_name, suffix=None):
        # Make sure there is no _digits, _tenths, _hms at the end
        if suffix is None:
            suffix = self.suffixes
        for s in suffix:
            if param_name.endswith(s):
                length = -1 * len(s)
                param_name = param_name[:length]
        return param_name

    def reset_param(self, param_name):
        self.log.debug("Resetting {}".format(param_name), extra=self.extra)
        self.p_raw[param_name] = 0

    def update_param(self, param):
        #print("param = {}, raw value = {} format = {}".format(param, self.p_raw[param], self.p_format[param]))
        if param in self.p_format:
            f = self.p_format[param]
        else:
            self.log.error("Formatting not available: param = {}".format(param), extra=self.extra)
            f = "%.1f"

        if self.p_raw[param] is not None:
            unit_raw = self.get_internal_unit(param)
            unit = self.get_unit(param)
            value = self.p_raw[param]
            if unit_raw != unit:
                value = self.uc.convert(value, unit_raw, unit)
            try:
                self.params[param] = f % float(value)
            except (ValueError, TypeError):
                self.params[param] = value
        else:
            self.params[param] = '-'

    def add_zero(self, value):
        if value < 10:
            value = "0" + format(value)
        return value

    def update_rtc(self):
        # FIXME proper localisation would be nice....
        self.params["date"] = strftime("%d-%m-%Y")
        self.params["time"] = strftime("%H:%M:%S")
