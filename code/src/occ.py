#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## @package occ
#  OpenCyclingCompyter main file
#
#  http://opencyclingcomputer.eu/

import argparse
import logging
import logging.handlers
import signal
import time

import events
import layout
import pyplum
import singleton


## Main OpenCyclingComputer class
# Based on RPI model Zero W and PiTFT 2.8" 320x240
class open_cycling_computer(object, metaclass=singleton.singleton):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    #  @param config_file Location of config file
    #  @param layout_file Location of layout file
    #  @param fonts_dir Location of font directory
    def __init__(self, config_file=None, layout_file=None, fonts_dir=None):
        ## @var log
        #  Handle to system logger
        self.log = logging.getLogger('system')
        ## @var pm
        #  Handle to pyplum instance
        self.pm = pyplum.pyplum()
        self.pm.register_parameter("log_level", self.extra["module_name"], value='debug', store=True)
        self.pm.register_parameter("config_file", self.extra["module_name"], value=config_file)
        self.pm.register_parameter("layout_file", self.extra["module_name"], value=layout_file)
        self.pm.register_parameter("fonts_dir", self.extra["module_name"], value=fonts_dir)
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
        self.pm.plugins['syscalls'].quit()


## Quit handler, triggers cleanup function after SIGTERM or SIGINT
#  @param signal TBC
#  @param frame TBC
def quit_handler(signal, frame):
    main_window = open_cycling_computer()
    main_window.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Open Cycling Copmuter.')
    parser.add_argument('-c', '--config', help='Main coonfig yaml file', required=True)
    parser.add_argument('-l', '--layout', help='Layout yaml file', required=True)
    parser.add_argument('-d', '--data-log', help='Data log config yaml file', required=True)
    parser.add_argument('-f', '--fonts', help='Directory with fonts', required=True)
    args = parser.parse_args()
    config_file = args.config
    data_log_config = args.data_log
    layout_file = args.layout
    fonts_dir = args.fonts

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
               'ble_scanner',
               'bmp280',
               'compute',
               'bicycle',
               'config',
               'editor',
               #'json_server',
               #'gtk_rendering',
               'pitft_rendering',
               'pitft_touchscreen',
               'lipo_shim',
               'data_log',
               'syscalls']
    p_manager.load_plugins('plugins', plugins)
    sys_logger.debug("Starting plugin manager", extra=ex)
    p_manager.start()
    ## @var main_window
    # OCC main window. It's instance of open_cycling_computer class
    main_window = open_cycling_computer(config_file, layout_file, fonts_dir)
    sys_logger.debug("Starting events loop", extra=ex)
    main_window.events.run()
    p_manager.stop()
    sys_logger.debug("Log end", extra=ex)
