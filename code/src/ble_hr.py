#! /usr/bin/python
## @package ble_hr
#  BLE heart rate sensor handling module.
from bluepy.btle import AssignedNumbers
from bluepy.btle import BTLEException
from bluepy.btle import DefaultDelegate
from bluepy.btle import Peripheral
import logging
import threading
import time

 
## Class for handling BLE heart rate sensor 
class ble_hr(Peripheral, threading.Thread):
    # FIXME - replace with proper service & characteristic scan
    HR_HANDLE = 0x000f  # FIXME - explain
    HR_ENABLE_HR = "10"    # FIXME - explain, try "01" is fails
    WAIT_TIME = 1      # Time of waiting for notifications
    EXCEPTION_WAIT_TIME = 10      # Time of waiting after an exception has been raies

    def __init__(self, addr):
        self.l = logging.getLogger('system')
        self.l.debug('[BLE_HR] WAIT_TIME {}'.format(self.WAIT_TIME))
        self.connected = False
        self.state = 0
        self.heart_rate = 0
        self.time_stamp = time.time()
        self.l.info('[BLE_HR] State = {}'.format(self.state))
        threading.Thread.__init__(self)
        self.addr = addr
        self.l.info('[BLE_HR] Connecting to {}'.format(addr))
        self.state = 1
        self.l.info('[BLE_HR] State = {}'.format(self.state))
        Peripheral.__init__(self, addr, addrType='random')
        self.connected = True
        self.state = 2
        self.l.info('[BLE_HR] State = {}'.format(self.state))
        self.name = self.get_device_name()
        self.l.info('[BLE_HR] Connected to {}'.format(self.name))
        self.l.debug('[BLE_HR] Setting notification handler')
        self.delegate = HR_Delegate()
        self.l.debug('[BLE_HR] Setting delegate')
        self.withDelegate(self.delegate)
        self.l.debug('[BLE_HR] Enabling notifications')
        self.set_notifications()

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.l.debug('[BLE_HR] Set notifications {}'.format(enable))
        try:
            self.writeCharacteristic(self.HR_HANDLE, self.HR_ENABLE_HR, enable)
        except BTLEException, e:
            if str(e) == "Helper not started (did you call connect()?)":
                self.l.error('[BLE_HR] Set notifications failed: {}'.format(e))
            else:
                self.l.critical(
                    '[BLE_HR] Set notifications failed with uncontrolled error: {}'.format(e))
                raise

    def get_device_name(self):
        c = self.getCharacteristics(uuid=AssignedNumbers.deviceName)
        name = c[0].read()
        self.l.debug('[BLE_HR] Device name: {}'.format(name))
        return name

    def get_battery_level(self):
        b = self.getCharacteristics(uuid=AssignedNumbers.batteryLevel)
        level = ord(b[0].read())
        self.l.debug('[BLE_HR] Battery lavel: {}'.format(level))
        return level

    def get_state(self):
        return self.state

    def run(self):
        while self.connected:
            try:
                if self.waitForNotifications(self.WAIT_TIME):
                    self.heart_rate = self.delegate.heart_rate
                    self.time_stamp = self.delegate.time_stamp
            except BTLEException, e:
                if str(e) == 'Device disconnected':
                    self.l.info('[BLE_HR] Device disconnected: {}'.format(self.name))
                    self.connected = False
                    self.state = 0
                    self.l.debug('[BLE_HR] State = {}'.format(self.state))
                    # We don't want to call waitForNotifications and fail too often
                    time.sleep(self.EXCEPTION_WAIT_TIME)
                else:
                    raise
            except AttributeError, e:
                if str(e) == "'NoneType' object has no attribute 'poll'":
                    self.l.debug('[BLE_HR] btle raised AttributeError exception {}'.format(e))
                    # We don't want to call waitForNotifications and fail too often
                    time.sleep(self.EXCEPTION_WAIT_TIME)
                else:
                    raise

    def get_data(self):
        r = dict(name=self.name, addr=self.addr, state=self.state,
                 time_stamp=self.time_stamp, heart_rate=self.heart_rate)
        return r

    def __del__(self):
        self.stop()

    def stop(self):
        self.l.debug('[BLE_HR] Stop called')
        if self.connected:
            self.connected = False
            time.sleep(1)
            self.l.debug('[BLE_HR] Disabling notifications')
            self.set_notifications(enable=False)
            self.l.debug('[BLE_HR] Disconnecting..')
            self.disconnect()
            self.state = 0
            self.l.debug('[BLE_HR] State = {}'.format(self.state))
            self.l.info('[BLE_HR] {} disconnected'.format(self.name))


class HR_Delegate(DefaultDelegate):

    def __init__(self):
        self.l = logging.getLogger('system')
        self.l.debug('[BLE_HR] Delegate __init__')
        DefaultDelegate.__init__(self)
        self.heart_rate = 0
        self.time_stamp = time.time()

    def handleNotification(self, cHandle, data):
        self.l.debug('[BLE_HR] Delegate:  Notification received. Handle: {}'.format(hex(cHandle)))

        # Heart Rate Measurement from BLE standard
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.heart_rate_measurement.xml
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.heart_rate_control_point.xml&u=org.bluetooth.characteristic.heart_rate_control_point.xml
        #
        self.time_stamp = time.time()

        i = 0
        data_b = {}
        for b in data:
            data_b[i] = ord(b)
            i += 1

        HR_VALUE_FORMAT = 0b00000001  # 0 UINT8, 1 UINT16
        # 0   Heart Rate Value Format is set to UINT8. Units: beats per minute (bpm)
        # 1   Heart Rate Value Format is set to UINT16. Units: beats per minute (bpm)
        # SENSOR_CONTACT_STATUS = 0b00000110
        # 0   Sensor Contact feature is not supported in the current connection
        # 1   Sensor Contact feature is not supported in the current connection
        # 2   Sensor Contact feature is supported, but contact is not detected
        # 3   Sensor Contact feature is supported and contact is detected
        # ENERGY_EXPENDED_STATUS = 0b00001000
        # 0   Energy Expended field is not present
        # 1   Energy Expended field is present. Units: kilo Joules
        # RR_INTERVAL = 0b000100000
        # 0   RR-Interval values are not present.
        # 1   One or more RR-Interval values are present.

        if data_b[0] & HR_VALUE_FORMAT:
            # UINT16
            # print ('HR: {}'.format(0xff * data_b[2] + data_b[1]))
            self.heart_rate = 0xff * data_b[2] + data_b[1]
        else:
            # UINT8
            # print ('HR: {}'.format(data_b[1]))
            self.heart_rate = data_b[1]
