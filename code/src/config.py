#!/usr/bin/python
## @package config
#  Package responsible for reading/writing config file. The config file contains different user and system related parameters that should be preserved between OCC starts.

import logging
import logging.handlers
import yaml
from shutil import copyfile
from wheel import wheel


## Main config class
class config(object):

    ## The constructor
    #  @param self The python object self
    #  @param config_file_path path to config file
    #  @param base_config_file_path base config file used when for some reason config file can't be read. Also used as seed file during the first run.
    def __init__(self, occ, config_file_path, base_config_file_path):
        self.l = logging.getLogger('system')
        self.occ = occ
        self.rp = occ.rp
        self.config_file_path = config_file_path
        self.base_config_file_path = base_config_file_path

    ## Function that reads config file. Currently read values are written directly to destination variables which is not really flexible solution.
    #  @param self The python object self
    def read_config(self):
        self.l.debug("[CON][F] read_config")
        try:
            with open(self.config_file_path) as f:
                self.config_params = yaml.safe_load(f)
        except IOError:
            self.l.error(
                "[CON] I/O Error when trying to parse config file. Overwriting with copy of base_config")
            copyfile(self.base_config_file_path, self.config_file_path)
            self.config_file_path = self.config_file_path
            try:
                with open(self.config_file_path) as f:
                    self.config_params = yaml.safe_load(f)
            except IOError:
                self.l.exception(
                    "[CON] I/O Error when trying to parse overwritten config. Quitting!!")
                self.cleanup()
        try:
            log_level = self.config_params["log_level"]
            self.occ.switch_log_level(log_level)
            self.rp.params["debug_level"] = log_level
        except KeyError:
            self.l.error(
                "[CON] log_level not found in config file. Using DEBUG log level")
            self.occ.switch_log_level("DEBUG")
            self.rp.params["debug_level"] = "DEBUG"
        try:
            self.occ.layout_path = self.config_params["layout_path"]
            self.l.debug("[CON] Setting layout. Path = {}".format(self.occ.layout_path))
        except AttributeError:
            self.occ.layout_path = "layouts/default.yaml"
            self.l.error(
                "[CON] Missing layout path, falling back to {}".format(self.occ.layout_path))

        error_list = []
        try:
            self.rp.p_raw["rider_weight"] = float(self.config_params["rider_weight"])
        except AttributeError:
            error_list.append("rider_weight")
        try:
            self.rp.p_raw["wheel_size"] = self.config_params["wheel_size"]
            self.rp.params["wheel_size"] = self.rp.p_raw["wheel_size"]
            w = wheel()
            try:
                self.rp.p_raw["wheel_circ"] = w.get_size(self.rp.p_raw["wheel_size"])
            except KeyError:
                error_list.append("wheel_circ")
            self.rp.params["wheel_circ"] = self.rp.p_raw["wheel_circ"]
        except AttributeError:
            error_list.append("wheel_size")
        try:
            self.rp.units["rider_weight"] = self.config_params["rider_weight_units"]
        except AttributeError:
            error_list.append("rider_weight_units")
        try:
            self.rp.p_raw["altitude_home"] = float(self.config_params["altitude_home"])
        except AttributeError:
            error_list.append("")
        try:
            self.rp.units["altitude_home"] = self.config_params["altitude_home_units"]
        except AttributeError:
            error_list.append("altitude_home")
        try:
            self.rp.p_raw["odometer"] = float(self.config_params["odometer"])
        except AttributeError:
            error_list.append("odometer")
        try:
            self.rp.units["odometer"] = self.config_params["odometer_units"]
        except AttributeError:
            error_list.append("odometer")
        try:
            self.rp.p_raw["ridetime_total"] = float(self.config_params["ridetime_total"])
        except AttributeError:
            error_list.append("ridetime_total")
        try:
            self.rp.p_raw["speed_max"] = float(self.config_params["speed_max"])
        except AttributeError:
            error_list.append("speed_max")
        try:
            self.rp.units["speed"] = self.config_params["speed_units"]
        except AttributeError:
            error_list.append("speed")
        try:
            self.rp.units["temperature"] = self.config_params["temperature_units"]
        except AttributeError:
            error_list.append("temperature")
        try:
            self.rp.params["ble_hr_name"] = self.config_params["ble_hr_name"]
            self.l.debug(
                "[CON] Read from config file: ble_hr_name = {}".format(self.rp.params["ble_hr_name"]))
        except AttributeError:
            error_list.append("ble_hr_name")
        try:
            self.rp.params["ble_hr_addr"] = self.config_params["ble_hr_addr"]
            self.l.debug(
                "[CON] Read from config file: ble_hr_addr = {}".format(self.rp.params["ble_hr_addr"]))
        except AttributeError:
            error_list.append("ble_hr_addr")
        try:
            self.rp.params["ble_sc_name"] = self.config_params["ble_sc_name"]
            self.l.debug(
                "[CON] Read from config file: ble_sc_name = {}".format(self.rp.params["ble_sc_name"]))
        except AttributeError:
            error_list.append("ble_sc_name")
        try:
            self.rp.params["ble_sc_addr"] = self.config_params["ble_sc_addr"]
            self.l.debug(
                "[CON] Read from config file: ble_sc_addr = {}".format(self.rp.params["ble_sc_addr"]))
        except AttributeError:
            error_list.append("ble_sc_addr")
        self.rp.update_param("speed_max")
        self.rp.split_speed("speed_max")
        if len(error_list) > 0:
            for item in error_list:
                self.l.error("[CON] Missing: {} in config file".format(item))
            error_list = []

    ## Function that writes config file.
    #  @param self The python object self
    def write_config(self):
        self.l.debug("[CON] Writing config file")
        log_level = logging.getLevelName(self.l.getEffectiveLevel())
        c = {}
        c["log_level"] = log_level
        c["layout_path"] = self.occ.layout_path
        c["rider_weight"] = self.rp.p_raw["rider_weight"]
        c["rider_weight_units"] = self.rp.units["rider_weight"]
        c["wheel_size"] = self.rp.p_raw["wheel_size"]
        c["altitude_home"] = self.rp.p_raw["altitude_home"]
        c["altitude_home_units"] = self.rp.units["altitude_home"]
        c["odometer"] = self.rp.p_raw["odometer"]
        c["odometer_units"] = self.rp.units["odometer"]
        c["ridetime_total"] = self.rp.p_raw["ridetime_total"]
        c["speed_max"] = self.rp.p_raw["speed_max"]
        c["speed_units"] = self.rp.units["speed"]
        c["temperature_units"] = self.rp.units["temperature"]
        c["ble_hr_name"] = self.rp.params["ble_hr_name"]
        c["ble_hr_addr"] = self.rp.params["ble_hr_addr"]
        c["ble_sc_name"] = self.rp.params["ble_sc_name"]
        c["ble_sc_addr"] = self.rp.params["ble_sc_addr"]
        # FIXME error handling for file operation
        f = open(self.config_file_path, "w")
        yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
        f.close()
