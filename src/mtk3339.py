import operator
import serial
import os
import time

class mt3339():
	def __init__(self, device):
		#NMEA sentences handled by this class
		self.valid_commands = { "CMD_HOT_START"		: 101,
					"CMD_WARM_START"	: 102,
					"CMD_COLD_START"	: 103,
					"CMD_FULL_COLD_START"	: 104,
					"SET_NMEA_UPDATERATE"	: 220,
					"SET_NMEA_BAUDRATE"	: 251,
					"API_SET_FIX_CTL"	: 300,
					"API_SET_NMEA_OUTPUT"	: 314,
					"SET_NAV_SPEED_TRESHOLD": 386,
		}
		#Valid baudrates for GPS serial port
		self.baudrates = 0, 4800, 9600, 14400, 19200, 38400, 57600, 115200
		#NMEA sentence update rate in ms
		self.update_rate = range(100, 10000)
		#NMEA sentence output frequency compared to position fix
		self.nmea_output_frequency = range(0, 6)
		#Valid nav speed tresholds
		self.speed_treshold = "0", "0.2", "0.4", "0.6", "0.8", "1.0", "1.5", "2.0" #m/s

		self.device = device
		self.baudrate = 9600

	def nmea_checksum(self, sentence):
		checksum = reduce(operator.xor, (ord(s) for s in sentence), 0)
		return checksum

	def create_nmea_command(self, command, params):
		if command not in self.valid_commands:
			return -1
		else:
			command_pmtk = "PMTK" + unicode(self.valid_commands[command]) + unicode(params)
			checksum = "{:02X}".format(self.nmea_checksum(command_pmtk))
			nmea_command = "".join(["$", command_pmtk, "*", checksum, "\r\n"])
			return nmea_command

	def set_baudrate(self, baudrate = 0):
	#Set baudrates for GPS serial port, 0 means reset to default speed
		if baudrate not in self.baudrates:
			return -1
		else:
			self.baudrate = baudrate
			command = "SET_NMEA_BAUDRATE"
			params = "," + unicode(baudrate)
			nmea_command = self.create_nmea_command(command, params)
			self.send_command(nmea_command)
			return 0

	def set_nmea_update_rate(self, rate = 1000):
	#set NMEA sentence update rate in ms
		if rate not in self.update_rate:
			return -1
		else:
			command = "SET_NMEA_UPDATERATE"
			params = "," + unicode(rate)
			nmea_command = self.create_nmea_command(command, params)
			self.send_command(nmea_command)
			return 0

	def set_fix_update_rate(self, rate = 1000):
	#set Position fix update rate in ms. Must by greater than 200 ms
		if rate < 200:
			return -1
		else:
			command = "API_SET_FIX_CTL"
			params = "," + unicode(rate) + ",0,0,0,0"
			nmea_command = self.create_nmea_command(command, params)
			self.send_command(nmea_command)
			return 0

	def set_nav_speed_threshold(self, treshold = 0):
	#set speed treshold. If speed is below the treshold the output position will stay frozen
		t = unicode(treshold)
		if t not in self.speed_treshold:
			return -1
		else:
			command = "SET_NAV_SPEED_TRESHOLD"
			params = "," + t
			nmea_command = self.create_nmea_command(command, params)
			self.send_command(nmea_command)
			return 0

	def hot_start(self):
	#hot restart - use all data from NV store
		command = "CMD_HOT_START"
		params = ""
		nmea_command = self.create_nmea_command(command, params)
		self.send_command(nmea_command)
		return 0

	def warm_start(self):
	#warm restart - don't use ephemeris at restart
		command = "CMD_WARM_START"
		params = ""
		nmea_command = self.create_nmea_command(command, params)
		self.send_command(nmea_command)
		return 0

	def cold_start(self):
	#cold start - don't use time, position, almanacs and ephemeris at restart
		command = "CMD_COLD_START"
		params = ""
		nmea_command = self.create_nmea_command(command, params)
		self.send_command(nmea_command)
		return 0

	def cold_reset(self):
	#reset GPS receiver to factory defaults
		command = "CMD_FULL_COLD_START"
		params = ""
		nmea_command = self.create_nmea_command(command, params)
		self.send_command(nmea_command)
		return 0

	def set_nmea_output(self, gll = 1, rmc = 1, vtg = 1, gga = 1, gsa = 1, gsv = 1):
	#set NMEA output frequency. 0 - disable, 1 - once per position fix, 2 every second fix..
	#That function ignores PMTKCHN interval - GPS channes status
		#Types of NMEA sentences:
		# http://aprs.gids.nl/nmea/#gll
		# http://aprs.gids.nl/nmea/#rmc
		# http://aprs.gids.nl/nmea/#vtg
		# http://aprs.gids.nl/nmea/#gga
		# http://aprs.gids.nl/nmea/#gsa
		# http://aprs.gids.nl/nmea/#gsv
		if gll not in self.nmea_output_frequency:
				return -1
		if rmc not in self.nmea_output_frequency:
				return -1
		if vtg not in self.nmea_output_frequency:
				return -1
		if gga not in self.nmea_output_frequency:
				return -1
		if gsa not in self.nmea_output_frequency:
				return -1
		if gsv not in self.nmea_output_frequency:
				return -1
		command = "API_SET_NMEA_OUTPUT"
		params = "," + unicode(gll) + "," + unicode(rmc) + "," + unicode(vtg)\
			+ "," + unicode(gga) + "," + unicode(gsa) + "," + unicode(gsv)\
			+ ",0,0,0,0,0,0,0,0,0,0,0,0,0"
		nmea_command = self.create_nmea_command(command, params)
		self.send_command(nmea_command)
		return 0

	def send_command(self, nmea_command):
		ser = serial.Serial(port = self.device, baudrate = self.baudrate, timeout=3)
		time.sleep(0.1)
		ser.write(nmea_command);
		time.sleep(0.1)
		ser.close()

#Example commands:
#gps = mt3339("/dev/ttyAMA0")
#gps.cold_start()
#gps.warm_start()
#gps.hot_start()
#gps.set_baudrate(115200)
#gps.set_nmea_update_rate(1000)
#gps.set_nav_speed_threshold(1.5)
#gps.set_nmea_output(gll = 0, rmc = 1, vtg = 0, gga = 5, gsa = 5, gsv = 5)

