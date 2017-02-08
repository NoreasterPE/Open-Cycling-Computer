from bmp183 import bmp183
from gps_mtk3339 import gps_mtk3339
from time import strftime
from units import units
import logging
import math
import time

INF_MIN = float("-inf")
INF = float("inf")
degC = u'\N{DEGREE SIGN}' + "C"


class ride_parameters():
        def __init__(self, occ, simulate=False):
                self.occ = occ
                self.l = logging.getLogger('system')
                self.r = self.setup_ridelog()
                self.uc = units()
                self.l.info("[RP] Initialising GPS")
                self.gps = gps_mtk3339(simulate)
                self.l.info("[RP] Initialising bmp183 sensor")
                self.bmp183_sensor = bmp183(self.occ, simulate)
                self.bmp183_first_run = True

                self.p_desc = {}
                self.p_editable = {}
                self.p_format = {}
                self.p_raw = {}
                self.p_raw_units = {}
                self.p_resettable = {}
                self.params = {}
                self.units = {}
                self.units_allowed = {}
                self.suffixes = ("_digits", "_tenths", "_hms")

                #Internal params of the ride.
                self.p_raw["time_stamp"] = time.time()
                #Time delta since last p_raw update
                self.p_raw["dtime"] = 1

                self.p_raw["Q"] = 0
                self.p_raw["altitude"] = 0
                self.p_raw["altitude_gps"] = 0
                self.p_raw["altitude_home"] = 0
                self.p_raw["altitude_max"] = INF_MIN
                self.p_raw["altitude_min"] = INF
                self.p_raw["altitude_previous"] = 0
                self.p_raw["cadence"] = 0
                self.p_raw["cadence_avg"] = 0
                self.p_raw["cadence_max"] = INF_MIN
                self.p_raw["climb"] = 0
                self.p_raw["daltitude"] = 0
                self.p_raw["daltitude_cumulative"] = 0
                self.p_raw["ddistance"] = 0
                self.p_raw["ddistance_cumulative"] = 0
                self.p_raw["distance"] = 0
                self.p_raw["eps"] = 0
                self.p_raw["ept"] = 0
                self.p_raw["epv"] = 0
                self.p_raw["epx"] = 0
                self.p_raw["gps_strength"] = 0
                self.p_raw["gpsfix"] = ""
                self.p_raw["heartrate"] = 0
                self.p_raw["latitude"] = 0
                self.p_raw["longitude"] = 0
                self.p_raw["odometer"] = 0
                self.p_raw["pressure"] = 0
                self.p_raw["pressure_at_sea_level"] = 0
                self.p_raw["riderweight"] = 0
                self.p_raw["ridetime"] = 0
                self.p_raw["ridetime_total"] = 0
                self.p_raw["rtc"] = ""
                self.p_raw["satellites"] = 0
                self.p_raw["satellitesused"] = 0
                self.p_raw["slope"] = 0
                self.p_raw["speed"] = 0
                self.p_raw["speed_avg"] = 0
                self.p_raw["speed_gps"] = 0
                self.p_raw["speed_max"] = 0
                self.p_raw["temperature"] = 0
                self.p_raw["temperature_avg"] = 0
                self.p_raw["temperature_max"] = INF_MIN
                self.p_raw["temperature_min"] = INF
                self.p_raw["timeon"] = 0.0001  # Avoid DIV/0
                self.p_raw["time_cadence_reset"] = 0.0001
                self.p_raw["track"] = 0
                self.p_raw["utc"] = ""

                #System params
                #Maximum allowable temperature change between measurements. If measurement differ more than delta they are ignored.
                self.p_raw["temperature_max_delta"] = 10  # degC

                #Internal units
                self.p_raw_units["Q"] = ""
                self.p_raw_units["altitude"] = "m"
                self.p_raw_units["cadence"] = "RPM"
                self.p_raw_units["climb"] = "m/s"
                self.p_raw_units["distance"] = "m"
                self.p_raw_units["eps"] = ""
                self.p_raw_units["ept"] = ""
                self.p_raw_units["epv"] = ""
                self.p_raw_units["epx"] = ""
                self.p_raw_units["dtime"] = "s"
                self.p_raw_units["gpsfix"] = ""
                self.p_raw_units["latitude"] = ""
                self.p_raw_units["longitude"] = ""
                self.p_raw_units["odometer"] = "m"
                self.p_raw_units["pressure"] = "Pa"
                self.p_raw_units["riderweight"] = "kg"
                self.p_raw_units["ridetime"] = "s"
                self.p_raw_units["ridetime_total"] = "s"
                self.p_raw_units["satellites"] = ""
                self.p_raw_units["satellitesused"] = ""
                self.p_raw_units["slope"] = "m/m"
                self.p_raw_units["speed"] = "m/s"
                self.p_raw_units["temperature"] = degC
                self.p_raw_units["timeon"] = "s"
                self.p_raw_units["time_cadence_reset"] = "s"
                #FIXME degrees
                self.p_raw_units["track"] = ""

                #Params of the ride ready for rendering.
                self.params["Q"] = "-"
                self.params["altitude"] = "-"
                self.params["altitude_gps"] = "-"
                self.params["altitude_home"] = "-"
                self.params["altitude_max"] = "-"
                self.params["altitude_min"] = "-"
                self.params["cadence"] = "-"
                self.params["cadence_avg"] = "-"
                self.params["cadence_max"] = "-"
                self.params["climb"] = "-"
                self.params["distance"] = 0
                self.params["eps"] = "-"
                self.params["ept"] = "-"
                self.params["epv"] = "-"
                self.params["epx"] = "-"
                self.params["dtime"] = 0
                self.params["gpsfix"] = "-"
                self.params["gpsfix_time"] = "-"
                self.params["heartrate"] = "-"
                self.params["latitude"] = "-"
                self.params["longitude"] = "-"
                self.params["odometer"] = 0.0
                self.params["pressure"] = "-"
                self.params["pressure_at_sea_level"] = "-"
                self.params["riderweight"] = 0.0
                self.params["ridetime"] = ""
                self.params["ridetime_hms"] = ""
                self.params["ridetime_total"] = ""
                self.params["ridetime_total_hms"] = ""
                self.params["rtc"] = ""
                self.params["satellites"] = "-"
                self.params["satellitesused"] = "-"
                self.params["slope"] = "-"
                self.params["speed"] = "-"
                self.params["speed_avg"] = "-"
                self.params["speed_avg_digits"] = "-"
                self.params["speed_avg_tenths"] = "-"
                self.params["speed_digits"] = "-"
                self.params["speed_max"] = "-"
                self.params["speed_max_digits"] = "-"
                self.params["speed_max_tenths"] = "-"
                self.params["speed_tenths"] = "-"
                self.params["temperature"] = ""
                self.params["temperature_avg"] = ""
                self.params["temperature_max"] = ""
                self.params["temperature_min"] = ""
                self.params["timeon"] = ""
                self.params["timeon_hms"] = ""
                self.params["time_cadence_reset"] = ""
                self.params["track"] = "-"
                self.params["utc"] = ""

                #System params
                self.params["debug_level"] = ""
                #Editor params
                self.params["editor_index"] = 0
                self.params["editor_type"] = 0
                self.params["variable"] = None
                self.params["variable_description"] = None
                self.params["variable_raw_value"] = None
                self.params["variable_unit"] = None
                self.params["variable_value"] = None

                #Formatting strings for params.
                self.p_format["Q"] = "%.3f"
                self.p_format["altitude"] = "%.0f"
                self.p_format["altitude_gps"] = "%.0f"
                self.p_format["altitude_home"] = "%.0f"
                self.p_format["altitude_max"] = "%.0f"
                self.p_format["altitude_min"] = "%.0f"
                self.p_format["cadence"] = "%.0f"
                self.p_format["cadence_avg"] = "%.0f"
                self.p_format["cadence_max"] = "%.0f"
                self.p_format["climb"] = "%.1f"
                self.p_format["distance"] = "%.1f"
                self.p_format["eps"] = "%.4f"
                self.p_format["epx"] = "%.4f"
                self.p_format["epv"] = "%.4f"
                self.p_format["ept"] = "%.4f"
                self.p_format["dtime"] = "%.2f"
                self.p_format["gpsfix"] = ""
                self.p_format["gpsfix_time"] = ""
                self.p_format["heartrate"] = "%.0f"
                self.p_format["latitude"] = "%.4f"
                self.p_format["longitude"] = "%.4f"
                self.p_format["odometer"] = "%.0f"
                self.p_format["pressure"] = "%.0f"
                self.p_format["pressure_at_sea_level"] = "%.0f"
                self.p_format["riderweight"] = "%.1f"
                self.p_format["ridetime"] = "%.0f"
                self.p_format["ridetime_hms"] = ""
                self.p_format["ridetime_total"] = ".0f"
                self.p_format["ridetime_total_hms"] = ""
                self.p_format["rtc"] = ""
                self.p_format["satellites"] = "%.0f"
                self.p_format["satellitesused"] = "%.0f"
                self.p_format["slope"] = "%.0f"
                self.p_format["speed"] = "%.1f"
                self.p_format["speed_avg"] = "%.1f"
                self.p_format["speed_avg_digits"] = "%.0f"
                self.p_format["speed_avg_tenths"] = "%.0f"
                self.p_format["speed_digits"] = "%.0f"
                self.p_format["speed_max"] = "%.1f"
                self.p_format["speed_max_digits"] = "%.0f"
                self.p_format["speed_max_tenths"] = "%.0f"
                self.p_format["speed_tenths"] = "%.0f"
                self.p_format["temperature"] = "%.0f"
                self.p_format["temperature_avg"] = "%.1f"
                self.p_format["temperature_max"] = "%.0f"
                self.p_format["temperature_min"] = "%.0f"
                self.p_format["timeon"] = "%.0f"
                self.p_format["timeon_hms"] = ""
                self.p_format["time_cadence_reset"] = "%.0f"
                self.p_format["track"] = "%.1f"
                self.p_format["utc"] = ""

                #Units - name has to be identical as in params
                self.units["Q"] = ""
                self.units["altitude"] = "m"
                self.units["cadence"] = "RPM"
                self.units["climb"] = "m/s"
                self.units["distance"] = "km"
                self.units["eps"] = ""
                self.units["epx"] = ""
                self.units["epv"] = ""
                self.units["ept"] = ""
                self.units["dtime"] = "s"
                self.units["gpsfix"] = ""
                self.units["gpsfix_time"] = ""
                self.units["heartrate"] = "BPM"
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
                self.units["satellitesused"] = ""
                self.units["slope"] = "%"
                self.units["speed"] = "km/h"
                self.units["temperature"] = degC
                self.units["timeon"] = "s"
                self.units["timeon_hms"] = ""
                self.units["time_cadence_reset"] = "s"
                self.units["track"] = ""

                #Allowed units - user can switch between those when editing value
                # FIXME switch to mi when mi/h are set for speed
                # FIXME switch to mi/h when mi are set for odometer
                self.units_allowed["odometer"] = ["km", "mi"]
                self.units_allowed["riderweight"] = ["kg", "st", "lb"]
                #self.units_allowed["slope"] = ["%", degC]
                self.units_allowed["speed"] = ["km/h", "m/s", "mi/h"]
                self.units_allowed["temperature"] = [degC, "F", "K"]

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
                self.p_editable["Q"] = 1
                self.p_editable["altitude_home"] = 1
                self.p_editable["odometer"] = 1
                self.p_editable["odometer_units"] = 0
                self.p_editable["riderweight"] = 1
                self.p_editable["riderweight_units"] = 0
                self.p_editable["speed_units"] = 0
                self.p_editable["temperature_units"] = 0

                self.p_resettable["distance"] = 1
                self.p_resettable["odometer"] = 1
                self.p_resettable["ridetime"] = 1
                self.p_resettable["speed_max"] = 1
                self.p_resettable["cadence"] = 1
                self.p_resettable["cadence_avg"] = 1
                self.p_resettable["cadence_max"] = 1
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
                self.cadence_timestamp = None
                self.cadence_timestamp_old = None
                #Temporary
                self.p_raw["Q"] = self.bmp183_sensor.Q

        def start_sensors(self):
                self.l.info("[RP] Starting GPS thread")
                self.gps.start()
                self.l.info("[RP] Starting BMP thread")
                self.bmp183_sensor.start()

        def setup_ridelog(self):
                ride_log_filename = "log/ride." + strftime("%Y-%m-%d-%H:%M:%S") + ".log"
                logging.getLogger('ride').setLevel(logging.INFO)
                ride_log_handler = logging.handlers.RotatingFileHandler(ride_log_filename)
                ride_log_format = '%(time)-8s,%(dtime)-8s,%(speed)-8s,%(cadence)-8s,%(pressure)-8s,%(temperature)-8s,%(altitude)-8s,%(altitude_gps)-8s,%(distance)-8s,%(slope)-8s,%(climb)-8s,%(track)-8s,%(eps)-8s,%(epx)-8s,%(epv)-8s,%(ept)-8s'
                ride_log_handler.setFormatter(logging.Formatter(ride_log_format))
                logging.getLogger('ride').addHandler(ride_log_handler)
                ride_logger = logging.getLogger('ride')
                ride_logger.info('', extra={'time': "Time", 'dtime': "Delta", 'speed': "Speed",
                                            'cadence': "Cadence", 'heartrate': "Heart RT",
                                            'pressure': "Pressure", 'temperature': "Temp",
                                            'altitude': "Altitude", 'altitude_gps': "Alt GPS",
                                            'distance': "Distance", 'slope': "Slope", 'climb': "Climb",
                                            'track': "Track", 'eps': "eps", 'epx': "epx", 'epv': "epv",
                                            'ept': "ept"})
                return ride_logger

        def stop(self):
                self.gps.stop()
                self.bmp183_sensor.stop()

        def __del__(self):
                self.stop()

        def update_values(self):
                self.p_raw["Q"] = self.bmp183_sensor.Q
                self.update_param("Q")
                t = time.time()
                self.p_raw["dtime"] = t - self.p_raw["time_stamp"]
                self.p_raw["time_stamp"] = t
                self.read_gps_data()
                #FIXME Move this to gps module?
                dt_adjustment = self.occ.rp.gps.time_adjustment_delta
                if dt_adjustment > 0:
                        self.p_raw["dtime"] = self.p_raw["dtime"] - dt_adjustment
                        self.occ.rp.gps.time_adjustment_delta = 0
                        self.l.info("[RP] dtime adjusted by {}".format(dt_adjustment))
                        self.occ.rp.gps.time_adjustment_delta = 0
                        #FIXME Correct other parameters like ridetime
                self.l.debug("[RP] timestamp: {} dtime {}".format(t, self.p_raw["dtime"]))
                self.read_bmp183_data()
                self.calculate_altitude()
                self.calculate_time_related_parameters()
                self.p_raw["daltitude_cumulative"] += self.p_raw["daltitude"]
                self.p_raw["ddistance_cumulative"] += self.p_raw["ddistance"]
                if self.p_raw["ddistance_cumulative"] == 0:
                        self.p_raw["slope"] = 0
                # FIXME make proper param for tunnig. Calculate slope if the distance delta was grater than 8,4m
                elif self.p_raw["ddistance_cumulative"] > 8.4:
                        self.p_raw["slope"] = self.p_raw["daltitude_cumulative"] / self.p_raw["ddistance_cumulative"]
                        self.l.debug("[RP] daltitude_cumulative: {} ddistance_cumulative: {}".
                                     format(self.p_raw["daltitude_cumulative"], self.p_raw["ddistance_cumulative"]))
                        self.p_raw["daltitude_cumulative"] = 0
                        self.p_raw["ddistance_cumulative"] = 0
                self.l.debug("[RP] slope: {}".format(self.p_raw["slope"]))
                self.update_params()

        def calculate_time_related_parameters(self):
                dt = self.p_raw["dtime"]
                self.p_raw["timeon"] += dt
                #FIXME calculate with speed not speed_gps when bt sensors are set up
                s = self.p_raw["speed_gps"]
                if (s > self.speed_gps_low):
                        d = float(dt * s)
                        self.p_raw["ddistance"] = d
                        self.p_raw["distance"] += d
                        self.p_raw["odometer"] += d
                        self.p_raw["ridetime"] += dt
                        self.p_raw["ridetime_total"] += dt
                        self.p_raw["speed_avg"] = self.p_raw["distance"] / self.p_raw["ridetime"]
                        self.update_param("speed_avg")
                        self.split_speed("speed_avg")
                        self.l.debug("[RP] speed_gps: {}, distance: {}, odometer: {}".
                                     format(s, self.p_raw["distance"], self.p_raw["odometer"]))
                else:
                        self.p_raw["ddistance"] = 0
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
                        value = self.get_unit(func[:-6])
                else:
                        if func in self.params:
                                value = self.params[func]
                        else:
                                value = None
                return value

        def get_unit(self, param_name):
                suffixes = ("_min", "_max", "_avg", "_gps", "_home")
                p = self.strip_end(param_name, suffixes)
                if p.endswith("_units"):
                        return None
                else:
                        return self.units[p]

        def get_internal_unit(self, param_name):
                suffixes = ("_min", "_max", "_avg", "_gps", "_home")
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

        def clean_value(self, variable, empty=0):
                if not math.isnan(variable):
                        return variable
                else:
                        return empty

        def read_gps_data(self):
                data = self.gps.get_data()
                self.p_raw["latitude"] = self.clean_value(data[0])
                self.p_raw["longitude"] = self.clean_value(data[1])
                self.p_raw["altitude_gps"] = self.clean_value(data[2])
                self.p_raw["speed_gps"] = self.clean_value(data[3])
                self.p_raw["utc"] = data[4]
                self.p_raw["satellitesused"] = self.clean_value(data[5])
                self.p_raw["satellites"] = self.clean_value(data[6])
                self.p_raw["gpsfix"] = data[7]
                self.p_raw["climb"] = self.clean_value(data[8])
                self.p_raw["track"] = self.clean_value(data[9])
                self.p_raw["eps"] = self.clean_value(data[10])
                self.p_raw["epx"] = self.clean_value(data[11])
                self.p_raw["epv"] = self.clean_value(data[12])
                self.p_raw["ept"] = self.clean_value(data[13])
                self.p_raw["gpsfix_time"] = data[14]

                gps_str = self.p_raw["satellitesused"] - 3
                if gps_str < 0:
                        gps_str = 0
                if gps_str > 3:
                        gps_str = 3
                self.p_raw["gps_strength"] = gps_str
                self.p_raw["speed"] = self.clean_value(self.p_raw["speed_gps"])
                if self.p_raw["speed"] < self.speed_gps_noise:
                        self.p_raw["speed"] = 0
                #FIXME That will have to be changed with bluetooth speed sensor
                self.p_raw["speed_gps"] = self.p_raw["speed"]

        def split_speed(self, speed_name):
                self.params[speed_name + "_digits"] = self.params[speed_name][:-2]
                self.params[speed_name + "_tenths"] = self.params[speed_name][-1:]

        def update_max_speed(self):
                if self.p_raw["speed"] > self.p_raw["speed_max"]:
                        self.p_raw["speed_max"] = self.p_raw["speed"]
                self.split_speed("speed_max")

        def update_gpsfix(self):
                self.params["gpsfix"] = self.p_raw["gpsfix"]
                self.params["gpsfix_time"] = self.p_raw["gpsfix_time"]

        def set_max(self, param):
                self.p_raw[param + "_max"] = max(self.p_raw[param], self.p_raw[param + "_max"])

        def set_min(self, param):
                self.p_raw[param + "_min"] = min(self.p_raw[param], self.p_raw[param + "_min"])

        def calculate_avg_temperature(self):
                dt = self.p_raw["dtime"]
                t = self.p_raw["temperature"]
                ta = self.p_raw["temperature_avg"]
                #FIXME Add and use time since reset not timeon
                tt = self.p_raw["timeon"]
                ta_new = (t * dt + ta * tt) / (tt + dt)
                self.p_raw["temperature_avg"] = ta_new

        def calculate_avg_cadence(self):
                dt = self.p_raw["dtime"]
                c = self.p_raw["cadence"]
                ca = self.p_raw["cadence_avg"]
                tt = self.p_raw["timeon"] - self.p_raw["time_cadence_reset"]
                ca_new = (c * dt + ca * tt) / (tt + dt)
                self.p_raw["cadence_avg"] = ca_new

        def update_altitude(self):
                self.update_param("altitude_gps")
                self.update_param("altitude_home")
                self.update_param("altitude")
                self.set_max("altitude")
                self.set_min("altitude")
                self.update_param("altitude_min")
                self.update_param("altitude_max")

        def update_params(self):
                self.update_rtc()
                self.update_gpsfix()
                self.update_param("dtime")
                self.update_param("latitude")
                self.update_param("longitude")
                self.update_altitude()
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
                self.params["utc"] = self.p_raw["utc"]
                self.update_param("odometer")
                self.update_param("riderweight")
                self.update_param("pressure")
                self.update_temperatures()
                self.update_param("satellitesused")
                self.update_param("satellites")
                self.update_param("slope")
                self.add_ridelog_entry()
                self.l.debug("[RP] speed: {}, speed_max: {}, average speed: {} {}, cadence {} {}".
                             format(self.params["speed"], self.params["speed_max"],
                                    self.params["speed_avg"], self.units["speed"],
                                    self.params["cadence"], self.units["cadence"]))
                self.force_refresh()

        def add_ridelog_entry(self):
                slp = self.params["slope"]
                hrt = self.params["heartrate"]
                tme = self.params["timeon_hms"]
                spd = self.params["speed"]
                cde = self.params["cadence"]
                dte = self.params["dtime"]
                pre = round(self.p_raw["pressure"], 1)
                tem = self.p_raw["temperature"]
                alt = self.p_raw["altitude"]
                alg = self.p_raw["altitude_gps"]
                dst = round(self.p_raw["distance"], 0)
                clb = self.p_raw["climb"]
                trk = self.p_raw["track"]
                eps = self.p_raw["eps"]
                epx = self.p_raw["epx"]
                epv = self.p_raw["epv"]
                ept = self.p_raw["ept"]
                self.r.info('', extra={'time': tme, 'dtime': dte, 'speed': spd, 'cadence': cde,
                                       'heartrate': hrt, 'pressure': pre, 'temperature': tem,
                                       'altitude': alt, 'altitude_gps': alg, 'distance': dst,
                                       'slope': slp, 'climb': clb, 'track': trk, 'eps': eps,
                                       'epx': epx, 'epv': epv, 'ept': ept})

        def strip_end(self, param_name, suffix=None):
                #Make sure there is no _digits, _tenths, _hms at the end
                if suffix is None:
                        suffix = self.suffixes
                for s in suffix:
                        if param_name.endswith(s):
                                l = -1 * len(s)
                                param_name = param_name[:l]
                return param_name

        def reset_ride(self):
                self.p_raw["distance"] = 0
                self.p_raw["ridetime"] = 0

        def reset_cadence(self):
                self.p_raw["cadence"] = 0
                self.p_raw["cadence_avg"] = 0
                self.p_raw["cadence_max"] = INF_MIN
                self.p_raw["time_cadence_reset"] = self.p_raw["timeon"]

        def reset_param(self, param_name):
                self.l.debug("[RP] Resetting {}".format(param_name))
                self.p_raw[param_name] = 0
                if param_name == "ridetime" or param_name == "distance":
                        self.reset_ride()
                if param_name == "cadence":
                        self.reset_cadence()
                self.force_refresh()

        def update_param(self, param_name):
                if param_name in self.p_format:
                        f = self.p_format[param_name]
                else:
                        self.l.error("[RP] Formatting not available: param_name = {}".format(param_name))
                        f = "%.1f"

                if self.p_raw[param_name] != "-":
                        unit_raw = self.get_internal_unit(param_name)
                        unit = self.get_unit(param_name)
                        value = self.p_raw[param_name]
                        if unit_raw != unit:
                                value = self.uc.convert(value, unit)
                        self.params[param_name] = f % float(value)
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

        def read_bmp183_data(self):
                self.p_raw["pressure"] = self.bmp183_sensor.pressure
                temperature = self.bmp183_sensor.temperature
                if not self.bmp183_first_run:
                        dtemperature = abs(temperature - self.p_raw["temperature"])
                else:
                        dtemperature = 0
                        self.bmp183_first_run = False
                #FIXME Kalman filter in bmp183 module will obsolete this code
                if dtemperature < self.p_raw["temperature_max_delta"]:
                        self.p_raw["temperature"] = temperature

        def calculate_altitude(self):
                def calc_alt():
                        alt = 0
                        if self.p_raw["pressure"] != 0:
                                alt = round(44330.0 * (1 - pow((self.p_raw["pressure"] /
                                            self.p_raw["pressure_at_sea_level"]), (1 / 5.255))), 2)
                        return alt

                if self.p_raw["pressure_at_sea_level"] == 0:
                        self.calculate_pressure_at_sea_level()
                        if self.p_raw["pressure_at_sea_level"] != 0:
                                self.p_raw["altitude"] = calc_alt()
                                self.p_raw["altitude_previous"] = self.p_raw["altitude"]
                else:
                        self.p_raw["altitude_previous"] = self.p_raw["altitude"]
                        self.p_raw["altitude"] = calc_alt()
                        self.p_raw["daltitude"] = self.p_raw["altitude"] - self.p_raw["altitude_previous"]
                self.l.debug("[RP] altitude: {}, daltitude {}".format(self.p_raw["altitude"], self.p_raw["daltitude"]))

        def calculate_pressure_at_sea_level(self):
                #Set pressure_at_sea_level based on given altitude
                pressure = self.p_raw["pressure"]
                altitude_home = self.p_raw["altitude_home"]
                if altitude_home < 43300:
                        self.p_raw["pressure_at_sea_level"] = float(pressure / pow((1 - altitude_home / 44330), 5.255))
                self.l.debug("[RP] pressure_at_sea_level: {}".format(self.p_raw["pressure_at_sea_level"]))

        def update_temperatures(self):
                self.set_min("temperature")
                self.set_max("temperature")
                self.calculate_avg_temperature()
                self.update_param("temperature")
                self.update_param("temperature_avg")
                self.update_param("temperature_min")
                self.update_param("temperature_max")

        def calculate_cadence(self):
                self.cadence_timestamp = time.time()
                if self.cadence_timestamp_old is not None:
                        dt = self.cadence_timestamp - self.cadence_timestamp_old
                        self.p_raw["cadence"] = 60 / dt
                self.cadence_timestamp_old = self.cadence_timestamp

        def update_cadence(self):
                self.calculate_avg_cadence()
                self.set_max("cadence")
                self.update_param("cadence")
                self.update_param("cadence_avg")
                self.update_param("cadence_max")
