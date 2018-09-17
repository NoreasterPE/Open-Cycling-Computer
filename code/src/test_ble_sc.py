import time
import sys
from ble_sc import ble_sc
from bluepy.btle import BTLEException
import logging
from wheel import wheel as w

M = {'module_name': 'test_ble_sc'}

if __name__ == '__main__':
    #sys_log_filename = "ble_sc." + time.strftime("%Y-%m-%d-%H:%M:%S") + ".log"
    logging.getLogger('system').setLevel(logging.DEBUG)
    sys_log_handler = logging.StreamHandler(sys.stdout)
    sys_log_format = '%(asctime)-25s %(levelname)-10s %(module_name)-12s %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    sys_logger = logging.getLogger('system')
    sys_logger.debug("Log start", extra=M)

    wheel = w()
    WHEEL_CIRC_700x25 = wheel.get_size("700x25C") / 1000.0
    try:
        sys_logger.debug("Initialising BLE device...", extra=M)
        ble_sc_device = ble_sc()
        sys_logger.debug("Setting address...", extra=M)
        ble_sc_device.set_addr("FD:DF:0E:4E:76:CF")
        sys_logger.debug("Starting BLE thread...", extra=M)
        ble_sc_device.start()
        connected = False
        while not connected:
            sys_logger.debug("Device not connected...", extra=M)
            try:
                sys_logger.debug("Calling is_connected", extra=M)
                connected = ble_sc_device.is_connected()
                sys_logger.debug("is_connected returned {}".format(connected), extra=M)
                time.sleep(3)
            except BTLEException as e:
                sys_logger.debug("Error: {}".format(e), extra=M)
                sys_logger.debug(".....sensor is not on? Waiting... ", extra=M)

        sys_logger.debug("Sensor started!", extra=M)
        #sys_logger.debug("Getting device name", extra=M)
        #sys_logger.debug("Device name: {}".format(ble_sc_device.get_device_name()), extra=M)
        #time.sleep(2)
        #sys_logger.debug("Getting battery level", extra=M)
        #sys_logger.debug("Battery level: {}".format(ble_sc_device.get_battery_level()), extra=M)
        time.sleep(2)

        #sys_logger.debug("Starting notifications", extra=M)
        #ble_sc_device.set_notifications()
        ts = 0
        while True:
            time.sleep(2)
            data = ble_sc_device.get_raw_data()
            new_ts = time.strftime("%Y-%b-%d %H:%M:%S", time.localtime(data['time_stamp']))
            if ts != new_ts:
                sys_logger.debug("Name: {}, state:{}, battery level: {}%".format(data['name'], data['state'], data['battery_level']), extra=M)
                ts = new_ts
                #sys_logger.debug(" Timestamp: {}, heart rate: {}".format(ts, data['heart_rate']), extra=M)
                speed = 3.6 * WHEEL_CIRC_700x25 / (data["wheel_rev_time"] + 0.00001)
                sys_logger.debug("TS: {}, speed: {:10.3f} km/h".format(data["wheel_time_stamp"], speed), extra=M)
                #if (time.time() - cadence_time_stamp) > NOTIFICATION_EXPIRY_TIME:
                #    sys_logger.debug("[EXPIRED] "),
                sys_logger.debug("TS: {}, RPM: {:10.3f}".format(data["cadence_time_stamp"], data["cadence"]), extra=M)
            sys_logger.debug("Tick...{}".format(new_ts), extra=M)

    except (KeyboardInterrupt, SystemExit):
        sys_logger.debug("BLE sc stop", extra=M)
        if connected:
            ble_sc_device.stop()
