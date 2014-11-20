#! /usr/bin/python
 
from gps import *
import os
import threading
import time

NaN = float('nan')
fix_mode = { 1 : "No fix",
	     2 : "Fix 2D",
	     3 : "Fix 3D"
}

NMEA_UPDATE_5HZ = "$PMTK220,200*2C"
NMEA_UPDATE_10HZ = "$PMTK220,100*2F"
#FIX_CTL_1HZ = "$PMTK300,1000,0,0,0,0*1C"
FIX_CTL_5HZ = "$PMTK300,200,0,0,0,0*2F"
SET_BAUD_57600 = "$PMTK251,57600*2C"

class gps_mtk3339(threading.Thread):
	#Class for gps mtk3339 as sold by Adafruit

	def __init__(self, occ = None, simulate = False):
		threading.Thread.__init__(self)
		self.occ = occ
		self.simulate = simulate
		self.altitude = 0
		self.climb = 0
		self.fix_mode = ""
		self.lag = 0
		self.latitude = NaN
		self.longitude = NaN
		self.present = False
		self.satellites = 0
		self.satellites_used = 0
		self.speed = NaN
		self.utc = None
		self.set_time = True
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
						#FIXME Fails sometimes with ImportError from gps.py - see TODO 21 [IN TESTING]
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
					self.fix_mode = fix_mode[self.data.fix.mode]
					self.fix_time = self.data.fix.time
					# Convert string time value to float if necessary. Snipped by Adafruit
					if not isinstance(self.fix_time, float):
						# self.data.fix.time is a string, so parse it to get the float time value.
						self.fix_time = time.mktime(time.strptime(self.data.fix.time, '%Y-%m-%dT%H:%M:%S.%fZ'))
					self.lag = timestamp - self.fix_time
					self.occ.log.debug("[GPS] timestamp to fix time delta: {}".format(self.lag))
					if self.set_time:
						if (self.utc is not None):
							if (len(self.utc) > 5):
								self.set_system_time()
					try:
						sat = self.data.satellites
						self.satellites = len(sat)
						self.satellites_used = self.data.satellites_used
					except AttributeError:
						self.occ.log.error("[GPS] AttributeError exception in GPS")
						pass
					self.occ.log.debug("[GPS] timestamp: {}, fix time: {}, UTC: {}, Satellites: {}, Used: {}"\
								.format(timestamp, self.fix_time, self.utc, self.satellites,\
								 self.satellites_used))
					self.occ.log.debug("[GPS] Mode: {}, Lat,Lon: {},{}, Speed: {}, Altitude: {}, Climb: {}"\
								.format(self.fix_mode, self.latitude, self.longitude,\
								self.speed, self.altitude, self.climb))
			else:
				self.latitude = 52.0001
				self.longitude = -8.0001
				self.utc = "utc"
				self.climb = 0.2
				self.speed = 9.99
				self.altitude = 50.0
				self.satellites = 10
				self.satellites_used = 4
				self.fix_mode = fix_mode[2]
				time.sleep(1)

	def get_data(self):
		return (self.latitude, self.longitude, 	#0, 1
			self.altitude, self.speed,	#2, 3
			self.utc, 			#4
			self.satellites_used,		#5
			self.satellites, self.fix_mode,	#6, 7
			self.climb, self.lag)		#8, 9

	def __del__(self):
		self.stop()

	def stop(self):
		self.running = False

	#FIXME temporary location
	def set_system_time(self):
		self.occ.log.debug("[GPS] Setting UTC system time to {}".format(self.utc))
		command = 'date -u --set={} "+%Y-%m-%dT%H:%M:%S.000Z" 2>&1 > /dev/null'.format(self.utc)
		ret = os.system(command)
		if ret == 0:
			self.set_time = False
