#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ble_sc
#  BLE speed and cadence sensor handling module.
import bluepy.btle
import logging
import threading
import time

M = {'module_name': 'ble_sc'}

## @var INF_MIN
# helper variable, minus infinity
INF_MIN = float("-inf")

## @var INF
# helper variable, infinity
INF = float("inf")

## @var NAN
# helper variable, not-a-number
NAN = float("nan")


## Class for handling BLE speed and cadence sensor
class ble_sc(Peripheral, threading.Thread):
    # FIXME - replace with proper service & characteristic scan
    CSC_HANDLE = 0x000f  # FIXME - explain
    CSC_ENABLE_SC = bytes("10", 'UTF-8')    # FIXME - explain
    CSC_DISABLE_SC = bytes("00", 'UTF-8')    # FIXME - explain
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    WAIT_TIME = 1.0
    ## @var RECONNECT_WAIT_TIME
    # Time of waiting after an exception has been raiesed or connection lost
    RECONNECT_WAIT_TIME = 3.0

    def __init__(self):
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')
        self.p_formats = dict(wheel_time_stamp='%.0f', wheel_rev_time='%.0f', cadence_time_stamp='%.0f', cadence="5.0f")
        self.p_units = dict(wheel_time_stamp='s', wheel_rev_time='s', cadence_time_stamp='s', cadence="RPM")
        self.p_raw_units = dict(wheel_time_stamp='s', wheel_rev_time='s', cadence_time_stamp='s', cadence="RPM")

        ## @var connected
        # Indicates if sensor is currently connected
        self.connected = False
        threading.Thread.__init__(self)
        self.reset_data()
        ## @var addr
        # Address of the cadence and speed sensor
        self.addr = addr
        ## @var name
        # Name of the cadence and speed sensor
        self.name = None
        ## @var state
        #State of the connection, same as in sensors.py STATE_DEV
        self.state = 0

        self.log.info('Connecting to {}'.format(addr), extra=M)
        self.state = 1
        self.log.info('State = {}'.format(self.state), extra=M)
        Peripheral.__init__(self, addr, addrType='random')
        self.connected = True
        self.state = 2
        self.log.info('State = {}'.format(self.state), extra=M)
        self.name = self.get_device_name()
        self.log.info('Connected to {}'.format(self.name), extra=M)
        self.log.debug('Setting notification handler', extra=M)
        self.delegate = CSC_Delegate()
        self.log.debug('Setting delegate', extra=M)
        self.withDelegate(self.delegate)
        self.log.debug('Enabling notifications', extra=M)
        self.set_notifications()

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.log.debug('[BLE_HR] Set notifications {}'.format(enable), extra=M)
        try:
            if enable:
                self.writeCharacteristic(self.CSC_HANDLE, self.CSC_ENABLE_SC, False)
            else:
                self.writeCharacteristic(self.CSC_HANDLE, self.CSC_DISABLE_SC, False)
        except BTLEException as e:
            if str(e) == "Helper not started (did you call connect()?)":
                self.log.error('[BLE_HR] Set notifications failed: {}'.format(e), extra=M)
            else:
                self.log.critical(
                    '[BLE_HR] Set notifications failed with uncontrolled error: {}'.format(e))
                    def get_device_name(self):
        c = self.getCharacteristics(uuid=AssignedNumbers.deviceName)
        name = c[0].read()
        self.log.debug('Device name: {}'.format(name), extra=M)
        return name

    def get_battery_level(self):
        b = self.getCharacteristics(uuid=AssignedNumbers.batteryLevel)
        #FIXME python3 check required (ord)
        level = ord(b[0].read())
        self.log.debug('Battery lavel: {}'.format(level), extra=M)
        return level

    def get_state(self):
        return self.state

    def run(self):
        while self.connected:
            try:
                if self.waitForNotifications(self.WAIT_TIME):
                    self.wheel_time_stamp = self.delegate.wheel_time_stamp
                    self.wheel_rev_time = self.delegate.wheel_rev_time
                    self.cadence_time_stamp = self.delegate.cadence_time_stamp
                    self.cadence = self.delegate.cadence
            except BTLEException as e:
                if str(e) == 'Device disconnected':
                    self.log.info('Device disconnected: {}'.format(self.name), extra=M)
                    self.connected = False
                    self.state = 0
                    self.log.debug('State = {}'.format(self.state), extra=M)
                    # We don't want to call waitForNotifications and fail too often
                    time.sleep(self.EXCEPTION_WAIT_TIME)
                else:
                    raise
            except AttributeError as e:
                if str(e) == "'NoneType' object has no attribute 'poll'":
                    self.log.debug('btle raised AttributeError exception {}'.format(e), extra=M)
                    # We don't want to call waitForNotifications and fail too often
                    time.sleep(self.EXCEPTION_WAIT_TIME)
                else:
                    raise

    def reset_data(self):
        ## @var cadence_time_stamp
        # Time stamp of the measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.
        self.wheel_time_stamp = time.time()
        ## @var wheel_rev_time
        # Measured wheel revolution time
        self.wheel_rev_time = 0
        ## @var cadence_time_stamp
        # Time stamp of the measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.
        self.cadence_time_stamp = time.time()
        ## @var cadence
        # Measured cadence
        self.cadence = 0

    def get_prefix(self):
        return M["module_name"]

    def get_raw_data(self):
        return dict(name=self.name,
                    addr=self.addr,
                    state=self.state,
                    wheel_time_stamp=self.wheel_time_stamp,
                    wheel_rev_time=self.wheel_rev_time,
                    cadence_time_stamp=self.cadence_time_stamp,
                    cadence=self.cadence)

