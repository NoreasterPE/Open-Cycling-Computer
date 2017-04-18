import time
from ble_hr import ble_hr
from bluepy.btle import BTLEException

if __name__ == '__main__':
    try:
        connected = False
        while not connected:
            try:
                print "Initialising BLE device..."
                ble_hr = ble_hr("D6:90:A8:08:F0:E4")
                print "Starting BLE thread..."
                # print "Device name: ", ble_hr.get_device_name()
                print "Battery level: ", ble_hr.get_battery_level()
                ble_hr.start()
                time.sleep(1)
                connected = ble_hr.connected
            except BTLEException, e:
                print ("Error: {}".format(e))
                print (".....sensor is not on? Waiting... ")
            time.sleep(1)

        print ".....sensor started!"
        while True:
                time.sleep(0.1)
                data = ble_hr.get_data()
                print "{}".format(data['state']),
                print " TS: {}".format(data['time_stamp']),
                print " HR: {}".format(data['heart_rate'])

    except (KeyboardInterrupt, SystemExit):
        if connected:
            try:
                print ("BLE hr stop")
                ble_hr.stop()
            except:
                pass
