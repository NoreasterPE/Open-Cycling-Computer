from bluepy.btle import DefaultDelegate
from bluepy.btle import Scanner


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

#    def handleDiscovery(self, dev, isNewDev, isNewData):
#        if isNewDev:
#            print "Discovered device", dev.addr
#        elif isNewData:
#            print "Received new data from", dev.addr


class ble_scan(object):

    def __init__(self):
        self.scanner = Scanner().withDelegate(ScanDelegate())
        self.dev_list_raw = []

    def scan(self, timeout=10.0):
        devices = self.scanner.scan(timeout)

        for dev in devices:
            local_name = "Unknown"
            for (adtype, desc, value) in dev.getScanData():
                if adtype == 9:
                    local_name = value
            self.dev_list_raw.append(dict(addr=dev.addr, name=local_name, addr_type=dev.addrType, rss=dev.rssi))

    def get_dev_list(self):
        dl = sorted(self.dev_list_raw, key=lambda k: k['rss'], reverse=True)
        return dl

if __name__ == '__main__':
    ble = ble_scan()
    ble.scan()
    for i in ble.get_dev_list():
        print (i)
