#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ble_sc
#  BLE speed and cadence sensor handling module.
import ble_sensor
import bluepy.btle
import math
import numbers
import plugin_manager
import time


## Class for handling BLE speed and cadence sensor
class ble_sc(ble_sensor.ble_sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}
    # FIXME - replace with proper service & characteristic scan
    HANDLE = 0x000f  # FIXME - explain
    ENABLE_NOTIFICATIONS = bytes("10", 'UTF-8')    # FIXME - explain, try "01" is fails
    DISABLE_NOTIFICATIONS = bytes("00", 'UTF-8')

    def __init__(self):
        super().__init__()
        self.log.debug("{} __init__ started".format(__name__), extra=self.extra)
        self.pm = plugin_manager.plugin_manager()
        self.pm.register_parameter("cadence_speed_device_name", self.extra["module_name"])
        self.pm.register_parameter("cadence_speed_battery_level", self.extra["module_name"])
        self.pm.register_parameter("wheel_revolution_time", self.extra["module_name"], raw_unit="s")
        self.pm.register_parameter("wheel_revolutions", self.extra["module_name"])
        self.pm.register_parameter("odometer", self.extra["module_name"], raw_unit="m", unit="km")
        self.pm.register_parameter("cadence", self.extra["module_name"], value=numbers.NAN, raw_unit="RPM")
        self.pm.register_parameter("cadence_notification_beat", self.extra["module_name"])
        self.pm.register_parameter("cadence_speed_device_address", self.extra["module_name"])
        self.pm.request_parameter("cadence_speed_device_address", self.extra["module_name"])
        self.pm.request_parameter("wheel_circumference", self.extra["module_name"])
        self.delegate_class = sc_delegate

    ## Process data delivered from delegate
    #  @param self The python object self
    def process_delegate_data(self):
        if self.delegate.measurement_no <= 2:
            #Fresh start or restart after lost connection. Update average value in the delegate
            self.delegate.cadence_avg = self.pm.parameters["cadence"]["value_avg"]
            self.measurement_time = self.delegate.measurement_time
        if self.pm.parameters["cadence"]["reset"]:
            #Reset by user, reset deletage data
            self.log.debug('reset request received', extra=self.extra)
            self.delegate.cadence = 0.0
            self.delegate.cadence_avg = 0.0
            self.delegate.measurement_time = 0.0
            self.pm.parameters["cadence"]["reset"] = False
        try:
            if self.delegate.wheel_time_stamp == self.delegate.wheel_revolution_time_stamp:
                self.pm.parameters["wheel_revolution_time"]["time_stamp"] = self.delegate.wheel_revolution_time_stamp
                self.pm.parameters["wheel_revolution_time"]["value"] = self.delegate.wheel_revolution_time
                self.log.debug('wheel_revolution_time {}'.format(self.pm.parameters["wheel_revolution_time"]["value"]), extra=self.extra)
                # Move to compute module
                self.pm.parameters["speed"]["value"] = self.pm.parameters["wheel_circumference"]["value"] / self.pm.parameters["wheel_revolution_time"]["value"]
                self.pm.parameters["speed"]["value_max"] = max(self.pm.parameters["speed"]["value_max"], self.pm.parameters["speed"]["value"])
            else:
                self.pm.parameters["speed"]["value"] = 0.0
            self.pm.parameters["speed"]["time_stamp"] = self.delegate.wheel_time_stamp

            if self.pm.parameters["wheel_revolutions"]["value"] != self.delegate.wheel_revolutions:
                self.log.debug('wheel_revolutions {}'.format(self.pm.parameters["wheel_revolutions"]["value"]), extra=self.extra)
                try:
                    self.pm.parameters["odometer"]["value"] += (self.delegate.wheel_revolutions -
                                                               self.pm.parameters["wheel_revolutions"]["value"]) * self.pm.parameters["wheel_circumference"]["value"]
                except TypeError:
                    pass
                self.pm.parameters["wheel_revolutions"]["value"] = self.delegate.wheel_revolutions

            self.pm.parameters["cadence"]["time_stamp"] = self.delegate.cadence_time_stamp
            self.pm.parameters["cadence"]["value"] = self.delegate.cadence
            self.pm.parameters["cadence"]["value_avg"] = self.delegate.cadence_avg
            self.measurement_time = self.delegate.measurement_time
            self.pm.parameters["cadence"]["value_max"] = max(self.pm.parameters["cadence"]["value_max"], self.delegate.cadence)
            self.pm.parameters["cadence_notification_beat"]["value"] = self.delegate.cadence_notification_beat
            if self.pm.parameters["cadence_speed_device_name"]["value"] != self.device_name:
                self.pm.parameters["cadence_speed_device_name"]["value"] = self.device_name
            if self.pm.parameters["cadence_speed_battery_level"]["value"] != self.battery_level:
                self.pm.parameters["cadence_speed_battery_level"]["value"] = self.battery_level
        except (AttributeError) as exception:
            self.handle_exception(exception, "process_delegate_data")

    def notification(self):
        if self.pm.parameters["cadence_speed_device_address"]["value"] != self.device_address:
            self.device_address = self.pm.parameters["cadence_speed_device_address"]["value"]
        if self.pm.parameters["cadence_speed_battery_level"]["value"] != self.battery_level:
            self.pm.parameters["cadence_speed_battery_level"]["value"] = self.battery_level

    def reset_data(self):
        super().reset_data()
        ## @var cadence_time_stamp
        # Time stamp of the wheel rev measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.


