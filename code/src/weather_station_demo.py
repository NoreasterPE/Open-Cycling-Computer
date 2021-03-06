#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package weather
#  Simple weather Monitor - pyplum usage demo
#

import events
import pyplum
import layout


def set_up_screen_logging():
    import logging
    import sys
    ex = {'module_name': 'weather'}
    logging.getLogger('system').setLevel(logging.DEBUG)
    sys_log_handler = logging.StreamHandler(sys.stdout)
    sys_log_format = '%(asctime)-25s %(levelname)-10s %(module_name)-12s %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    sys_logger = logging.getLogger('system')
    sys_logger.debug("Log start", extra=ex)


# Uncomment the line below to get detailed info what's happening
#set_up_screen_logging()

p_manager = pyplum.pyplum()
p_manager.register_parameter("display_size", value=(240, 320))
# Register weather station altitude. Required for MSLP pressure calculation
p_manager.update_parameter("reference_altitude", dict(value='30', raw_unit='m'))
# Lock altitude. Normally pressure changes are used to determine altitude change, but for weather station altitude doesn't change
p_manager.update_parameter("altitude_lock", dict(value=True))
p_manager.register_parameter("data_log_config", value='config/weather_log.yaml')
p_manager.register_parameter("layout_location", None, value='layouts/weather_station_demo/')
p_manager.register_parameter("fonts_dir", None, value='fonts/')
p_manager.load_plugins('plugins', ['bmp280', 'ds18b20', 'compute', 'json_server',
                                   'pitft_rendering', 'pitft_touchscreen', 'data_log', 'syscalls'])
layout = layout.layout()
events = events.events()
p_manager.start()
#p_manager.stop()
