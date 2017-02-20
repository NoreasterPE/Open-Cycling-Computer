#! /usr/bin/python

from ble import ble
from bluepy.btle import BTLEException
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import logging
import threading


class sensors(threading.Thread):
    # Class for handling starting/stopping sensors in separate threads

    def __init__(self, occ, simulate=False):
        threading.Thread.__init__(self)
        self.l = logging.getLogger('system')
        self.sensors = dict(ble=None, gps=None, bmp183=None)
        self.simulate = simulate
        self.connected = dict(ble=False, gps=False, bmp183=False)
        self.l.info("[SE] Initialising GPS")
        self.sensors['gps'] = gps_mtk3339(simulate)
        self.l.info("[SE] Initialising bmp183 sensor")
        self.sensors['bmp183'] = bmp183(simulate)
        self.running = True

    def run(self):
        self.l.info("[RP] Starting GPS thread")
        self.sensors['gps'].start()
        self.l.info("[RP] Starting bmp183 thread")
        self.sensors['bmp183'].start()
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
        if name in self.sensors and self.connected[name]:
            return self.sensors[name]
        else:
            self.l.debug("[SE] Sensor {} not ready or doesn't exist".format(name))
            return None

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False
        for s in self.sensors:
            if self.sensors[s]:
                self.connected[s] = False
                self.l.debug("[SE] Stopping {} thread".format(s))
                self.sensors[s].stop()
                self.sensors[s] = None
