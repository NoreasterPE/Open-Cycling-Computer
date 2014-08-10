from time import strftime
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
		self.rtc = ""
		self.set_val("speed")
		self.set_val("speed_units")
		self.set_val("heart_rate")
		self.set_val("heart_rate_units")
		self.set_val("gradient")
		self.set_val("gradient_units")
		self.set_val("cadence")
		self.set_val("rtc")

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
		}
		functions[func]()

	def set_speed(self):
		#Read speed from GPS or sensors here
                self.speed = 43.2
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

