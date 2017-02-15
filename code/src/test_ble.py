import time
from bluepy.btle import BTLEException
import ble

if __name__ == '__main__':
    try:

        WHEEL_PERIM_700x25 = 2.112
        connected = False
        while not connected:
            try:
                lez = ble.ble("fd:df:0e:4e:76:cf")
                print "Battery level: ", lez.get_battery_level()
                lez.set_notifications()
                val = lez.delegate
                connected = True
            except BTLEException:
                print ".....sensor is not on? Retrying."

        counter = 0
        NOTIFICATION_EXPIRY_TIME = 1.0
        while True:
            if lez.waitForNotifications(0.01):
                # handleNotification() was called
                print "TS: {}".format(time.time())
                if (time.time() - val.wheel_time_stamp) > NOTIFICATION_EXPIRY_TIME:
                    print "[EXPIRED] ",
                speed = 3.6 * WHEEL_PERIM_700x25 / \
                    (val.wheel_rev_time + 0.00001)
                # print "Speed / RPM: {:10.3f}".format(speed / val.crank_rpm)
                print "TS: {}, speed: {:10.3f}".format(val.wheel_time_stamp, speed)
                if (time.time() - val.crank_time_stamp) > NOTIFICATION_EXPIRY_TIME:
                    print "[EXPIRED] ",
                print "TS: {}, RPM: {:10.3f}".format(val.crank_time_stamp, val.crank_rpm)

    except (KeyboardInterrupt, SystemExit):
        if connected:
            try:
                lez.set_notifications(enable=False)
            except:
                pass
            try:
                lez.disconnect()
            except:
                pass
