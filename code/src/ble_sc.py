#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ble_sc
#  BLE speed and cadence sensor handling module.
import bluepy.btle
import numbers
import time
import sensor


## Class for handling BLE speed and cadence sensor
class ble_sc(sensor.sensor):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ble_sc'}
    # FIXME - replace with proper service & characteristic scan
    CSC_HANDLE = 0x000f  # FIXME - explain
    CSC_ENABLE_SC = bytes("10", 'UTF-8')    # FIXME - explain
    CSC_DISABLE_SC = bytes("00", 'UTF-8')    # FIXME - explain
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    WAIT_TIME = 1.0
    ## @var RECONNECT_WAIT_TIME
    # Time of waiting after an exception has been raiesed or connection lost
    RECONNECT_WAIT_TIME = 5.0

    def __init__(self):
        super().__init__()
        self.log.debug('WAIT_TIME {}'.format(self.WAIT_TIME), extra=self.extra)
        self.p_formats = dict(time_stamp='%.0f', wheel_time_stamp='%.0f', wheel_rev_time='%.0f', cadence_time_stamp='%.0f', cadence="%5.0f", cadence_max="%5.0f", battery_level="%.0f")
        self.p_units = dict(time_stamp='s', wheel_time_stamp='s', wheel_rev_time='s', cadence_time_stamp='s', cadence="RPM", cadence_max="RPM", battery_level="%")
        self.p_raw_units = dict(time_stamp='s', wheel_time_stamp='s', wheel_rev_time='s', cadence_time_stamp='s', cadence="RPM", cadence_max="RPM", battery_level="%")

        self.reset_data()
        ## @var addr
        # Address of the cadence and speed sensor
        self.addr = None
        ## @var state
        #State of the connection, same as in sensors.py STATE_DEV
        self.state = 0
        self.notifications_enabled = False
        self.running = False

    def set_notifications(self, enable=True):
        # Enable/disable notifications
        self.log.debug('Set notifications started. enable={}'.format(enable), extra=self.extra)
        try:
            if enable:
                self.peripherial.writeCharacteristic(self.CSC_HANDLE, self.CSC_ENABLE_SC, False)
                self.log.debug('Notifications enabled', extra=self.extra)
                self.notifications_enabled = True
            else:
                self.peripherial.writeCharacteristic(self.CSC_HANDLE, self.CSC_DISABLE_SC, False)
                self.log.debug('Notifications disabled', extra=self.extra)
                self.notifications_enabled = False
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.handle_exception(e, "set_notifications")
        self.log.debug('Set notifications finished', extra=self.extra)

    def initialise_connection(self):
        if self.addr is not None and self.connected is False and self.running:
            self.log.debug('Initialising connection started', extra=self.extra)
            try:
                self.log.debug('Setting delegate', extra=self.extra)
                self.delegate = CSC_Delegate(self.log)
                self.log.debug('Setting peripherial', extra=self.extra)
                self.peripherial = bluepy.btle.Peripheral()
                self.log.debug('Setting notification handler', extra=self.extra)
                self.peripherial.withDelegate(self.delegate)
                self.log.debug('Notification handler set', extra=self.extra)
                self.log.debug('Connecting', extra=self.extra)
                self.state = 1
                self.peripherial.connect(self.addr, addrType='random')
                self.log.debug('Connected', extra=self.extra)
                self.connected = True
                self.state = 2
                self.log.debug('Getting device name', extra=self.extra)
                self.name = self.get_device_name()
                self.log.debug('Getting battery level', extra=self.extra)
                self.battery_level = self.get_battery_level()
            except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
                self.handle_exception(e, "initialise_connection")
                self.state = 0
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
            elif str(e) == "Helper exited":  # FIXME - what to do with this?
                self.log.error(e, extra=self.extra)
                self.connected = False
                self.notifications_enabled = False
            elif str(e) == "Error from Bluetooth stack (badstate)":  # FIXME - what to do with this?
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
        self.log.debug('Starting the main BLE_SC loop', extra=self.extra)
        self.running = True
        self.state = 0
        while self.running:
            self.log.debug('Address: {}, connected: {}, notifications: {}'.format(self.addr, self.connected, self.notifications_enabled), extra=self.extra)
            if self.addr is not None:
                if self.connected and self.notifications_enabled:
                    try:
                        if self.peripherial.waitForNotifications(self.WAIT_TIME):
                            if self.time_stamp != self.delegate.time_stamp:
                                self.time_stamp = self.delegate.time_stamp
                                self.wheel_time_stamp = self.delegate.wheel_time_stamp
                                self.wheel_rev_time = self.delegate.wheel_rev_time
                                self.cadence_time_stamp = self.delegate.cadence_time_stamp
                                self.cadence = self.delegate.cadence
                                self.cadence_max = max(self.cadence_max, self.delegate.cadence)
                                self.cadence_beat = self.delegate.cadence_beat
                                self.log.debug('cadence = {} @ {}'.format(self.cadence, time.strftime("%H:%M:%S", time.localtime(self.time_stamp))), extra=self.extra)
                    except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
                        self.handle_exception(e, "waitForNotifications")
                else:
                    self.log.debug('ble_sc NOT connected', extra=self.extra)
                    self.initialise_connection()
                    time.sleep(5.0)
                    self.set_notifications(enable=True)
                    time.sleep(5.0)
            else:
                #Waiting for ble address
                time.sleep(5.0)
            self.log.debug('Main ble_sc loop running {}'.format(self.running), extra=self.extra)
        self.log.debug('Main ble_sc loop finished', extra=self.extra)

    def safe_disconnect(self):
        self.connected = False
        self.notifications_enabled = False
        self.log.debug('safe_disconnect started', extra=self.extra)
        # Make sure the device is not sending notifications (is this required?)
        try:
            self.log.debug('safe_disconnect 1', extra=self.extra)
            self.set_notifications(enable=False)
            self.log.debug('safe_disconnect 2', extra=self.extra)
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.log.debug('safe_disconnect 3', extra=self.extra)
            # Not connected yet
            self.log.error('{}'.format(e), extra=self.extra)
            self.log.debug('safe_disconnect 4', extra=self.extra)
            pass
        # Make sure the device is disconnected
        try:
            self.log.debug('safe_disconnect 5', extra=self.extra)
            self.peripherial.disconnect()
            self.log.debug('safe_disconnect 6', extra=self.extra)
            self.state = 0
        except (bluepy.btle.BTLEException, BrokenPipeError, AttributeError) as e:
            self.log.debug('safe_disconnect 7', extra=self.extra)
            # Not connected yet
            self.log.error('AttributeError: {}'.format(e), extra=self.extra)
            pass
        self.log.debug('safe_disconnect 8', extra=self.extra)
        self.log.debug('State = {}. Waiting {} s to reconnect'.format(self.state, self.RECONNECT_WAIT_TIME), extra=self.extra)
        time.sleep(self.RECONNECT_WAIT_TIME)
        self.log.debug('safe_disconnect 9', extra=self.extra)
        self.log.debug('safe_disconnect finished', extra=self.extra)

    def get_raw_data(self):
        return dict(name=self.name,
                    addr=self.addr,
                    battery_level=self.battery_level,
                    state=self.state,
                    time_stamp=self.time_stamp,
                    wheel_time_stamp=self.wheel_time_stamp,
                    wheel_rev_time=self.wheel_rev_time,
                    cadence_time_stamp=self.cadence_time_stamp,
                    cadence=self.cadence,
                    cadence_max=self.cadence_max,
                    cadence_beat=self.cadence_beat)

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
        return self.state

    def reset_data(self):
        ## @var name
        # Battery level in %
        self.battery_level = numbers.NAN
        ## @var time_stamp
        # Time stamp of the measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.
        self.time_stamp = time.time()
        ## @var cadence_time_stamp
        # Time stamp of the wheel rev measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.
        self.wheel_time_stamp = time.time()
        ## @var wheel_rev_time
        # Measured wheel revolution time
        self.wheel_rev_time = 0
        ## @var cadence_time_stamp
        # Time stamp of the cadence measurement, initially set by the constructor to "now", later overridden by time stamp of the notification with measurement.
        self.cadence_time_stamp = time.time()
        ## @var cadence
        # Measured cadence
        self.cadence = 0
        ## @var cadence_max
        # Measured cadence
        self.cadence_max = numbers.INF_MIN
        ## @var cadence_beat
        # Cadence icon beat, used to show if ble notifications are coming.
        self.cadence_beat = 0

    def __del__(self):
        self.stop()

    def set_addr(self, addr):
        self.log.debug('address set to {}'.format(addr), extra=self.extra)
        self.addr = addr

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
        self.state = 0
        self.log.info('{} disconnected'.format(self.name), extra=self.extra)
        self.log.debug('Stop finished', extra=self.extra)


