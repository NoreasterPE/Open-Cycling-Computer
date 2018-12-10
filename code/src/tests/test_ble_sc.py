#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bluepy
import logging
import sys
import time
sys.path.insert(0, '../plugins')
sys.path.insert(0, '../')

import ble_sc
import helpers

ADDR = "FD:DF:0E:4E:76:CF"

if __name__ == '__main__':
    ex = {'module_name': 'test_ble_sc'}
    logging.getLogger('system').setLevel(logging.DEBUG)
    sys_log_handler = logging.StreamHandler(sys.stdout)
    sys_log_format = '%(asctime)-25s %(levelname)-10s %(module_name)-12s %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    sys_logger = logging.getLogger('system')
    sys_logger.debug("Log start", extra=ex)

    wheel = helpers.wheel()
    WHEEL_CIRC_700x25 = wheel.get_circumference("700x25C") / 1000.0
    try:
        sys_logger.debug("Initialising BLE device...", extra=ex)
        ble_sc_device = ble_sc.ble_sc()
        sys_logger.debug("Setting address...", extra=ex)
        ble_sc_device.set_addr(ADDR)
        sys_logger.debug("Starting BLE thread...", extra=ex)
        ble_sc_device.start()
        connected = False
        while not connected:
            sys_logger.debug("Device not connected...", extra=ex)
            try:
                sys_logger.debug("Calling is_connected", extra=ex)
                connected = ble_sc_device.is_connected()
                sys_logger.debug("is_connected returned {}".format(connected), extra=ex)
                time.sleep(3)
            except bluepy.btle.BTLEException as e:
                sys_logger.debug("Error: {}".format(e), extra=ex)
                sys_logger.debug(".....sensor is not on? Waiting... ", extra=ex)

        sys_logger.debug("Sensor started!", extra=ex)
        time.sleep(2)

        ts = 0
        while True:
            time.sleep(2)
            data = ble_sc_device.get_raw_data()
            new_ts = time.strftime("%Y-%b-%d %H:%M:%S", time.localtime(data['time_stamp']))
            if ts != new_ts:
                sys_logger.debug("Name: {}, state:{}, battery level: {}%".format(data['name'], data['state'], data['battery_level']), extra=ex)
                ts = new_ts
                speed = 3.6 * WHEEL_CIRC_700x25 / (data["wheel_rev_time"] + 0.00001)
                sys_logger.debug("TS: {}, speed: {:10.3f} km/h".format(data["wheel_time_stamp"], speed), extra=ex)
                sys_logger.debug("TS: {}, RPM: {:10.3f}".format(data["cadence_time_stamp"], data["cadence"]), extra=ex)
            sys_logger.debug("Tick...{}".format(new_ts), extra=ex)

    except (KeyboardInterrupt, SystemExit):
        sys_logger.debug("BLE sc stop", extra=ex)
        if connected:
            ble_sc_device.stop()
