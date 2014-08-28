import time
from bmp183 import bmp183

bmp = bmp183()
bmp.start()
run = 0

while (run != 60):
	print "Temperature: ", bmp.temperature, "deg C"
	print "Pressure: ", bmp.pressure/100.0, " hPa"
	time.sleep(1)
	run += 1

bmp.stop_measurement()
quit()
