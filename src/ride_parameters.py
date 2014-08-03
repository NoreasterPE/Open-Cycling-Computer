import math

class ride_parameters():
        def __init__(self):
                self.speed = 0
		self.speed_tenths = math.floor (10 * (self.speed - math.floor(self.speed)))
		self.heart_rate = 165
		self.heart_rate_units = "BPM"
		self.gradient = 10
		self.gradient_units = "%"
		self.cadence = 109
		self.units = "km/h"
