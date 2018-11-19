#!/usr/bin/python3
## @package config
#  Package responsible for reading/writing config file. The config file contains different user and system related parameters that should be preserved between OCC starts.

from shutil import copyfile
import plugin
import pyplum
import time
import yaml


## Main config class
class config(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.pm = pyplum.pyplum()
        self.pm.register_parameter("write_config_period", self.extra["module_name"], value=15.0, raw_unit='s', store=True)
        self.pm.register_parameter("write_config_requested", self.extra["module_name"], value=False)
        self.pm.request_parameter("write_config_requested", self.extra["module_name"])
        self.pm.request_parameter("config_file", self.extra["module_name"])
        self.pm.request_parameter("log_level", self.extra["module_name"])
        self.log_level = None
        #FIXME Add config safe copy
        ## @var config_file
        #  Config file path passed from the command line
        self.config_file = None
        ## @var base_config_file
        #  Hardcoded config file, used if the bain config can't be read.
        self.base_config_file = "config/config_base.yaml"
        ## @var filter_out_fields
        # Tuple of fields that are not supposed to be written to the config file
        self.filter_out_fields = ('reset', 'force_notification', 'plugin_name', 'required_by', 'store', 'units_allowed', 'value_default', 'value_list')

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            period = self.pm.parameters['write_config_period']['value']
            try:
                p = float(period)
            except (ValueError, TypeError) as e:
                self.log.error("Cannot use {} as time to set writing config. Using 15s .Error: {}".format(period, e), extra=self.extra)
                p = 15
            time.sleep(p)
            self.write_config()
        self.log.debug("Main loop finished", extra=self.extra)

    ## CNotification handler for config module
    #  @param self The python object self
    def notification(self):
        try:
            if self.config_file != self.pm.parameters['config_file']['value']:
                # Config path changed, load it
                self.log.debug("Config file changed from {} to {}".format(self.config_file, self.pm.parameters['config_file']['value']), extra=self.extra)
                self.config_file = self.pm.parameters['config_file']['value']
                self.read_config()
        except KeyError:
            pass
        try:
            if self.log_level != self.pm.parameters['log_level']['value']:
                self.log_level = self.pm.parameters['log_level']['value']
                self.log.debug("Switching to log_level {}".format(self.log_level), extra=self.extra)
                self.log.setLevel(self.log_level)
        except KeyError:
            pass
        except ValueError:
            self.log.warning("Switching to log_level {} failed. Using DEBUG".format(self.log_level), extra=self.extra)
            self.log.setLevel('DEBUG')
        try:
            if self.pm.parameters['write_config_requested']['value']:
                self.pm.parameters['write_config_requested']['value'] = False
                self.write_config()
        except KeyError:
            pass

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
        for p in self.config_params:
            self.log.debug("Updating {} with values from {}".format(p, self.config_file), extra=self.extra)
            try:
                self.pm.update_parameter(p, self.config_params[p])
            except AttributeError as e:
                self.log.critical("Updating {} failed with: {}".format(p, e), extra=self.extra)

        self.log.debug("read_config finished", extra=self.extra)

    ## Function that writes config file.
    #  @param self The python object self
    def write_config(self):
        self.log.debug("Writing config file started", extra=self.extra)
        storage = {}
        for p in self.pm.parameters:
            if self.pm.parameters[p]['store']:
                storage[p] = {}
                for f in self.pm.parameters[p]:
                    if f not in self.filter_out_fields:
                        storage[p][f] = self.pm.parameters[p][f]
                        if type(storage[p][f]) == tuple:
                            self.log.debug("Tuple detected as {} in {}. Setting to None as pyyaml can't handle loading it".format(f, p), extra=self.extra)
                            storage[p][f] = None

        self.log.debug("Data ready for config file", extra=self.extra)
        # FIXME error handling for file operation
        self.log.debug("Preparing data dump", extra=self.extra)
        fv = yaml.dump(storage, default_flow_style=False, allow_unicode=True)
        self.log.debug("Writing config file", extra=self.extra)
        f = open(self.config_file, "w")
        f.write(fv)
        f.close()
        self.log.debug("Writing config file finished", extra=self.extra)

    def stop(self):
        self.running = False
