#!/usr/bin/python3
## @package json_server
#  Package responsible for serving parameters in json format

import bottle
import plugin
import pyplum
import math


## Main json_server class
class json_server(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.pm = pyplum.pyplum()

    def run(self):

        @bottle.get('/')
        def serve_json():
            s = {}
            for p in self.pm.parameters:
                s[p] = self.pm.parameters[p]['value']
                print(s[p])
                try:
                    if s[p] is None:
                        s[p] = 'None'
                    if math.isnan(s[p]):
                        s[p] = 'NaN'
                except TypeError:
                    pass
            return s

        bottle.run(host='192.168.0.33', port=8080)
