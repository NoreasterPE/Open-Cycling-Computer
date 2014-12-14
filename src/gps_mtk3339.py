#! /usr/bin/python
 
from gps import *
import logging
import mtk3339
import os
import serial
import threading
import time

NaN = float('nan')
fix_mode = { 0 : "No data",
	     1 : "No fix",
	     2 : "Fix 2D",
	     3 : "Fix 3D"
}

class gps_mtk3339(threading.Thread):
	#Class for gps mtk3339 as sold by Adafruit

	def __init__(self, simulate = False):
		threading.Thread.__init__(self)
		self.l = logging.getLogger('system')
		self.simulate = simulate
		self.restart_gps = False
		if not self.simulate:
			ser = mtk3339.mt3339("/dev/ttyAMA0")
			ser.set_baudrate(115200)
			ser.set_fix_update_rate(1000)
			ser.set_nmea_update_rate(1000)
			#ser.set_nmea_output(gll = 0, rmc = 1, vtg = 0, gga = 5, gsa = 5, gsv = 5)
			ser.set_nmea_output(gll = 0, rmc = 1, vtg = 0, gga = 1, gsa = 5, gsv = 5)
		self.altitude = NaN
		self.climb = NaN
		self.fix_mode = ""
		self.latitude = NaN
		self.longitude = NaN
		self.present = False
		self.satellites = 0
		self.satellitesused = 0
		self.speed = NaN
		self.utc = None
		self.set_time = True
		self.time_adjustment_delta = 0
		if not self.simulate:
			self.gpsd_link_init()
		else:
			self.present = True

	def gpsd_link_init(self):
		try:
			#FIXME Add check for running gpsd. Restart if missing. Consider watchdog thread to start gpsd
			#FIXME Check how that reacts for missing gps hardware
			self.data = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
			self.present = True
		except:
			self.l.error("[GPS] Cannot talk to GPS")
			self.present = False

	def restart_gpsd(self):
		command = "service gpsd restart"
		ret = os.system(command)
		if ret == 0:
			self.l.info("[GPS] gpsd restarted succesfully")
		self.restart_gps = False
		self.gpsd_link_init()
		time.sleep(3)

	def run(self):
		#FIXME split it into functions - lines are too long
		if self.present:
			self.running = True
			if not self.simulate:
				while self.running:
					if self.restart_gps:
						self.restart_gpsd()
					self.process_gps()
			else:
				self.latitude = 52.0001
				self.longitude = -8.0001
				self.utc = "utc"
				self.climb = 0.2
				self.speed = 9.99
				self.altitude = 50.0
				self.satellites = 10
				self.satellitesused = 4
				self.fix_mode = fix_mode[2]
				time.sleep(1)

	def process_gps(self):
		timestamp = time.time()
		self.l.debug("[GPS] timestamp: {}, running: {},".format(timestamp, self.running))
		gps_data_available = False
		try:
			#FIXME Fails sometimes with ImportError from gps.py - see TODO 21 [IN TESTING]
			self.data.next()
			data = self.data
			gps_data_available = True
		except StopIteration:
			self.l.error("[GPS] StopIteration exception in GPS. Restarting GPS in 10 s")
			#FIXME Reinit gps after a delay (from RP?) as restarting gpsd doesn't help
			#so this need to be in the loop as well: self.data = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
			time.sleep(10)
			self.restart_gps = True
			pass
		if gps_data_available:
			self.latitude = data.fix.latitude
			self.longitude = data.fix.longitude
			self.utc = data.utc
			self.climb = data.fix.climb
			self.speed = data.fix.speed
			self.altitude = data.fix.altitude
			self.fix_mode = fix_mode[data.fix.mode]
			if isinstance(data.fix.time, float):
				self.fix_time = data.fix.time
			else:
				#Workaround for python bug
				#ImportError: Failed to import _strptime because the import lock is held by another thread.
				try:
					#self.data.fix.time is a string, so parse it to get the float time value.
					self.fix_time = time.mktime(time.strptime(data.fix.time, '%Y-%m-%dT%H:%M:%S.%fZ'))
				except ImportError:
					self.l.critical("[GPS] self.fix_time {}".format(self.fix_time))
					pass
			if self.set_time:
				if (self.utc is not None):
					if (len(self.utc) > 5):
						self.set_system_time()
			try:
				sat = self.data.satellites
				self.satellites = len(sat)
				self.satellitesused = self.data.satellites_used
			except AttributeError:
				self.l.error("[GPS] AttributeError exception in GPS")
				pass
			self.l.debug("[GPS] timestamp: {}, fix time: {}, UTC: {}, Satellites: {}, Used: {}"\
						.format(timestamp, self.fix_time, self.utc, self.satellites,\
						 self.satellitesused))
			self.l.debug("[GPS] Mode: {}, Lat,Lon: {},{}, Speed: {}, Altitude: {}, Climb: {}"\
						.format(self.fix_mode, self.latitude, self.longitude,\
						self.speed, self.altitude, self.climb))
		else:
			self.l.debug("[GPS] Setting null values to GPS params")
			self.latitude = NaN
			self.longitude = NaN
			self.utc = None
			self.climb = NaN
			self.speed = NaN
			self.altitude = NaN
			self.fix_mode = fix_mode[1]
			self.fix_time = NaN
			self.satellites = 0
			self.satellitesused = 0

	def get_data(self):
		return (self.latitude, self.longitude, 	#0, 1
			self.altitude, self.speed,	#2, 3
			self.utc, 			#4
			self.satellitesused,		#5
			self.satellites, self.fix_mode,	#6, 7
			self.climb)			#8

	def __del__(self):
		self.stop()

	def stop(self):
		self.running = False

	def set_system_time(self):
		tt_before = time.time()
		self.l.error("[GPS] time.time before {}".format(tt_before))
		self.l.debug("[GPS] Setting UTC system time to {}".format(self.utc))
		command = 'date -u --set={} "+%Y-%m-%dT%H:%M:%S.000Z" 2>&1 > /dev/null'.format(self.utc)
		ret = os.system(command)
		if ret == 0:
			self.set_time = False
			tt_after = time.time()
			self.time_adjustment_delta = tt_before - tt_after
			self.l.error("[GPS] time.time after {}".format(tt_after))
			self.l.error("[GPS] time.time delta {}".format(self.time_adjustment_delta))

