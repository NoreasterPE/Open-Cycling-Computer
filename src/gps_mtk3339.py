#! /usr/bin/python
 
from gps import *
from time import *
import os
import threading
import time
 
class gps_mtk3339(threading.Thread):
	#Class for gps mtk3339 as sold by Adafruit

	def __init__(self):
		threading.Thread.__init__(self)
		self.present = False
		self.speed = float('nan')
		try:
			#Add check for running gpsd. Restart if missing. Consider watchdog thread to start gpsd
			self.data = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
			self.present = True
		except:
			#can not talk to gps
			self.present = False
	def run(self):
		if self.present:
			self.running = True
			while self.running:
				self.data.next()
				#FIXME filter for nan value and set to 0 or --
				self.latitude = self.data.fix.latitude
				self.longitude = self.data.fix.longitude
				self.utc = self.data.utc #Add to rp module
				self.climb = self.data.fix.climb #Add to rp module
				self.speed = self.data.fix.speed
				self.altitude = self.data.fix.altitude
	def get_data(self):
		return (self.latitude, self.longitude, 	#0, 1
			self.altitude, self.speed,	#2, 3
			self.utc)			#4

	def __del__(self):
		self.stop()

	def stop(self):
		self.running = False
 
if __name__ == '__main__':
	gps = gps_mtk3339()
	gps.start()
	try:
		while True:
			os.system('clear')
			data = gps.get_data()
			print 'latitude    ' , data[0]
			print 'longitude   ' , data[1]
			print 'time utc    ' , gps.data.utc
			print 'fix time    ' , gps.data.fix.time
			print 'altitude (m)' , data[2]
			print 'eps         ' , gps.data.fix.eps
			print 'epx         ' , gps.data.fix.epx
			print 'epv         ' , gps.data.fix.epv
			print 'ept         ' , gps.data.fix.ept
			print 'speed (m/s) ' , data[3]
			print 'climb       ' , gps.data.fix.climb
			print 'track       ' , gps.data.fix.track
			print 'mode        ' , gps.data.fix.mode
			print 'sats        ' , gps.data.satellites

			time.sleep(1)
 
	except (KeyboardInterrupt, SystemExit):
	#FIXME possibly required on shutdown
		gps.stop()
		gps.join()
