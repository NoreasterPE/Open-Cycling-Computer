#!/usr/bin/python3
## @package config
#  Package responsible for reading/writing config file. The config file contains different user and system related parameters that should be preserved between OCC starts.

import yaml
from shutil import copyfile
import sensor
import sensors


## Main config class
class config(sensor.sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'config'}

    ## The constructor
    #  @param self The python object self
    #  @param config_file path to config file
    #  @param base_config_file base config file used when for some reason config file can't be read. Also used as seed file during the first run.
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.s = sensors.sensors()
        self.s.register_parameter("write_config_requested", self.extra["module_name"], value=False)
        self.s.request_parameter("write_config_requested", self.extra["module_name"])
        self.s.request_parameter("config_file", self.extra["module_name"])
        self.log_level = None
        #FIXME Add config safe copy
        ## @var config_file
        #  Config file path passed from the command line
        self.config_file = None
        ## @var base_config_file
        #  Hardcoded config file, used if the bain config can't be read.
        self.base_config_file = "config/config_base.yaml"

    ## CNotification handler for config module
    #  @param self The python object self
    def notification(self):
        if self.config_file != self.s.parameters['config_file']['value']:
            # Config path changed, load it
            self.log.debug("Config file changed from {} to {}".format(self.config_file, self.s.parameters['config_file']['value']), extra=self.extra)
            self.config_file = self.s.parameters['config_file']['value']
            self.read_config()
        if self.log_level != self.s.parameters['log_level']['value']:
            self.log_level = self.s.parameters['log_level']['value']
            self.log.debug("Switching to log_level {}".format(self.log_level), extra=self.extra)
            self.log.setLevel(self.log_level)
        if self.s.parameters['write_config_requested']['value']:
            self.s.parameters['write_config_requested']['value'] = False
            self.write_config()

    ## Function that reads config file.
    #  @param self The python object self
    def read_config(self):
        self.log.debug("read_config started, file {}".format(self.config_file), extra=self.extra)
        try:
            with open(self.config_file) as f:
                self.config_params = yaml.safe_load(f)
        except IOError:
            self.log.error("I/O Error when trying to parse config file. Overwriting with copy of base_config", extra=self.extra)
            copyfile(self.base_config_file, self.config_file)
            self.config_file = self.config_file
            try:
                with open(self.config_file) as f:
                    self.config_params = yaml.safe_load(f)
            except IOError:
                self.log.exception("I/O Error when trying to parse overwritten config. Quitting!!", extra=self.extra)
                #FIXME no cleanup function
                self.cleanup()
        error_list = []
        try:
            self.s.update_parameter("log_level", self.config_params["log_level"])
        except KeyError:
            error_list.append("log_level")

        try:
            self.s.update_parameter("layout_file", self.config_params["layout_file"])
        except KeyError:
            error_list.append("layout_file")

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
        c["layout_file"] = self.s.parameters["layout_file"]
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
        f = open(self.config_file, "w")
        self.log.debug("Writing config file", extra=self.extra)
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
        self.log.debug("Closing config file", extra=self.extra)
        f.close()
        self.log.debug("Writing config file finished", extra=self.extra)
