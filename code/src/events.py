#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package events
#  eventts handling
#

import logging
import operator
import time

## @var LONG_CLICK
# Time of long click in ms All clicks over 0.8s are considered "long".
LONG_CLICK = 0.8

## @var SWIPE_LENGTH
# Lenght of swipe in pixels. All clicks with length over 50 pixels are considered swipes.
SWIPE_LENGTH = 70

## @var MAIN_LOOP_BEAT
# Period oiting time in event main loop
MAIN_LOOP_BEAT = 0.2

## @var CONFIG_SAVE_TIME
# Period of time in s between EV_SAVE_CONFIG events.
CONFIG_SAVE_TIME = 15


## Events  class
# Handle input and internal events
class events():
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'events'}

    ## The constructor
    #  @param self The python object self
    def __init__(self, layout, touchscreen, ride_log, rendering):
        ## @var l
        # System logger handle
        self.log = logging.getLogger('system')
        # Run init for super class
        super(events, self).__init__()
        self.layout = layout
        self.touchscreen = touchscreen
        self.rendering = rendering
        self.ride_log = ride_log
        self.running = False
        self.ignore_touch = False

    ## Main click and swipe handler
    #  @param self The python object self
    #  @param time_now is event time passed from the main event loop
    def screen_touched_handler(self, time_now):
        dx = self.relative_movement[0]
        dy = self.relative_movement[1]
        dt = time_now - self.relative_movement_time_start
        self.log.debug("screen_touched_handler: {} {} {}".format(dx, dy, dt), extra=self.extra)
        if (self.released_timestamp is not None and dt < LONG_CLICK):
            self.log.debug("Short click: {} {}".format(dt, self.touch_position), extra=self.extra)
            self.layout.check_click(self.touch_position, 'SHORT')
            self.reset_motion()
        if (dt > LONG_CLICK):
            self.log.debug("Long click: {} {}".format(dt, self.touch_position), extra=self.extra)
            self.layout.check_click(self.touch_position, 'LONG')
            #The finger is still touching the screen, make sure it's ignored to avoid generating ghost events
            self.reset_motion()
            self.ignore_touch = True
        if (abs(dx)) > SWIPE_LENGTH:
            if dx < 0:
                self.log.debug("Swipe right to left: {} {}".format(dx, dy), extra=self.extra)
                self.layout.check_click(self.touch_position, 'R_TO_L')
                self.ignore_touch = True
            else:
                self.log.debug("Swipe left to right: {} {}".format(dx, dy), extra=self.extra)
                self.layout.check_click(self.touch_position, 'L_TO_R')
                self.ignore_touch = True
        elif (abs(dy)) > SWIPE_LENGTH:
            if dy > 0:
                self.log.debug("Swipe bottom to toP: {} {}".format(dx, dy), extra=self.extra)
                self.layout.check_click(self.touch_position, 'B_TO_T')
                self.ignore_touch = True
            else:
                self.log.debug("Swipe top to bottom: {} {}".format(dx, dy), extra=self.extra)
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
            self.log.debug("current touch: {} {}".format(t, current_touch_position), extra=self.extra)
            if self.touch_position is None:
                self.touch_position = current_touch_position
                self.log.debug("touch start: {}".format(self.touch_position), extra=self.extra)
            if self.previous_position is None:
                self.relative_movement = (0, 0)
                self.relative_movement_time_start = t
                self.log.debug("relative_movement start", extra=self.extra)
            else:
                rm = tuple(map(operator.sub, self.previous_position, current_touch_position))
                self.relative_movement = tuple(map(operator.add, self.relative_movement, rm))
                self.log.debug("relative_movement: {}  change {}".format(self.relative_movement, rm), extra=self.extra)
            self.previous_position = current_touch_position
        elif event['touch'] == 0:
            self.released_timestamp = t
            if self.ignore_touch:
                self.ignore_touch = False
                self.released_timestamp = None
                self.reset_motion()
            self.log.debug("touch end", extra=self.extra)
        if self.ignore_touch:
            self.reset_motion()
        if self.touch_position is not None:
            self.screen_touched_handler(t)

    ## Resets all parameters related to clicks/swipes
    #  @param self The python object self
    def reset_motion(self):
        self.log.debug("reset_motion", extra=self.extra)
        self.touch_timestamp = None
        self.touch_position = None
        self.released_timestamp = None
        self.relative_movement = None
        self.previous_position = None
        self.relative_movement = None
        self.relative_movement_time_start = None
        #self.layout.render_button = None

    ## Main event loop. Pools events from event terator, calls event_handler
    #  @param self The python object self
    def run(self):
        self.log.debug("event loop started", extra=self.extra)
        self.running = True
        self.reset_motion()
        self.touchscreen.start()
        while self.running:
            self.log.debug("event loop running", extra=self.extra)
            while not self.touchscreen.queue_empty():
                for e in self.touchscreen.get_event():
                    self.input_event_handler(e)
            self.ride_log.event_scheduler.run(blocking=False)
            time.sleep(MAIN_LOOP_BEAT)
            #self.log.debug("Ride event scheduler, next event in: {0:.3f}".format(t), extra=self.extra)
            if self.layout.render:
                self.layout.render_page()
                self.rendering.force_render()
            if self.touch_position is not None:
                self.layout.render_pressed_button(self.touch_position)
                self.rendering.force_render()
        self.log.debug("event loop finsished", extra=self.extra)
        self.touchscreen.stop()

    ## Stops main event loop
    #  @param self The python object self
    def stop(self):
        self.log.debug("stop called", extra=self.extra)
        self.running = False
