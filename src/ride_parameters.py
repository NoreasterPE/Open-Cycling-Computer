from time import strftime
import math

class ride_parameters():
        def __init__(self):
		self.params_changed = 0
                self.set_speed()
                self.set_speed_units()
		self.set_heart_rate()
		self.set_heart_rate_units()
		self.set_gradient()
		self.set_gradient_units()
		self.set_cadence()
		self.set_rtc()

	def get_val(self, func):
		functions = {   "speed" : "%.0f" % self.speed,
				"speed_tenths" :  "%.0f" % self.speed_tenths,
				"speed_units" : self.speed_units,
				"heart_rate" : self.heart_rate,
				"heart_rate_units" : self.heart_rate_units,
				"gradient" : self.gradient,
				"gradient_units" : self.gradient_units,
				"cadence" : self.cadence,
				"date" : self.date,
				"time" : self.time,
		}
		return functions[func]

	def set_val(self, func):
		functions = {   "speed" : set_speed,
				"speed_units" : set_speed_units,
				"gradient" : set_gradient,
				"gradient_units" : set_gradient_units,
				"heart_rate" : set_heart_rate,
				"heart_rate_units" : set_heart_rate_units,
				"cadence" : set_cadence,
		}

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

