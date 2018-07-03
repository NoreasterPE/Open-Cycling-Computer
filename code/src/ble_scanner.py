#!/usr/bin/python3
## @package ble_scanner
#  BLE scanner module. Provides list of BLE devices. Can be run directly printing the list of devices to the console.
#  Uses fixed scan time (10s)
import bluepy
import logging

M = {'module_name': 'ble_scanner'}


## Helper class inheriting from bluepy DefaultDelegate
class ScanDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)

#    def handleDiscovery(self, dev, isNewDev, isNewData):
#        if isNewDev:
#            print "Discovered device", dev.addr
#        elif isNewData:
#            print "Received new data from", dev.addr


## BLE Scanner class
# Scans for and returns list of BLE devices.
class ble_scanner(object):

    ## The constructor
    #  @param self The python object self
    def __init__(self, occ):
        ## @var l
        # System logger handle
        self.log = logging.getLogger('system')
        ## @var occ
        # OCC Handle
        self.occ = occ
        ## @var rp
        # ride_parameters instance handle
        self.rp = occ.rp
        ## @var scanner
        #  BLE scanner from bluepy
        self.scanner = bluepy.btle.Scanner().withDelegate(ScanDelegate())
        ## @var dev_list_raw
        #  List of BLE devices stored for get_dev_list function
        self.dev_list_raw = []

    ## Searches for BLE devices over 10 seconds (defaut). Stores found devices to self.dev_list_raw
    #  @param self The python object self
    #  @param timeout time that scanner should look for BLE devices
    def scan(self, timeout=10.0):
        ## @var devices
        #  List of devices returned by bluepy scanner
        try:
            devices = self.scanner.scan(timeout)
        except bluepy.btle.BTLEException as exception:
            #Failed to execute mgmt cmd 'le on'
            self.log.error("Exception {}".format(exception), extra=M)
        else:
            self.dev_list_raw = []
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

    def ble_scan(self):
        self.log.debug("starting BLE scanning", extra=M)
        for i in range(5):
            self.rp.set_param('ble_dev_name_' + str(i), "Scanning..")
        self.scan()
        for i in range(5):
            self.rp.set_param('ble_dev_name_' + str(i), "")
        i = 1
        for dev in self.get_dev_list():
            self.log.debug("BLE device found! Name:\"{}\" addr:\"{}\"".format(dev['name'], dev['addr']), extra=M)
            self.rp.set_param('ble_dev_name_' + str(i), dev['name'])
            self.rp.set_param('ble_dev_addr_' + str(i), dev['addr'])
            i += 1
        self.log.debug("BLE scanning finished", extra=M)

    def ble_dev_helper(self, no, master):
        if master == 'ble_hr_name':
            dev_type = 'hr'
        elif master == 'ble_sc_name':
            dev_type = 'sc'
        name = self.rp.get_param('ble_dev_name_' + str(no))
        addr = self.rp.get_param('ble_dev_addr_' + str(no))
        self.log.debug("Selected BLE device {} {}".format(name, addr), extra=M)
        self.rp.set_param("variable_value", (name, addr, dev_type))
        self.occ.layout.ed_accept()

    def ble_dev_name_1(self):
        self.ble_dev_helper(1, self.rp.params["variable"])

    def ble_dev_name_2(self):
        self.ble_dev_helper(2, self.rp.params["variable"])

    def ble_dev_name_3(self):
        self.ble_dev_helper(3, self.rp.params["variable"])

    def ble_dev_name_4(self):
        self.ble_dev_helper(4, self.rp.params["variable"])


#TODO Currently doesn't work as it is OCC dependent
if __name__ == '__main__':
    ble = ble_scanner()
    ble.scan()
    for i in ble.get_dev_list():
        print(i)
