#!/usr/bin/python3
## @package ble_scanner
#  BLE scanner module. Provides list of BLE devices and info about number of devices connected
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
        self.pm.register_parameter("ble_scan_done", self.extra["module_name"], value=False)
        self.pm.register_parameter("ble_scan_results", self.extra["module_name"], value=[])
        self.pm.register_parameter('ble_no_of_devices_connected', self.extra['module_name'], value=0)
        ## @var scanner
        #  BLE scanner from bluepy
        self.scanner = bluepy.btle.Scanner().withDelegate(ScanDelegate())
        ## @var ble_devices
        #  List of BLE devices sorted by signal strength
        # Example results (list of dict):
        # [{'rss': -68, 'addr': 'fd:df:0e:4e:76:cf', 'name': 'Lezyne S&C 249', 'addr_type': 'random'},
        #  {'rss': -71, 'addr': 'd6:90:a8:08:f0:e4', 'name': 'Tacx HRB 04741', 'addr_type': 'random'}]
        self.ble_devices = []
        self.current_device_type = None
        self.scan_in_progress = False
        ## @var animation_frame
        #  Current number of BLE scan animation frame
        self.animation_frame = 0
        ## @var animation_frame_max
        #  Total number af animation frames
        self.animation_frame_max = 2
        ## @var heart_rate_device_found
        #  Variable indicating that a heart rate device has been found. Used to control displaying ovelay image showing that information
        self.heart_rate_device_found = False
        ## @var speed_cadence_device_found
        #  Variable indicating that a speed-cadence device has been found. Used to control displaying ovelay image showing that information
        self.speed_cadence_device_found = False

    ## Searches for BLE devices over 5 seconds (defaut). Stores found devices in self.ble_devices
    #  @param self The python object self
    #  @param timeout time that scanner should look for BLE devices
    def scan(self, timeout=4.0):
        self.log.debug("starting scan", extra=self.extra)
        self.scan_in_progress = True
        devices = []
        try:
            devices_raw = self.scanner.scan(timeout)
            self.log.debug("got devices from scanner", extra=self.extra)
        except bluepy.btle.BTLEException as exception:
            self.log.debug("initial scan finished with error", extra=self.extra)
            self.log.error("Exception {}".format(exception), extra=self.extra)
            self.pm.parameters['ble_scan_results']['data'] = None
        else:
            self.log.debug("getting services", extra=self.extra)
            devices = []
            for dev in devices_raw:
                local_name = None
                for (adtype, desc, value) in dev.getScanData():
                    if adtype == 9:
                        local_name = value
                    if local_name is None:
                        local_name = dev.addr
                if dev.connectable:
                    self.log.debug("device {} addr: {} connectable, getting services".format(local_name, dev.addr), extra=self.extra)
                    services = self.get_services(dev.addr, dev.addrType)
                else:
                    services = ''
                devices.append(dict(addr=dev.addr, name=local_name, addr_type=dev.addrType, rss=dev.rssi, services=services))
            self.ble_devices = sorted(devices, key=lambda k: k['rss'], reverse=True)
            self.pm.parameters['ble_scan_results']['data'] = self.ble_devices
        finally:
            self.pm.parameters['ble_scan_results']['value'] = self.current_device_type
            self.current_device_type = None
            self.pm.parameters['ble_scan_results']['time_stamp'] = time.time()
            self.pm.parameters['ble_scan_done']['value'] = True
            self.log.debug("scan finished", extra=self.extra)
            self.scan_in_progress = False

    def run(self):
        self.running = True
        while self.running:
            connected = 0
            for pl in self.pm.plugins:
                if self.pm.plugins[pl].connected:
                    connected += 1
            self.pm.parameters['ble_no_of_devices_connected']['value'] = connected
            #self.log.debug("ble_no_of_devices_connected: {}".format(connected), extra=self.extra)
            if self.scan_in_progress:
                self.ble_scan_animation_next_frame()
            time.sleep(1.0)

    def find_ble_device(self, device_type):
        self.preload_images()
        if self.pm.event_queue is not None:
            self.pm.event_queue.put(('show_overlay', 'images/ol_ble_scanning.png', 1.0))
        self.current_device_type = device_type
        threading.Thread(target=self.scan).start()

    def ble_scan_animation_next_frame(self):
        if self.heart_rate_device_found:
            next_ol_image = 'images/ol_ble_hr_connected.png'
            period = 2
            self.heart_rate_device_found = False
        elif self.speed_cadence_device_found:
            next_ol_image = 'images/ol_ble_sc_connected.png'
            period = 2
            self.speed_cadence_device_found = False
        else:
            next_ol_image = 'images/ol_ble_scanning_{}.png'.format(self.animation_frame)
            period = 1

        if self.pm.event_queue is not None:
            self.pm.event_queue.put(('show_overlay', next_ol_image, period))
        if self.animation_frame == self.animation_frame_max:
            self.animation_frame = 0
        else:
            self.animation_frame += 1

    def get_services(self, addr, addr_type):
        self.log.debug("getting services for '{}'".format(addr), extra=self.extra)
        services = ''
        try:
            peripheral = bluepy.btle.Peripheral(addr, addrType=addr_type)
            try:
                peripheral.getServiceByUUID(bluepy.btle.AssignedNumbers.heartRate)
                services += 'heart_rate'
                self.heart_rate_device_found = True
            except (bluepy.btle.BTLEException, BrokenPipeError):
                pass
            try:
                peripheral.getServiceByUUID(bluepy.btle.AssignedNumbers.cyclingSpeedAndCadence)
                services += 'speed_cadence'
                self.speed_cadence_device_found = True
            except (bluepy.btle.BTLEException, BrokenPipeError):
                pass
            try:
                self.log.debug("getting all services for '{}'".format(addr), extra=self.extra)
                s = peripheral.getServices()
                self.log.debug("all services for '{}' are:".format(addr), extra=self.extra)
                for _s in s:
                    self.log.debug("'{}'".format(_s), extra=self.extra)
                    c = _s.getCharacteristics()
                    self.log.debug("all characteristics for service '{}' are".format(_s), extra=self.extra)
                    for _c in c:
                        self.log.info("'{}'".format(_c), extra=self.extra)
            except (bluepy.btle.BTLEException, BrokenPipeError) as e:
                self.log.info("{}".format(e), extra=self.extra)
            try:
                self.log.debug("getting all characteristics for '{}'".format(addr), extra=self.extra)
                c = peripheral.getCharacteristics()
                self.log.debug("all characteristics for '{}' are".format(addr), extra=self.extra)
                for _c in c:
                    self.log.info("'{}'".format(_c), extra=self.extra)
            except (bluepy.btle.BTLEException, BrokenPipeError) as e:
                self.log.debug("{}".format(e), extra=self.extra)
        except bluepy.btle.BTLEException as e:
            self.log.info("{}".format(e), extra=self.extra)
        self.log.debug("services for '{}' are '{}'".format(addr, services), extra=self.extra)
        return services

    def preload_images(self):
        if self.pm.event_queue is not None:
            images = ['images/ol_ble_scanning.png', 'images/ol_ble_hr_connected.png']
            for af in range(self.animation_frame_max + 1):
                images.append('images/ol_ble_scanning_{}.png'.format(af))
            for image in images:
                self.pm.event_queue.put(('preload_image', image))
