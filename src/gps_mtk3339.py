#! /usr/bin/python
 
from gps import *
import threading
import time
 
class gps_mtk3339(threading.Thread):
	#Class for gps mtk3339 as sold by Adafruit

	def __init__(self, simulate = False):
		threading.Thread.__init__(self)
		self.simulate = simulate
		self.present = False
		self.speed = float('nan')
		self.altitude = 50.0
		self.utc = "UTC"
		if not self.simulate:
			try:
				#Add check for running gpsd. Restart if missing. Consider watchdog thread to start gpsd
				self.data = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
				self.present = True
			except:
				#can not talk to gps
				self.present = False
		else:
			self.present = True
	def run(self):
		if self.present:
			self.running = True
			if not self.simulate:
				while self.running:
					self.data.next()
					self.latitude = self.data.fix.latitude
					self.longitude = self.data.fix.longitude
					self.utc = self.data.utc
					self.climb = self.data.fix.climb #Add to rp module
					self.speed = self.data.fix.speed
					self.altitude = self.data.fix.altitude
			else:
				self.latitude = 52.0001
				self.longitude = -8.0001
				self.utc = "utc"
				self.climb = "0.2"
				self.speed = 9.99
				self.altitude = 50.0
				time.sleep(1)

	def get_data(self):
		return (self.latitude, self.longitude, 	#0, 1
			self.altitude, self.speed,	#2, 3
			self.utc)			#4

	def __del__(self):
		self.stop()

	def stop(self):
		self.running = False
