#! /usr/bin/python
 
from gps import *
import threading
import time

NaN = float('nan')

class gps_mtk3339(threading.Thread):
	#Class for gps mtk3339 as sold by Adafruit

	def __init__(self, occ = None, simulate = False):
		threading.Thread.__init__(self)
		self.occ = occ
		self.simulate = simulate
		self.present = False
		self.latitude = NaN
		self.longitude = NaN
		self.speed = NaN
		self.altitude = 50.0
		self.utc = "UTC"
		self.satellites = 0
		self.satellites_used = 0
		self.satellites_visible = 0
		if not self.simulate:
			try:
				#FIXME Add check for running gpsd. Restart if missing. Consider watchdog thread to start gpsd
				self.data = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
				self.present = True
			except:
				self.occ.log.error("{}: Cannot talk to GPS".format(__name__))
				self.present = False
		else:
			self.present = True
	def run(self):
		if self.present:
			self.running = True
			if not self.simulate:
				while self.running:
					self.occ.log.debug("{}: GPS running = {}".format(__name__, self.running))
					try:
						self.data.next()
						self.occ.log.debug("{}: Received next GPS event. timestamp: {}".format(__name__, time.time()))
						self.latitude = self.data.fix.latitude
						self.longitude = self.data.fix.longitude
						self.occ.log.debug("{}: Coordinates: {}, {}".format(__name__, self.latitude, self.longitude))
						self.utc = self.data.utc
						self.occ.log.debug("{}: UTC: {}".format(__name__, self.utc))
						self.climb = self.data.fix.climb #Add to rp module
						self.occ.log.debug("{}: Climb: {}".format(__name__, self.climb))
						self.speed = self.data.fix.speed
						self.occ.log.debug("{}: Speed: {}".format(__name__, self.speed))
						self.altitude = self.data.fix.altitude
						self.occ.log.debug("{}: Altitude: {}".format(__name__, self.altitude))
						try:
							sat = gps.data.satellites
							self.satellites = len(sat)
							self.satellites_used = 0
							self.satellites_visible = 0
							for i in sat:
								if i.used:
									self.satellites_used += 1
								if i.ss > 0:
									self.satellites_visible += 1
						except AttributeError:
							self.occ.log.error("{}: AttributeError exception in GPS".format(__name__))
							pass
					except StopIteration:
						self.occ.log.error("{}: StopIteration exception in GPS".format(__name__))
						pass
			else:
				self.latitude = 52.0001
				self.longitude = -8.0001
				self.utc = "utc"
				self.climb = "0.2"
				self.speed = 9.99
				self.altitude = 50.0
				self.satellites = 10
				self.satellites_used = 4
				self.satellites_visible = 5
				time.sleep(1)

	def get_data(self):
		return (self.latitude, self.longitude, 	#0, 1
			self.altitude, self.speed,	#2, 3
			self.utc, 			#4
			self.satellites_used,		#5
			self.satellites_visible,	#6
			self.satellites)		#7

	def __del__(self):
		self.stop()

	def stop(self):
		self.running = False
