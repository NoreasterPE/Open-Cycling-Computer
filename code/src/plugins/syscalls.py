#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package compute
#  Convinience plugin to system calls like halt, reboot, etc

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
        print('halt')
        import os
        os.system("sudo halt")

    def reboot(self):
        print('reboot')
        import os
        os.system("sudo reboot")

    def quit(self):
        print('quit')
        # FIXME It doesn't stop all threades, so it's useless
        quit()

    def cycle_log_level(self):
        import logging
        import pyplum
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
        import pyplum
        pm = pyplum.pyplum()
        if pm.event_queue is not None:
            pm.event_queue.put(('reload_layout',))
