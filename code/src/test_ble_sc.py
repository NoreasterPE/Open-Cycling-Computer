import time
import logging
import logging.handlers
from ble_sc import ble_sc
from bluepy.btle import BTLEException
from wheel import wheel as w

if __name__ == '__main__':
    suffix = time.strftime("%d-%H:%M:%S")
    sys_log_filename = "ble_sc_debug." + suffix + ".log"
    logging.getLogger('system').setLevel(logging.DEBUG)
    sys_log_handler = logging.handlers.RotatingFileHandler(sys_log_filename)
    sys_log_format = '[%(levelname)-5s] %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    sys_logger = logging.getLogger('system')
    sys_logger.debug("[BLESC] Log start")

    try:
        wheel = w()
        WHEEL_CIRC_700x25 = wheel.get_size("700x25C") / 1000.0
        connected = False
        while not connected:
            try:
                print("Initialising BLE device...")
                lez = ble_sc("fd:df:0e:4e:76:cf")
                print(lez)
                print("Starting BLE thread...")
                print("Device name: {}".format(lez.get_device_name()))
                print("Battery level: {}".format(lez.get_battery_level()))
                lez.start()
                time.sleep(1)
                connected = lez.connected
            except BTLEException as e:
                print("Error: {}".format(e))
                print(".....sensor is not on? Waiting...")

        print(".....sensor started!")
        NOTIFICATION_EXPIRY_TIME = 2.0
        while True:
                data = lez.get_data()
                wheel_time_stamp = data['wheel_time_stamp']
                wheel_rev_time = data['wheel_rev_time']
                cadence_time_stamp = data['cadence_time_stamp']
                cadence = data['cadence']

                # handleNotification() was called
                print("TS: {}".format(time.time()))
                if (time.time() - wheel_time_stamp) > NOTIFICATION_EXPIRY_TIME:
                    print("[EXPIRED] "),
                speed = 3.6 * WHEEL_CIRC_700x25 / (wheel_rev_time + 0.00001)
                # print "Speed / RPM: {:10.3f}".format(speed / val.crank_rpm)
                print("TS: {}, speed: {:10.3f} km/h".format(wheel_time_stamp, speed))
                if (time.time() - cadence_time_stamp) > NOTIFICATION_EXPIRY_TIME:
                    print("[EXPIRED] "),
                print("TS: {}, RPM: {:10.3f}".format(cadence_time_stamp, cadence))
                time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        if connected:
            try:
                print("Lez stop")
                lez.stop()
            except:
                pass
