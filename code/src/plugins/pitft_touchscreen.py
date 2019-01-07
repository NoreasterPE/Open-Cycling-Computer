# -*- coding: utf-8 -*-
#  piTFT touchscreen handling using evdev

import evdev
import threading
try:
    # python 3.5+
    import queue
except ImportError:
    # python 2.7
    import Queue as queue

import plugin


## Class for handling events from piTFT touchscreen
#
# Input event structure:
#
#    On touch:
#
#    {'time': 1541236849.210577, 'id': 20, 'x': 54, 'y': 148, 'touch': 1}
#
#    On touch end:
#
#    {'time': 1541236849.222711, 'id': -1, 'x': None, 'y': None, 'touch': 0}
class pitft_touchscreen(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self, device_path="/dev/input/touchscreen"):
        super(pitft_touchscreen, self).__init__()
        self.device_path = device_path
        self.events = queue.Queue()
        self.pm.register_input_queue(self.extra['module_name'], self.events)
        self.shutdown = threading.Event()

    def run(self):
        thread_process = threading.Thread(target=self.process_device)
        # run thread as a daemon so it gets cleaned up on exit.
        thread_process.daemon = True
        thread_process.start()
        self.shutdown.wait()

    # thread function
    def process_device(self):
        device = None
        # if the path to device is not found, InputDevice raises an OSError
        # exception.  This will handle it and close thread.
        try:
            device = evdev.InputDevice(self.device_path)
        except Exception as ex:
            message = "Unable to load device {0} due to a {1} exception with" \
                      " message: {2}.".format(self.device_path,
                                              type(ex).__name__, str(ex))
            raise Exception(message)
        finally:
            if device is None:
                self.shutdown.set()
        # Loop for getting evdev events
        event = {'time': None, 'id': None, 'x': None, 'y': None, 'touch': None}
        while True:
            for input_event in device.read_loop():
                if input_event.type == evdev.ecodes.EV_ABS:
                    if input_event.code == evdev.ecodes.ABS_X:
                        event['x'] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_Y:
                        event['y'] = input_event.value
                    elif input_event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                        event['id'] = input_event.value
                        if input_event.value == -1:
                            event['x'] = None
                            event['y'] = None
                            event['touch'] = None
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_X:
                        pass
                    elif input_event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                        pass
                elif input_event.type == evdev.ecodes.EV_KEY:
                    event['touch'] = input_event.value
                elif input_event.type == evdev.ecodes.SYN_REPORT:
                    event['time'] = input_event.timestamp()
                    self.events.put(event)
                    e = event
                    event = {'x': e['x'], 'y': e['y']}
                    try:
                        event['id'] = e['id']
                    except KeyError:
                        event['id'] = None
                    try:
                        event['touch'] = e['touch']
                    except KeyError:
                        event['touch'] = None

    def get_event(self):
        if not self.events.empty():
            event = self.events.get()
            yield event
        else:
            yield None

    def queue_empty(self):
        return self.events.empty()

    def stop(self):
        self.shutdown.set()

    def __del__(self):
        self.shutdown.set()
