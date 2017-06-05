#! /usr/bin/python
## @package ble_scanner
#  BLE scanner module. Provides list of BLE devices. Can be run directly printing the list of devices to the console.
#  Uses fixed scan time (10s)
from bluepy.btle import DefaultDelegate
from bluepy.btle import Scanner


## Helper class inheriting from bluepy DefaultDelegate
class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

#    def handleDiscovery(self, dev, isNewDev, isNewData):
#        if isNewDev:
#            print "Discovered device", dev.addr
#        elif isNewData:
#            print "Received new data from", dev.addr


## BLE Scanner class
# Scans for and returns list of BLE devices.
class ble_scan(object):

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        ## @var scanner
        #  BLE scanner from bluepy
        self.scanner = Scanner().withDelegate(ScanDelegate())
        ## @var dev_list_raw
        #  List of BLE devices stored for get_dev_list function
        self.dev_list_raw = []

    ## Searches for BLE devices over 10 seconds (defaut). Stores found devices to self.dev_list_raw
    #  @param self The python object self
    #  @param timeout time that scanner should look for BLE devices
    def scan(self, timeout=10.0):
        ## @var devices
        #  List of devices returned by bluepy scanner
        devices = self.scanner.scan(timeout)

        for dev in devices:
            ## @var local_name
            #  By default all devices are named "Unknown". If device reports a bane it will be used instead.
            local_name = "Unknown"
            for (adtype, desc, value) in dev.getScanData():
                if adtype == 9:
                    local_name = value
            self.dev_list_raw.append(dict(addr=dev.addr, name=local_name, addr_type=dev.addrType, rss=dev.rssi))

    ## Returns list of BLE devices. scan function needs to be called first.
    #  List of BLE devices stored for get_dev_list function
    def get_dev_list(self):
        ## @var dl
        #  Local variable, used to sort list of BLE devices per signal strength
        dl = sorted(self.dev_list_raw, key=lambda k: k['rss'], reverse=True)
        return dl

if __name__ == '__main__':
    ble = ble_scan()
    ble.scan()
    for i in ble.get_dev_list():
        print (i)
