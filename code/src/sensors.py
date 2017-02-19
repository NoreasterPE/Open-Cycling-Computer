#! /usr/bin/python

import threading
import logging
#import time
#from gps import gps
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
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
        self.l.info("[SE] Initialising GPS")
        self.sensors['gps'] = gps_mtk3339(simulate)
        self.l.info("[SE] Initialising bmp183 sensor")
        self.sensor['bmp183'] = bmp183(self.occ, simulate)

    def run(self):
        if not self.simulate:
            while not self.connected['ble'] and self.running:
                self.l.info("[SE] Initialising BLE sensor")
                #FIXME Hardcoded address
                try:
                    self.sensors['ble'] = ble(self.simulate, "fd:df:0e:4e:76:cf")
                    self.l.info("[SE] Starting BLE thread")
                    self.sensors['ble'].start()
                    self.connected['ble'] = True
                except BTLEException:
                    self.l.info("[SE] Connecion to BLE sensor failed")

    def get_sensor(self, name):
        #FIXME Currnetly only ble
        if name in self.sensors and self.connected[name]:
            return self.sensors[name]
        else:
            self.l.debug("[SE] Sensor {} not ready or doesn't exist").format(name)
            return None

    def __del__(self):
        self.stop()

    def stop(self):
        self.connected['ble'] = False
        self.running = False
        self.l.info("[SE] Stopping BLE thread")
        if self.sensors['ble']:
            self.sensors['ble'].stop()
        self.sensors['ble'] = None
