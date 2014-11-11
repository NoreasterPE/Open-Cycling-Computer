#! /usr/bin/python
 
from gps import *
import threading
import time

NaN = float('nan')
status = { 0 : "No fix",
	   1 : "Fix",
	   2 : "DGPS fix" #Differential GPS fix
}
fix_mode = { 1 : "No fix",
	     2 : "Fix 2D",
	     3 : "Fix 3D"
}

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
				self.occ.log.error("[GPS] Cannot talk to GPS")
				self.present = False
		else:
			self.present = True
	def run(self):
		if self.present:
			self.running = True
			if not self.simulate:
				while self.running:
					self.occ.log.debug("[GPS] running = {}".format(self.running))
					try:
						#FIXME Fails sometimes with ImportError form gps.py - see TODO 21
						self.data.next()
					except StopIteration:
						self.occ.log.error("[GPS] StopIteration exception in GPS")
						pass
					timestamp = time.time()
					self.latitude = self.data.fix.latitude
					self.longitude = self.data.fix.longitude
					self.utc = self.data.utc
					self.climb = self.data.fix.climb
					self.speed = self.data.fix.speed
					self.altitude = self.data.fix.altitude
					self.status = status[self.data.status]
					self.online = self.data.online
					self.fix_mode = fix_mode[self.data.fix.mode]
					try:
						sat = self.data.satellites
						self.satellites = len(sat)
						self.satellites_used = self.data.satellites_used
						self.satellites_visible = 0
						#FIXME there should be a value for that in gps module already
						for i in sat:
							if i.ss > 0:
								self.satellites_visible += 1
					except AttributeError:
						self.occ.log.error("[GPS] AttributeError exception in GPS")
						pass
					self.occ.log.debug("[GPS] Event: timestamp: {}, UTC: {}, Satellites: {}, Visible: {}, Used: {}"\
								.format(time.time(), self.utc, self.satellites, self.satellites_visible,\
								self.satellites_used))
					self.occ.log.debug("[GPS] Status: {}, Online: {}, Mode: {}, Lat,Lon: {},{}, Speed: {}, Altitude: {}, Climb: {}"\
								.format(self.status, self.online, self.fix_mode, self.latitude, self.longitude,\
								self.speed, self.altitude, self.climb))
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
				self.status = status[1]
				self.online = 1
				self.fix_mode = fix_mode[2]
				time.sleep(1)

	def get_data(self):
		return (self.latitude, self.longitude, 	#0, 1
			self.altitude, self.speed,	#2, 3
			self.utc, 			#4
			self.satellites_used,		#5
			self.satellites_visible,	#6
			self.satellites, self.status,	#7, 8
			self.online, self.fix_mode,	#9, 10
			self.climb)			#11

	def __del__(self):
		self.stop()

	def stop(self):
		self.running = False
