from time import strftime
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import math

class ride_parameters():
	def __init__(self, simulate = False):
		#Init sensors
		#Init gps
		#FIXME Add clean gps stop and ride_params stop
		#print "Initialising GPS"
		self.gps = gps_mtk3339(simulate)
		#print "GPS thread starting"
		self.gps.start()
		#Init pressure sensor
		self.bmp183_sensor = bmp183(simulate)
		self.params_changed = 0

		self.params = {}
		#Params of the ride
		self.params["altitude"] = 0.0
		self.params["altitude_gps"] = 0.0
		self.params["altitude_units"] = ""
		self.params["cadence"] = 0
		self.params["gradient"] = 0
		self.params["heart_rate"] = 0
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
		self.params["heart_rate"] = 165
		self.params["heart_rate_units"] = "BPM"
		self.params["pressure_units"] = "hPa"
		self.params["temperature_units"] = u'\N{DEGREE SIGN}' + "C"
		self.params["rider_weight"] = 80.0
                self.params["speed_units"] = "km/h"

		#Helpers for editing values
		self.params["ed_value"] = None
		self.params["ed_original_value"] = None
		self.params["ed_value_description"] = None
		self.params["ed_variable"] = None

	def stop(self):
		self.gps.stop()
		self.bmp183_sensor.stop()

	def __del__(self):
		self.stop()

	def update_values(self):
		self.update_rtc()
		self.read_bmp183_sensor()
		self.read_gps_data()
		#FIXME Add calculations of gradient, trip time, etc

	def get_val(self, func):
		#FIXME try/except for invalid func?
		print func, ":", self.params[func]
		return self.params[func]

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
		self.params_changed = 1

	def update_rtc(self):
		#FIXME proper localisation would be nice....
		self.params["date"] = strftime("%d-%m-%Y")
		self.params["time"] = strftime("%H:%M:%S")
		self.params["rtc"] = self.params["date"] + " " + self.params["time"]
		self.params_changed = 1

	def read_bmp183_sensor(self):
		#Read pressure and temperature from BMP183
		self.bmp183_sensor.measure_pressure()
		self.params["pressure"] = "%.0f" % int(self.bmp183_sensor.pressure/100.0)
		self.params["temperature"] = "%.0f" % int(self.bmp183_sensor.temperature)
		#Set current altitude based on current pressure and calculated pressure_at_sea_level, cut to meters
		#self.params["altitude"] = int(44330*(1 - pow((self.params["pressure"]/self.params["pressure_at_sea_level"]), (1/5.255))))
		self.params_changed = 1

	def set_pressure_at_sea_level(self):
		#Set pressure_at_sea_level based on given altitude
		self.params["pressure_at_sea_level"] = round((self.pressure/pow((1 - self.altitude_at_home/44330), 5.255)), 0)
		self.params_changed = 1

	def accept_edit(self):
		self.params[self.params["ed_variable"]] = self.params["ed_value"]
		self.params_changed = 1
