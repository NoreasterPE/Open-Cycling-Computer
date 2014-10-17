from time import strftime
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import math

class ride_parameters():
	def __init__(self, occ, simulate = False):
		self.occ = occ
		#Init sensors
		#Init gps
		#FIXME Add clean gps stop and ride_params stop
		#print "Initialising GPS"
		self.gps = gps_mtk3339(simulate)
		#print "GPS thread starting"
		self.gps.start()
		#Init pressure sensor
		self.bmp183_sensor = bmp183(simulate)

		self.params = {}
		self.p_desc = {}
		#Params of the ride
		self.params["altitude"] = 0.0
		self.params["altitude_gps"] = 0.0
		self.params["altitude_units"] = ""
		self.params["cadence"] = 0
		self.params["gradient"] = 0
		self.params["heart_rate"] = 165
		self.params["pressure"] = 1013.0
		self.params["pressure_at_sea_level"] = 1013.0
		self.params["rtc"] = ""
		self.params["speed"] = 0.0
		self.params["speed_tenths"] = 0.0
		self.params["utc"] = ""

		#Params that can be changed in Settings by user
		#FIXME Write/Read to config
		self.params["altitude_at_home"] = 89.0
		self.params["altitude_units"] = "m"
		self.params["gradient_units"] = "%"
		self.params["heart_rate_units"] = "BPM"
		self.params["pressure_units"] = "hPa"
		self.params["temperature_units"] = u'\N{DEGREE SIGN}' + "C"
		self.params["rider_weight"] = 80.0
                self.params["speed_units"] = "km/h"

		#Params description FIXME localisation
		self.p_desc["altitude_at_home"] = "Home altitude"
		self.p_desc["rider_weight"] = "Rider weight"

	def stop(self):
		self.gps.stop()
		self.bmp183_sensor.stop()

	def __del__(self):
		self.stop()

	def update_values(self):
		self.update_rtc()
		self.read_bmp183_sensor()
		self.read_gps_data()
		self.force_refresh()
		#FIXME Calc pressure only when gps altitude is known or 
		#when we're at home and the altitude is provided by user
		#self.calculate_pressure_at_sea_level()
		#FIXME Add calculations of gradient, trip time, etc

	def force_refresh(self):
		self.occ.force_refresh()

	def get_val(self, func):
		#FIXME try/except for invalid func?
		return self.params[func]

	def get_description(self, func):
		#FIXME try/except for invalid func?
		return self.p_desc[func]

	def clean_value(self, variable, empty_string = "-"):
		if not math.isnan(variable):
			return variable
		else:
			return empty_string
		
	def read_gps_data(self):
		data = self.gps.get_data()
		lat = data[0]
		lon = data[1]
		alt = data[2]
		spd = data[3]
		self.params["utc"] = data[4]

		self.params["latitude"] = self.clean_value(lat);
		self.params["longitude"] = self.clean_value(lon);
		self.params["altitude_gps"] = self.clean_value(alt);
		#FIXME optimise code to use clean_value for speed
		if not math.isnan(spd):
			sf = math.floor(spd)
			self.params["speed"] = "%.0f" % sf
			self.params["speed_tenths"] = "%.0f" % (math.floor (10 * (spd - sf)))
		else:
			self.params["speed"] = "?"
			self.params["speed_tenths"] = "-"

	def update_rtc(self):
		#FIXME proper localisation would be nice....
		self.params["date"] = strftime("%d-%m-%Y")
		self.params["time"] = strftime("%H:%M:%S")
		self.params["rtc"] = self.params["date"] + " " + self.params["time"]

	def read_bmp183_sensor(self):
		#Read pressure and temperature from BMP183
		self.bmp183_sensor.measure_pressure()
		self.params["pressure"] = "%.0f" % int(self.bmp183_sensor.pressure/100.0)
		self.params["temperature"] = "%.0f" % int(self.bmp183_sensor.temperature)
		#Set current altitude based on current pressure and calculated pressure_at_sea_level, cut to meters
		#self.params["altitude"] = int(44330*(1 - pow((self.params["pressure"]/self.params["pressure_at_sea_level"]), (1/5.255))))

	#def calculate_pressure_at_sea_level(self):
	#	#Set pressure_at_sea_level based on given altitude
	#	self.params["pressure_at_sea_level"] = round((self.params["pressure"]/pow((1 - self.params["altitude_at_home"]/44330), 5.255)), 0)
