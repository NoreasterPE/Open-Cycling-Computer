#!/usr/bin/python3

import time
from bmp183 import bmp183
# Init sensor
bmp = bmp183()
# Start measuring
bmp.start()
# Run printing out results for 60 seconds, every second
run = 0
try:
    while (run != -1):
        print("Temperature: ", bmp.temperature, " deg C")
        print("Pressure: ", bmp.pressure / 100.0, " hPa")
        time.sleep(1)
        run += 1
except:
    # an error or Ctrl-C
    pass
# Stop measuring
bmp.stop()
quit()
