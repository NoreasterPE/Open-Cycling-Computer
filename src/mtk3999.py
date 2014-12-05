import operator

class mt3k339():
	def __init__(self, device):
		#NMEA sentences handled by this class
		self.valid_commands = { "SET_NMEA_BAUDRATE"	   	: 251,
					"SET_NMEA_UPDATERATE"	   	: 220,
					"CMD_FULL_COLD_START"	   	: 104,
					"SET_NAV_SPEED_TRESHOLD"	: 386,
		}
		#Valid baudrates for GPS serial port
		self.baudrates = 0, 4800, 9600, 14400, 19200, 38400, 57600, 115200
		#NMEA sentence update rate in ms
		self.update_rate = range(100, 10000)
		#Valid nav speed tresholds
		self.speed_treshold = "0", "0.2", "0.4", "0.6", "0.8", "1.0", "1.5", "2.0" #m/s

		self.device = device

	def nmea_checksum(self, sentence):
		checksum = reduce(operator.xor, (ord(s) for s in sentence), 0)
		return checksum

	def create_nmea_command(self, command, params):
		if command not in self.valid_commands:
			return -1
		else:
			command_pmtk = "PMTK" + unicode(self.valid_commands[command]) + unicode(params)
			checksum = "{:02x}".format(self.nmea_checksum(command_pmtk))
			nmea_command = "".join(["$", command_pmtk, "*", checksum, "\n\r"])
			return nmea_command

	def set_baudrate(self, baudrate = 0):
	#Set baudrates for GPS serial port, 0 means reset to default speed
		if baudrate not in self.baudrates:
			return -1
		else:
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

	def set_nav_speed_threshold(self, treshold = 0):
	#set speed treshold. If speed is below the treshold the output  
position will stay frozen
		t = unicode(treshold)
		if t not in self.speed_treshold:
			return -1
		else:
			command = "SET_NAV_SPEED_TRESHOLD"
			params = "," + t
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

	def send_command(self, nmea_command):
		print nmea_command
		#open_serial
		#send command
		#close_serial

gps = mt3339("/dev/ttyAMA0")
gps.cold_reset()
gps.set_baudrate()
gps.set_baudrate(57600)
gps.set_baudrate(115200)
gps.set_nmea_update_rate(1000)
gps.set_nmea_update_rate(200)
gps.set_nmea_update_rate(100)
gps.set_nav_speed_threshold(0)
gps.set_nav_speed_threshold(0.2)
gps.set_nav_speed_threshold(2.0)

