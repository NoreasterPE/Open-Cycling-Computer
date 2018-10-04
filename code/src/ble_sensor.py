#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ble_sensor
#  Abstract base BLE sensor handling module.
import bluepy.btle
import time
import math
import numbers
import sensor


##Abstract base Class for handling BLE sensors
class ble_sensor(sensor.sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ble_sensor'}
    #Overwrite in real device class
    HANDLE = 0x000f
    #Overwrite in real device class
    ENABLE_NOTIFICATIONS = bytes("10", 'UTF-8')
    #Overwrite in real device class
    DISABLE_NOTIFICATIONS = bytes("00", 'UTF-8')
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    WAIT_TIME = 1.0
    ## @var RECONNECT_WAIT_TIME
    # Time of waiting after an exception has been raised or connection lost
    RECONNECT_WAIT_TIME = 1.0

    def __init__(self):
        super().__init__()
        self.log.debug('WAIT_TIME {}'.format(self.WAIT_TIME), extra=self.extra)
        self.p_raw = dict(time_stamp=numbers.NAN, name=None, addr=None, state=numbers.NAN, battery_level=numbers.NAN)
        self.p_formats = dict(time_stamp="", name="", addr="", state="", battery_level="%.0f")
        self.p_units = dict(time_stamp="s", name="", addr="", state="", battery_level="%")
        self.p_raw_units = dict(time_stamp="s", name="", addr="", state="", battery_level="%")
        self.required = dict()

        self.notifications_enabled = False
        #Delegate class handling notification has to be set be the real device class in __init__
        self.delegate_class = None

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.log.debug('Set notifications started. enable={}'.format(enable), extra=self.extra)
        try:
            if enable:
                self.peripherial.writeCharacteristic(self.HANDLE, self.ENABLE_NOTIFICATIONS, False)
                self.log.debug('Notifications enabled', extra=self.extra)
                self.notifications_enabled = True
            else:
                self.peripherial.writeCharacteristic(self.HANDLE, self.DISABLE_NOTIFICATIONS, False)
                self.log.debug('Notifications disabled', extra=self.extra)
                self.notifications_enabled = False
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.handle_exception(e, "set_notifications")
        self.log.debug('Set notifications finished', extra=self.extra)

    def initialise_connection(self):
        if self.p_raw["addr"] is not None and self.connected is False and self.running:
            self.log.debug('Initialising connection started', extra=self.extra)
            try:
                self.log.debug('Setting delegate', extra=self.extra)
                self.delegate = self.delegate_class(self.log)
                self.log.debug('Setting peripherial', extra=self.extra)
                self.peripherial = bluepy.btle.Peripheral()
                self.log.debug('Setting notification handler', extra=self.extra)
                self.peripherial.withDelegate(self.delegate)
                self.log.debug('Notification handler set', extra=self.extra)
                self.log.debug('Connecting', extra=self.extra)
                self.p_raw["state"] = 1
                self.log.debug('{}'.format(self.p_raw['addr']), extra=self.extra)
                self.peripherial.connect(self.p_raw["addr"], addrType='random')
                self.log.debug('Connected', extra=self.extra)
                self.connected = True
                self.p_raw["state"] = 2
                self.log.debug('Getting device name', extra=self.extra)
                self.p_raw["name"] = self.get_device_name()
                self.log.debug('Getting battery level', extra=self.extra)
                self.p_raw["battery_level"] = self.get_battery_level()
            except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
                self.handle_exception(e, "initialise_connection")
                self.p_raw["state"] = 0
            self.log.debug('Initialising connection finished', extra=self.extra)

    def handle_exception(self, exception, caller):
        self.log.error(exception, extra=self.extra)
        self.log.error("{}".format(type(exception)), extra=self.extra)
        self.log.error("Exception {} in {}".format(exception, caller), extra=self.extra)
        try:
            raise (exception)
        except bluepy.btle.BTLEException as e:
            if str(e).startswith("Failed to connect to peripheral"):
                self.log.info(e, extra=self.extra)
                self.connected = False
                self.notifications_enabled = False
            elif str(e) == "Helper not started (did you call connect()?)":
                self.log.info(e, extra=self.extra)
                self.connected = False
                self.notifications_enabled = False
            elif str(e) == "Device disconnected":
                self.log.info(e, extra=self.extra)
                self.connected = False
                self.notifications_enabled = False
            elif str(e) == "Helper exited":
                self.log.error(e, extra=self.extra)
                self.connected = False
                self.notifications_enabled = False
            elif (str(e) == "Error from Bluetooth stack (badstate)" or
                    str(e) == "Error from Bluetooth stack (comerr)"):
                self.log.error(e, extra=self.extra)
                self.connected = False
                self.notifications_enabled = False
            elif (str(e) == "Unexpected response (rd)" or
                    str(e) == "Unexpected response (find)" or
                    str(e) == "Unexpected response (wr)"):
                self.log.info(e, extra=self.extra)
            else:
                self.log.error('Uncontrolled error {} in {}'.format(e, caller), extra=self.extra)
                self.connected = False
                self.notifications_enabled = False
                raise
        except (BrokenPipeError, AttributeError) as e:
            self.log.error('{} in {}'.format(e, caller), extra=self.extra)
            self.connected = False
            self.notifications_enabled = False

    def run(self):
        self.log.debug('Starting the main loop', extra=self.extra)
        self.running = True
        self.p_raw["state"] = 0
        while self.running:
            self.log.debug('Address: {}, connected: {}, notifications: {}'.format(self.p_raw["addr"], self.connected, self.notifications_enabled), extra=self.extra)
            if self.p_raw["addr"] is not None:
                if self.connected and self.notifications_enabled:
                    try:
                        if self.peripherial.waitForNotifications(self.WAIT_TIME):
                            if self.time_stamp != self.delegate.time_stamp:
                                self.process_delegate_data()
                    except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
                        self.handle_exception(e, "waitForNotifications")
                else:
                    self.log.debug('NOT connected', extra=self.extra)
                    self.initialise_connection()
                    time.sleep(1.0)
                    self.set_notifications(enable=True)
                    time.sleep(1.0)
            else:
                #Waiting for ble address
                self.log.debug('address is None, waiting...', extra=self.extra)
                time.sleep(1.0)
            self.log.debug('Main loop running {}'.format(self.running), extra=self.extra)
        self.log.debug('Main loop finished', extra=self.extra)

    ## Overwrite in real BLE sensor class
    def process_delegate_data(self):
        pass

    def safe_disconnect(self):
        self.connected = False
        self.notifications_enabled = False
        self.log.debug('safe_disconnect started', extra=self.extra)
        # Make sure the device is not sending notifications
        try:
            self.set_notifications(enable=False)
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            # Not connected yet
            self.log.error('{}'.format(e), extra=self.extra)
            pass
        # Make sure the device is disconnected
        try:
            self.peripherial.disconnect()
            self.p_raw["state"] = 0
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            # Not connected yet
            self.log.error('AttributeError: {}'.format(e), extra=self.extra)
            pass
        self.log.debug('State = {}. Waiting {} s to reconnect'.format(self.p_raw["state"], self.RECONNECT_WAIT_TIME), extra=self.extra)
        time.sleep(self.RECONNECT_WAIT_TIME)
        self.log.debug('safe_disconnect finished', extra=self.extra)

    def get_raw_data(self):
        return self.p_raw

    def get_device_name(self):
        name = ""
        try:
            c = self.peripherial.getCharacteristics(uuid=bluepy.btle.AssignedNumbers.deviceName)
            name = c[0].read()
            self.log.debug('Device name: {}'.format(name), extra=self.extra)
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
            self.log.debug('Battery lavel: {}'.format(level), extra=self.extra)
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.handle_exception(e, "get_battery_level")
        return level

    def get_state(self):
        return self.p_raw["state"]

    def reset_data(self):
        ## @var battery_level
        # Battery level in %
        self.p_raw["battery_level"] = numbers.NAN
        ## @var time_stamp
        # Time stamp of the measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.
        self.time_stamp = time.time()

    ## Receive updated parameters from sensors module. Overwrite in real device module.
    #  @param self The python object self
    #  @param required Dict with updated by sensors module
    def notification(self, required):
        self.log.debug("required {}".format(required), extra=self.extra)
        pass

    def __del__(self):
        self.stop()

    def set_addr(self, addr):
        self.log.debug('address set to {}'.format(addr), extra=self.extra)
        self.p_raw["addr"] = addr

    def stop(self):
        super().stop()
        time.sleep(1)
        self.log.debug('Disabling notifications', extra=self.extra)
        self.set_notifications(enable=False)
        time.sleep(1)
        self.log.debug('Disconnecting', extra=self.extra)
        try:
            self.peripherial.disconnect()
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.handle_exception(e, "stop, disconnecting")
        self.p_raw["state"] = 0
        self.log.info('{} disconnected'.format(self.name), extra=self.extra)
        self.log.debug('Stop finished', extra=self.extra)