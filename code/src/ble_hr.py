#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ble_hr
#  BLE heart rate sensor handling module.
import bluepy.btle
import logging
import threading
import time
import numbers

M = {'module_name': 'ble_hr'}


## Class for handling BLE heart rate sensor
class ble_hr(threading.Thread):
    # FIXME - replace with proper service & characteristic scan
    HR_HANDLE = 0x000f  # FIXME - explain
    HR_ENABLE_HR = bytes("10", 'UTF-8')    # FIXME - explain, try "01" is fails
    HR_DISABLE_HR = bytes("00", 'UTF-8')
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    WAIT_TIME = 5.0
    ## @var RECONNECT_WAIT_TIME
    # Time of waiting after an exception has been raiesed or connection lost
    RECONNECT_WAIT_TIME = 3.0

    def __init__(self):
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')
        self.log.debug('WAIT_TIME {}'.format(self.WAIT_TIME), extra=M)
        self.p_formats = dict(heart_rate='%.0f', heart_rate_min='%.0f', heart_rate_max='%.0f', battery_level="%.0f")
        self.p_units = dict(heart_rate='BPM', heart_rate_min='BPM', heart_rate_max='BPM', battery_level="%")
        self.p_raw_units = dict(heart_rate='BPM', heart_rate_min='BPM', heart_rate_max='BPM', battery_level="%")

        ## @var connected
        # Indicates if sensor is currently connected
        self.connected = False
        threading.Thread.__init__(self)
        self.reset_data()
        ## @var addr
        # Address of the heart rate sensor
        self.addr = None
        ## @var name
        # Name of the heart rate sensor
        self.name = None
        ## @var state
        #State of the connection, same as in sensors.py STATE_DEV
        self.state = 0
        self.notifications_enabled = False
        self.running = False

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.log.debug('Set notifications started. enable={}'.format(enable), extra=M)
        try:
            if enable:
                self.peripherial.writeCharacteristic(self.HR_HANDLE, self.HR_ENABLE_HR, False)
                self.log.debug('Notifications enabled', extra=M)
                self.notifications_enabled = True
            else:
                self.peripherial.writeCharacteristic(self.HR_HANDLE, self.HR_DISABLE_HR, False)
                self.log.debug('Notifications disabled', extra=M)
                self.notifications_enabled = False
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.handle_exception(e, "set_notifications")
        self.log.debug('Set notifications finished', extra=M)

    def initialise_connection(self):
        if self.addr is not None and self.connected is False and self.running:
            self.log.debug('Initialising connection started', extra=M)
            try:
                self.log.debug('Setting delegate', extra=M)
                self.delegate = HR_Delegate()
                self.log.debug('Setting peripherial', extra=M)
                self.peripherial = bluepy.btle.Peripheral()
                self.log.debug('Setting notification handler', extra=M)
                self.peripherial.withDelegate(self.delegate)
                self.log.debug('Notification handler set', extra=M)
                self.log.debug('Connecting', extra=M)
                self.state = 1
                self.peripherial.connect(self.addr, addrType='random')
                self.log.debug('Connected', extra=M)
                self.connected = True
                self.state = 2
                self.log.debug('Getting device name', extra=M)
                self.name = self.get_device_name()
                self.log.debug('Getting battery level', extra=M)
                self.battery_level = self.get_battery_level()
            except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
                self.handle_exception(e, "initialise_connection")
                self.state = 0
            self.log.debug('Initialising connection finished', extra=M)

    def handle_exception(self, exception, caller):
        self.log.critical(exception, extra=M)
        self.log.critical("{}".format(type(exception)), extra=M)
        self.log.error("Exception {} in {}".format(exception, caller), extra=M)
        try:
            raise (exception)
        except bluepy.btle.BTLEException as e:
            if str(e).startswith("Failed to connect to peripheral"):
                self.log.info(e, extra=M)
                self.connected = False
                self.notifications_enabled = False
            elif str(e) == "Helper not started (did you call connect()?)":
                self.log.info(e, extra=M)
                self.connected = False
                self.notifications_enabled = False
            elif str(e) == "Device disconnected":
                self.log.info(e, extra=M)
                self.connected = False
                self.notifications_enabled = False
            elif str(e) == "Helper exited":  # FIXME - what to do with this?
                self.log.critical(e, extra=M)
                self.connected = False
                self.notifications_enabled = False
            elif (str(e) == "Error from Bluetooth stack (badstate)" or
                    str(e) == "Error from Bluetooth stack (comerr)"):
                self.log.critical(e, extra=M)
                self.connected = False
                self.notifications_enabled = False
            elif (str(e) == "Unexpected response (rd)" or
                    str(e) == "Unexpected response (find)" or
                    str(e) == "Unexpected response (wr)"):
                self.log.info(e, extra=M)
            else:
                self.log.critical('Uncontrolled error {} in {}'.format(e, caller), extra=M)
                self.connected = False
                self.notifications_enabled = False
                raise
        except (BrokenPipeError, AttributeError) as e:
            self.log.error('{} in {}'.format(e, caller), extra=M)
            self.connected = False
            self.notifications_enabled = False

    def run(self):
        self.log.debug('Starting the main BLE_HR loop', extra=M)
        self.running = True
        self.state = 0
        while self.running:
            self.log.debug('Address: {}, connected: {}, notifications: {}'.format(self.addr, self.connected, self.notifications_enabled), extra=M)
            if self.addr is not None:
                if self.connected and self.notifications_enabled:
                    try:
                        if self.peripherial.waitForNotifications(self.WAIT_TIME):
                            if self.time_stamp != self.delegate.time_stamp:
                                self.time_stamp = self.delegate.time_stamp
                                self.heart_rate = self.delegate.heart_rate
                                self.heart_rate_min = min(self.heart_rate_min, self.delegate.heart_rate)
                                self.heart_rate_max = max(self.heart_rate_max, self.delegate.heart_rate)
                                self.heart_rate_beat = self.delegate.heart_rate_beat
                                self.log.debug('heart rate = {} @ {}'.format(self.heart_rate, time.strftime("%H:%M:%S", time.localtime(self.time_stamp))), extra=M)
                    except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
                        self.handle_exception(e, "waitForNotifications")
                else:
                    self.log.debug('ble_hr NOT connected', extra=M)
                    self.initialise_connection()
                    time.sleep(5.0)
                    self.set_notifications(enable=True)
                    time.sleep(5.0)
            else:
                #Waiting for ble address
                self.log.debug('ble_hr add is None, waiting...', extra=M)
                time.sleep(5.0)
        self.log.debug('Main ble_hr loop finished', extra=M)

    def safe_disconnect(self):
        self.connected = False
        self.notifications_enabled = False
        self.log.debug('safe_disconnect started', extra=M)
        # Make sure the device is not sending notifications (is this required?)
        try:
            self.set_notifications(enable=False)
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            # Not connected yet
            self.log.critical('{}'.format(e), extra=M)
            pass
        # Make sure the device is disconnected
        try:
            self.peripherial.disconnect()
            self.state = 0
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            # Not connected yet
            self.log.error('AttributeError: {}'.format(e), extra=M)
            pass
        self.log.debug('State = {}. Waiting {} s to reconnect'.format(self.state, self.RECONNECT_WAIT_TIME), extra=M)
        time.sleep(self.RECONNECT_WAIT_TIME)
        self.log.debug('safe_disconnect finished', extra=M)

    def get_prefix(self):
        return M["module_name"]

    def get_raw_data(self):
        self.log.debug('get_raw_data called', extra=M)
        return dict(name=self.name,
                    battery_level=self.battery_level,
                    addr=self.addr,
                    state=self.state,
                    time_stamp=self.time_stamp,
                    heart_rate=self.heart_rate,
                    heart_rate_min=self.heart_rate_min,
                    heart_rate_max=self.heart_rate_max,
                    heart_rate_beat=self.heart_rate_beat)

    def get_device_name(self):
        name = ""
        try:
            c = self.peripherial.getCharacteristics(uuid=bluepy.btle.AssignedNumbers.deviceName)
            name = c[0].read()
            self.log.debug('Device name: {}'.format(name), extra=M)
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.handle_exception(e, "get_device_name")
        if type(name) is bytes:
            name = name.decode("utf-8")
        return name

    def get_battery_level(self):
        level = numbers.NAN
        try:
            b = self.peripherial.getCharacteristics(uuid=bluepy.btle.AssignedNumbers.batteryLevel)
            level = ord(b[0].read())
            self.log.debug('Battery lavel: {}'.format(level), extra=M)
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.handle_exception(e, "get_battery_level")
        return level

    def get_state(self):
        return self.state

    def reset_data(self):
        ## @var name
        # Battery level in %
        self.battery_level = numbers.NAN
        ## @var heart_rate
        # Measured current heart rate
        self.heart_rate = numbers.NAN
        ## @var heart_rate_min
        # Minimum measured heart rate since reset
        self.heart_rate_min = numbers.INF
        ## @var heart_rate_avg
        # Average heart rate since reset
        self.heart_rate_avg = numbers.NAN
        ## @var heart_rate_max
        # Maximum measured heart rate since reset
        self.heart_rate_max = numbers.INF_MIN
        ## @var heart_rate_beat
        # Heart rate icon beat, used to show if ble notifications are coming. This is not the real heart rate beat
        self.heart_rate_beat = 0
        ## @var time_stamp
        # Time stamp of the measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.
        self.time_stamp = time.time()
        ## @var time_of_reset
        # Time stamp of the data reset. Used to calculate average
        self.time_of_reset = time.time()

    def get_raw_units(self):
        return self.p_raw_units

    def get_units(self):
        return self.p_units

