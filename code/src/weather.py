#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package weather
#  Weather Monitor - pyplum usage demo
#

import pyplum
import time

p_manager = pyplum.pyplum()
p_manager.register_parameter
p_manager.load_plugins('plugins', ['bmp280', 'compute', 'json_server'])
p_manager.start()
time.sleep(100)
p_manager.stop()
