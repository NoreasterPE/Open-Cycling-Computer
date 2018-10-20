#!/usr/bin/python3

import time
import bmp280
# Init sensor
bmp = bmp280.bmp280()
# Start measuring
bmp.start()
run = 0
try:
    while (run != -1):
        print("Temperature: {:.3f} degC".format(bmp.temperature))
        print("Pressure: {:.3f} hPa".format(bmp.pressure_unfiltered / 100.0))
        time.sleep(1)
        run += 1
except:
    # an error or Ctrl-C
    pass
# Stop measuring
bmp.stop()
quit()
