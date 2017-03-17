#! /usr/bin/python

from ble_sc import ble_sc
from ble_hr import ble_hr
from bluepy.btle import BTLEException
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import logging
import threading
import time

# Time between check if BLE connection need to be re-established
RECONNECT_DELAY = 2


#  FIXME BLE host states in documentation:
#  - disabled (state 0)
#  - present (state 1)
#  - scanning (state 2,3)
#  - connected 1 (state 4)
#  - connected 2 (state 5)
#  - connected 3 (state 6)
#  - connected 4 (state 7)

#  FIXME BLE device states in documentation:
#  - disconnected (state 0)
#  - connecting (state 1)
#  - connected (state 2)

class sensors(threading.Thread):
    # Class for handling starting/stopping sensors in separate threads

    def __init__(self, occ, simulate=False):
        threading.Thread.__init__(self)
        self.l = logging.getLogger('system')
        self.sensors = dict(ble_sc=None, ble_hr=None, gps=None, bmp183=None)
        self.simulate = simulate
        self.ble_state = 0
        self.no_of_connected = 0
        self.connecting = False
        self.connected = dict(ble_sc=False, ble_hr=None, gps=False, bmp183=False)
        self.l.info("[SE] Initialising GPS")
        self.sensors['gps'] = gps_mtk3339(simulate)
        # FIXME Real device will need a check
        self.connected['gps'] = True
        self.l.info("[SE] Initialising bmp183 sensor")
        self.sensors['bmp183'] = bmp183(simulate)
        # FIXME Real device will need a check
        self.connected['bmp183'] = True
        self.running = True

    def run(self):
        self.l.info("[SE] Starting GPS thread")
        self.sensors['gps'].start()
        self.l.info("[SE] Starting bmp183 thread")
        self.sensors['bmp183'].start()
        while self.running:
            self.set_ble_state()
            if not self.connected['ble_hr']:
                self.l.info("[SE] Initialising BLE heart rate sensor")
                #FIXME Hardcoded address
                try:
                    self.sensors['ble_hr'] = ble_hr("D6:90:A8:08:F0:E4")
                    self.l.info("[SE] Starting BLE heart rate thread")
                    self.sensors['ble_hr'].start()
                except BTLEException:
                    self.l.info("[SE] Connecion to BLE heart rate sensor failed")
                else:
                    self.connected['ble_hr'] = True
            self.set_ble_state()
            if not self.connected['ble_sc']:
                self.l.info("[SE] Initialising BLE speed & cadence sensor")
                #FIXME Hardcoded address
                try:
                    self.sensors['ble_sc'] = ble_sc("fd:df:0e:4e:76:cf")
                    self.l.info("[SE] Starting BLE speed & cadence thread")
                    self.sensors['ble_sc'].start()
                except BTLEException, e:
                    self.l.info("[SE] Connecion to BLE speed & cadence sensor failed: {}".format(e))
                else:
                    self.connected['ble_sc'] = True

            # Wait before checking again if we need to reconnect
            time.sleep(RECONNECT_DELAY)

    def set_ble_state(self):
        self.no_of_connected = 0
        self.connecting = False
        for name in self.sensors:
            try:
                s = self.sensors[name].get_state()
                if s == 1:
                    self.connecting = True
                if s == 2:
                    self.no_of_connected += 1
            except:
                pass
        if self.no_of_connected == 0:
            self.ble_state = 1
        if self.no_of_connected == 1:
            self.ble_state = 4
        if self.no_of_connected == 2:
            self.ble_state = 5
        if self.no_of_connected == 3:
            self.ble_state = 6
        if self.no_of_connected == 4:
            self.ble_state = 7
        #FIXME Tidy it up - showing "connecting" state doesn't work (blocking call is the problem)
        if self.connecting:
                self.ble_state = 2

    def get_ble_state(self):
        return self.ble_state

    def get_sensor(self, name):
        self.l.debug('[SE] get_sensor called for {}'.format(name))
        if name in self.sensors and self.connected[name]:
            return self.sensors[name]
        else:
            self.l.debug("[SE] Sensor {} not ready or doesn't exist".format(name))
            return None

    def reconnect_sensor(self, name):
        self.connected[name] = False

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False
        for s in self.sensors:
            if self.connected[s]:
                self.connected[s] = False
                self.l.debug("[SE] Stopping {} thread".format(s))
                self.sensors[s].stop()
                self.sensors[s] = None
