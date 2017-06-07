#! /usr/bin/python
## @package sensors
#  Sensors module. Responsible for connecting to, starting and stopping sensors. Currently used sensors are:
#  BLE heart rate
#  BLE speed & cadence sensor
#  GPS (MTK3339) - [disabled]
#  BMP183 pressure & temperature sensor

from ble_sc import ble_sc
from ble_hr import ble_hr
from bluepy.btle import BTLEException
from bmp183 import bmp183
# Disable GPS (temporary)
# from gps_mtk3339 import gps_mtk3339
import logging
import threading
import time

## @var RECONNECT_DELAY
# Time between check if BLE connection need to be re-established
RECONNECT_DELAY = 2


## @var STATE_HOST
# BLE host states. Linked with different icons.
#  - disabled (state 0)
#  - present (state 1)
#  - scanning (state 2,3)
#  - connected 1 device (state 4)
#  - connected 2 devices (state 5)
#  - connected 3 devices (state 6)
#  - connected 4 devices (state 7)

STATE_HOST = {'disabled': 0,
              'enabled': 1,
              'scanning_1': 2,
              'scanning_2': 3,
              'connected_1': 4,
              'connected_2': 5,
              'connected_3': 6,
              'connected_4': 7}

## @var STATE_DEV
# BLE device states.
#  - disconnected (state 0)
#  - connecting (state 1)
#  - connected (state 2)
STATE_DEV = {'disconnected': 0,
             'connecting': 1,
             'connected': 2}


