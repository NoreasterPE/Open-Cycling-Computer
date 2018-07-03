#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package occ
#  OpenCyclingCompyter main file
#
#  http://opencyclingcomputer.eu/

from ble_scanner import ble_scanner
from config import config
from layout import layout
from pitft_touchscreen import pitft_touchscreen
from rendering import rendering
from ride_parameters import ride_parameters
from sensors import sensors
import logging
import logging.handlers
import operator
import platform
import signal
import time

M = {'module_name': 'OCC'}

## @var LONG_CLICK
# Time of long click in ms All clicks over 0.8s are considered "long".
LONG_CLICK = 0.8

## @var SWIPE_LENGTH
# Lenght of swipe in pixels. All clicks with length over 50 pixels are considered swipes.
SWIPE_LENGTH = 50

## @var MAIN_LOOP_BEAT
# Period oiting time in event main loop
MAIN_LOOP_BEAT = 0.2

## @var CONFIG_SAVE_TIME
# Period of time in s between EV_SAVE_CONFIG events.
CONFIG_SAVE_TIME = 15


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
        self.ble_scanner = ble_scanner(self)
        ## @var layout
        #  Handle to layout instance
        self.layout = layout(self, self.layout_path)
        self.log.debug("Starting RP sensors", extra=M)
        self.rp.start_sensors()
        self.log.debug("Setting up rendering", extra=M)
        ## @var rendering
        #  Handle to rendering instance
        self.rendering = rendering(self.layout)
        ## @var surface
        #  Main cairo surface
        self.surface = self.rendering.surface
        ## @var cr
        #  Main cairo context
        self.cr = self.rendering.cr
        self.log.debug("Starting rendering thread", extra=M)
        self.rendering.start()
        ## @var touchscreen
        #  Handle to touchscreen (pitft_touchscreen module)
        self.touchscreen = pitft_touchscreen()
        ## @var refresh
        #  Variable controlling if the screen need to be refreshed
        self.refresh = False

    def force_refresh(self):
        self.refresh = True

    ## Switches logging level
    #  @param self The python object self
    #  @param log_level Log level to be set.
    def switch_log_level(self, log_level):
        self.log.debug("Switching to log_level {}".format(log_level), extra=M)
        self.log.setLevel(log_level)

    ## Main click and swipe handler
    #  @param self The python object self
    #  @param time_now is event time passed from the main event loop
    def screen_touched_handler(self, time_now):
        dx = self.relative_movement[0]
        dy = self.relative_movement[1]
        dt = time_now - self.relative_movement_time_start
        self.log.debug("screen_touched_handler: {} {} {}".format(dx, dy, dt), extra=M)
        if (self.released_timestamp is not None and dt < LONG_CLICK):
            self.log.debug("Short click: {} {}".format(dt, self.touch_position), extra=M)
            self.layout.check_click(self.touch_position, 'SHORT')
            self.reset_motion()
        if (dt > LONG_CLICK):
            self.log.debug("Long click: {} {}".format(dt, self.touch_position), extra=M)
            self.layout.check_click(self.touch_position, 'LONG')
            #The finger is still touching the screen, make sure it's ignored to avoid generating ghost events
            self.ignore_touch = True
        if (abs(dx)) > SWIPE_LENGTH:
            if dx < 0:
                self.log.debug("Swipe right to left: {} {}".format(dx, dy), extra=M)
                self.layout.check_click(self.touch_position, 'R_TO_L')
                self.ignore_touch = True
            else:
                self.log.debug("Swipe left to right: {} {}".format(dx, dy), extra=M)
                self.layout.check_click(self.touch_position, 'L_TO_R')
                self.ignore_touch = True
        elif (abs(dy)) > SWIPE_LENGTH:
            if dy > 0:
                self.log.debug("Swipe bottom to toP: {} {}".format(dx, dy), extra=M)
                self.layout.check_click(self.touch_position, 'B_TO_T')
                self.ignore_touch = True
            else:
                self.log.debug("Swipe top to bottom: {} {}".format(dx, dy), extra=M)
                self.layout.check_click(self.touch_position, 'T_TO_B')
                self.ignore_touch = True

    ## Main event handler
    #  @param self The python object self
    #  @param event Event, might be input event or internal event
    #  @param time_now is event time passed from the main event loop
    def input_event_handler(self, event):
        if not ('x' in event and 'y' in event and 'id' in event and 'time' in event and 'touch' in event):
            #Ignore incomplete event
            return
        if (event["touch"] == 1 and (event["x"] is None or event["y"] is None)):
            #Ignore invalid event
            return
        t = event['time']
        if event['touch'] == 1 and not self.ignore_touch:
            if self.touch_timestamp is None:
                self.touch_timestamp = t
            # FIXME Screen in cairo and evdev don't have the same origin
            current_touch_position = (240 - event["x"], 320 - event["y"])
            self.log.debug("current touch: {} {}".format(t, current_touch_position), extra=M)
            if self.touch_position is None:
                self.touch_position = current_touch_position
                self.log.debug("touch start: {}".format(self.touch_position), extra=M)
            if self.previous_position is None:
                self.relative_movement = (0, 0)
                self.relative_movement_time_start = t
                self.log.debug("relative_movement start", extra=M)
            else:
                rm = tuple(map(operator.sub, self.previous_position, current_touch_position))
                self.relative_movement = tuple(map(operator.add, self.relative_movement, rm))
                self.log.debug("relative_movement: {}  change {}".format(self.relative_movement, rm), extra=M)
            self.previous_position = current_touch_position
        elif event['touch'] == 0:
            #Wait for the end of touch before starting a new event
            self.ignore_touch = False
            #if self.released_timestamp is None:
            self.released_timestamp = t
            self.log.debug("touch end", extra=M)
        if self.ignore_touch:
            self.reset_motion()
        if self.touch_position is not None:
            self.screen_touched_handler(t)

    ## Resets all parameters related to clicks/swipes
    #  @param self The python object self
    def reset_motion(self):
        self.log.debug("reset_motion", extra=M)
        self.touch_timestamp = None
        self.touch_position = None
        self.released_timestamp = None
        self.relative_movement = None
        self.previous_position = None
        self.relative_movement = None
        self.relative_movement_time_start = None
        #self.layout.render_button = None

    ## Main event loop. Pools eventr from event_iterator, calls event_handler
    #  @param self The python object self
    def main_loop(self):
        self.log.debug("main loop started", extra=M)
        self.previous_position = None
        self.ignore_touch = False
        self.reset_motion()
        self.running = True
        self.touchscreen.start()
        while self.running:
            while not self.touchscreen.queue_empty():
                for e in self.touchscreen.get_event():
                    self.input_event_handler(e)
            if self.refresh:
                self.refresh = False
                self.rendering.force_refresh()
            #t = self.rp.event_scheduler.run(blocking=False)
            self.rp.event_scheduler.run(blocking=False)
            time.sleep(MAIN_LOOP_BEAT)
            #self.log.debug("Ride event scheduler, next event in: {0:.3f}".format(t), extra=M)
        self.log.debug("main loop finsished", extra=M)
        self.touchscreen.stop()

    ## Stops main event loop
    #  @param self The python object self
    def stop(self):
        self.log.debug("occ stop called", extra=M)
        self.running = False
        time.sleep(2.0)
        self.cleanup()

    ## Returns simulate variable
    #  @param self The python object self
    def get_simulate(self):
        return self.simulate

    ## Clean up function. Stops ride_parameters, writes config and layout and ends OCC. Should never be user it the real device once the code is ready. Used on development version.
    #  @param self The python object self
    def cleanup(self):
        self.log.debug("Cleaning...", extra=M)
        time.sleep(1)
        self.rp.stop()
        try:
            self.rendering.stop()
        except AttributeError:
            self.log.debug("self.rendering.stop() produced AttributeError", extra=M)
        try:
            self.config.write_config()
        except AttributeError:
            self.log.debug("self.config.write_config() produced AttributeError", extra=M)
        try:
            self.layout.write_layout()
        except AttributeError:
            self.log.debug("self.layout.write_layout() produced AttributeError", extra=M)
        self.log.debug("Log end", extra=M)


## Quit handler, triggers cleanup function after SIGTERM or SIGINT
#  @param signal TBC
#  @param frame TBC
def quit_handler(signal, frame):
    main_window.cleanup()
    quit()


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
    ## @var main_window
    # OCC main window. It's instance of open_cycling_computer class
    main_window = open_cycling_computer(simulate)
    sys_logger.debug("simulate = {}".format(simulate), extra=M)
    main_window.main_loop()
    main_window.cleanup()
