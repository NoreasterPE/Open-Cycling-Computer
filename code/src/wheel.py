#!/usr/bin/pyhon


class wheel:
    def __init__(self):
        self.wheel_size = {}
        self.wheel_size['700x18C'] = 2.070
        self.wheel_size['700x19C'] = 2.080
        self.wheel_size['700x20C'] = 2.086
        self.wheel_size['700x23C'] = 2.096
        self.wheel_size['700x25C'] = 2.105
        self.wheel_size['700x28C'] = 2.136
        self.wheel_size['700x30C'] = 2.146
        self.wheel_size['700x32C'] = 2.155
        self.wheel_size['700x35C'] = 2.168
        self.wheel_size['700x38C'] = 2.180
        self.wheel_size['700x40C'] = 2.200
        self.wheel_size['700x42C'] = 2.224
        self.wheel_size['700x44C'] = 2.235
        self.wheel_size['700x45C'] = 2.242
        self.wheel_size['700x47C'] = 2.268

    def get_size(self, name):
            return self.wheel_size[name]
