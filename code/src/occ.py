#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package occ
#  OpenCyclingCompyter main file
#
#  http://opencyclingcomputer.eu/

#from ble_scanner import ble_scanner
import events
import layout
import pitft_touchscreen
import rendering
import sensors
import logging
import sys
import logging.handlers
import signal
import time


class singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


## Main OpenCyclingComputer class
# Based on RPI model Zero W and PiTFT 2.8" 320x240
class open_cycling_computer(object, metaclass=singleton):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'OCC'}

    ## The constructor
    #  @param self The python object self
    #  @param config_file Location of config file
    #  @param width Width of screen or window. Default value is 240 pixels
    #  @param height Height of screen or window.  Default value is 320 pixels
    def __init__(self, config_file=None, layout_file=None, width=240, height=320):
        ## @var log
        #  Handle to system logger
        self.log = logging.getLogger('system')
        ## @var running
        #  Variable controlling if OCC should keep running
        self.running = True
        ## @var cleaning
        #  Variable indicating is cleaning is in progress
        self.cleaning = False
        self.log.debug("Screen size is {} x {}".format(width, height), extra=self.extra)
        self.log.debug("Calling sensors", extra=self.extra)
        ## @var sensors
        #  Handle to sensors instance
        self.sensors = sensors.sensors(self)
        self.sensors.register_parameter("log_level", self.extra["module_name"], value='debug')
        self.sensors.register_parameter("config_file", self.extra["module_name"], value=config_file)
        self.sensors.register_parameter("layout_file", self.extra["module_name"], value=layout_file)
        self.sensors.register_parameter("display_size", self.extra["module_name"], value=(width, height))
        ## @var ble_scanner
        #  Handle to ble_scanner instance
        ##self.log.debug("Initialising ble_scanner", extra=self.extra)
        ##self.ble_scanner = ble_scanner(self)
        ## @var rendering
        #  Handle to rendering instance
        self.log.debug("Initialising rendering", extra=self.extra)
        self.rendering = rendering.rendering(width, height)
        ## @var surface
        #  Main cairo surface
        self.surface = self.rendering.surface
        ## @var cr
        #  Main cairo context
        self.cr = self.rendering.cr
        ## @var layout
        #  Handle to layout instance
        self.layout = layout.layout(self.cr)
        self.log.debug("Starting rendering thread", extra=self.extra)
        self.rendering.start()
        ## @var touchscreen
        #  Handle to touchscreen (pitft_touchscreen module)
        self.log.debug("Initialising pitft touchscreen", extra=self.extra)
        self.touchscreen = pitft_touchscreen.pitft_touchscreen()
        ## @var events
        #  Handle to events instance
        self.log.debug("Initialising events", extra=self.extra)
        self.events = events.events(self.layout, self.touchscreen, self.rendering)

    ## Stops main event loop
    #  @param self The python object self
    def stop(self):
        self.log.debug("occ stop called", extra=self.extra)
        self.cleanup()
        self.running = False

    ## Returns simulate variable
    #  @param self The python object self
    def get_simulate(self):
        return self.simulate

    ## Clean up function. Writes config and layout and ends OCC. Should never be user it the real device once the code is ready. Used on development version.
    #  @param self The python object self
    def cleanup(self):
        if self.cleaning is False:
            self.log.debug("Cleaning called", extra=self.extra)
            self.cleaning = True
        elif self.cleaning:
            #Already in progress, ignore
            self.log.debug("Cleaning already in progress", extra=self.extra)
            return
        self.events.stop()
        time.sleep(2.0)
        try:
            self.rendering.stop()
        except AttributeError:
            self.log.debug("self.rendering.stop() produced AttributeError", extra=self.extra)
        try:
            self.config.write_config()
        except AttributeError:
            self.log.debug("self.config.write_config() produced AttributeError", extra=self.extra)
        # Wait for all processes to finish
        ##time.sleep(5)


## Quit handler, triggers cleanup function after SIGTERM or SIGINT
#  @param signal TBC
#  @param frame TBC
def quit_handler(signal, frame):
    main_window.stop()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Argument 1: config file, argument 2: layout file')
        quit()
    config_file = sys.argv[1]
    layout_file = sys.argv[2]
    ## @var sys_log_filename
    # Log filename, helper variable
    sys_log_filename = "log/debug." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
    logging.getLogger('system').setLevel(logging.DEBUG)
    ## @var sys_log_handler
    # Log handler
    sys_log_handler = logging.handlers.RotatingFileHandler(sys_log_filename)
    ## @var sys_log_format
    # Log format string
    sys_log_format = '%(asctime)-25s %(levelname)-10s %(module_name)-12s %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    ## @var sys_logger
    # System logger handle
    sys_logger = logging.getLogger('system')
    signal.signal(signal.SIGTERM, quit_handler)
    signal.signal(signal.SIGINT, quit_handler)

    ex = {'module_name': 'Main'}
    sys_logger.debug("Log start", extra=ex)
    # This is a simple check if we're running on Raspberry PI.
    # Switch to simulation mode if we're not
    if (platform.machine() == "armv6l"):
        ## @var simulate
        #  Stores simulate parameter. It's True on non armv6l platform
        simulate = False
    else:
        simulate = True
        sys_logger.warning("Warning! platform.machine() is NOT armv6l. I'll run in simulation mode. No real data will be shown.", extra=ex)
    sys_logger.debug("simulate = {}".format(simulate), extra=ex)
    sys_logger.debug("Setting up sensors", extra=ex)
    sensor_manager = sensors.sensors()
    sys_logger.debug("Starting sensors", extra=ex)
    sensor_manager.start()
    ## @var main_window
    # OCC main window. It's instance of open_cycling_computer class
    main_window = open_cycling_computer(config_file, layout_file)
    sys_logger.debug("Starting events loop", extra=ex)
    main_window.events.run()
    main_window.stop()
    sensor_manager.stop()
    sys_logger.debug("Log end", extra=ex)
    quit()
