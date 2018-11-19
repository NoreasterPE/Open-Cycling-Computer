#!/usr/bin/pyhon
## @package wheel
#  Helper module providing wheel size based on tyre size/width.


## wheel class
class wheel:

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        #FIXME move to csv file, add more wheels
        self.wheel_circ = {}
        self.wheel_circ['700X18C'] = 2.070
        self.wheel_circ['700X19C'] = 2.080
        self.wheel_circ['700X20C'] = 2.086
        self.wheel_circ['700X23C'] = 2.096
        self.wheel_circ['700X25C'] = 2.105
        self.wheel_circ['700X28C'] = 2.136
        self.wheel_circ['700X30C'] = 2.146
        self.wheel_circ['700X32C'] = 2.155
        self.wheel_circ['700X35C'] = 2.168
        self.wheel_circ['700X38C'] = 2.180
        self.wheel_circ['700X40C'] = 2.200
        self.wheel_circ['700X42C'] = 2.224
        self.wheel_circ['700X44C'] = 2.235
        self.wheel_circ['700X45C'] = 2.242
        self.wheel_circ['700X47C'] = 2.268

    ## Helper function returning wheel size in meters
    #  @param self The python object self
    #  @param name String describing wheel, i.e. 700x25C
    def get_circumference(self, name):
            return self.wheel_circ[name.upper()]

    ## Helper function returning all allowed values for wheel size
    #  @param self The python object self
    def get_allowed_values(self):
        return ('700X18C', '700X19C', '700X20C', '700X23C', '700X25C', '700X28C', '700X30C', '700X32C',
                '700X35C', '700X38C', '700X40C', '700X42C', '700X44C', '700X45C', '700X47C')
