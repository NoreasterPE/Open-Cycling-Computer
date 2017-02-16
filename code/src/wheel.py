#!/usr/bin/pyhon


class wheel:
    def __init__(self):
        self.wheel_size = {}
        self.wheel_size['700x18C'] = 2070
        self.wheel_size['700x19C'] = 2080
        self.wheel_size['700x20C'] = 2086
        self.wheel_size['700x23C'] = 2096
        self.wheel_size['700x25C'] = 2105
        self.wheel_size['700x28C'] = 2136
        self.wheel_size['700x30C'] = 2146
        self.wheel_size['700x32C'] = 2155
        self.wheel_size['700x35C'] = 2168
        self.wheel_size['700x38C'] = 2180
        self.wheel_size['700x40C'] = 2200
        self.wheel_size['700x42C'] = 2224
        self.wheel_size['700x44C'] = 2235
        self.wheel_size['700x45C'] = 2242
        self.wheel_size['700x47C'] = 2268

    def get_size(self, name):
            return self.wheel_size[name]