#    FIXME make decision if get_data and get_raw_data are required
#    def get_data(self):
#        return dict(name=self.name, addr=self.addr, state=self.state, time_stamp=self.time_stamp, heart_rate=self.heart_rate, heart_rate_beat=self.heart_rate_beat)

    def get_formats(self):
        return self.p_formats

    def is_connected(self):
        return self.connected

    def __del__(self):
        self.stop()

    def set_addr(self, addr):
        self.log.debug('address set to {}'.format(addr), extra=M)
        self.addr = addr

    def stop(self):
        self.running = False
        self.log.debug('Stop started', extra=M)
        self.connected = False
        time.sleep(1)
        self.log.debug('Disabling notifications', extra=M)
        self.set_notifications(enable=False)
        time.sleep(1)
        self.log.debug('Disconnecting', extra=M)
        self.peripherial.disconnect()
        self.state = 0
        self.log.info('{} disconnected'.format(self.name), extra=M)
        self.log.debug('Stop finished', extra=M)


## Class for handling BLE notifications from heart rate sensor
class HR_Delegate(bluepy.btle.DefaultDelegate):

    def __init__(self):
        self.log = logging.getLogger('system')
        self.log.debug('Delegate __init__ started', extra=M)
        bluepy.btle.DefaultDelegate.__init__(self)
        self.heart_rate = numbers.NAN
        self.heart_rate_beat = 0
        self.time_stamp = time.time()
        self.measurement_no = 0
        self.log.debug('Delegate __init__ finished', extra=M)

    def handleNotification(self, cHandle, data):
        self.log.debug('Delegate: handleNotification started', extra=M)
        self.log.debug('Delegate: Notification received. Handle: {}, data: {}'.format(hex(cHandle), data), extra=M)

        # Heart Rate Measurement from BLE standard
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.heart_rate_measurement.xml
        # https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.heart_rate_control_point.xml&u=org.bluetooth.characteristic.heart_rate_control_point.xml
        #
        self.time_stamp = time.time()
        self.measurement_no += 1
        self.heart_rate_beat = int(not(self.heart_rate_beat))

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

        hr = numbers.NAN
        if data_b[0] & HR_VALUE_FORMAT:
            # UINT16
            hr = 0xff * data_b[2] + data_b[1]
        else:
            # UINT8
            hr = data_b[1]
        self.log.debug('Delegate: calculated heart rate {}'.format(hr), extra=M)

        # Sometimes heart rate sensor delivers 0 as heart rate
        if hr != 0:
            self.heart_rate = hr
        else:
            self.heart_rate = numbers.NAN

        #Ignore first 3 measurements to avoid "wild" values
        if self.measurement_no < 3:
            self.log.debug('Ignoring measurement no {}'.format(self.measurement_no), extra=M)
            self.heart_rate = numbers.NAN

        ts_formatted = time.strftime("%H:%M:%S", time.localtime(self.time_stamp))
        self.log.debug('Delegate: set heart rate {}, time stamp {}'.format(self.heart_rate, ts_formatted), extra=M)
        self.log.debug('Delegate: handleNotification finished', extra=M)
