#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bluepy
import time
import sys
sys.path.insert(0, '../plugins')
sys.path.insert(0, '../helpers')
sys.path.insert(0, '../')

import ble_hr
import logging
import pyplum


ADDR = "D6:90:A8:08:F0:E4"

if __name__ == '__main__':
    ex = {'module_name': 'test_ble_hr'}
    #sys_log_filename = "ble_hr." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
    logging.getLogger('system').setLevel(logging.DEBUG)
    sys_log_handler = logging.StreamHandler(sys.stdout)
    sys_log_format = '%(asctime)-25s %(levelname)-10s %(module_name)-12s %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    sys_logger = logging.getLogger('system')
    sys_logger.debug("Log start", extra=ex)
    s = pyplum.pyplum()

    try:
        sys_logger.debug("Initialising BLE device...", extra=ex)
        ble_hr_device = ble_hr.ble_hr()
        sys_logger.debug("Setting address...", extra=ex)
        ble_hr_device.set_addr(ADDR)
        sys_logger.debug("Starting BLE thread...", extra=ex)
        ble_hr_device.start()
        connected = False
        while not connected:
            sys_logger.debug("Device not connected...", extra=ex)
            try:
                sys_logger.debug("Calling is_connected", extra=ex)
                connected = ble_hr_device.is_connected()
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
            hr = s.parameters['heart_rate']['value']
            ts = s.parameters['heart_rate']['time_stamp']
            new_ts = time.strftime("%Y-%b-%d %H:%M:%S", time.localtime(ts))
            if ts != new_ts:
                ts = new_ts
                sys_logger.debug(" Timestamp: {}, heart rate: {}".format(ts, hr), extra=ex)
            sys_logger.debug("Tick...{}".format(new_ts), extra=ex)

    except (KeyboardInterrupt, SystemExit):
        sys_logger.debug("BLE hr stop", extra=ex)
        if connected:
            ble_hr_device.stop()
