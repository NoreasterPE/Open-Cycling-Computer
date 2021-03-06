#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package plugin
#  Abstract base class for all plugins.
import logging
import threading
import time

import pyplum

## Abstract base class for plugins
class plugin(threading.Thread):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self):
        super().__init__()
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')

        ## @var connected
        # Variable indicating it the plugin hardware is currently connected
        self.connected = False

        ## @var pm
        # PYthon PLUgin Manager instance
        self.pm = pyplum.pyplum()

        ## @var name
        # Name of the plugin
        self.name = None

        ## @var running
        # Variable controlling the main loop. Should be set to True when starting the loop.
        self.running = False

    def run(self):
        self.log.debug("Starting the main loop", extra=self.extra)
        self.running = True
        while self.running:
            time.sleep(10)
            # Copy the above code to a real plugin code and replace sleep with whatewer the plugin needs to provide data
        self.log.debug("Main loop finished", extra=self.extra)

    ## Resets all parameters to the default values
    #  @param self The python object self
    def reset_data(self):
        pass

    ## Usedb by module pyplum to notify about change of a parameter that the plugin subscribed for. Overwrite with code that needs to be executed on change of the parameters.
    #  @param self The python object self
    #  @param reqired Dict with new values for require parameters
    def notification(self):
        pass

    def is_connected(self):
        return self.connected

    def stop(self):
        self.log.debug("Stop started", extra=self.extra)
        self.running = False