#    FIXME make decision if get_data and get_raw_data are required
#    def get_data(self):
#        r = dict(
#            name=self.name, addr=self.addr, state=self.state, wheel_time_stamp=self.wheel_time_stamp, wheel_rev_time=self.wheel_rev_time,
#            cadence_time_stamp=self.cadence_time_stamp, cadence=self.cadence)
#        return r


## Class for handling BLE notifications from cadence and speed sensor
class CSC_Delegate(bluepy.btle.DefaultDelegate):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ble_sc_dgte'}
    WHEEL_REV_DATA_PRESENT = 0x01
    CRANK_REV_DATA_PRESENT = 0x02
    ## @var WAIT_TIME
    # Time of waiting for notifications in seconds
    EXPIRY_TIME = 2.0

    def __init__(self, log):
        self.log = log
        self.log.debug('Delegate __init__ started', extra=self.extra)
        bluepy.btle.DefaultDelegate.__init__(self)
        self.wheel_time_stamp = time.time()
        self.wheel_cumul = 0
        self.wheel_last_time_event = 0
        self.wheel_last_time_delta = 0
        self.wheel_rev_time = 0
        self.cadence_time_stamp = time.time()
        self.last_measurement = self.cadence_time_stamp
        self.crank_cumul = 0
        self.crank_last_time_event = 0
        self.crank_last_time_delta = 0
        self.crank_rev_time = 0
        self.cadence = 0
        self.cadence_beat = 0
        self.measurement_no = 0
        self.log.debug('Delegate __init__ finished', extra=self.extra)

    def handleNotification(self, cHandle, data):
        self.log.debug('Delegate: handleNotification started', extra=self.extra)
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
        self.time_stamp = time.time()
        self.measurement_no += 1
        self.cadence_beat = int(not(self.cadence_beat))

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
            wh_cr = 0xff0000 * data_b[4] + 0xff00 * \
                data_b[3] + 0xff * data_b[2] + data_b[1]
            wh_le = (1.0 / 1024) * (0xff * data_b[6] + data_b[5])
            wh_dt = wh_le - self.wheel_last_time_event

            if wh_dt < 0:
                wh_dt = 64 + wh_le - self.wheel_last_time_event

            if (self.wheel_cumul != wh_cr) and (self.wheel_last_time_event != wh_le):
                rt = wh_dt / (wh_cr - self.wheel_cumul)

                self.wheel_time_stamp = self.time_stamp
                self.wheel_last_time_event = wh_le
                self.wheel_last_time_delta = wh_dt
                self.wheel_rev_time = rt
                self.wheel_cumul = wh_cr
                self.wheel_last_measurement = self.wheel_time_stamp
            else:
                if (self.wheel_time_stamp - self.wheel_last_measurement) > self.EXPIRY_TIME:
                    self.wheel_rev_time = numbers.NAN
        else:
            self.wheel_time_stamp = numbers.NAN
            self.wheel_rev_time = numbers.NAN

        self.log.debug('Last wheel event time: {:10.3f}, delta {:10.3f}'.format(self.wheel_last_time_event, self.wheel_last_time_delta), extra=self.extra)
        self.log.debug('Wheel cumul revs: {:5d}'.format(wh_cr), extra=self.extra)
        self.log.debug('Last wheel rev time: {:10.3f}'.format(self.wheel_rev_time), extra=self.extra)

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
            self.wheel_rev_time = numbers.NAN
            self.crank_rev_time = numbers.NAN
            self.cadence = numbers.NAN
            self.wheel_last_measurement = time.time()

        self.log.debug('Last crank event time: {:10.3f}, delta {:10.3f}'.format(self.crank_last_time_event, self.crank_last_time_delta), extra=self.extra)
        self.log.debug('Crank cumul revs: {:5d}'.format(cr_cr), extra=self.extra)
        self.log.debug('Last crank rev time: {:10.3f}'.format(self.crank_rev_time), extra=self.extra)

        ts_formatted = time.strftime("%H:%M:%S", time.localtime(self.time_stamp))
        self.log.debug('Delegate: set cadence {}, time stamp {}'.format(self.cadence, ts_formatted), extra=self.extra)
        self.log.debug('Delegate: handleNotification finished', extra=self.extra)
