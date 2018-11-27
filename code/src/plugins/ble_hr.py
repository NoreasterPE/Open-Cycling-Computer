#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ble_hr
#  BLE heart rate sensor handling module.
import ble_sensor
import bluepy.btle
import math
import num
import time


## Class for handling BLE heart rate sensor
class ble_hr(ble_sensor.ble_sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}
    # FIXME - replace with proper service & characteristic scan
    HANDLE = 0x000f  # FIXME - explain
    ENABLE_NOTIFICATIONS = bytes("10", 'UTF-8')    # FIXME - explain, try "01" is fails
    DISABLE_NOTIFICATIONS = bytes("00", 'UTF-8')

    def __init__(self):
        super().__init__()
        self.pm.register_parameter("heart_rate_device_name", self.extra["module_name"], store=True)
        self.pm.register_parameter("heart_rate_battery_level", self.extra["module_name"])
        self.pm.register_parameter("heart_rate", self.extra["module_name"], value=num.NAN, raw_unit="BPM", unit="BPM", units_allowed=["BMP"], store=True)
        self.pm.register_parameter("heart_rate_notification_beat", self.extra["module_name"])
        self.pm.register_parameter("heart_rate_device_address", self.extra["module_name"], store=True)
        self.pm.request_parameter("ble_scan_done", self.extra["module_name"])
        self.pm.request_parameter("heart_rate_device_address", self.extra["module_name"])
        self.pm.request_parameter("heart_rate_device_name", self.extra["module_name"])
        self.delegate_class = hr_delegate
        self.editor_fields = {}

    ## Process data delivered from delegate
    #  @param self The python object self
    def process_delegate_data(self):
        if self.delegate.measurement_no <= 2:
            #Fresh start or restart after lost connection. Seed average value and measurement time in the delegate
            self.delegate.heart_rate_avg = self.pm.parameters["heart_rate"]["value_avg"]
            self.measurement_time = self.delegate.measurement_time
        if self.pm.parameters["heart_rate"]["reset"]:
            #Reset by user, reset deletage data
            self.log.debug('reset request received', extra=self.extra)
            self.delegate.reset_data()
            self.pm.parameters["heart_rate"]["reset"] = False
        try:
            self.pm.parameters["heart_rate"]["time_stamp"] = self.delegate.time_stamp
            self.pm.parameters["heart_rate"]["value"] = self.delegate.heart_rate
            self.pm.parameters["heart_rate"]["value_min"] = min(self.pm.parameters["heart_rate"]["value_min"], self.delegate.heart_rate)
            self.pm.parameters["heart_rate"]["value_avg"] = self.delegate.heart_rate_avg
            self.measurement_time = self.delegate.measurement_time
            self.pm.parameters["heart_rate"]["value_max"] = max(self.pm.parameters["heart_rate"]["value_max"], self.delegate.heart_rate)
            self.pm.parameters["heart_rate_notification_beat"]["value"] = self.delegate.heart_rate_notification_beat
            if self.pm.parameters["heart_rate_battery_level"]["value"] != self.battery_level:
                self.pm.parameters["heart_rate_battery_level"]["value"] = self.battery_level
        except (AttributeError) as exception:
            self.handle_exception(exception, "process_delegate_data")
        self.log.debug("heart rate = {} @ {}".format(self.pm.parameters["heart_rate"]["value"], time.strftime("%H:%M:%S", time.localtime(self.pm.parameters["heart_rate"]["time_stamp"]))), extra=self.extra)

    def notification(self):
        # BLE Scan end, consume results using editor_list
        if self.pm.parameters['ble_scan_done']['value'] and \
                self.pm.parameters['ble_scan_results']['value'] == 'heart_rate':
            self.pm.parameters['ble_scan_done']['value'] = False
            if self.connected or self.pm.parameters["heart_rate_device_name"]["value"] is not None:
                self.pm.parameters['ble_scan_results']['data'].append({'name': 'Disconnect', 'addr': None, 'addr_type': None})
            self.set_up_editor()

        # Device name has been changed by editor
        if self.pm.parameters["heart_rate_device_name"]["value"] != self.device_name:
            try:
                data = self.pm.parameters["heart_rate_device_name"]["data"][1]
                name = data['name']
                self.device_name = name
                self.pm.parameters["heart_rate_device_name"]["value"] = name
                addr = data['addr']
                self.device_address = addr
                self.pm.parameters["heart_rate_device_address"]["value"] = addr
                # FIXME - that might need to be passed to ble_sensor
                #addr_type = data[1]['addr_type']
            except TypeError:
                pass

        # Device address changed
        if self.pm.parameters["heart_rate_device_address"]["value"] != self.device_address:
            self.device_address = self.pm.parameters["heart_rate_device_address"]["value"]
            if self.device_address is None:
                self.pm.parameters["heart_rate_device_name"]["value"] = 'Disconnected'
                self.device_name = self.pm.parameters["heart_rate_device_name"]["value"]
                self.safe_disconnect()

        # Update battery level, level read from physical sensor
        if self.pm.parameters["heart_rate_battery_level"]["value"] != self.battery_level:
            self.pm.parameters["heart_rate_battery_level"]["value"] = self.battery_level

    def find_heart_rate_device(self):
        self.pm.plugins['ble_scanner'].find_ble_device('heart_rate')

    def set_up_editor(self):
        self.editor_fields = {}
        self.editor_fields["parameter"] = 'heart_rate_device_name'
        self.editor_fields["editor"] = 'editor_list'
        self.editor_fields['type'] = 'editor_list'
        self.editor_fields['editor_title'] = 'BLE heart rate'
        self.editor_fields["format"] = '%.0f'
        self.editor_fields['index'] = 0
        self.editor_fields['parameter'] = 'heart_rate_device_name'
        self.editor_fields['value_list'] = []
        for device in self.pm.parameters['ble_scan_results']['data']:
            self.editor_fields['value_list'].append((device['name'], device))
        if self.pm.event_queue is not None:
            self.pm.event_queue.put(('open_editor', self.editor_fields))