#    FIXME make decision if get_data and get_raw_data are required
#    def get_data(self):
#        r = dict(
#            name=self.name, addr=self.addr, state=self.state, wheel_time_stamp=self.wheel_time_stamp, wheel_rev_time=self.wheel_rev_time,
#            cadence_time_stamp=self.cadence_time_stamp, cadence=self.cadence)
#        return r

    def get_formats(self):
        return self.p_formats

    def is_connected(self):
        return self.connected

    def __del__(self):
        self.stop()

    def stop(self):
        self.log.debug('Stop called', extra=M)
        if self.connected:
            self.connected = False
            time.sleep(1)
            self.log.debug('Disabling notifications', extra=M)
            self.set_notifications(enable=False)
            self.log.debug('Disconnecting..', extra=M)
            self.disconnect()
            self.state = 0
            self.log.info('State = {}'.format(self.state), extra=M)
            self.log.debug('Disconnected', extra=M)


## Class for handling BLE notifications from cadence and speed sensor
class CSC_Delegate(DefaultDelegate):
    WHEEL_REV_DATA_PRESENT = 0x01
    CRANK_REV_DATA_PRESENT = 0x02

    def __init__(self):
        self.log = logging.getLogger('system')
        DefaultDelegate.__init__(self)
        self.wheel_time_stamp = time.time()
        self.wheel_cumul = 0
        self.wheel_last_time_event = 0
        self.wheel_last_time_delta = 0
        self.wheel_rev_time = 0
        self.cadence_time_stamp = time.time()
        self.crank_cumul = 0
        self.crank_last_time_event = 0
        self.crank_last_time_delta = 0
        self.crank_rev_time = 0
        self.cadence = 0

    def handleNotification(self, cHandle, data):
        self.log.debug('Notification received from : {}'.format(hex(cHandle)), extra=M)

        # CSC Measurement from BLE_SC standard
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.csc_measurement.xml
        #
        # 03|02 00 00 00|88 11|02 00|30 08
        # ^ data content description
        #    ^ Last Wheel Event Time, unit has a resolution of 1/1024s.
        #                ^ Cumulative Crank Revolutions
        #                      ^ Cumulative Crank Revolutions
        #                            ^ Last Crank Event Time, unit has a resolution of 1/1024s.
        ts = time.time()

        i = 0
        data_b = {}
        for b in data:
            data_b[i] = b
            i += 1

        if data_b[0] & self.WHEEL_REV_DATA_PRESENT:
            # cr - cumularive revolutions
            # le - last event time
            # dt - time delta
            wh_cr = 0xff0000 * data_b[4] + 0xff00 * \
                data_b[3] + 0xff * data_b[2] + data_b[1]
            wh_le = (1.0 / 1024) * (0xff * data_b[6] + data_b[5])
            wh_dt = wh_le - self.wheel_last_time_event

            if wh_dt < 0:
                wh_dt = 64 + wh_le - self.wheel_last_time_event

            if (self.wheel_cumul != wh_cr) and (self.wheel_last_time_event != wh_le):
                rt = wh_dt / (wh_cr - self.wheel_cumul)

                self.wheel_time_stamp = ts
                self.wheel_last_time_event = wh_le
                self.wheel_last_time_delta = wh_dt
                self.wheel_rev_time = rt
                self.wheel_cumul = wh_cr

                self.log.debug('Last wheel event time: {:10.3f}, delta {:10.3f}'.format(self.wheel_last_time_event, self.wheel_last_time_delta), extra=M)
                self.log.debug('Wheel cumul revs: {:5d}'.format(wh_cr), extra=M)
                self.log.debug('Last wheel rev time: {:10.3f}'.format(self.wheel_rev_time), extra=M)

        if (data_b[0] & self.CRANK_REV_DATA_PRESENT):
            # cr - cumularive revolutions
            # le - last event time
            # dt - time delta
            cr_cr = 0xff * data_b[8] + data_b[7]
            cr_le = (1.0 / 1024) * (0xff * data_b[10] + data_b[9])
            cr_dt = cr_le - self.crank_last_time_event
            # FIXME - there seems to be some accuracy loss on timer overflow?
            if cr_dt < 0:
                cr_dt = 64 + cr_le - self.crank_last_time_event
            if (self.crank_cumul != cr_cr) and (self.crank_last_time_event != cr_le):
                rt = cr_dt / (cr_cr - self.crank_cumul)

                self.cadence_time_stamp = ts
                self.crank_last_time_event = cr_le
                self.wheel_last_time_delta = cr_dt
                self.crank_rev_time = rt
                self.crank_cumul = cr_cr
                self.cadence = 60.0 / rt

                self.log.debug('Last crank event time: {:10.3f}, delta {:10.3f}'.format(self.crank_last_time_event, self.crank_last_time_delta), extra=M)
                self.log.debug('Crank cumul revs: {:5d}'.format(cr_cr), extra=M)
                self.log.debug('Last crank rev time: {:10.3f}'.format(self.crank_rev_time), extra=M)
                self.log.debug('Cadence: {:10.3f}'.format(60.0 / rt), extra=M)
