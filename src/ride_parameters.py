from time import strftime
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import math
import time
import quantities as q

class ride_parameters():
	def __init__(self, occ, simulate = False):
		self.occ = occ
		self.occ.log.info("[RP] Initialising GPS")
		self.gps = gps_mtk3339(occ, simulate)
		self.occ.log.info("[RP] Starting GPS thread")
		self.gps.start()
		self.occ.log.info("[RP] Initialising bmp183 sensor")
		self.bmp183_sensor = bmp183(occ, simulate)
		self.bmp183_first_run = True
		self.occ.log.info("[RP] Starting BMP thread")
		self.bmp183_sensor.start()

		self.p_desc = {}
		self.p_editable = {}
		self.p_format = {}
		self.p_raw = {}
		self.p_raw_units = {}
		self.params = {}
		self.units = {}
		self.units_allowed = {}

		#Internal params of the ride.
		self.p_raw["time_stamp"] = time.time()
		#Time delta since last p_raw update
		self.p_raw["dtime"] = 1

		self.p_raw["altitude"] = 0
		self.p_raw["altitude_home"] = 0
		self.p_raw["altitude_gps"] = 0
		self.p_raw["cadence"] = 0
		self.p_raw["climb"] = 0
		self.p_raw["distance"] = 0
		self.p_raw["gps_fix"] = ""
		self.p_raw["gradient"] = 0
		self.p_raw["heart_rate"] = 0
		self.p_raw["latitude"] = 0
		self.p_raw["longitude"] = 0
		self.p_raw["odometer"] = 0
		self.p_raw["pressure"] = 0
		self.p_raw["pressure_at_sea_level"] = 0
		self.p_raw["rider_weight"] = 0
		self.p_raw["ride_time"] = 0
		self.p_raw["ride_time_total"] = 0
		self.p_raw["rtc"] = ""
		self.p_raw["satellites"] = 0
		self.p_raw["satellites_used"] = 0
		self.p_raw["speed"] = 0
		self.p_raw["speed_average"] = 0
		self.p_raw["speed_gps"] = 0
		self.p_raw["speed_max"] = 0
		self.p_raw["temperature"] = 0
		self.p_raw["temperature_average"] = 0
		self.p_raw["temperature_min"] = float("inf")
		self.p_raw["temperature_max"] = float("-inf")
		self.p_raw["time_on"] = 0.0001 #Avoid DIV/0
		self.p_raw["utc"] = ""

		#System params
		#Maximum allowable temperature change between measurements. If measurement differ more than delta they are ignored.
		self.p_raw["temperature_max_delta"] = 10 #degC
		self.p_raw["pressure_max_delta"] = 1 #hPa

		#Internal units
		self.p_raw_units["altitude"] = "m"
		self.p_raw_units["altitude_home"] = "m"
		self.p_raw_units["altitude_gps"] = "m"
		self.p_raw_units["distance"] = "m"
		self.p_raw_units["climb"] = "m/s"
		self.p_raw_units["gps_fix"] = ""
		self.p_raw_units["latitude"] = ""
		self.p_raw_units["longitude"] = ""
		self.p_raw_units["odometer"] = "m"
		self.p_raw_units["pressure"] = "hPa"
		self.p_raw_units["rider_weight"] = "kg"
		self.p_raw_units["ride_time"] = "s"
		self.p_raw_units["ride_time_total"] = "s"
		self.p_raw_units["satellites"] = ""
		self.p_raw_units["satellites_used"] = ""
		self.p_raw_units["speed"] = "m/s"
		self.p_raw_units["speed_average"] = "m/s"
		self.p_raw_units["speed_gps"] = "m/s"
		self.p_raw_units["speed_max"] = "m/s"
		self.p_raw_units["temperature"] = "C"
		self.p_raw_units["temperature_average"] = "C"
		self.p_raw_units["temperature_min"] = "C"
		self.p_raw_units["temperature_max"] = "C"
		self.p_raw_units["time_on"] = "s"

		#Params of the ride ready for rendering.
		self.params["altitude"] = "-"
		self.params["altitude_home"] = "-"
		self.params["altitude_gps"] = "-"
		self.params["cadence"] = "-"
		self.params["climb"] = "-"
		self.params["distance"] = 0
		self.params["gps_fix"] = "-"
		self.params["gradient"] = "-"
		self.params["heart_rate"] = "-"
		self.params["latitude"] = "-"
		self.params["longitude"] = "-"
		self.params["odometer"] = 0.0
		self.params["pressure"] = "-"
		self.params["pressure_at_sea_level"] = "-" 
		self.params["rtc"] = ""
		self.params["rider_weight"] = 80.0
		self.params["ride_time"] = ""
		self.params["ride_time_hms"] = ""
		self.params["ride_time_total"] = ""
		self.params["ride_time_total_hms"] = ""
		self.params["satellites"] = "-"
		self.params["satellites_used"] = "-"
		self.params["speed"] = "-"
		self.params["speed_digits"] = "-"
		self.params["speed_tenths"] = "-"
		self.params["speed_average"] = "-"
		self.params["speed_average_digits"] = "-"
		self.params["speed_average_tenths"] = "-"
		self.params["speed_max"] = "-"
		self.params["speed_max_digits"] = "-"
		self.params["speed_max_tenths"] = "-"
		self.params["temperature"] = ""
		self.params["temperature_average"] = ""
		self.params["temperature_min"] = ""
		self.params["temperature_max"] = ""
		self.params["time_on"] = ""
		self.params["utc"] = ""

		#System params
		self.params["debug_level"] = ""

		#Formatting strings for params.
		self.p_format["altitude"] = "%.1f"
		self.p_format["altitude_home"] = "%.0f"
		self.p_format["altitude_gps"] = "%.1f"
		self.p_format["cadence"] = "%.0f"
		self.p_format["climb"] = "%.1f"
		self.p_format["distance"] = "%.1f"
		self.p_format["gps_fix"] = ""
		self.p_format["gradient"] = ""
		self.p_format["heart_rate"] = "%.0f"
		self.p_format["latitude"] = "%.4f"
		self.p_format["longitude"] = "%.4f"
		self.p_format["odometer"] = "%.0f"
		self.p_format["pressure"] = "%.0f"
		self.p_format["pressure_at_sea_level"] = "%.0f"
		self.p_format["rider_weight"] = "%.1f"
		self.p_format["rtc"] = ""
		self.p_format["ride_time"] = "%.0f"
		self.p_format["ride_time_hms"] = ""
		self.p_format["ride_time_total"] = ".0f"
		self.p_format["ride_time_total_hms"] = ""
		self.p_format["satellites"] = "%.0f"
		self.p_format["satellites_used"] = "%.0f"
		self.p_format["speed"] = "%.1f"
		self.p_format["speed_digits"] = "%.0f"
		self.p_format["speed_tenths"] = "%.0f"
		self.p_format["speed_average"] = "%.1f"
		self.p_format["speed_average_digits"] = "%.0f"
		self.p_format["speed_average_tenths"] = "%.0f"
		self.p_format["speed_max"] = "%.1f"
		self.p_format["speed_max_digits"] = "%.0f"
		self.p_format["speed_max_tenths"] = "%.0f"
		self.p_format["temperature"] = "%.0f"
		self.p_format["temperature_average"] = "%.1f"
		self.p_format["temperature_min"] = "%.0f"
		self.p_format["temperature_max"] = "%.0f"
		self.p_format["time_on"] = "%.0f"
		self.p_format["time_on_hms"] = ""
		self.p_format["utc"] = ""

		#Units - name has to be identical as in params #FIXME reduce number of units (i.e one for speed)
		self.units["altitude"] = "m"
		self.units["altitude_home"] = "m"
		self.units["altitude_gps"] = "m"
		self.units["climb"] = "m/s"
		self.units["distance"] = "km"
		self.units["gps_fix"] = ""
		self.units["gradient"] = "%"
		self.units["heart_rate"] = "BPM"
		self.units["latitude"] = ""
		self.units["longitude"] = ""
		self.units["odometer"] = "km"
		self.units["pressure"] = "hPa"
		self.units["rider_weight"] = "kg"
		self.units["ride_time"] = "s"
		self.units["ride_time_hms"] = ""
		self.units["ride_time_total"] = "s"
		self.units["ride_time_total_hms"] = ""
		self.units["satellites"] = ""
		self.units["satellites_used"] = ""
		self.units["speed"] = "km/h"
		self.units["speed_average"] = "km/h"
		self.units["speed_max"] = "km/h"
		self.units["temperature"] = "C"
		self.units["temperature_average"] = "C"
		self.units["temperature_min"] = "C"
		self.units["temperature_max"] = "C"
		self.units["time_on"] = "s"
		self.units["time_on_hms"] = "s"

		#Allowed units - user can switch between those when editing value 
		self.units_allowed["odometer"] = ["km", "mi"]
		self.units_allowed["rider_weight"] = ["kg", "st", "lb"]

		#FIXME python-quantities won't like those deg C
		#FXIME double defined
		self.units["temperature"] = "C"
		#FIXME Make pretty units for temperature
		#self.units["temperature"] = u'\N{DEGREE SIGN}' + "C"

		#Params description FIXME localisation
		self.p_desc["altitude_home"] = "Home altitude"
		self.p_desc["odometer"] = "Odometer" 
		self.p_desc["odometer_units"] = "Odometer units" 
		self.p_desc["rider_weight"] = "Rider weight"
		self.p_desc["rider_weight_units"] = "Rider weight units"

		#Define id a param is editable FIXME editor type - number, calendar, unit, etc.
		#Params that can be changed in Settings by user
		self.p_editable["altitude_home"] = 1
		self.p_editable["odometer"] = 1 
		self.p_editable["odometer_units"] = 0
		self.p_editable["rider_weight"] = 1
		self.p_editable["rider_weight_units"] = 0

		#Do not record any speed below 2.5 m/s
		self.speed_gps_low = 2.5
		self.occ.log.info("[RP] speed_gps_low treshold set to {}".format(self.speed_gps_low))
		#Do not show speed below 1 m/s
		self.speed_gps_noise = 1
		self.occ.log.info("[RP] speed_gps_noise treshold set to {}".format(self.speed_gps_noise))
		self.update_speed_max()
		self.update_param("altitude_home")
		self.occ.log.info("[RP] altitude_home set to {}".format(self.params["altitude_home"]))
		self.pressure_at_sea_level_calculated = False

	def stop(self):
		self.gps.stop()
		self.bmp183_sensor.stop()

	def __del__(self):
		self.stop()

	def update_values(self):
		t = time.time()
		self.p_raw["dtime"] = t - self.p_raw["time_stamp"]
		self.p_raw["time_stamp"] = t
		self.occ.log.debug("[RP] update_values timestamp: {}".format(t))
		self.update_rtc()
		self.read_bmp183_sensor()
		if not self.pressure_at_sea_level_calculated:
			self.calculate_pressure_at_sea_level()
		self.read_gps_data()
		self.update_params()
		self.calculate_distance()
		self.calculate_altitude()
		self.force_refresh()
		#FIXME Add calculations of gradient, trip time, etc

	#FIXME change name
	def calculate_distance(self):
		dt = self.p_raw["dtime"]
		self.p_raw["time_on"] += dt
		#FIXME calculate with speed not speed_gps when bt sensors are set up
		s = self.p_raw["speed_gps"]
		if s > self.speed_gps_low:
			d = 0
			try:
				d = dt * s
				d = float(d)
			except (TypeError, ValueError):
				#Speed is not set yet - do nothing
				pass
			self.p_raw["distance"] += d
			self.p_raw["odometer"] += d
			self.p_raw["ride_time"] += self.p_raw["dtime"]
			self.p_raw["ride_time_total"] += self.p_raw["dtime"]
			self.p_raw["speed_average"] = self.p_raw["distance"] / self.p_raw["ride_time"]
			self.update_speed_average()
			self.occ.log.debug("[RP] speed_gps: {}, distance: {}, odometer: {}".\
					format(s, self.p_raw["distance"], self.p_raw["odometer"]))
		else:
			self.occ.log.debug("[RP] speed_gps: below speed_gps_low treshold")

	def force_refresh(self):
		self.occ.force_refresh()

	def get_val(self, func):
		if func.endswith("_units"):
			return self.units[func[:-6]]
		else:
			return self.params[func]

	def get_unit(self, func):
		if func.endswith("_units"):
			return None
		else:
			return self.units[func]

	def get_internal_unit(self, func):
		if func.endswith("_units"):
			return None
		else:
			return self.p_raw_units[func]

	def get_description(self, func):
		return self.p_desc[func]

	def clean_value(self, variable, empty = 0):
		if not math.isnan(variable):
			return variable
		else:
			return empty

	def read_gps_data(self):
		data = self.gps.get_data()
		lat = data[0]
		lon = data[1]
		alt = data[2]
		spd = data[3]
		self.p_raw["utc"] = data[4]
		sud = data[5]
		sat = data[6]
		self.p_raw["gps_fix"] = data[7]
		cmb = data[8]
		self.p_raw["latitude"] = self.clean_value(lat);
		self.p_raw["longitude"] = self.clean_value(lon);
		self.p_raw["altitude_gps"] = self.clean_value(alt);
		self.p_raw["speed_gps"] = self.clean_value(spd);
		self.p_raw["satellites_used"] = self.clean_value(sud);
		self.p_raw["satellites"] = self.clean_value(sat);
		self.p_raw["speed"] = self.clean_value(spd);
		if self.p_raw["speed"] < self.speed_gps_noise:
			self.p_raw["speed"] = 0
		#FIXME That will have to be changed with bluetooth speed sensor
		self.p_raw["speed_gps"] = self.p_raw["speed"] 
		self.p_raw["climb"] = self.clean_value(cmb);
	#FIXME use one function for all 3 speeds
	def update_speed(self):
		if self.p_raw["speed"] > self.p_raw["speed_max"]:
			self.p_raw["speed_max"] = self.p_raw["speed"]
			self.update_speed_max()
		self.update_param("speed")
		self.params["speed_digits"] = self.params["speed"][:-2]
		self.params["speed_tenths"] = self.params["speed"][-1:]
		self.occ.log.debug("[RP] speed: {} {}".\
				format(self.params["speed"], self.units["speed"]))

	def update_speed_max(self):
		self.update_param("speed_max")
		self.params["speed_max_digits"] = self.params["speed_max"][:-2]
		self.params["speed_max_tenths"] = self.params["speed_max"][-1:]
		self.occ.log.debug("[RP] max speed: {} {}".\
				format(self.params["speed_max"], self.units["speed_max"]))

	def update_speed_average(self):
		self.update_param("speed_average")
		self.params["speed_average_digits"] = self.params["speed_average"][:-2]
		self.params["speed_average_tenths"] = self.params["speed_average"][-1:]
		self.occ.log.debug("[RP] average speed: {} {}".\
				format(self.params["speed_average"], self.units["speed_average"]))

	def update_gps(self):
		self.params["gps_fix"] = self.p_raw["gps_fix"]
	
	def set_max(self, param):
		self.p_raw[param + "_max"] = max(self.p_raw[param], self.p_raw[param + "_max"])

	def set_min(self, param):
		self.p_raw[param + "_min"] = min(self.p_raw[param], self.p_raw[param + "_min"])

	def calculate_average_temperature(self):
		dt = self.p_raw["dtime"]
		t = self.p_raw["temperature"]
		ta = self.p_raw["temperature_average"]
		tt = self.p_raw["time_on"]
		ta_new = (t * dt + ta * tt) / (tt + dt)
		self.p_raw["temperature_average"] = ta_new

	def update_params(self):
		#FIXME Make a list of params and call from for loop
		#FIXME Use the list to dump DEBUG data
		self.update_gps()
		self.update_param("latitude")
		self.update_param("longitude")
		self.update_param("altitude_gps")
		self.update_param("altitude_home")
		self.update_param("altitude")
		self.update_param("climb")
		self.update_param("distance")
		self.update_param("ride_time")
		self.update_hms("ride_time")
		self.update_hms("ride_time_total")
		self.update_hms("time_on")
		self.update_speed()
			
		self.params["utc"] = self.p_raw["utc"]
		self.update_param("odometer")
		self.update_param("rider_weight")
		self.update_param("pressure")
		self.set_max("temperature")
		self.set_min("temperature")
		self.calculate_average_temperature()
		self.update_param("temperature")
		self.update_param("temperature_average")
		self.update_param("temperature_min")
		self.update_param("temperature_max")
		self.update_param("satellites_used")
		self.update_param("satellites")

	def update_param(self, param_name):
		try:
			f = self.p_format[param_name]
		except KeyError:
			self.occ.log.error("[RP] Formatting not available: param_name = {}".format(param_name))
			f = "%.1f"

		if self.p_raw[param_name] != "-":
			iu = self.get_internal_unit(param_name)
			try:
				v = q.Quantity(self.p_raw[param_name], iu)
				v.units = self.get_unit(param_name)
				self.params[param_name] = f % float(v.item())
			except TypeError:
				#Value conversion failed, so don't change anything
				self.occ.log.debug("[RP] TypeError: update_param exception: {} {} {}".\
						format(__name__ ,param_name, self.params[param_name],\
							self.p_raw[param_name]))
				pass
			except ValueError:
				self.occ.log.debug("[RP] ValueError: update_param exception: {} {} {}".\
						format(__name__ ,param_name, self.params[param_name],\
							self.p_raw[param_name]))
			
	def add_zero(self, value):
		if value < 10:
			value = "0" + unicode(value)
		return value

	def update_hms(self, param):
		t = divmod(int(self.p_raw[param]), 3600)
		hrs = t[0]
		sec = t[1]
		t = divmod(t[1], 60)
		mins = t[0]
		sec = t[1]
		hrs = self.add_zero(hrs)
		mins = self.add_zero(mins)
		sec = self.add_zero(sec)
		self.params[param + "_hms"] = "{}:{}:{}".format(hrs, mins, sec)

	def update_rtc(self):
		#FIXME proper localisation would be nice....
		self.params["date"] = strftime("%d-%m-%Y")
		self.params["time"] = strftime("%H:%M:%S")
		self.params["rtc"] = self.params["date"] + " " + self.params["time"]

	def read_bmp183_sensor(self):
		temperature = self.bmp183_sensor.temperature
		pressure = self.bmp183_sensor.pressure/100.0
		if not self.bmp183_first_run:
			dtemperature = abs(temperature - self.p_raw["temperature"])
			dpressure = abs(pressure - self.p_raw["pressure"])
		else:
			dtemperature = 0
			dpressure = 0
			self.bmp183_first_run = False
		if dtemperature < self.p_raw["temperature_max_delta"]:
			self.p_raw["temperature"] = temperature
		if dpressure < self.p_raw["pressure_max_delta"]:
			self.p_raw["pressure"] = pressure
		
	def calculate_altitude(self):
		pressure = self.p_raw["pressure"]
		pressure_at_sea_level = self.p_raw["pressure_at_sea_level"]
		if pressure_at_sea_level > 0:
			self.p_raw["altitude"] = float(44330*(1 - pow((pressure/pressure_at_sea_level), (1/5.255))))
		else:
			self.p_raw["altitude"] = 0
		self.occ.log.debug("[RP] altitude: {}".format(self.p_raw["altitude"]))

	def calculate_pressure_at_sea_level(self):
		#Set pressure_at_sea_level based on given altitude
		pressure = self.p_raw["pressure"]
		altitude_home = self.p_raw["altitude_home"]
		#Potential DIV/0 is altitude_home set to 44330
		self.p_raw["pressure_at_sea_level"] = float(pressure/pow((1 - altitude_home/44330), 5.255))
		self.pressure_at_sea_level_calculated = True
		self.occ.log.debug("[RP] pressure_at_sea_level: {}".format(self.p_raw["pressure_at_sea_level"]))
