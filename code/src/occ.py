#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package occ
#  OpenCyclingCompyter main file
#
#  http://opencyclingcomputer.eu/

#from ble_scanner import ble_scanner
import events
import layout
import logging
import logging.handlers
import pyplum
import signal
import sys
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
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    #  @param config_file Location of config file
    #  @param width Width of screen or window. Default value is 240 pixels
    #  @param height Height of screen or window.  Default value is 320 pixels
    def __init__(self, config_file=None, layout_file=None, fonts_dir=None):
        ## @var log
        #  Handle to system logger
        self.log = logging.getLogger('system')
        ## @var cleaning
        #  Variable indicating is cleaning is in progress
        self.cleaning = False
        self.log.debug("Getting plugin manager pyplum", extra=self.extra)
        ## @var pm
        #  Handle to pyplum instance
        self.pm = pyplum.pyplum()
        self.pm.register_parameter("log_level", self.extra["module_name"], value='debug')
        self.pm.register_parameter("config_file", self.extra["module_name"], value=config_file)
        self.pm.register_parameter("layout_file", self.extra["module_name"], value=layout_file)
        self.pm.register_parameter("fonts_dir", self.extra["module_name"], value=fonts_dir)
        ## @var ble_scanner
        #  Handle to ble_scanner instance
        ##self.log.debug("Initialising ble_scanner", extra=self.extra)
        ##self.ble_scanner = ble_scanner(self)
        ## @var layout
        #  Handle to layout instance
        self.layout = layout.layout()
        ## @var events
        #  Handle to events instance
        self.log.debug("Initialising events", extra=self.extra)
        self.events = events.events()

    ## Stops main event loop
    #  @param self The python object self
    def stop(self):
        self.log.debug("occ stop called", extra=self.extra)
        self.cleanup()

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
    if len(sys.argv) != 5:
        print('Need 4 args')
        print('Argument 1: config file, argument 2: ride log config, argument 3: layout file, argument 4: fonts directory')
        quit()
    #FIXME Make proper option parsing
    config_file = sys.argv[1]
    data_log_config = sys.argv[2]
    layout_file = sys.argv[3]
    fonts_dir = sys.argv[4]
    ## @var sys_log_filename
    # Log filename, helper variable
    sys_log_filename = "log/debug." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
    logging.getLogger('system').setLevel(logging.DEBUG)
    ## @var sys_log_handler
    # Log handler
    sys_log_handler = logging.handlers.RotatingFileHandler(sys_log_filename)
    ## @var sys_log_format
    # Log format string
    sys_log_format = '%(asctime)-25s %(levelname)-10s %(module_name)-15s %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    ## @var sys_logger
    # System logger handle
    sys_logger = logging.getLogger('system')
    signal.signal(signal.SIGTERM, quit_handler)
    signal.signal(signal.SIGINT, quit_handler)

    ex = {'module_name': 'Main'}
    sys_logger.debug("Log start", extra=ex)
    sys_logger.debug("Setting up plugin manager", extra=ex)
    p_manager = pyplum.pyplum()
    width, height = 240, 320
    sys_logger.debug("Screen size is {} x {}".format(width, height), extra=ex)
    # pitft_rendering needs this
    p_manager.register_parameter("display_size", value=(width, height))
    # data_log needs this
    p_manager.register_parameter("data_log_config", value=data_log_config)
    #print(p_manager.list_plugins('plugins'))
    plugins = ['ble_hr',
               'ble_sc',
               'bmp280',
               'compute',
               'config',
               'editor',
               #'json_server',
               'pitft_rendering',
               'pitft_touchscreen',
               'data_log',
               'syscalls']
    p_manager.load_plugins('plugins', plugins)
    # Above code could be replaced with p_manager.load_all_plugins(), it's here for testing
    sys_logger.debug("Starting plugin manager", extra=ex)
    p_manager.start()
    ## @var main_window
    # OCC main window. It's instance of open_cycling_computer class
    main_window = open_cycling_computer(config_file, layout_file, fonts_dir)
    sys_logger.debug("Starting events loop", extra=ex)
    main_window.events.run()
    main_window.stop()
    p_manager.stop()
    sys_logger.debug("Log end", extra=ex)
    quit()
