#! /usr/bin/python

from gps_mtk3339 import gps_mtk3339
import time
import os

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
			print 
			sat = gps.data.satellites
			l = len(sat)
			total_sat_used = 0
			total_sat_visi = 0
			for i in sat:
				print i
				if i.used:
					total_sat_used += 1
				if i.ss > 0:
					total_sat_visi += 1

			print 
			print "No of satellites: {} / {} / {}".format(total_sat_used, total_sat_visi, l)

			time.sleep(1)
 
	except (KeyboardInterrupt, SystemExit):
	#FIXME possibly required on shutdown
		gps.stop()
		gps.join()
