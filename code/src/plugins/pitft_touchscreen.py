#!/usr/bin/python3
# -*- coding: utf-8 -*-
#  piTFT touchscreen handling using evdev

import evdev
import queue
import plugin
import plugin_manager


# Class for handling events from piTFT
class pitft_touchscreen(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self, device_path="/dev/input/touchscreen"):
        super().__init__()
        self.device = evdev.InputDevice(device_path)
        if self.device is None:
            self.log.critical("Input device {} not found".format(device_path), extra=self.extra)
            exit()
        #FIXME Add event structure documentation
        self.event = {}
        self.event['time'] = None
        self.event['id'] = None
        self.event['x'] = None
        self.event['y'] = None
        self.event['touch'] = None
        self.events = queue.Queue()
        self.pm = plugin_manager.plugin_manager()
        self.pm.register_input_queue(self.extra['module_name'], self.events)

    def run(self):
        self.stopping = False
        for event in self.device.read_loop():
            if self.stopping:
                break
            if event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_X:
                    self.event['x'] = event.value
                elif event.code == evdev.ecodes.ABS_Y:
                    self.event['y'] = event.value
                elif event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                    self.event['id'] = event.value
                    if event.value == -1:
                        self.event['x'] = None
                        self.event['y'] = None
                        self.event['touch'] = None
                elif event.code == evdev.ecodes.ABS_MT_POSITION_X:
                    pass
                elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                    pass
            elif event.type == evdev.ecodes.EV_KEY:
                self.event['touch'] = event.value
            elif event.type == evdev.ecodes.SYN_REPORT:
                self.event['time'] = event.timestamp()
                self.events.put(self.event)
                e = self.event
                self.event = {}
                self.event['x'] = e['x']
                self.event['y'] = e['y']
                try:
                    self.event['id'] = e['id']
                except KeyError:
                    self.event['id'] = None
                try:
                    self.event['touch'] = e['touch']
                except KeyError:
                    self.event['touch'] = None

    def stop(self):
        self.stopping = True
        # Inject event to force immediate breaking "for" loop in run procedure.
        self.device.write(evdev.ecodes.EV_ABS, evdev.ecodes.ABS_X, 1)
        self.device.write(evdev.ecodes.SYN_REPORT, 0, 0)

    def __del__(self):
        self.stop()
