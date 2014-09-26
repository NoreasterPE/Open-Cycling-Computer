from time import strftime
from bmp183 import bmp183
import gps_mkt3339
import math

class ride_parameters():
	def __init__(self):
		self.params_changed = 0
		self.speed = 0
		self.speed_tenths = 0
		self.speed_units = ""
		self.heart_rate = 0
		self.heart_rate_units = ""
		self.gradient = 0
		self.gradient_units = ""
		self.cadence = 0
		self.altitude_at_home = 89.0
		self.pressure = 1013.0
		self.pressure_units = ""
		self.pressure_at_sea_level = 1013.0
		self.altitude = 0.0
		self.altitude_units = ""
		self.rtc = ""
		self.set_val("speed")
		self.set_val("speed_units")
		self.set_val("heart_rate")
		self.set_val("heart_rate_units")
		self.set_val("gradient")
		self.set_val("gradient_units")
		self.set_val("cadence")
		self.set_val("rtc")
		self.bmp183_sensor = bmp183()
		self.set_val("pressure")
		self.set_val("pressure_units")
		self.set_val("pressure_at_sea_level")
		self.set_val("altitude")
		self.set_val("altitude_units")
		self.set_val("altitude_at_home")
		self.set_val("temperature")
		self.set_val("temperature_units")

		#Init gps
		#FIXME Add clean gps stop and ride_params stop
		self.gps = gps_mkt3339()
		self.gps.start()

	def get_val(self, func):
		functions = {   "speed" : "%.0f" % self.speed,
				"speed_tenths" :  "%.0f" % self.speed_tenths,
				"speed_units" : self.speed_units,
				"heart_rate" : self.heart_rate,
				"heart_rate_units" : self.heart_rate_units,
				"gradient" : self.gradient,
				"gradient_units" : self.gradient_units,
				"cadence" : self.cadence,
				"rtc" : self.rtc,
				"date" : self.date,
				"time" : self.time,
				"pressure" : "%.0f" % self.pressure,
				"pressure_units" : self.pressure_units,
				"pressure_at_sea_level" : self.pressure_at_sea_level,
				"altitude" : self.altitude,
				"altitude_units" : self.altitude_units,
				"altitude_at_home" : self.altitude_at_home,
				"temperature" : self.temperature,
				"temperature_units" : self.temperature_units,
		}
		return functions[func]

	def set_val(self, func):
		functions = {   "speed" : self.set_speed,
				"speed_units" : self.set_speed_units,
				"gradient" : self.set_gradient,
				"gradient_units" : self.set_gradient_units,
				"heart_rate" : self.set_heart_rate,
				"heart_rate_units" : self.set_heart_rate_units,
				"cadence" : self.set_cadence,
				"rtc" : self.set_rtc,
				"date" : self.set_rtc,
				"time" : self.set_rtc,
				"pressure" : self.read_bmp183_sensor,
				"pressure_units" : self.set_pressure_units,
				"pressure_at_sea_level" : self.set_pressure_at_sea_level,
				"altitude" : self.read_bmp183_sensor,
				"altitude_units" : self.set_altitude_units,
				"altitude_at_home" : self.set_altitude_at_home,
				"temperature" : self.read_bmp183_sensor,
				"temperature_units" : self.set_temperature_units,
		}
		functions[func]()

	def set_speed(self):
		#Read speed from GPS
                self.speed = self.gps.speed
		#FIXME - read speed from wheel sensor
		self.speed_tenths = math.floor (10 * (self.speed - math.floor(self.speed)))
		self.params_changed = 1

	def set_speed_units(self):
                self.speed_units = "km/h"
		self.params_changed = 1

	def set_heart_rate(self):
		#Read heart rate from sensors here
		self.heart_rate = 165
		self.params_changed = 1

	def set_heart_rate_units(self):
		self.heart_rate_units = "BPM"
		self.params_changed = 1

	def set_gradient(self):
		self.gradient= 9
		self.params_changed = 1

	def set_gradient_units(self):
		self.gradient_units= "%"
		self.params_changed = 1

	def set_cadence(self):
		#Read cadence from sensors here
		self.cadence = 98
		self.params_changed = 1

	def set_rtc(self):
		#FIXME proper localisation would be nice....
		self.date = strftime("%d-%m-%Y")
		self.time = strftime("%H:%M:%S")
		self.rtc = self.date + " " + self.time
		self.params_changed = 1

	def read_bmp183_sensor(self):
		#Read pressure from BMP183
		self.bmp183_sensor.measure_pressure()
		self.pressure = self.bmp183_sensor.pressure/100.0
		self.temperature = self.bmp183_sensor.temperature
		#Set current altitude based on current pressure and calculated pressure_at_sea_level, cut to meters
		self.altitude = int(44330*(1 - pow((self.pressure/self.pressure_at_sea_level), (1/5.255))))
		self.params_changed = 1

	def set_pressure_units(self):
		self.pressure_units = "hPa"
		self.params_changed = 1

	def set_pressure_at_sea_level(self):
		#Set pressure_at_sea_level based on given altitude
		self.pressure_at_sea_level = round((self.pressure/pow((1 - self.altitude_at_home/44330), 5.255)), 0)
		self.params_changed = 1

	def set_altitude_units(self):
		self.altitude_units = "m"
		self.params_changed = 1

	def set_altitude_at_home(self):
 #FIXME Ask user for home altitude
		self.altitude_at_home = 89.0
		self.params_changed = 1

	def set_temperature_units(self):
		self.temperature_units = u"\u2103"
		self.params_changed = 1

