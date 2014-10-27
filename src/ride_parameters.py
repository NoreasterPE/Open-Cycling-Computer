from time import strftime
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import math
import quantities as q

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

		self.p_raw = {}
		self.p_raw_units = {}
		self.params = {}
		self.p_desc = {}
		self.p_editable = {}
		self.units = {}
		self.units_allowed = {}
		#Internal params of the ride.
		self.p_raw["altitude"] = "-"
		self.p_raw["altitude_gps"] = "-"
		self.p_raw["altitude_at_home"] = "-"
		self.p_raw["cadence"] = "-"
		self.p_raw["gradient"] = "-"
		self.p_raw["heart_rate"] = "-"
		self.p_raw["odometer"] = "-"
		self.p_raw["pressure"] = "-"
		self.p_raw["pressure_at_sea_level"] = "-"
		self.p_raw["rider_weight"] = "-"
		self.p_raw["rtc"] = ""
		self.p_raw["speed"] = float("nan")
		self.p_raw["utc"] = ""

		#Internal units
		self.p_raw_units["altitude_at_home"] = "m"
		self.p_raw_units["altitude_gps"] = "m"
		self.p_raw_units["latitude"] = ""
		self.p_raw_units["longitude"] = ""
		self.p_raw_units["odometer"] = "m"
		self.p_raw_units["rider_weight"] = "kg"

		#Params of the ride ready for rendering.
		self.params["altitude"] = "-"
		self.params["altitude_gps"] = "-"
		self.params["cadence"] = "-"
		self.params["gradient"] = "-"
		self.params["heart_rate"] = "-"
		self.params["latitude"] = "-"
		self.params["longitude"] = "-"
		self.params["pressure"] = "-"
		self.params["pressure_at_sea_level"] = "-" 
		self.params["rtc"] = ""
		self.params["speed"] = "-"
		self.params["speed_tenths"] = "-"
		self.params["utc"] = ""

		#Params that can be changed in Settings by user
		#FIXME Write/Read to config
		self.params["altitude_at_home"] = 89.0
		self.params["odometer"] = 0.0
		self.params["rider_weight"] = 80.0

		#Units - name has to be identical as in params
		self.units["altitude"] = "m"
		self.units["altitude_at_home"] = "m"
		self.units["altitude_gps"] = "m"
		self.units["gradient"] = "%"
		self.units["heart_rate"] = "BPM"
		self.units["latitude"] = ""
		self.units["longitude"] = ""
		self.units["odometer"] = "km"
		self.units["pressure"] = "hPa"
		self.units["rider_weight"] = "kg"
		self.units["speed"] = "km/h"

		#Allowed units - user can switch between those when editing value 
		self.units_allowed["odometer"] = ["km", "mi"]
		self.units_allowed["rider_weight"] = ["kg", "st", "lb"]

		#FIXME python-quantities won't like those deg C
		self.units["temperature"] = u'\N{DEGREE SIGN}' + "C"

		#Params description FIXME localisation
		self.p_desc["altitude_at_home"] = "Home altitude"
		self.p_desc["odometer"] = "Odometer" 
		self.p_desc["odometer_units"] = "Odometer units" 
		self.p_desc["rider_weight"] = "Rider weight"
		self.p_desc["rider_weight_units"] = "Rider weight units"

		#Define id a param is editable FIXME editor type - number, calendar, unit, etc.
		self.p_editable["altitude_at_home"] = 1
		self.p_editable["odometer"] = 1 
		self.p_editable["odometer_units"] = 0
		self.p_editable["rider_weight"] = 1
		self.p_editable["rider_weight_units"] = 0

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
		self.update_params()
		#FIXME Calc pressure only when gps altitude is known or 
		#when we're at home and the altitude is provided by user
		#self.calculate_pressure_at_sea_level()
		#FIXME Add calculations of gradient, trip time, etc

	def force_refresh(self):
		self.occ.force_refresh()

	def get_val(self, func):
		#FIXME try/except for invalid func?
		if func.endswith("_units"):
			return self.units[func[:-6]]
		else:
			return self.params[func]

	def get_unit(self, func):
		#FIXME try/except for invalid func?
		if func.endswith("_units"):
			return None
		else:
			return self.units[func]

	def get_internal_unit(self, func):
		#FIXME try/except for invalid func?
		if func.endswith("_units"):
			return None
		else:
			return self.p_raw_units[func]

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
		self.p_raw["utc"] = data[4]
		self.p_raw["latitude"] = self.clean_value(lat);
		self.p_raw["longitude"] = self.clean_value(lon);
		self.p_raw["altitude_gps"] = self.clean_value(alt);

	def update_params(self):
		self.update_param("latitude", "%.4f")
		self.update_param("longitude", "%.4f")
		self.update_param("altitude_gps", "%.0f")

		#FIXME optimise code to use clean_value for speed
		spd = self.p_raw["speed"]
		if not math.isnan(spd):
			spd_f = math.floor(spd)
			self.params["speed"] = "%.0f" % spd_f
			self.params["speed_tenths"] = "%.0f" % (math.floor (10 * (spd - spd_f)))
		else:
			self.params["speed"] = "-"
			self.params["speed_tenths"] = "-"

		self.params["utc"] = self.p_raw["utc"]

		self.update_param("odometer", "%.1f")
		self.update_param("rider_weight", "%.1f")

	def update_param(self, param_name, formatting):
		iu = self.get_internal_unit(param_name)
		try:
			v = q.Quantity(self.p_raw[param_name], iu)
			v.units = self.get_unit(param_name)
			self.params[param_name] = float(formatting % v.item())
		except TypeError:
			#Value conversion failed, so don't change anything
			#print "TypeError: update_param exception: ", param_name, " params[] =", self.params[param_name], " p_raw[] =", self.p_raw[param_name]
			pass
		except ValueError:
			print "ValueError: update_param exception: ", param_name, " params[] =", self.params[param_name], " p_raw[] =", self.p_raw[param_name]
			

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
