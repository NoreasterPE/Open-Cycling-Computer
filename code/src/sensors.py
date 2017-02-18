#! /usr/bin/python

import threading
import logging
import time
#from gps import gps
#from bmp183 import bmp183
#from gps_mtk3339 import gps_mtk3339
from ble import ble


class sensors(threading.Thread):
    # Class for handling starting/stopping sensors in separate threads

    def __init__(self, simulate=False):
        threading.Thread.__init__(self)
        self.l = logging.getLogger('system')
        self.simulate = simulate
        self.connected = {'ble': False}
        if not self.simulate:
            print "Init called..."

    def run(self):
        if not self.simulate:
            while not self.connected['ble']:
                self.l.info("[RP] Initialising BLE sensor")
                #FIXME Hardcoded address
                self.ble = ble(self.simulate, "fd:df:0e:4e:76:cf")
                self.l.info("[RP] Starting BLE thread")
                self.ble.start()
                time.sleep(2)
            self.connected['ble'] = True

    def get_sensor(self, name):
        #FIXME Currnetly only ble
        if self.connected[name]:
            return self.ble
        else:
            return None

    def __del__(self):
        self.stop()

    def stop(self):
        self.connected['ble'] = False
        self.l.info("[RP] Stopping BLE thread")
        self.ble.stop()