## Class for handling BLE notifications from heart rate sensor
class hr_delegate(bluepy.btle.DefaultDelegate):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self, log):
        self.log = log
        self.log.debug('Delegate __init__ started', extra=self.extra)
        super().__init__()
        self.reset_data()
        self.measurement_no = 0
        self.log.debug('Delegate __init__ finished', extra=self.extra)

    def handleNotification(self, cHandle, data):
        #self.log.debug('Delegate: handleNotification started', extra=self.extra)
        self.log.debug('Delegate: Notification received. Handle: {}, data: {}'.format(hex(cHandle), data), extra=self.extra)

        # Heart Rate Measurement from BLE standard
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.heart_rate_measurement.xml
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.heart_rate_control_point.xml&u=org.bluetooth.characteristic.heart_rate_control_point.xml
        #
        self.time_stamp_previous = self.time_stamp
        self.time_stamp = time.time()
        self.measurement_no += 1
        self.heart_rate_notification_beat = int(not(self.heart_rate_notification_beat))

        i = 0
        data_b = {}
        for b in data:
            data_b[i] = b
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

        hr = num.NAN
        if data_b[0] & HR_VALUE_FORMAT:
            # UINT16
            hr = 0xff * data_b[2] + data_b[1]
        else:
            # UINT8
            hr = data_b[1]
        self.log.debug('Delegate: calculated heart rate {}'.format(hr), extra=self.extra)

        # Sometimes heart rate sensor delivers 0 as heart rate
        if hr != 0:
            self.heart_rate = hr
        else:
            self.heart_rate = num.NAN

        #Ignore first 3 measurements to avoid "wild" values
        # FIXME Kalman fiter to absolete this piece of code
        if self.measurement_no < 3:
            self.log.debug('Ignoring measurement no {}'.format(self.measurement_no), extra=self.extra)
            self.heart_rate = num.NAN

        if not math.isnan(self.heart_rate) and self.heart_rate != 0:
            self.calculate_avg_heart_rate()

        ts_formatted = time.strftime("%H:%M:%S", time.localtime(self.time_stamp))
        self.log.debug('Delegate: set heart rate {}, time stamp {}'.format(self.heart_rate, ts_formatted), extra=self.extra)
        #self.log.debug('Delegate: handleNotification finished', extra=self.extra)

    ## Calculates average heart rate. The calculation will use only time with valid measurements, so it won't be the same as ride time.
    #  @param self The python object self
    def calculate_avg_heart_rate(self):
        if math.isnan(self.heart_rate_avg):
            hr_avg_current = 0.0
        else:
            hr_avg_current = self.heart_rate_avg
        self.time_delta = self.time_stamp_previous - self.time_stamp
        if self.time_delta < 2.0:
            try:
                hr_avg = (self.heart_rate * self.time_delta + (hr_avg_current * self.measurement_time)) / (self.measurement_time + self.time_delta)
                self.measurement_time += self.time_delta
            except ZeroDivisionError:
                hr_avg = num.NAN
            self.heart_rate_avg = hr_avg
        self.log.debug("heart_rate_avg {}".format(self.heart_rate_avg), extra=self.extra)

    ## Resets ble_hr delegate to initial values
    #  @param self The python object self
    def reset_data(self):
        self.time_stamp = time.time()
        self.time_stamp_previous = self.time_stamp
        self.heart_rate = num.NAN
        self.heart_rate_min = num.INF
        self.heart_rate_avg = num.NAN
        self.heart_rate_max = num.INF_MIN
        # Internal measuremet time, indicates for how long there was a valid measurement.
        self.measurement_time = 0.0
        self.heart_rate_notification_beat = 0
