#! /usr/bin/python
import time
from bluepy.btle import AssignedNumbers
from bluepy.btle import Peripheral
from bluepy.btle import DefaultDelegate


class bt_csc(Peripheral):
    # FIXME - replace with proper service & characteristic scan
    CSC_HANDLE = 0x000f  # FIXME - explain
    CSC_ENABLE = "10"    # FIXME - explain

    def __init__(self, addr):

        print('Connecting to ' + addr)
        Peripheral.__init__(self, addr, addrType='random')
        self.connected = True
        print ".....connected to ", self.get_device_name()

        # Set notification handler
        self.delegate = CSC_Delegate()
        self.withDelegate(self.delegate)
        self.notifications_enabled = False

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.writeCharacteristic(self.CSC_HANDLE, self.CSC_ENABLE, enable)

    def get_device_name(self):
        c = self.getCharacteristics(uuid=AssignedNumbers.deviceName)
        return c[0].read()

    def get_battery_level(self):
        b = self.getCharacteristics(uuid=AssignedNumbers.batteryLevel)
        return ord(b[0].read())


class CSC_Delegate(DefaultDelegate):
    DATA_EXPIRY_TIME = 1.0  # sensor data expiry time
    WHEEL_REV_DATA_PRESENT = 0x01
    CRANK_REV_DATA_PRESENT = 0x02

    def __init__(self):
        DefaultDelegate.__init__(self)
        self.wheel_time_stamp = time.time()
        self.wheel_cumul = 0
        self.wheel_last_time_event = 0
        self.wheel_last_time_delta = 0
        self.wheel_rev_time = 0
        self.crank_time_stamp = time.time()
        self.crank_cumul = 0
        self.crank_last_time_event = 0
        self.crank_last_time_delta = 0
        self.crank_rev_time = 0
        self.crank_rpm = 0

    def handleNotification(self, cHandle, data):
        # print "Notification received from :", hex(cHandle)

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

                # print "Wheel: cumul revs: {:5d}".format(wh_cr),
                # print "| last time: {:10.3f}".format(self.wheel_last_time_event),
                # print "| last time dt: {:10.3f}".format(self.wheel_last_time_delta),
                # print "| rev time: {:10.3f}".format(self.wheel_rev_time),

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

                self.crank_time_stamp = ts
                self.crank_last_time_event = cr_le
                self.wheel_last_time_delta = cr_dt
                self.crank_rev_time = rt
                self.crank_cumul = cr_cr
                self.crank_rpm = 60.0 / rt

                # print "Crank: cumul revs: {:5d}".format(cr_cr),
                # print "| last time: {:10.3f}".format(self.crank_last_time_event),
                # print "| last time dt: {:10.3f}".format(self.crank_last_time_delta),
                # print "| rev time: {:10.3f}".format(self.crank_rev_time),

                #rpm = 60 / rt
                # print "| RPM: {:10.3f}".format(rpm)