## Class for handling starting/stopping sensors in separate threads
class sensors(threading.Thread):

    ## The constructor
    #  @param self The python object self
    #  @param occ OCC instance
    def __init__(self, occ):
        threading.Thread.__init__(self)
        ## @var l
        # System logger handle
        self.l = logging.getLogger('system')
        ## @var occ
        # OCC Handle
        self.occ = occ
        ## @var sensors
        # Dict with sensor instances
        self.sensors = dict(ble_sc=None, ble_hr=None, gps=None, bmp183=None)
        ## @var names
        # Dict with names of the sensors
        self.names = dict(ble_sc='', ble_hr='', gps='', bmp183='')
        ## @var addrs
        # Dict with BLE addresses of the sensors
        self.addrs = dict(ble_sc='', ble_hr='', gps='', bmp183='')
        ## @var simulate
        # Local copy of simulate variable from OCC
        self.simulate = occ.get_simulate()
        ## @var ble_state
        # BLE host state
        self.ble_state = STATE_HOST['enabled']
        ## @var no_of_connected
        # Number of connected BLE devices
        self.no_of_connected = 0
        ## @var connecting
        # Indicates if host is currently trying to establish connection
        self.connecting = False
        ## @var connected
        # Dict keeping track of which sensor is connected
        self.connected = dict(ble_sc=False, ble_hr=None, gps=False, bmp183=False)
        self.l.info("[SE] Initialising GPS")
        try:
            # Disable GPS (temporary)
            # self.sensors['gps'] = gps_mtk3339(simulate)
            # self.connected['gps'] = True
            self.sensors['gps'] = None
            self.connected['gps'] = False
        except IOError:
            self.sensors['gps'] = None
        self.l.info("[SE] Initialising bmp183 sensor")
        try:
            self.sensors['bmp183'] = bmp183(self.simulate)
            self.connected['bmp183'] = True
        except IOError:
            self.connected['bmp183'] = None
        self.running = True

    ## Reads BLE devices names/addresses from ride_parameters module
    #  @param self The python object self
    def init_data_from_ride_parameters(self):
        self.names['ble_hr'] = self.occ.rp.params['ble_hr_name']
        self.names['ble_sc'] = self.occ.rp.params['ble_sc_name']
        self.addrs['ble_hr'] = self.occ.rp.params['ble_hr_addr']
        self.addrs['ble_sc'] = self.occ.rp.params['ble_sc_addr']

    ## Helper for setting BLE devices name and address
    #  @param self The python object self
    #  @param name Name of the device
    #  @param addr Address of the device
    #  @param dev_type Device type "hr" for heart rate sensor, "sc" for speed & cadence sensor
    def set_ble_device(self, name, addr, dev_type):
        self.names['ble_' + dev_type] = name
        self.addrs['ble_' + dev_type] = addr
        self.occ.rp.params['ble_' + dev_type + '_name'] = name
        self.occ.rp.params['ble_' + dev_type + '_addr'] = addr
        self.connected['ble_' + dev_type + '_addr'] = False

    ## Main loop of sensors module. Constantly tries to reconnect with BLE devices
    #  @param self The python object self
    def run(self):
        self.init_data_from_ride_parameters()
        if not self.simulate:
            if self.sensors['gps']:
                self.l.info("[SE] Starting GPS thread")
                self.sensors['gps'].start()
            if self.sensors['bmp183']:
                self.l.info("[SE] Starting bmp183 thread")
                self.sensors['bmp183'].start()
        while self.running:
            self.set_ble_state()
            if not self.connected['ble_hr']:
                self.l.info("[SE] Initialising BLE heart rate sensor")
                try:
                    self.sensors['ble_hr'] = ble_hr(self.addrs['ble_hr'])
                    self.names['ble_hr'] = self.sensors[
                        'ble_hr'].get_device_name()
                    self.l.info("[SE] Starting BLE heart rate thread")
                    self.sensors['ble_hr'].start()
                except BTLEException:
                    self.l.info(
                        "[SE] Connecion to BLE heart rate sensor failed")
                else:
                    self.connected['ble_hr'] = True
            self.set_ble_state()
            if not self.connected['ble_sc']:
                self.l.info("[SE] Initialising BLE speed & cadence sensor")
                try:
                    self.sensors['ble_sc'] = ble_sc(self.addrs['ble_sc'])
                    self.names['ble_sc'] = self.sensors[
                        'ble_sc'].get_device_name()
                    self.l.info("[SE] Starting BLE speed & cadence thread")
                    self.sensors['ble_sc'].start()
                except BTLEException, e:
                    self.l.info(
                        "[SE] Connecion to BLE speed & cadence sensor failed: {}".format(e))
                else:
                    self.connected['ble_sc'] = True

            # Wait before checking again if we need to reconnect
            time.sleep(RECONNECT_DELAY)

    ## Helper function for setting ble_state variable.
    #  @param self The python object self
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
            self.ble_state = STATE_HOST['enabled']
        if self.no_of_connected == 1:
            self.ble_state = STATE_HOST['connected_1']
        if self.no_of_connected == 2:
            self.ble_state = STATE_HOST['connected_2']
        if self.no_of_connected == 3:
            self.ble_state = STATE_HOST['connected_3']
        if self.no_of_connected == 4:
            self.ble_state = STATE_HOST['connected_4']
        # FIXME Tidy it up - showing "connecting" state doesn't work (blocking
        # call is the problem)
        if self.connecting:
            self.ble_state = STATE_HOST['scanning_1']

    ## Helper function for getting ble_state variable.
    #  @param self The python object self
    def get_ble_state(self):
        return self.ble_state

    ## Helper function for getting sensor handle
    #  @param self The python object self
    def get_sensor(self, name):
        self.l.debug('[SE] get_sensor called for {}'.format(name))
        if name in self.sensors and self.connected[name]:
            return self.sensors[name]
        else:
            self.l.debug("[SE] Sensor {} not ready or doesn't exist".format(name))
            return None

    ## Helper function for forcing sensor reconnection
    #  @param self The python object self
    #  @param name Sensor name
    def reconnect_sensor(self, name):
        self.connected[name] = False

    ## The destructor
    #  @param self The python object self
    def __del__(self):
        self.stop()

    ## Function stopping all sensors. Called by the destructor
    #  @param self The python object self
    def stop(self):
        self.l.debug("[SE] Stopping.. {}".format(__name__))
        self.running = False
        for s in self.sensors:
            if self.connected[s]:
                self.connected[s] = False
                self.l.debug("[SE] Stopping {} thread".format(s))
                self.sensors[s].stop()
                self.l.debug("[SE] Stopped {} thread".format(s))
                self.sensors[s] = None
