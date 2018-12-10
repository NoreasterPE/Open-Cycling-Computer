#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package compute
#  Module for handling generic date, like real time, session time, etc

import math
from helpers import num
import plugin
import pyplum
import time


## Compute module, handles all cross sensor calculations. I.e. slope calculation can be done with data from altimeter and speed sensor.
class compute(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()

        self.pm = pyplum.pyplum()
        self.pm.register_parameter("real_time", self.extra["module_name"])
        self.pm.register_parameter("session_start_time", self.extra["module_name"], value=time.time(), raw_unit="s")
        self.session_start_time = self.pm.parameters['session_start_time']['value']
        self.pm.register_parameter("session_time", self.extra["module_name"], value=0.0, value_default=num.NAN, raw_unit="s")
        self.reset_data()
        self.log.debug("Initialised.", extra=self.extra)

    def run(self):
        self.log.debug("Main loop started", extra=self.extra)
        self.running = True
        while self.running:
            t = time.time()
            # Check if there was a reset of session time
            if math.isnan(self.pm.parameters["session_time"]["value"]):
                self.pm.parameters["session_start_time"]["value"] = t

            session_time = t - self.pm.parameters["session_start_time"]["value"]
            session_time_delta = session_time - self.pm.parameters["session_time"]["value"]
            if abs(session_time_delta) > 2.0:
                self.log.warning("Session time change bigger than 2s ({:.3f} s), assuming system time change.".format(session_time_delta), extra=self.extra)
                self.pm.parameters["session_start_time"]["value"] += session_time_delta
            self.pm.parameters["session_time"]["value"] = t - self.pm.parameters["session_start_time"]["value"]
            self.pm.parameters["real_time"]["value"] = t
            time.sleep(0.1)
        self.log.debug("Main loop finished", extra=self.extra)
