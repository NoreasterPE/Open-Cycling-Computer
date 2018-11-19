#!/usr/bin/python3
## @package ble_scanner
#  BLE scanner module. Provides list of BLE devices.
import bluepy
import plugin
import pyplum
import threading
import time


## Helper class inheriting from bluepy DefaultDelegate
class ScanDelegate(bluepy.btle.DefaultDelegate):
    def __init__(self):
        # Run init for super class
        super().__init__()

#    def handleDiscovery(self, dev, isNewDev, isNewData):
#        if isNewDev:
#            print "Discovered device", dev.addr
#        elif isNewData:
#            print "Received new data from", dev.addr


## BLE Scanner class
# Scans for and returns list of BLE devices.
class ble_scanner(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.pm = pyplum.pyplum()
        self.pm.register_parameter("ble_scan_in_progress", self.extra["module_name"], value=False)
        self.pm.register_parameter("ble_devices", self.extra["module_name"], value=[])
        ## @var scanner
        #  BLE scanner from bluepy
        self.scanner = bluepy.btle.Scanner().withDelegate(ScanDelegate())
        ## @var ble_devices
        #  List of BLE devices sorted by signal strength
        # Example results (list of dict):
        # [{'rss': -68, 'addr': 'fd:df:0e:4e:76:cf', 'name': 'Lezyne S&C 249', 'addr_type': 'random'},
        #  {'rss': -71, 'addr': 'd6:90:a8:08:f0:e4', 'name': 'Tacx HRB 04741', 'addr_type': 'random'}]
        self.ble_devices = []

    def scan(self):
        if self.pm.event_queue is not None:
            for i in range(4):
                self.pm.event_queue.put(('show_overlay', 'images/ol_ble_scanning.png', 1.0))
                self.pm.event_queue.put(('show_overlay', 'images/ol_ble_scanning_0.png', 1.0))
                self.pm.event_queue.put(('show_overlay', 'images/ol_ble_scanning_1.png', 1.0))
                self.pm.event_queue.put(('show_overlay', 'images/ol_ble_scanning_2.png', 1.0))
        threading.Thread(target=self._scan).start()

    ## Searches for BLE devices over 5 seconds (defaut). Stores found devices in self.ble_devices
    #  @param self The python object self
    #  @param timeout time that scanner should look for BLE devices
    def _scan(self, timeout=10.0):
        self.pm.parameters['ble_scan_in_progress']['value'] = True
        devices = []
        try:
            devices_raw = self.scanner.scan(timeout)
        except bluepy.btle.BTLEException as exception:
            self.log.error("Exception {}".format(exception), extra=self.extra)
        else:
            devices = []
            for dev in devices_raw:
                local_name = 'Unknown'
                for (adtype, desc, value) in dev.getScanData():
                    if adtype == 9:
                        local_name = value
                devices.append(dict(addr=dev.addr, name=local_name, addr_type=dev.addrType, rss=dev.rssi))
        self.ble_devices = sorted(devices, key=lambda k: k['rss'], reverse=True)
        self.pm.parameters['ble_devices']['value'] = self.ble_devices
        self.pm.parameters['ble_devices']['time_stamp'] = time.time()
        self.pm.parameters['ble_scan_in_progress']['value'] = False

    def run(self):
        pass