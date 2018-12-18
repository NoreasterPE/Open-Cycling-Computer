#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package compute
#  Convinience plugin to system calls like halt, reboot, etc

import logging
import os
import threading

import events
import plugin


## Convinience plugin to system calls like halt, reboot, etc
class syscalls(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def run(self):
        # This plugin doesn't need to run in background in a separate thread
        pass

    def halt(self):
        def _halt():
            os.system("sudo halt")

        if pm.event_queue is not None:
            pm.event_queue.put(('show_overlay', 'images/ol_shutdown.png', 60.0))
        threading.Thread(target=_halt).start()
        self.quit()

    def reboot(self):
        def _reboot():
            os.system("sudo reboot")

        pm = pyplum.pyplum()
        if pm.event_queue is not None:
            pm.event_queue.put(('show_overlay', 'images/ol_shutdown.png', 60.0))
        threading.Thread(target=_reboot).start()
        self.quit()

    def quit(self):
        pm = pyplum.pyplum()
        # Stop pyplum
        pm.parameters['quit']['value'] = True
        # Stop events
        if pm.event_queue is not None:
            pm.event_queue.put(('quit',))
        events_instance = events.events()
        events_instance.stop()

    def cycle_log_level(self):
        pm = pyplum.pyplum()
        log = logging.getLogger('system')
        log_level = log.getEffectiveLevel()
        log_level += 10
        if log_level > 50:
            log_level = 10
        log_level_name = logging.getLevelName(log_level)
        try:
            pm.parameters['log_level']['value'] = log_level_name
        except KeyError:
            pass

    def reload_layout(self):
        pm = pyplum.pyplum()
        if pm.event_queue is not None:
            pm.event_queue.put(('reload_layout',))

    def screenshot_mode(self):
        pm = pyplum.pyplum()
        try:
            if 'screenshot_mode' not in pm.parameters:
                pm.register_parameter('screenshot_mode', self.extra['module_name'], value=True)
            else:
                pm.parameters['screenshot_mode']['value'] = not pm.parameters['screenshot_mode']['value']
        except KeyError:
            pass

    def show_low_battery(self):
        pm = pyplum.pyplum()
        if pm.event_queue is not None:
            pm.event_queue.put(('show_overlay', 'images/ol_ble_scanning.png', 10.0))
            pm.event_queue.put(('show_overlay', 'images/ol_battery_low_warning.png', 2.0))
            pm.event_queue.put(('show_overlay', 'images/ol_ble_sc_connected.png'))
            pm.event_queue.put(('show_overlay', 'images/ol_ble_hr_connected.png', 2.0))
