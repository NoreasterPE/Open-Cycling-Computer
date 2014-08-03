import math

class ride_parameters():
        def __init__(self):
                self.speed = 0
		self.speed_tenths = math.floor (10 * (self.speed - math.floor(self.speed)))
