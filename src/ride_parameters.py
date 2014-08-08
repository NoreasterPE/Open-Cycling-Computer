import math

class ride_parameters():
        def __init__(self):
                self.speed = 43.2
		self.speed_tenths = math.floor (10 * (self.speed - math.floor(self.speed)))
		self.heart_rate = 165
		self.heart_rate_units = "BPM"
		self.gradient = 10
		self.gradient_units = "%"
		self.cadence = 109
		self.speed_units = "km/h"

	def get_val(self, func):
		functions = {   "speed" : "%.0f" % self.speed,
				"speed_tenths" :  "%.0f" % self.speed_tenths,
				"speed_units" : self.speed_units,
				"heart_rate" : self.heart_rate,
				"heart_rate_units" : self.heart_rate_units,
				"gradient" : self.gradient,
				"gradient_units" : self.gradient_units,
				"cadence" : self.cadence,
		}
		return functions[func]
