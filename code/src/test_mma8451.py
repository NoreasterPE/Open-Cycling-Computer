#! /usr/bin/python

import time
from mma8451 import mma8451
#Init sensor
mma = mma8451()
#Check ID
mma.check_id()
#Run printing out results for 60 seconds, every second
run = 0
while (run != 60):
	(x, y, z) = mma.read_xyz()
	print "X:", x, "Y:", y, "Z:", z
	time.sleep(1)
	run += 1
quit()

