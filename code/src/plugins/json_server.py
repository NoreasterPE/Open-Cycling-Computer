#!/usr/bin/python3
## @package json_server
#  Package responsible for serving parameters in json format

import bottle
import math
import plugin
import socket


## Main json_server class
class json_server(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def run(self):

        @bottle.get('/')
        def serve_json():
            s = {}
            for p in self.pm.parameters:
                s[p] = self.pm.parameters[p]['value']
                try:
                    if s[p] is None:
                        s[p] = 'None'
                    if math.isnan(s[p]):
                        s[p] = 'NaN'
                except TypeError:
                    pass
            return s

        bottle.run(host=self.get_ip(), port=8080)

    def stop(self):
        bottle.stop()
