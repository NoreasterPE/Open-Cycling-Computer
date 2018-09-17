#!/usr/bin/python3
## @package sensors
#  Sensors module. Responsible for connecting to, starting and stopping sensors. Currently used sensors are:
#  BLE heart rate
#  BLE speed & cadence sensor
#  GPS (MTK3339) - [disabled]
#  BMP183 pressure & temperature sensor

import ble_sc
import ble_hr
#from bluepy.btle import BTLEException
#from bmp183 import bmp183
# Disable GPS (temporary)
# from gps_mtk3339 import gps_mtk3339
import logging
import threading
import time

M = {'module_name': 'sensors'}

## @var RECONNECT_DELAY
# Time between check if BLE connection need to be re-established
RECONNECT_DELAY = 2.0


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
        self.log = logging.getLogger('system')
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
        ## @var ble_host_state
        # BLE host state
        self.ble_host_state = STATE_HOST['enabled']
        ## @var no_of_connected
        # Number of connected BLE devices
        self.no_of_connected = 0
        ## @var connecting
        # Indicates if host is currently trying to establish connection
        self.connecting = False
        ## @var connected
        # Dict keeping track of which sensor is connected
        self.connected = dict(ble_sc=False, ble_hr=False, gps=False, bmp183=False)
        '''
        self.log.info("Initialising GPS", extra=M)
        try:
            # Disable GPS (temporary)
            # self.sensors['gps'] = gps_mtk3339(simulate)
            # self.connected['gps'] = True
            self.sensors['gps'] = None
            self.connected['gps'] = False
        except IOError:
            self.sensors['gps'] = None
        self.log.info("Initialising bmp183 sensor", extra=M)
        try:
            self.sensors['bmp183'] = bmp183(self.simulate)
            self.connected['bmp183'] = True
        except IOError:
            self.connected['bmp183'] = None'''
        self.sensors['ble_hr'] = ble_hr.ble_hr()
        self.sensors['ble_sc'] = ble_sc.ble_sc()
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
        self.log.debug("run started", extra=M)
        self.init_data_from_ride_parameters()

        self.log.debug("Setting ble_hr device address to {}".format(self.addrs["ble_hr"]), extra=M)
        self.sensors['ble_hr'].set_addr(self.addrs["ble_hr"])
        self.log.debug("Starting ble_hr thread", extra=M)
        self.sensors['ble_hr'].start()

        self.log.debug("Setting ble_sc device address to {}".format(self.addrs["ble_sc"]), extra=M)
        self.sensors['ble_sc'].set_addr(self.addrs["ble_sc"])
        self.log.debug("Starting ble_sc tscead", extra=M)
        self.sensors['ble_sc'].start()

        while self.running:
            self.set_ble_host_state()
            time.sleep(1.0)
        self.log.debug("run finished", extra=M)

    ## Helper function for setting ble_host_state variable.
    #  @param self The python object self
    def set_ble_host_state(self):
        self.no_of_connected = 0
        self.connecting = False
        for name in self.sensors:
            try:
                s = self.sensors[name].get_state()
                if s == 1:
                    self.connecting = True
                if s == 2:
                    self.no_of_connected += 1
            except AttributeError:
                #Sensor is not ready yet, let's wait
                pass
        if self.no_of_connected == 0:
            self.ble_host_state = STATE_HOST['enabled']
        if self.no_of_connected == 1:
            self.ble_host_state = STATE_HOST['connected_1']
        if self.no_of_connected == 2:
            self.ble_host_state = STATE_HOST['connected_2']
        if self.no_of_connected == 3:
            self.ble_host_state = STATE_HOST['connected_3']
        if self.no_of_connected == 4:
            self.ble_host_state = STATE_HOST['connected_4']
        # FIXME Tidy it up - showing "connecting" state doesn't work (blocking
        # call is the problem)
        if self.connecting:
            self.ble_host_state = STATE_HOST['scanning_1']

    ## Helper function for getting ble_host_state variable.
    #  @param self The python object self
    def get_ble_host_state(self):
        return STATE_HOST[self.ble_host_state]

    ## Helper function for getting sensor handle
    #  @param self The python object self
    def get_sensor(self, name):
        self.log.debug('get_sensor called for {}'.format(name), extra=M)
        if name in self.sensors:
            return self.sensors[name]
        else:
            self.log.debug("Sensor {} not ready or doesn't exist".format(name), extra=M)
            return None

    ## The destructor
    #  @param self The python object self
    def __del__(self):
        self.stop()

    ## Function stopping all sensors. Called by the destructor
    #  @param self The python object self
    def stop(self):
        self.log.debug("stop started", extra=M)
        self.running = False
        for s in self.sensors:
            self.connected[s] = False
            self.log.debug("Stopping {} thread".format(s), extra=M)
            try:
                self.sensors[s].stop()
                self.log.debug("Stopped {} thread".format(s), extra=M)
            except AttributeError:
                pass
            self.sensors[s] = None
        self.log.debug("stop finished", extra=M)
