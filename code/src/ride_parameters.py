from sensors import sensors
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
        self.l.info("[RP] Initialising sensors")
        self.sensors = sensors(False)
        self.ble = None
        self.l.info("[RP] Initialising GPS")
        self.gps = gps_mtk3339(simulate)
        self.l.info("[RP] Initialising bmp183 sensor")
        self.bmp183_sensor = bmp183(self.occ, simulate)
        self.bmp183_first_run = True

        self.suffixes = ("_digits", "_tenths", "_hms")

        self.p_raw = dict(time_stamp=time.time(),
                          # Time delta since last p_raw update
                          dtime=1,
                          altitude=0, altitude_gps=0, altitude_home=0, altitude_max=INF_MIN, altitude_min=INF, altitude_previous=0,
                          pressure=0, pressure_at_sea_level=0,
                          climb=0, daltitude=0, daltitude_cumulative=0,
                          odometer=0, ddistance=0, ddistance_cumulative=0, distance=0,
                          eps=0, ept=0, epv=0, epx=0, gps_strength=0, gpsfix='', latitude=0, longitude=0, satellites=0, satellitesused=0,
                          Q=0,
                          cadence=0, cadence_avg=0, cadence_max=INF_MIN,
                          cadence_time_stamp=time.time(), cadence_expiry_time=1.5, time_cadence_reset=0.0001,
                          heartrate=0,
                          riderweight=0,
                          ridetime=0, ridetime_total=0,
                          slope=0,
                          speed=0, speed_avg=0, speed_gps=0, speed_max=0,
                          temperature=0, temperature_avg=0, temperature_max=INF_MIN, temperature_min=INF,
                          # Maximum allowable temperature change between measurements. If measurement differ more than delta they are ignored.
                          temperature_max_delta=10,
                          track=0,
                          timeon=0.0001, utc='', rtc='')

        # Internal units
        self.p_raw_units = dict(Q='', altitude='m', cadence='RPM', climb='m/s', distance='m', eps='', ept='', epv='', epx='',
                                dtime='s', gpsfix='', latitude='', longitude='', odometer='m', pressure='Pa', riderweight='kg',
                                ridetime='s', ridetime_total='s', satellites='', satellitesused='', slope='m/m', speed='m/s',
                                temperature=degC, timeon='s', time_cadence_reset='s',
                                # FIXME degrees, what is track? Nomber of tracked sats?
                                track='')

        # Params of the ride ready for rendering.
        self.params = dict(Q='-', altitude='-', altitude_gps='-', altitude_home='-', altitude_max='-', altitude_min='-',
                           cadence='-', cadence_avg='-', cadence_max='-', climb='-', distance=0, eps='-', ept='-', epv='-', epx='-',
                           dtime=0, gpsfix='-', gpsfix_time='-', heartrate='-', latitude='-', longitude='-', odometer=0.0,
                           pressure='-', pressure_at_sea_level='-', riderweight=0.0, ridetime='', ridetime_hms='', ridetime_total='',
                           ridetime_total_hms='', rtc='', satellites='-', satellitesused='-', slope='-', speed='-', speed_avg='-',
                           speed_avg_digits='-', speed_avg_tenths='-', speed_digits='-', speed_max='-', speed_max_digits='-',
                           speed_max_tenths='-', speed_tenths='-', temperature='', temperature_avg='', temperature_max='',
                           temperature_min='', timeon='', timeon_hms='', time_cadence_reset='', track='-', utc='')

        # System params - shoud be in raw or new category: system
        self.sysvar = dict(debug_level='', editor_index=0, editor_type=0, variable=None,
                           variable_description=None, variable_raw_value=None, variable_unit=None, variable_value=None)

        # Formatting strings for params.
        self.p_format = dict(Q='%.3f', altitude='%.0f', altitude_gps='%.0f', altitude_home='%.0f', altitude_max='%.0f', altitude_min='%.0f',
                             cadence='%.0f', cadence_avg='%.0f', cadence_max='%.0f', climb='%.1f', distance='%.1f', eps='%.4f', epx='%.4f', epv='%.4f', ept='%.4f',
                             dtime='%.2f', gpsfix='', gpsfix_time='', heartrate='%.0f', latitude='%.4f', longitude='%.4f', odometer='%.0f',
                             pressure='%.0f', pressure_at_sea_level='%.0f', riderweight='%.1f', ridetime='%.0f', ridetime_hms='', ridetime_total='.0f',
                             ridetime_total_hms='', rtc='', satellites='%.0f', satellitesused='%.0f', slope='%.0f', speed='%.1f', speed_avg='%.1f',
                             speed_avg_digits='%.0f', speed_avg_tenths='%.0f', speed_digits='%.0f', speed_max='%.1f', speed_max_digits='%.0f', speed_max_tenths='%.0f',
                             speed_tenths='%.0f', temperature='%.0f', temperature_avg='%.1f', temperature_max='%.0f', temperature_min='%.0f',
                             timeon='%.0f', timeon_hms='', time_cadence_reset='%.0f', track='%.1f', utc='')

        # Units - name has to be identical as in params
        self.units = dict(Q='', altitude='m', cadence='RPM', climb='m/s', distance='km', eps='', epx='', epv='', ept='',
                          dtime='s', gpsfix='', gpsfix_time='', heartrate='BPM', latitude='', longitude='', odometer='km', pressure='hPa',
                          riderweight='kg', ridetime='s', ridetime_hms='', ridetime_total='s', ridetime_total_hms='', satellites='',
                          satellitesused='', slope='%', speed='km/h', temperature=degC, timeon='s', timeon_hms='', time_cadence_reset='s',
                          track='')

        # Allowed units - user can switch between those when editing value
        # FIXME switch to mi when mi/h are set for speed
        # FIXME switch to mi/h when mi are set for odometer
        self.units_allowed = dict(odometer=['km', 'mi'], riderweight=['kg', 'st', 'lb'], slope=['%', degC],
                                  speed=['km/h', 'm/s', 'mi/h'], temperature=[degC, 'F', 'K'])

        # Params description FIXME localisation
        self.p_desc = dict(altitude_home='Home altitude', odometer='Odometer', odometer_units='Odometer units',
                           riderweight='Rider weight', riderweight_units='Rider weight units', speed_units='Speed units',
                           temperature_units='Temp. unit')

        # Define id a param is editable FIXME editor type - number, calendar, unit, etc.
        # 0 - unit editor
        # 1 - number editor
        # Params that can be changed in Settings by user
        self.p_editable = dict(Q=1, altitude_home=1, odometer=1, odometer_units=0,
                               riderweight=1, riderweight_units=0, speed_units=0, temperature_units=0)

        self.p_resettable = dict(distance=1, odometer=1, ridetime=1, speed_max=1,
                                 cadence=1, cadence_avg=1, cadence_max=1)

        # Do not record any speed below 2.5 m/s
        self.speed_gps_low = 2.5
        self.l.info("[RP] speed_gps_low treshold set to {}".format(self.speed_gps_low))

        # Do not show speed below 1 m/s
        self.speed_gps_noise = 1
        self.l.info("[RP] speed_gps_noise treshold set to {}".format(self.speed_gps_noise))

        self.update_param("speed_max")
        self.split_speed("speed_max")
        self.update_param("altitude_home")
        self.l.info("[RP] altitude_home set to {}".format(self.params["altitude_home"]))
        # Temporary
        self.p_raw["Q"] = self.bmp183_sensor.Q

    def start_sensors(self):
        self.l.info("[RP] Starting sensors thread")
        self.sensors.start()
        self.l.info("[RP] Starting GPS thread")
        self.gps.start()
        self.l.info("[RP] Starting BMP thread")
        self.bmp183_sensor.start()

    def setup_ridelog(self):
        ride_log_filename = "log/ride." + \
            strftime("%Y-%m-%d-%H:%M:%S") + ".log"
        logging.getLogger('ride').setLevel(logging.INFO)
        ride_log_handler = logging.handlers.RotatingFileHandler(
            ride_log_filename)
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
        self.l.info("[RP] Stopping sensors thread")
        self.sensors.stop()
        self.l.info("[RP] Stopping GPS thread")
        self.gps.stop()
        self.l.info("[RP] Stopping BMP thread")
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
        # FIXME Move this to gps module?
        dt_adjustment = self.occ.rp.gps.time_adjustment_delta
        if dt_adjustment > 0:
            self.p_raw["dtime"] = self.p_raw["dtime"] - dt_adjustment
            self.occ.rp.gps.time_adjustment_delta = 0
            self.l.info("[RP] dtime adjusted by {}".format(dt_adjustment))
            self.occ.rp.gps.time_adjustment_delta = 0
            # FIXME Correct other parameters like ridetime
        self.l.debug("[RP] timestamp: {} dtime {}".format(t, self.p_raw["dtime"]))
        self.read_ble_data()
        self.read_bmp183_data()
        self.calculate_altitude()
        self.calculate_time_related_parameters()
        self.p_raw["daltitude_cumulative"] += self.p_raw["daltitude"]
        self.p_raw["ddistance_cumulative"] += self.p_raw["ddistance"]
        if self.p_raw["ddistance_cumulative"] == 0:
            self.p_raw["slope"] = 0
        # FIXME make proper param for tunnig. Calculate slope if the distance
        # delta was grater than 8,4m
        elif self.p_raw["ddistance_cumulative"] > 8.4:
            self.p_raw["slope"] = self.p_raw[
                "daltitude_cumulative"] / self.p_raw["ddistance_cumulative"]
            self.l.debug("[RP] daltitude_cumulative: {} ddistance_cumulative: {}".
                         format(self.p_raw["daltitude_cumulative"], self.p_raw["ddistance_cumulative"]))
            self.p_raw["daltitude_cumulative"] = 0
            self.p_raw["ddistance_cumulative"] = 0
        self.l.debug("[RP] slope: {}".format(self.p_raw["slope"]))
        self.update_params()

    def calculate_time_related_parameters(self):
        dt = self.p_raw["dtime"]
        self.p_raw["timeon"] += dt
        # FIXME calculate with speed not speed_gps when bt sensors are set up
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
            self.l.debug("[RP] speed_gps: {}, distance: {}, odometer: {}".format(s, self.p_raw["distance"], self.p_raw["odometer"]))
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
            self.l.error(
                "[RP] {} has no description defined".format(param_name))
            return "No description"

    def clean_value(self, variable, empty=0):
        if not math.isnan(variable):
            return variable
        else:
            return empty

    def read_ble_data(self):
        if self.ble:
            data = self.ble.get_data()
            self.p_raw['wheel_time_stamp'] = self.clean_value(data['wheel_time_stamp'])
            self.p_raw['wheel_rev_time'] = self.clean_value(data['wheel_rev_time'])
            self.p_raw['cadence_time_stamp'] = self.clean_value(data['cadence_time_stamp'])
            if (time.time() - self.p_raw['cadence_time_stamp']) < self.p_raw['cadence_expiry_time']:
                self.p_raw['cadence'] = self.clean_value(data['cadence'])
            else:
                self.p_raw["cadence"] = 0
        else:
            #FIXME Add time check to avoid too many messages
            self.l.info('[RP] BLE sensor not set, trying to set it...')
            self.ble = self.sensors.get_sensor('ble')

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
        # FIXME That will have to be changed with bluetooth speed sensor
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
        # FIXME Add and use time since reset not timeon
        tt = self.p_raw["timeon"]
        ta_new = (t * dt + ta * tt) / (tt + dt)
        self.p_raw["temperature_avg"] = ta_new

    def calculate_avg_cadence(self):
        dt = self.p_raw["dtime"]
        c = self.p_raw["cadence"]
        ca = self.p_raw["cadence_avg"]
        tt = self.p_raw["ridetime"] - self.p_raw["time_cadence_reset"]
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
        # Make sure there is no _digits, _tenths, _hms at the end
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
        self.reset_cadence()

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
            self.l.error(
                "[RP] Formatting not available: param_name = {}".format(param_name))
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
        # FIXME proper localisation would be nice....
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
        # FIXME Kalman filter in bmp183 module will obsolete this code
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
        self.l.debug("[RP] altitude: {}, daltitude {}".format(
            self.p_raw["altitude"], self.p_raw["daltitude"]))

    def calculate_pressure_at_sea_level(self):
        # Set pressure_at_sea_level based on given altitude
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

    def update_cadence(self):
        self.calculate_avg_cadence()
        self.set_max("cadence")
        self.update_param("cadence")
        self.update_param("cadence_avg")
        self.update_param("cadence_max")
