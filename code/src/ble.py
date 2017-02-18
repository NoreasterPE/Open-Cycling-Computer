#! /usr/bin/python
import time
import threading
import logging
from bluepy.btle import AssignedNumbers
from bluepy.btle import Peripheral
from bluepy.btle import DefaultDelegate


class ble(Peripheral, threading.Thread):
    # FIXME - replace with proper service & characteristic scan
    CSC_HANDLE = 0x000f  # FIXME - explain
    CSC_ENABLE = "10"    # FIXME - explain
    WAIT_TIME = 0.3      # Time of waiting for notifications or time between simulations. Can we wait for notifications longer?

    def __init__(self, simulate, addr):
        self.l = logging.getLogger('system')
        self.l.debug('[BLE] WAIT_TIME {}'.format(self.WAIT_TIME))
        self.connected = False
        threading.Thread.__init__(self)
        self.l.info('[BLE] Connecting to {}'.format(addr))
        self.simulate = simulate
        self.addr = addr
        self.notifications_enabled = False
        self.wheel_time_stamp = 0
        self.wheel_rev_time = 0
        self.cadence_time_stamp = 0
        self.cadence = 0
        Peripheral.__init__(self, addr, addrType='random')
        self.connected = True
        if not self.simulate:
            self.name = self.get_device_name()
            self.l.info('[BLE] Connected to {}'.format(self.name))
            # Set notification handler
            self.l.debug('[BLE] Setting notification handler')
            self.delegate = CSC_Delegate()
            self.withDelegate(self.delegate)
            self.set_notifications()
        else:
            self.l.info('[BLE] Connection simulated')

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.l.debug('[BLE] Enabling notifications')
        self.writeCharacteristic(self.CSC_HANDLE, self.CSC_ENABLE, enable)

    def get_device_name(self):
        c = self.getCharacteristics(uuid=AssignedNumbers.deviceName)
        name = c[0].read()
        self.l.debug('[BLE] Device name: {}'.format(name))
        return name

    def get_battery_level(self):
        b = self.getCharacteristics(uuid=AssignedNumbers.batteryLevel)
        level = ord(b[0].read())
        self.l.debug('[BLE] Battery lavel: {}'.format(level))
        return level

    def run(self):
        while self.connected:
            if not self.simulate:
                if self.waitForNotifications(self.WAIT_TIME):
                    self.wheel_time_stamp = self.delegate.wheel_time_stamp
                    self.wheel_rev_time = self.delegate.wheel_rev_time
                    self.cadence_time_stamp = self.delegate.cadence_time_stamp
                    self.cadence = self.delegate.cadence
            else:
                    time.sleep(self.WAIT_TIME)
                    self.wheel_time_stamp = time.time()
                    self.wheel_rev_time = 1.0
                    self.cadence_time_stamp = time.time()
                    self.cadence = 96.0

    def get_data(self):
        r = dict(wheel_time_stamp=self.wheel_time_stamp,
                 wheel_rev_time=self.wheel_rev_time,
                 cadence_time_stamp=self.cadence_time_stamp,
                 cadence=self.cadence)
        return r

    def __del__(self):
        self.stop()

    def stop(self):
        self.l.debug('[BLE] Stop called')
        if not self.simulate and self.connected:
            self.l.debug('[BLE] Disabling notifications')
            self.connected = False
            time.sleep(1)
            self.set_notifications(enable=False)
            self.l.debug('[BLE] Disconnecting..')
            self.disconnect()
            self.l.debug('[BLE] Disconnected')


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
        self.l.debug('[BLE] Notification received from : {}'.format(hex(cHandle)))

        # CSC Measurement from BLE standard
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

                self.l.debug('[BLE] Last wheel event time: {:10.3f}, delta {:10.3f}'.format(self.wheel_last_time_event, self.wheel_last_time_delta))
                self.l.debug('[BLE] Wheel cumul revs: {:5d}'.format(wh_cr))
                self.l.debug('[BLE] Last wheel rev time: {:10.3f}'.format(self.wheel_rev_time))

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

                self.l.debug('[BLE] Last crank event time: {:10.3f}, delta {:10.3f}'.format(self.crank_last_time_event, self.crank_last_time_delta))
                self.l.debug('[BLE] Crank cumul revs: {:5d}'.format(cr_cr))
                self.l.debug('[BLE] Last crank rev time: {:10.3f}'.format(self.crank_rev_time))
                self.l.debug('[BLE] Cadence: {:10.3f}'.format(60.0 / rt))
