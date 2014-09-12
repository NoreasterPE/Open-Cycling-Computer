import gps

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

while True:
	try:
		report = session.next()
		print 'latitude ' , session.fix.latitude
		print 'longitude ' , session.fix.longitude
		print 'time utc ' , session.utc, session.fix.time
		print 'speed ' , session.fix.speed
	except KeyError:
		pass
	except KeyboardInterrupt:
		quit()
	except StopIteration:
		session = None
		print "GPSD has terminated"

