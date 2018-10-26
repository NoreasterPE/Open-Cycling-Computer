#!/usr/bin/python3

import logging
import time
import sys
sys.path.insert(0, '../plugins')
sys.path.insert(0, '../')

import bmp280

# Init sensor
ex = {'module_name': 'test_bmp280'}
logging.getLogger('system').setLevel(logging.DEBUG)
sys_log_handler = logging.StreamHandler(sys.stdout)
sys_log_format = '%(asctime)-25s %(levelname)-10s %(module_name)-12s %(message)s'
sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
logging.getLogger('system').addHandler(sys_log_handler)
sys_logger = logging.getLogger('system')
sys_logger.debug("Log start", extra=ex)

bmp = bmp280.bmp280()
# Start measuring
sys_logger.debug('Start measuring', extra=ex)
bmp.start()
run = 0
while (run != 10):
    sys_logger.debug("Temperature: {:.3f} degC".format(bmp.temperature), extra=ex)
    sys_logger.debug("Pressure: {:.3f} hPa".format(bmp.pressure_unfiltered / 100.0), extra=ex)
    time.sleep(1)
    run += 1
# Stop measuring
bmp.stop()
quit()
