#! /usr/bin/python
 
from gps import *
from time import *
import os
import threading
import time
 
class gps_mtk3339(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.present = False
		try:
			self.data = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
		except:
			#can not talk to gps
			self.present = False
		self.running = False
	def run(self):
		if self.present:
			self.running = True
			while self.running:
				self.data.next()
				#FIXME filter for nan value and set to 0 or --
				self.speed = self.data.fix.speed
	def stop(self):
		self.running = False
 
if __name__ == '__main__':
	gps = gps_mtk3339()
	try:
		gps.start()
		while True:
			os.system('clear')

			print 'latitude    ' , gps.data.fix.latitude
			print 'longitude   ' , gps.data.fix.longitude
			print 'time utc    ' , gps.data.utc
			print 'fix time    ' , gps.data.fix.time
			print 'altitude (m)' , gps.data.fix.altitude
			print 'eps         ' , gps.data.fix.eps
			print 'epx         ' , gps.data.fix.epx
			print 'epv         ' , gps.data.fix.epv
			print 'ept         ' , gps.data.fix.ept
			print 'speed (m/s) ' , gps.data.fix.speed
			print 'climb       ' , gps.data.fix.climb
			print 'track       ' , gps.data.fix.track
			print 'mode        ' , gps.data.fix.mode
			print 'sats        ' , gps.data.satellites

			time.sleep(1)
 
	except (KeyboardInterrupt, SystemExit):
	#FIXME possibly required on shutdown
		gps.stop()
		gps.join()
