from time import strftime
from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
import logging
import math
import time
from units import units

INF_MIN = float("-inf")
INF = float("inf")

class ride_parameters():
	def __init__(self, occ, simulate = False):
		self.occ = occ
		self.l = logging.getLogger('system')
		self.r = self.setup_ridelog()
		self.uc = units()
		self.l.info("[RP] Initialising GPS")
		self.gps = gps_mtk3339(occ, simulate)
		self.l.info("[RP] Starting GPS thread")
		self.gps.start()
		self.l.info("[RP] Initialising bmp183 sensor")
		self.bmp183_sensor = bmp183(simulate)
		self.bmp183_first_run = True
		self.l.info("[RP] Starting BMP thread")
		self.bmp183_sensor.start()

		self.p_desc = {}
		self.p_editable = {}
		self.p_format = {}
		self.p_raw = {}
		self.p_raw_units = {}
		self.params = {}
		self.p_resettable = {}
		self.units = {}
		self.units_allowed = {}
		self.suffixes =("_digits", "_tenths", "_hms")

		#Internal params of the ride.
		self.p_raw["time_stamp"] = time.time()
		#Time delta since last p_raw update
		self.p_raw["dtime"] = 1

		self.p_raw["altitude"] = 0
		self.p_raw["altitude_home"] = 0
		self.p_raw["altitude_gps"] = 0
		self.p_raw["altitude_min"] = INF
		self.p_raw["altitude_max"] = INF_MIN
		self.p_raw["cadence"] = 0
		self.p_raw["cadence_average"] = 0
		self.p_raw["cadence_max"] = INF_MIN
		self.p_raw["climb"] = 0
		self.p_raw["distance"] = 0
		#FIXME Name doesn't follow the policy
		self.p_raw["gps_fix"] = ""
		self.p_raw["gps_strength"] = 0
		self.p_raw["gradient"] = 0
		self.p_raw["heart_rate"] = 0
		self.p_raw["latitude"] = 0
		self.p_raw["longitude"] = 0
		self.p_raw["odometer"] = 0
		self.p_raw["pressure"] = 0
		#FIXME Name doesn't follow the policy
		self.p_raw["pressure_at_sea_level"] = 0
		self.p_raw["riderweight"] = 0
		self.p_raw["ridetime"] = 0
		self.p_raw["ridetime_total"] = 0
		self.p_raw["rtc"] = ""
		self.p_raw["satellites"] = 0
		#FIXME Name doesn't follow the policy
		self.p_raw["satellites_used"] = 0
		self.p_raw["speed"] = 0
		self.p_raw["speed_average"] = 0
		#FIXME Name doesn't follow the policy
		self.p_raw["speed_gps"] = 0
		self.p_raw["speed_max"] = 0
		self.p_raw["temperature"] = 0
		#FIXME Use avg?
		self.p_raw["temperature_average"] = 0
		self.p_raw["temperature_min"] = INF
		self.p_raw["temperature_max"] = INF_MIN
		#FIXME Name doesn't follow the policy
		self.p_raw["timeon"] = 0.0001 #Avoid DIV/0
		self.p_raw["utc"] = ""

		#System params
		#Maximum allowable temperature change between measurements. If measurement differ more than delta they are ignored.
		self.p_raw["temperature_max_delta"] = 10 #degC
		self.p_raw["pressure_max_delta"] = 1 #hPa

		#Internal units
		self.p_raw_units["altitude"] = "m"
		self.p_raw_units["distance"] = "m"
		self.p_raw_units["cadence"] = "RPM"
		self.p_raw_units["climb"] = "m/s"
		self.p_raw_units["dtime"] = "s"
		self.p_raw_units["gps_fix"] = ""
		self.p_raw_units["latitude"] = ""
		self.p_raw_units["longitude"] = ""
		self.p_raw_units["odometer"] = "m"
		self.p_raw_units["pressure"] = "hPa"
		self.p_raw_units["riderweight"] = "kg"
		self.p_raw_units["ridetime"] = "s"
		self.p_raw_units["ridetime_total"] = "s"
		self.p_raw_units["satellites"] = ""
		self.p_raw_units["satellites_used"] = ""
		self.p_raw_units["speed"] = "m/s"
		self.p_raw_units["temperature"] = "C"
		self.p_raw_units["timeon"] = "s"

		#Params of the ride ready for rendering.
		self.params["altitude"] = "-"
		self.params["altitude_home"] = "-"
		self.params["altitude_gps"] = "-"
		self.params["altitude_min"] = "-"
		self.params["altitude_max"] = "-"
		self.params["cadence"] = "-"
		self.params["cadence_average"] = "-"
		self.params["cadence_max"] = "-"
		self.params["climb"] = "-"
		self.params["distance"] = 0
		self.params["dtime"] = 0
		self.params["gps_fix"] = "-"
		self.params["gradient"] = "-"
		self.params["heart_rate"] = "-"
		self.params["latitude"] = "-"
		self.params["longitude"] = "-"
		self.params["odometer"] = 0.0
		self.params["pressure"] = "-"
		self.params["pressure_at_sea_level"] = "-" 
		self.params["rtc"] = ""
		self.params["riderweight"] = 0.0
		self.params["ridetime"] = ""
		self.params["ridetime_hms"] = ""
		self.params["ridetime_total"] = ""
		self.params["ridetime_total_hms"] = ""
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
		self.params["timeon"] = ""
		self.params["timeon_hms"] = ""
		self.params["utc"] = ""

		#System params
		self.params["debug_level"] = ""

		#Formatting strings for params.
		self.p_format["altitude"] = "%.0f"
		self.p_format["altitude_home"] = "%.0f"
		self.p_format["altitude_gps"] = "%.0f"
		self.p_format["altitude_min"] = "%.0f"
		self.p_format["altitude_max"] = "%.0f"
		self.p_format["cadence"] = "%.0f"
		self.p_format["cadence_average"] = "%.0f"
		self.p_format["cadence_max"] = "%.0f"
		self.p_format["climb"] = "%.1f"
		self.p_format["distance"] = "%.1f"
		self.p_format["dtime"] = "%.2f"
		self.p_format["gps_fix"] = ""
		self.p_format["gradient"] = ""
		self.p_format["heart_rate"] = "%.0f"
		self.p_format["latitude"] = "%.4f"
		self.p_format["longitude"] = "%.4f"
		self.p_format["odometer"] = "%.0f"
		self.p_format["pressure"] = "%.0f"
		self.p_format["pressure_at_sea_level"] = "%.0f"
		self.p_format["riderweight"] = "%.1f"
		self.p_format["rtc"] = ""
		self.p_format["ridetime"] = "%.0f"
		self.p_format["ridetime_hms"] = ""
		self.p_format["ridetime_total"] = ".0f"
		self.p_format["ridetime_total_hms"] = ""
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
		self.p_format["timeon"] = "%.0f"
		self.p_format["timeon_hms"] = ""
		self.p_format["utc"] = ""

		#Units - name has to be identical as in params #FIXME reduce number of units (i.e one for speed)
		self.units["altitude"] = "m"
		self.units["climb"] = "m/s"
		self.units["cadence"] = "RPM"
		self.units["distance"] = "km"
		self.units["dtime"] = "s"
		self.units["gps_fix"] = ""
		self.units["gradient"] = "%"
		self.units["heart_rate"] = "BPM"
		self.units["latitude"] = ""
		self.units["longitude"] = ""
		self.units["odometer"] = "km"
		self.units["pressure"] = "hPa"
		self.units["riderweight"] = "kg"
		self.units["ridetime"] = "s"
		self.units["ridetime_hms"] = ""
		self.units["ridetime_total"] = "s"
		self.units["ridetime_total_hms"] = ""
		self.units["satellites"] = ""
		self.units["satellites_used"] = ""
		self.units["speed"] = "km/h"
		self.units["temperature"] = "C"
		self.units["timeon"] = "s"
		self.units["timeon_hms"] = ""

		#Allowed units - user can switch between those when editing value 
		self.units_allowed["odometer"] = ["km", "mi"]
		self.units_allowed["riderweight"] = ["kg", "st", "lb"]
		self.units_allowed["speed"] = ["km/h", "m/s", "mi/h"]
		self.units_allowed["temperature"] = ["C", "F", "K"]

		#FIXME Make pretty units for temperature
		#self.units["temperature"] = u'\N{DEGREE SIGN}' + "C"

		#Params description FIXME localisation
		self.p_desc["altitude_home"] = "Home altitude"
		self.p_desc["odometer"] = "Odometer" 
		self.p_desc["odometer_units"] = "Odometer units" 
		self.p_desc["riderweight"] = "Rider weight"
		self.p_desc["riderweight_units"] = "Rider weight units"
		self.p_desc["speed_units"] = "Speed units"
		self.p_desc["temperature_units"] = "Temp. unit"

		#Define id a param is editable FIXME editor type - number, calendar, unit, etc.
		# 0 - unit editor
		# 1 - number editor
		#Params that can be changed in Settings by user
		self.p_editable["altitude_home"] = 1
		self.p_editable["odometer"] = 1 
		self.p_editable["odometer_units"] = 0
		self.p_editable["riderweight"] = 1
		self.p_editable["riderweight_units"] = 0
		self.p_editable["speed_units"] = 0
		self.p_editable["temperature_units"] = 0

		self.p_resettable["distance"] = 1
		self.p_resettable["odometer"] = 1
		self.p_resettable["speed_max"] = 1
		self.p_resettable["ridetime"] = 1
		#Do not record any speed below 2.5 m/s
		self.speed_gps_low = 2.5
		self.l.info("[RP] speed_gps_low treshold set to {}".format(self.speed_gps_low))
		#Do not show speed below 1 m/s
		self.speed_gps_noise = 1
		self.l.info("[RP] speed_gps_noise treshold set to {}".format(self.speed_gps_noise))
		self.update_param("speed_max")
		self.split_speed("speed_max")
		self.update_param("altitude_home")
		self.l.info("[RP] altitude_home set to {}".format(self.params["altitude_home"]))
		self.pressure_at_sea_level_calculated = False
		self.cadence_timestamp = None
		self.cadence_timestamp_old = None

	def setup_ridelog(self):
		ride_log_filename = "log/ride." + strftime("%Y-%m-%d-%H:%M:%S") + ".log"
		logging.getLogger('ride').setLevel(logging.INFO)
		ride_log_handler = logging.handlers.RotatingFileHandler(ride_log_filename)
		ride_log_format = '%(time)s, %(dtime)s, %(pressure)-7s, %(temperature)-4s, %(altitude)-7s'
		ride_log_handler.setFormatter(logging.Formatter(ride_log_format))
		logging.getLogger('ride').addHandler(ride_log_handler)
		ride_logger = logging.getLogger('ride')
		ride_logger.info('', extra={'time': "Time", 'dtime': "Delta",\
			'pressure': "Pressure", 'temperature': "Temperature",\
			'altitude': "Altitude"})
		return ride_logger

	def stop(self):
		self.gps.stop()
		self.bmp183_sensor.stop()

	def __del__(self):
		self.stop()

	def update_values(self):
		t = time.time()
		self.p_raw["dtime"] = t - self.p_raw["time_stamp"]
		dt_adjustment = self.occ.rp.gps.time_adjustment_delta = 0
		if dt_adjustment > 0:
			self.p_raw["dtime"] = self.p_raw["dtime"] - dt_adjustment
			self.occ.rp.gps.time_adjustment_delta = 0
			self.l.debug("[RP] dtime adjusted by {}".format(dt_adjustment))
		self.p_raw["time_stamp"] = t
		self.l.debug("[RP] timestamp: {} dtime {}".format(t, self.p_raw["dtime"]))
		self.update_rtc()
		self.read_bmp183_sensor()
		if not self.pressure_at_sea_level_calculated:
			self.calculate_pressure_at_sea_level()
		self.read_gps_data()
		self.calculate_altitude()
		self.update_params()
		self.calculate_time_related_parameters()
		self.force_refresh()
		#FIXME Add calculations of gradient, etc

	def calculate_time_related_parameters(self):
		dt = self.p_raw["dtime"]
		self.p_raw["timeon"] += dt
		#FIXME calculate with speed not speed_gps when bt sensors are set up
		s = self.p_raw["speed_gps"]
		if (s > self.speed_gps_low):
			d = 0
			try:
				d = dt * s
				d = float(d)
			except ValueError:
				self.l.error("[RP] calculate_time_related_parameters ValueError")
				pass
			except TypeError:
				self.l.error("[RP] calculate_time_related_parameters TypeError")
			self.p_raw["distance"] += d
			self.p_raw["odometer"] += d
			self.p_raw["ridetime"] += self.p_raw["dtime"]
			self.p_raw["ridetime_total"] += self.p_raw["dtime"]
			self.p_raw["speed_average"] = self.p_raw["distance"] / self.p_raw["ridetime"]
			self.update_param("speed_average")
			self.split_speed("speed_average")
			self.l.debug("[RP] speed_gps: {}, distance: {}, odometer: {}".\
					format(s, self.p_raw["distance"], self.p_raw["odometer"]))
		else:
			self.l.debug("[RP] speed_gps: below speed_gps_low treshold")

	def force_refresh(self):
		self.occ.force_refresh()

	def get_raw_val(self, func):
		if func.endswith("_units"):
			return 0
		else:
			return self.p_raw[func]

	def get_val(self, func):
		if func.endswith("_units"):
			return self.units[func[:-6]]
		else:
			return self.params[func]

	def get_unit(self, param_name):
		suffixes =("_min", "_max", "_average", "_gps", "_home")
		p = self.strip_end(param_name, suffixes)
		if p.endswith("_units"):
			return None
		else:
			return self.units[p]

	def get_internal_unit(self, param_name):
		suffixes =("_min", "_max", "_average", "_gps", "_home")
		p = self.strip_end(param_name, suffixes)
		if p.endswith("_units"):
			return None
		else:
			return self.p_raw_units[p]

	def get_description(self, param_name):
		if param_name in self.p_desc:
			return self.p_desc[param_name]
		else:
			self.l.error("[RP] {} has no description defined".format(param_name))
			return "No description"

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
		lag = data[9]
		self.params["lag"] = "%.2f" % lag
		self.p_raw["latitude"] = self.clean_value(lat);
		self.p_raw["longitude"] = self.clean_value(lon);
		self.p_raw["altitude_gps"] = self.clean_value(alt);
		self.p_raw["speed_gps"] = self.clean_value(spd);
		self.p_raw["satellites_used"] = self.clean_value(sud);
		self.p_raw["satellites"] = self.clean_value(sat);
		gps_str = self.p_raw["satellites_used"] - 3
		if gps_str < 0:
			gps_str = 0
		if gps_str > 3:
			gps_str = 3
		self.p_raw["gps_strength"] = gps_str
		self.p_raw["speed"] = self.clean_value(spd);
		if self.p_raw["speed"] < self.speed_gps_noise:
			self.p_raw["speed"] = 0
		#FIXME That will have to be changed with bluetooth speed sensor
		self.p_raw["speed_gps"] = self.p_raw["speed"] 
		self.p_raw["climb"] = self.clean_value(cmb);

	def split_speed(self, speed_name):
		self.params[speed_name + "_digits"] = self.params[speed_name][:-2]
		self.params[speed_name + "_tenths"] = self.params[speed_name][-1:]

	def update_max_speed(self):
		if self.p_raw["speed"] > self.p_raw["speed_max"]:
			self.p_raw["speed_max"] = self.p_raw["speed"]
		self.split_speed("speed_max")

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
		tt = self.p_raw["timeon"]
		ta_new = (t * dt + ta * tt) / (tt + dt)
		self.p_raw["temperature_average"] = ta_new

	def calculate_average_cadence(self):
		dt = self.p_raw["dtime"]
		c = self.p_raw["cadence"]
		ca = self.p_raw["cadence_average"]
		tt = self.p_raw["timeon"]
		ca_new = (c * dt + ca * tt) / (tt + dt)
		self.p_raw["cadence_average"] = ca_new

	def update_params(self):
		#FIXME Make a list of params and call from for loop
		#FIXME Use the list to dump DEBUG data
		self.update_gps()
		self.update_param("dtime")
		self.update_param("latitude")
		self.update_param("longitude")
		self.update_param("altitude_gps")
		self.update_param("altitude_home")
		self.update_param("altitude")
		self.set_max("altitude")
		self.set_min("altitude")
		self.update_param("altitude_min")
		self.update_param("altitude_max")
		self.update_cadence()
		self.update_param("climb")
		self.update_param("distance")
		self.update_param("ridetime")
		self.update_hms("ridetime")
		self.update_hms("ridetime_total")
		self.update_hms("timeon")
		self.update_param("timeon")
		self.update_max_speed()
		self.update_param("speed")
		self.update_param("speed_max")
		self.split_speed("speed")
		self.l.debug("[RP] speed: {}, speed_max: {}, average speed: {} {}, cadence {} {}".\
				format(self.params["speed"], self.params["speed_max"],\
				self.params["speed_average"], self.units["speed"],\
				self.params["cadence"], self.units["cadence"]))
			
		self.params["utc"] = self.p_raw["utc"]
		self.update_param("odometer")
		self.update_param("riderweight")
		self.update_param("pressure")
		self.update_temperatures()
		self.update_param("satellites_used")
		self.update_param("satellites")
		tme = self.params["timeon_hms"]
		dte = self.params["dtime"]
		pre = self.p_raw["pressure"]
		tem = self.p_raw["temperature"]
		alt = self.p_raw["altitude"]
		self.r.info('', extra={'time': tme, 'dtime': dte, 'pressure': pre, 'temperature': tem, 'altitude': alt})

	def strip_end(self, param_name, suffix = None):
		#Make sure there is no _digits, _tenths, _hms at the end
		if suffix is None:
			suffix = self.suffixes
		for s in suffix:
			if param_name.endswith(s):
				l = -1 * len(s)
				param_name = param_name[:l]
		return param_name

	def reset_param(self, param_name):
		self.l.debug("[RP] Resetting {}".format(param_name))
		self.p_raw[param_name] = 0
		#FIXME make a function like reset ride 
		if param_name == "ridetime" or param_name == "distance":
			self.p_raw["distance"] = 0
			self.p_raw["ridetime"] = 0
			
		#Speed needs special handling due to digit/tenth split
		#if param_name.startswith("speed"):
		#	self.update_and_split_speed(param_name)

	def update_param(self, param_name):
		if param_name in self.p_format:
			f = self.p_format[param_name]
		else:
			self.l.error("[RP] Formatting not available: param_name = {}".format(param_name))
			f = "%.1f"

		if self.p_raw[param_name] != "-":
			unit_raw = self.get_internal_unit(param_name)
			try:
				unit = self.get_unit(param_name)
				value = self.p_raw[param_name]
				if unit_raw != unit:
					value = self.uc.convert(value, unit)
				self.params[param_name] = f % float(value)
			except TypeError:
			#FIXME Required?
				#Value conversion failed, so don't change anything
				self.l.error("[RP] TypeError: update_param exception: {} {} {}".\
						format(__name__ ,param_name, self.params[param_name],\
							self.p_raw[param_name]))
			#FIXME Required?
			except ValueError:
				self.l.error("[RP] ValueError: update_param exception: {} {} {}".\
						format(__name__ ,param_name, self.params[param_name],\
							self.p_raw[param_name]))
		else:
			self.l.debug("[RP] param_name {} = -".format(param_name))
			
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
		#FIXME Kalman filter in bmp183 module will obsolete this code
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
			self.p_raw["altitude"] = round(44330.0*(1 - pow((pressure/pressure_at_sea_level), (1/5.255))), 2)
		else:
			self.p_raw["altitude"] = 0
		self.l.debug("[RP] altitude: {}".format(self.p_raw["altitude"]))

	def calculate_pressure_at_sea_level(self):
		#Set pressure_at_sea_level based on given altitude
		pressure = self.p_raw["pressure"]
		altitude_home = self.p_raw["altitude_home"]
		#Potential DIV/0 is altitude_home set to 44330
		self.p_raw["pressure_at_sea_level"] = float(pressure/pow((1 - altitude_home/44330), 5.255))
		self.pressure_at_sea_level_calculated = True
		self.l.debug("[RP] pressure_at_sea_level: {}".format(self.p_raw["pressure_at_sea_level"]))

	def update_temperatures(self):
		self.set_min("temperature")
		self.set_max("temperature")
		self.calculate_average_temperature()
		self.update_param("temperature")
		self.update_param("temperature_average")
		self.update_param("temperature_min")
		self.update_param("temperature_max")

	def calculate_cadence(self):
		self.cadence_timestamp = time.time()
		if self.cadence_timestamp_old is not None:
			dt = self.cadence_timestamp - self.cadence_timestamp_old 
			self.p_raw["cadence"] = 60 / dt
		self.cadence_timestamp_old = self.cadence_timestamp

	def update_cadence(self):
		self.calculate_average_cadence()
		self.set_max("cadence")
		self.update_param("cadence")
		self.update_param("cadence_average")
		self.update_param("cadence_max")
