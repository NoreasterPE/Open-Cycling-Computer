#!/usr/bin/pyhon
## @package wheel
#  Helper module providing wheel size based on tyre size/width.


## wheel class
class wheel:

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        #FIXME move to csv fiel, add more wheels
        self.wheel_circ = {}
        self.wheel_circ['700x18C'] = 2.070
        self.wheel_circ['700x19C'] = 2.080
        self.wheel_circ['700x20C'] = 2.086
        self.wheel_circ['700x23C'] = 2.096
        self.wheel_circ['700x25C'] = 2.105
        self.wheel_circ['700x28C'] = 2.136
        self.wheel_circ['700x30C'] = 2.146
        self.wheel_circ['700x32C'] = 2.155
        self.wheel_circ['700x35C'] = 2.168
        self.wheel_circ['700x38C'] = 2.180
        self.wheel_circ['700x40C'] = 2.200
        self.wheel_circ['700x42C'] = 2.224
        self.wheel_circ['700x44C'] = 2.235
        self.wheel_circ['700x45C'] = 2.242
        self.wheel_circ['700x47C'] = 2.268

    ## Helper function returning wheel size in meters
    #  @param self The python object self
    #  @param name String describing wheel, i.e. 700x25C
    def get_circ(self, name):
            return self.wheel_circ[name]
