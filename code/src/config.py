#!/usr/bin/python3
## @package config
#  Package responsible for reading/writing config file. The config file contains different user and system related parameters that should be preserved between OCC starts.

import logging
import logging.handlers
import yaml
from shutil import copyfile
import sensors


## Main config class
class config(object):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'config'}

    ## The constructor
    #  @param self The python object self
    #  @param config_file_path path to config file
    #  @param base_config_file_path base config file used when for some reason config file can't be read. Also used as seed file during the first run.
    def __init__(self, occ, config_file_path, base_config_file_path):
        self.log = logging.getLogger('system')
        self.occ = occ
        self.config_file_path = config_file_path
        self.base_config_file_path = base_config_file_path
        self.s = sensors.sensors()

    ## Function that reads config file.
    #  @param self The python object self
    def read_config(self):
        self.log.debug("read_config started", extra=self.extra)
        try:
            with open(self.config_file_path) as f:
                self.config_params = yaml.safe_load(f)
        except IOError:
            self.log.error("I/O Error when trying to parse config file. Overwriting with copy of base_config", extra=self.extra)
            copyfile(self.base_config_file_path, self.config_file_path)
            self.config_file_path = self.config_file_path
            try:
                with open(self.config_file_path) as f:
                    self.config_params = yaml.safe_load(f)
            except IOError:
                self.log.exception("I/O Error when trying to parse overwritten config. Quitting!!", extra=self.extra)
                self.cleanup()
        self.s.register_parameter("log_level", self.extra["module_name"])
        try:
            log_level = self.config_params["log_level"]
            self.s.update_parameter("log_level", log_level)
            self.occ.switch_log_level(log_level["value"])
        except KeyError:
            self.log.error("log_level not found in config file. Using debug log level", extra=self.extra)
            self.occ.switch_log_level("debug")
            self.s.parameters["log_level"]["value"] = "debug"
        try:
            self.occ.layout_path = self.config_params["layout_path"]
            self.log.debug("Setting layout. Path = {}".format(self.occ.layout_path), extra=self.extra)
        except AttributeError:
            self.occ.layout_path = "layouts/default.yaml"
            self.log.error("Missing layout path, falling back to {}".format(self.occ.layout_path), extra=self.extra)

        error_list = []
        try:
            self.s.register_parameter("rider_weight", self.extra["module_name"])
            self.s.update_parameter("rider_weight", self.config_params["rider_weight"])

        except AttributeError:
            error_list.append("rider_weight")

        try:
            self.s.update_parameter("wheel_size", self.config_params["wheel_size"])
            import wheel
            w = wheel.wheel()
            wc = w.get_circumference(self.s.parameters["wheel_size"]["value"])
        except AttributeError:
            wc = 0.0
            error_list.append("wheel_size")
        try:
            self.s.update_parameter("wheel_circumference", self.config_params["wheel_circumference"])
        except AttributeError:
            self.s.update_parameter("wheel_circumference", dict(value=wc))
            error_list.append("wheel_circumference")

        ## @var reference_altitude
        #  Home altitude. Used as reference altitude for calculation of pressure at sea level and subsequent altitude calculations.
        #  It is being set through the notification system - see \link notification \endlink function
        try:
            self.s.register_parameter("reference_altitude",
                                      self.extra["module_name"],
                                      raw_unit="m")
            self.s.update_parameter("reference_altitude", self.config_params["reference_altitude"])
        except AttributeError:
            error_list.append("reference_altitude")

        try:
            self.s.update_parameter("odometer", self.config_params["odometer"])
        except AttributeError:
            error_list.append("odometer")

#        try:
#            self.s.update_parameter("total_ride_time", self.config_params["total_ride_time"])
#            self.s.update_parameter("total_ride_time",
#                                    dict(value=float(self.config_params["total_ride_time"]),
#                                         raw_unit="s"))
#        except AttributeError:
#            error_list.append("total_ride_time")

        try:
            self.s.update_parameter("speed", self.config_params["speed"])
        except AttributeError:
            error_list.append("speed")

        try:
            self.s.update_parameter("temperature", self.config_params["temperature"])
        except AttributeError:
            error_list.append("temperature")

        try:
            self.s.update_parameter("heart_rate_device_name", self.config_params["heart_rate_device_name"])
        except AttributeError:
            error_list.append("heart_rate_device_name")

        try:
            self.s.register_parameter("heart_rate_device_address", self.extra["module_name"])
            self.s.update_parameter("heart_rate_device_address", self.config_params["heart_rate_device_address"])
        except AttributeError:
            error_list.append("heart_rate_device_address")

        try:
            self.s.update_parameter("cadence_speed_device_name", self.config_params["cadence_speed_device_name"])
        except AttributeError:
            error_list.append("cadence_speed_device_name")

        try:
            self.s.register_parameter("cadence_speed_device_address", self.extra["module_name"])
            self.s.update_parameter("cadence_speed_device_address", self.config_params["cadence_speed_device_address"])
        except AttributeError:
            error_list.append("cadence_speed_device_address")

        if len(error_list) > 0:
            for item in error_list:
                self.log.error("Missing or invalid: {} in config file".format(item), extra=self.extra)
            error_list = []
        self.log.debug("read_config finished", extra=self.extra)

    ## Function that writes config file.
    #  @param self The python object self
    def write_config(self):
        self.log.debug("Writing config file started", extra=self.extra)
        c = {}
        c["log_level"] = self.s.parameters["log_level"]
        c["layout_path"] = self.occ.layout_path
        c["rider_weight"] = self.s.parameters["rider_weight"]
        c["wheel_size"] = self.s.parameters["wheel_size"]
        c["wheel_circumference"] = self.s.parameters["wheel_circumference"]
        c["reference_altitude"] = self.s.parameters["reference_altitude"]
        c["odometer"] = self.s.parameters["odometer"]
        #c["total_ride_time"] = self.s.parameters["total_ride_time"]
        c["speed"] = self.s.parameters["speed"]
        c["temperature"] = self.s.parameters["temperature"]
        c["heart_rate_device_name"] = self.s.parameters["heart_rate_device_name"]
        c["heart_rate_device_address"] = self.s.parameters["heart_rate_device_address"]
        c["cadence_speed_device_name"] = self.s.parameters["cadence_speed_device_name"]
        c["cadence_speed_device_address"] = self.s.parameters["cadence_speed_device_address"]
        self.log.debug("Data ready for config file", extra=self.extra)
        # FIXME error handling for file operation
        f = open(self.config_file_path, "w")
        self.log.debug("Writing config file", extra=self.extra)
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
        self.log.debug("Closing config file", extra=self.extra)
        f.close()
        self.log.debug("Writing config file finished", extra=self.extra)