## Class for handling BLE notifications from cadence and speed sensor
class sc_delegate(bluepy.btle.DefaultDelegate):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}
    WHEEL_REV_DATA_PRESENT = 0x01
    CRANK_REV_DATA_PRESENT = 0x02
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    EXPIRY_TIME = 3.0

    def __init__(self, log):
        self.log = log
        self.log.debug('Delegate __init__ started', extra=self.extra)
        super().__init__()
        self.reset_data()
        self.log.debug('Delegate __init__ finished', extra=self.extra)

    def handleNotification(self, cHandle, data):
        #self.log.debug('Delegate: handleNotification started', extra=self.extra)
        self.log.debug('Delegate: Notification received. Handle: {}, data: {}'.format(hex(cHandle), data), extra=self.extra)

        # CSC Measurement from BLE_SC standard
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.csc_measurement.xml
        #
        # 03|02 00 00 00|88 11|02 00|30 08
        # ^ data content description
        #    ^ Last Wheel Event Time, unit has a resolution of 1/1024s.
        #                ^ Cumulative Crank Revolutions
        #                      ^ Cumulative Crank Revolutions
        #                            ^ Last Crank Event Time, unit has a resolution of 1/1024s.
        self.time_stamp_previous = self.time_stamp
        self.time_stamp = time.time()
        self.measurement_no += 1
        self.cadence_notification_beat = int(not(self.cadence_notification_beat))

        i = 0
        data_b = {}
        for b in data:
            data_b[i] = b
            i += 1

        if data_b[0] & self.WHEEL_REV_DATA_PRESENT:
            self.log.debug('WHEEL_REV_DATA_PRESENT', extra=self.extra)
            self.wheel_time_stamp = self.time_stamp
            # cr - cumularive revolutions
            # le - last event time
            # dt - time delta
            wh_cr = 0xff0000 * data_b[4] + 0xff00 * data_b[3] + 0xff * data_b[2] + data_b[1]
            wh_le = (1.0 / 1024) * (0xff * data_b[6] + data_b[5])
            wh_dt = wh_le - self.wheel_last_time_event

            if wh_dt < 0:
                wh_dt = 64 + wh_le - self.wheel_last_time_event

            if (self.wheel_revolutions != wh_cr) and (self.wheel_last_time_event != wh_le):
                rt = wh_dt / (wh_cr - self.wheel_revolutions)

                self.wheel_time_stamp = self.time_stamp
                self.wheel_last_time_event = wh_le
                self.wheel_last_time_delta = wh_dt
                self.wheel_revolution_time = rt
                self.wheel_revolutions = wh_cr
                self.wheel_revolution_time_stamp = self.wheel_time_stamp
            else:
                if (self.wheel_time_stamp - self.wheel_revolution_time_stamp) > self.EXPIRY_TIME:
                    self.wheel_revolution_time = numbers.NAN
        else:
            self.wheel_time_stamp = numbers.NAN
            self.wheel_revolution_time = numbers.NAN

        self.log.debug('Last wheel event time: {:10.3f}, delta {:10.3f}'.format(self.wheel_last_time_event, self.wheel_last_time_delta), extra=self.extra)
        self.log.debug('Wheel cumul revs: {:5d}'.format(wh_cr), extra=self.extra)
        self.log.debug('Last wheel rev time: {:10.3f}'.format(self.wheel_revolution_time), extra=self.extra)

        if (data_b[0] & self.CRANK_REV_DATA_PRESENT):
            self.log.debug('CRANK_REV_DATA_PRESENT', extra=self.extra)
            self.cadence_time_stamp = self.time_stamp
            # cr - cumularive revolutions
            # le - last event time
            # dt - time delta
            cr_cr = 0xff * data_b[8] + data_b[7]
            cr_le = (1.0 / 1024) * (0xff * data_b[10] + data_b[9])
            cr_dt = cr_le - self.crank_last_time_event
            # FIXME - there seems to be some accuracy loss on timer overflow?
            if cr_dt < 0:
                cr_dt = 64 + cr_le - self.crank_last_time_event
                self.crank_last_time_delta = cr_dt
            if (self.crank_cumul != cr_cr) and (self.crank_last_time_event != cr_le):
                rt = cr_dt / (cr_cr - self.crank_cumul)
                self.crank_rev_time = rt
                self.crank_cumul = cr_cr
                self.cadence = 60.0 / rt
                self.crank_last_time_event = cr_le
                self.crank_last_measurement = self.cadence_time_stamp
            else:
                if (self.cadence_time_stamp - self.crank_last_measurement) > self.EXPIRY_TIME:
                    self.crank_rev_time = numbers.NAN
                    self.cadence = numbers.NAN
        else:
            self.cadence_time_stamp = numbers.NAN
            self.cadence = numbers.NAN

        #Ignore first 3 measurements to avoid "wild" values
        if self.measurement_no < 3:
            self.log.debug('Ignoring measurement no {}'.format(self.measurement_no), extra=self.extra)
            self.wheel_revolution_time = numbers.NAN
            self.crank_rev_time = numbers.NAN
            self.cadence = numbers.NAN
            self.wheel_revolution_time_stamp = time.time()

        if (not math.isnan(self.cadence)):
            self.calculate_avg_cadence()

        self.log.debug('Last crank event time: {:10.3f}, delta {:10.3f}'.format(self.crank_last_time_event, self.crank_last_time_delta), extra=self.extra)
        self.log.debug('Crank cumul revs: {:5d}'.format(cr_cr), extra=self.extra)
        self.log.debug('Last crank rev time: {:10.3f}'.format(self.crank_rev_time), extra=self.extra)

        ts_formatted = time.strftime("%H:%M:%S", time.localtime(self.time_stamp))
        self.log.debug('Delegate: set cadence {}, time stamp {}'.format(self.cadence, ts_formatted), extra=self.extra)
        #self.log.debug('Delegate: handleNotification finished', extra=self.extra)

    ## Calculates average cadence. The calculation will use only time with valid measurements, so it won't be the same as ride time.
    #  @param self The python object self
    def calculate_avg_cadence(self):
        if math.isnan(self.cadence_avg):
            cd_avg_current = 0.0
        else:
            cd_avg_current = self.cadence_avg
        self.time_delta = self.time_stamp_previous - self.time_stamp
        if self.time_delta < 2.0:
            try:
                cd_avg = (self.cadence * self.time_delta + (cd_avg_current * self.measurement_time)) / (self.measurement_time + self.time_delta)
                self.measurement_time += self.time_delta
            except ZeroDivisionError:
                cd_avg = numbers.NAN
        self.cadence_avg = cd_avg
        self.log.debug("cadence_avg {}".format(self.cadence_avg), extra=self.extra)

    ## Resets ble_sc delegate to initial values
    #  @param self The python object self
    def reset_data(self):
        self.wheel_time_stamp = time.time()
        self.wheel_revolutions = 0
        self.wheel_last_time_event = 0
        self.wheel_last_time_delta = 0
        self.wheel_revolution_time = 0
        self.cadence_time_stamp = time.time()
        self.last_measurement = self.cadence_time_stamp
        self.crank_cumul = 0
        self.crank_last_time_event = 0
        self.crank_last_time_delta = 0
        self.crank_rev_time = 0
        self.cadence = 0
        self.cadence_avg = 0
        self.measurement_time = 0.0
        self.cadence_notification_beat = 0
        self.measurement_no = 0
        self.time_stamp = time.time()
        self.time_stamp_previous = self.time_stamp
