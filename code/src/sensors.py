#! /usr/bin/python

import threading
import logging
#import time
#from gps import gps
#from bmp183 import bmp183
#from gps_mtk3339 import gps_mtk3339
from ble import ble
from bluepy.btle import BTLEException


class sensors(threading.Thread):
    # Class for handling starting/stopping sensors in separate threads

    def __init__(self, simulate=False):
        threading.Thread.__init__(self)
        self.l = logging.getLogger('system')
        self.sensors = dict(ble=None)
        self.simulate = simulate
        self.connected = {'ble': False}
        self.running = True

    def run(self):
        if not self.simulate:
            while not self.connected['ble'] and self.running:
                self.l.info("[RP] Initialising BLE sensor")
                #FIXME Hardcoded address
                try:
                    self.sensors['ble'] = ble(self.simulate, "fd:df:0e:4e:76:cf")
                    self.l.info("[RP] Starting BLE thread")
                    self.sensors['ble'].start()
                    self.connected['ble'] = True
                except BTLEException:
                    self.l.info("[RP] Connecion to BLE sensor failed")

    def get_sensor(self, name):
        #FIXME Currnetly only ble
        if name in self.sensors and self.connected[name]:
            return self.sensors[name]
        else:
            return None

    def __del__(self):
        self.stop()

    def stop(self):
        self.connected['ble'] = False
        self.running = False
        self.l.info("[RP] Stopping BLE thread")
        if self.sensors['ble']:
            self.sensors['ble'].stop()
        self.sensors['ble'] = None
