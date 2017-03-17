#! /usr/bin/python
from bluepy.btle import AssignedNumbers
from bluepy.btle import BTLEException
from bluepy.btle import DefaultDelegate
from bluepy.btle import Peripheral
import logging
import threading
import time


class ble_sc(Peripheral, threading.Thread):
    # FIXME - replace with proper service & characteristic scan
    CSC_HANDLE = 0x000f  # FIXME - explain
    CSC_ENABLE_SC = "10"    # FIXME - explain
    WAIT_TIME = 0.3      # Time of waiting for notifications
    EXCEPTION_WAIT_TIME = 10      # Time of waiting after an exception has been raies

    def __init__(self, addr):
        self.l = logging.getLogger('system')
        self.l.debug('[BLE_SC] WAIT_TIME {}'.format(self.WAIT_TIME))
        self.connected = False
        self.state = 0
        self.l.info('[BLE_SC] State = {}'.format(self.state))
        threading.Thread.__init__(self)
        self.addr = addr
        self.notifications_enabled = False
        self.wheel_time_stamp = time.time()
        self.wheel_rev_time = 0
        self.cadence_time_stamp = time.time()
        self.cadence = 0
        self.l.info('[BLE_SC] Connecting to {}'.format(addr))
        self.state = 1
        self.l.info('[BLE_SC] State = {}'.format(self.state))
        Peripheral.__init__(self, addr, addrType='random')
        self.connected = True
        self.state = 2
        self.l.info('[BLE_SC] State = {}'.format(self.state))
        self.name = self.get_device_name()
        self.l.info('[BLE_SC] Connected to {}'.format(self.name))
        self.l.debug('[BLE_SC] Setting notification handler')
        self.delegate = CSC_Delegate()
        self.l.debug('[BLE_SC] Setting delegate')
        self.withDelegate(self.delegate)
        self.l.debug('[BLE_SC] Enabling notifications')
        self.set_notifications()

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.l.debug('[BLE_HR] Set notifications {}'.format(enable))
        try:
            self.writeCharacteristic(self.CSC_HANDLE, self.CSC_ENABLE_SC, enable)
        except BTLEException, e:
            if str(e) == "Helper not started (did you call connect()?)":
                self.l.error('[BLE_HR] Set notifications failed: {}'.format(e))
            else:
                self.l.critical('[BLE_HR] Set notifications failed with uncontrolled error: {}'.format(e))
                raise

    def get_device_name(self):
        c = self.getCharacteristics(uuid=AssignedNumbers.deviceName)
        name = c[0].read()
        self.l.debug('[BLE_SC] Device name: {}'.format(name))
        return name

    def get_battery_level(self):
        b = self.getCharacteristics(uuid=AssignedNumbers.batteryLevel)
        level = ord(b[0].read())
        self.l.debug('[BLE_SC] Battery lavel: {}'.format(level))
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
            except BTLEException, e:
                if str(e) == 'Device disconnected':
                    self.l.info('[BLE_SC] Device disconnected: {}'.format(self.name))
                    self.connected = False
                    self.state = 0
                    self.l.debug('[BLE_SC] State = {}'.format(self.state))
                    # We don't want to call waitForNotifications and fail too often
                    time.sleep(self.EXCEPTION_WAIT_TIME)
                else:
                    raise
            except AttributeError, e:
                if str(e) == "'NoneType' object has no attribute 'poll'":
                    self.l.debug('[BLE_SC] btle raised AttributeError exception {}'.format(e))
                    # We don't want to call waitForNotifications and fail too often
                    time.sleep(self.EXCEPTION_WAIT_TIME)
                else:
                    raise

    def get_data(self):
        r = dict(state=self.state, wheel_time_stamp=self.wheel_time_stamp, wheel_rev_time=self.wheel_rev_time,
                 cadence_time_stamp=self.cadence_time_stamp, cadence=self.cadence)
        return r

    def __del__(self):
        self.stop()

    def stop(self):
        self.l.debug('[BLE_SC] Stop called')
        if self.connected:
            self.connected = False
            time.sleep(1)
            self.l.debug('[BLE_SC] Disabling notifications')
            self.set_notifications(enable=False)
            self.l.debug('[BLE_SC] Disconnecting..')
            self.disconnect()
            self.state = 0
            self.l.info('[BLE_SC] State = {}'.format(self.state))
            self.l.debug('[BLE_SC] Disconnected')


class CSC_Delegate(DefaultDelegate):
    WHEEL_REV_DATA_PRESENT = 0x01
    CRANK_REV_DATA_PRESENT = 0x02

    def __init__(self):
        self.l = logging.getLogger('system')
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
        self.l.debug('[BLE_SC] Notification received from : {}'.format(hex(cHandle)))

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
            data_b[i] = ord(b)
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

                self.l.debug('[BLE_SC] Last wheel event time: {:10.3f}, delta {:10.3f}'.format(self.wheel_last_time_event, self.wheel_last_time_delta))
                self.l.debug('[BLE_SC] Wheel cumul revs: {:5d}'.format(wh_cr))
                self.l.debug('[BLE_SC] Last wheel rev time: {:10.3f}'.format(self.wheel_rev_time))

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

                self.l.debug('[BLE_SC] Last crank event time: {:10.3f}, delta {:10.3f}'.format(self.crank_last_time_event, self.crank_last_time_delta))
                self.l.debug('[BLE_SC] Crank cumul revs: {:5d}'.format(cr_cr))
                self.l.debug('[BLE_SC] Last crank rev time: {:10.3f}'.format(self.crank_rev_time))
                self.l.debug('[BLE_SC] Cadence: {:10.3f}'.format(60.0 / rt))
