#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package weather
#  Weather Monitor - pyplum usage demo
#

import pyplum
import time

p_manager = pyplum.pyplum()
p_manager.register_parameter
width, height = 240, 320
p_manager.register_parameter("display_size", value=(width, height))
p_manager.load_plugins('plugins', ['bmp280', 'compute', 'json_server', 'gtk_rendering'])
p_manager.start()
time.sleep(100)
p_manager.stop()
