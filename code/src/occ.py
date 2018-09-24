#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package occ
#  OpenCyclingCompyter main file
#
#  http://opencyclingcomputer.eu/

#from ble_scanner import ble_scanner
from config import config
from events import events
import layout
from pitft_touchscreen import pitft_touchscreen
from rendering import rendering
from ride_parameters import ride_parameters
from sensors import sensors
import logging
import logging.handlers
import platform
import signal
import time

M = {'module_name': 'OCC'}


## Main OpenCyclingComputer class
# Based on RPI model Zero W and PiTFT 2.8" 320x240
class open_cycling_computer(object):

    ## The constructor
    #  @param self The python object self
    #  @param simulate Decides if OCC runs in simulation mode or real device mode. Simulation mode is useful for test on non-raspberry pi hardware. Default value is False.
    #  @param width Width of screen or window. Default value is 240 pixels
    #  @param height Height of screen or window.  Default value is 320 pixels
    def __init__(self, simulate=False, width=240, height=320):
        ## @var simulate
        #  Stores simulate parameter from constructor call
        self.simulate = simulate
        ## @var l
        #  Handle to system logger
        self.log = logging.getLogger('system')
        if not self.simulate:
            pass
        ## @var running
        #  Variable controlling if OCC should keep running
        self.running = True
        ## @var cleaning
        #  Variable indicating is cleaning is in progress
        self.cleaning = False
        ## @var width
        #  Window/screen width
        self.width = width
        ## @var height
        #  Window/screen height
        self.height = height
        self.log.debug("Screen size is {} x {}".format(self.width, self.height), extra=M)
        self.log.debug("Calling sensors", extra=M)
        ## @var sensors
        #  Handle to sensors instance
        self.sensors = sensors(self)
        self.log.debug("Calling ride_parameters", extra=M)
        ## @var rp
        #  Handle to ride_parameters instance
        self.rp = ride_parameters(self, simulate)
        ## @var layout_path
        #  Path to layout file
        self.layout_path = ''
        self.log.debug("Initialising config", extra=M)
        ## @var config
        #  Handle to config instance
        self.config = config(self, "config/config.yaml", "config/config_base.yaml")
        self.log.debug("Reading config", extra=M)
        self.config.read_config()
        ## @var ble_scanner
        #  Handle to ble_scanner instance
        ##self.log.debug("Initialising ble_scanner", extra=M)
        ##self.ble_scanner = ble_scanner(self)
        ## @var rendering
        #  Handle to rendering instance
        self.log.debug("Initialising rendering", extra=M)
        self.rendering = rendering()
        ## @var surface
        #  Main cairo surface
        self.surface = self.rendering.surface
        ## @var cr
        #  Main cairo context
        self.cr = self.rendering.cr
        ## @var layout
        #  Handle to layout instance
        self.layout = layout.layout(self, self.cr, self.layout_path)
        self.log.debug("Starting RP sensors", extra=M)
        self.rp.start_sensors()
        self.log.debug("Setting up rendering", extra=M)
        self.log.debug("Starting rendering thread", extra=M)
        self.rendering.start()
        ## @var touchscreen
        #  Handle to touchscreen (pitft_touchscreen module)
        self.log.debug("Initialising pitft touchscreen", extra=M)
        self.touchscreen = pitft_touchscreen()
        ## @var events
        #  Handle to events instance
        self.log.debug("Initialising events", extra=M)
        self.events = events(self.layout, self.touchscreen, self.rp, self.rendering)
        self.log.debug("Starting events thread", extra=M)
        self.events.start()

    ## Switches logging level
    #  @param self The python object self
    #  @param log_level Log level to be set.
    def switch_log_level(self, log_level):
        self.log.debug("Switching to log_level {}".format(log_level), extra=M)
        self.log.setLevel(log_level)

    ## Stops main event loop
    #  @param self The python object self
    def stop(self):
        self.log.debug("occ stop called", extra=M)
        self.cleanup()
        self.running = False

    ## Returns simulate variable
    #  @param self The python object self
    def get_simulate(self):
        return self.simulate

    ## Clean up function. Stops ride_parameters, writes config and layout and ends OCC. Should never be user it the real device once the code is ready. Used on development version.
    #  @param self The python object self
    def cleanup(self):
        if self.cleaning is False:
            self.log.debug("Cleaning called", extra=M)
            self.cleaning = True
        elif self.cleaning:
            #Already in progress, ignore
            self.log.debug("Cleaning already in progress", extra=M)
            return
        self.events.stop()
        self.rp.stop()
        time.sleep(2.0)
        try:
            self.rendering.stop()
        except AttributeError:
            self.log.debug("self.rendering.stop() produced AttributeError", extra=M)
        try:
            self.config.write_config()
        except AttributeError:
            self.log.debug("self.config.write_config() produced AttributeError", extra=M)
        # Wait for all processes to finish
        ##time.sleep(5)


## Quit handler, triggers cleanup function after SIGTERM or SIGINT
#  @param signal TBC
#  @param frame TBC
def quit_handler(signal, frame):
    main_window.stop()


if __name__ == "__main__":
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
    sys_logger.debug("Log start", extra=M)
    # This is a simple check if we're running on Raspberry PI.
    # Switch to simulation mode if we're not
    if (platform.machine() == "armv6l"):
        ## @var simulate
        #  Stores simulate parameter. It's True on non armv6l platform
        simulate = False
    else:
        simulate = True
        sys_logger.warning("Warning! platform.machine() is NOT armv6l. I'll run in simulation mode. No real data will be shown.", extra=M)
    sys_logger.debug("simulate = {}".format(simulate), extra=M)
    ## @var main_window
    # OCC main window. It's instance of open_cycling_computer class
    main_window = open_cycling_computer(simulate)
    while main_window.running:
        main_window.log.debug("main loop running", extra=M)
        time.sleep(2)
    main_window.stop()
    main_window.log.debug("Log end", extra=M)
    quit()
