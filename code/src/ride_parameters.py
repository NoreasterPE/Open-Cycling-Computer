#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package ride_parameters
#  Module for handling all ride parameters. This is the main module responsible for pulling all data together and preparing values for displaying, logging and saving.
from time import strftime
import unit_converter
import numbers
import logging
import math
import time
import sched
import wheel
import ride_log


## @var RIDE_PARAMETERS_UPDATE
# Period of time in m between ride parameters update events.
RIDE_PARAMETERS_UPDATE = 1.0


## Class for handling all ride parameters
class ride_parameters():
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'ride_param'}

    ## The constructor
    #  @param self The python object self
    #  @param occ OCC instance
    #  @param simulate Decides if ride_parameters runs in simulation mode or real device mode.
    def __init__(self, occ, simulate=False):
        ## @var occ
        # OCC Handle
        self.occ = occ
        ## @var l
        # System logger handle
        self.log = logging.getLogger('system')
        ## @var stopping
        # Variable indicating is stopping is in progress
        self.stopping = False
        ## @var ride_log
        # Ride logger handle
        self.ride_log = ride_log.ride_log()
        ## @var uc
        # Units converter
        self.uc = unit_converter.unit_converter()
        ## @var event_scheduler
        # Event scheduler triggering parameters update and writing ride log entry
        self.event_scheduler = sched.scheduler(time.time, time.sleep)
        self.log.info("Initialising sensors", extra=self.extra)
        ## @var sensors
        # Handle of sensors instance
        self.sensors = occ.sensors
        ## @var ble_sc
        # Handle of BLE speed and cadence sensor
        self.ble_sc = self.sensors.get_sensor('ble_sc')
        ## @var bmp183
        # Handle of bmp183 sensor
        self.bmp183 = self.sensors.get_sensor('bmp183')

        self.suffixes = ("_digits", "_tenths", "_hms")

        self.p_raw = dict(time_stamp=time.time(),
                          # Time delta since last p_raw update
                          time_delta=1, time_adjustment_delta=0.0,
                          altitude_delta_cumulative=0.0,
                          odometer=0.0, distance_delta=0.0, distance_delta_cumulative=0.0, distance=0.0,
                          ride_time_reset=0.0001,
                          rider_weight=0.0,
                          ride_time=0.0, ride_time_total=0.0,
                          slope=0.0,
                          speed=0.0, speed_avg=0.0, speed_max=0.0,
                          speed_low=1.0,
                          temperature_avg=0.0,
                          timeon=0.0001, utc='', rtc='')

        # Internal units
        self.p_raw_units = dict(
            distance='m', time_delta='s', odometer='m', rider_weight='kg', wheel_size='',
            ride_time='s', ride_time_total='s', slope='m/m', speed='m/s', timeon='s', ride_time_reset='s')

        # Params of the ride ready for rendering.
        self.params = dict(
            distance=0, time_delta=0, odometer=0.0, rider_weight=0.0,
            wheel_size='', wheel_circ='', ride_time='', ride_time_hms='', ride_time_total='',
            ride_time_total_hms='', rtc='', slope='-', speed='-', speed_avg='-',
            speed_avg_digits='-', speed_avg_tenths='-', speed_digits='-', speed_max='-', speed_max_digits='-',
            speed_max_tenths='-', speed_tenths='-', timeon='', timeon_hms='', ride_time_reset='', utc='',
            # Editor params
            editor_index=0, variable=None,
            variable_description=None, variable_raw_value=None, variable_unit=None, variable_value=None)

        # Formatting strings for params.
        self.p_format = dict(
            distance='%.1f', time_delta='%.2f', odometer='%.0f',
            rider_weight='%.1f', ride_time='%.0f', ride_time_hms='', ride_time_total='.0f',
            ride_time_total_hms='', rtc='', slope='%.0f', speed='%.1f', speed_avg='%.1f',
            speed_avg_digits='%.0f', speed_avg_tenths='%.0f', speed_digits='%.0f', speed_max='%.1f', speed_max_digits='%.0f', speed_max_tenths='%.0f',
            speed_tenths='%.0f', timeon='%.0f', timeon_hms='', ride_time_reset='%.0f', utc='')

        # Units - name has to be identical as in params
        # FIXME rename to p_units for consistency
        self.units = dict(
            distance='km', time_delta='s', odometer='km',
            rider_weight='kg', wheel_size='', ride_time='s', ride_time_hms='', ride_time_total='s', ride_time_total_hms='',
            slope='%', speed='km/h', timeon='s', timeon_hms='', ride_time_reset='s')

        # Allowed units - user can switch between those when editing value
        # FIXME switch to mi when mi/h are set for speed
        # FIXME switch to mi/h when mi are set for odometer
        self.units_allowed = dict(
            odometer=['km', 'mi'], rider_weight=['kg', 'st'],
            # slope=['%', 'C'],
            wheel_size=[''],
            speed=['km/h', 'm/s', 'mi/h'], temperature=['C', 'F'])

        self.update_param("speed_max")
        self.split_speed("speed_max")

        #FIXME Use wheel size from config
        w = wheel.wheel()
        self.p_raw["wheel_circ"] = w.get_circ("700x25C")

        self.ble_hr = self.init_sensor_data("ble_hr")
        self.ble_sc = self.init_sensor_data("ble_sc")
        self.bmp183 = self.init_sensor_data("bmp183")
        self.log.debug("Setting up event scheduler", extra=self.extra)
        self.event_scheduler.enter(RIDE_PARAMETERS_UPDATE, 1, self.schedule_update_event)

    def init_sensor_data(self, sensor_name):
        sensor = self.sensors.get_sensor(sensor_name)
        sensor_prefix = sensor.get_prefix()
        # Get all parameters provided by sensor
        sensor_raw_data = sensor.get_raw_data()
        # Add prefix to keys in the dictionary
        sensor_raw_data = {sensor_prefix + "_" + key: value for key, value in sensor_raw_data.items()}
        # Add the blr_hr parameters to p_raw
        self.p_raw.update(sensor_raw_data)

        sensor_units = sensor.get_units()
        # Add prefix to keys in the dictionary
        sensor_units = {sensor_prefix + "_" + key: value for key, value in sensor_units.items()}
        # Add the blr_hr parameters to p_raw
        self.units.update(sensor_units)

        sensor_raw_units = sensor.get_raw_units()
        # Add prefix to keys in the dictionary
        sensor_raw_units = {sensor_prefix + "_" + key: value for key, value in sensor_raw_units.items()}
        # Add the blr_hr parameters to p_raw
        self.p_raw_units.update(sensor_raw_units)

        sensor_formats = sensor.get_formats()
        # Add prefix to keys in the dictionary
        sensor_formats = {sensor_prefix + "_" + key: value for key, value in sensor_formats.items()}
        # Add the blr_hr parameters to p_raw
        self.p_format.update(sensor_formats)
        return sensor

    def schedule_update_event(self):
        self.log.debug("Calling update values from event scheduler", extra=self.extra)
        self.update_values()
        self.ride_log.add_entry(self.params)
        if not self.stopping:
            #Setting up next update event
            self.event_scheduler.enter(RIDE_PARAMETERS_UPDATE, 1, self.schedule_update_event)
            t = self.event_scheduler.run(blocking=False)
            self.log.debug("Event scheduler, next event in: {0:.3f}".format(t), extra=self.extra)

    def stop(self):
        self.stopping = True
        self.log.debug("Stop started", extra=self.extra)
        self.log.debug("Stopping sensors thread", extra=self.extra)
        self.sensors.stop()
        self.log.debug("Stop finished", extra=self.extra)

    def __del__(self):
        self.stop()

    def update_values(self):
        t = time.time()
        self.p_raw["time_delta"] = t - self.p_raw["time_stamp"]
        self.p_raw["time_stamp"] = t
        #FIXME Time adjustment
        #dt_adjustment = self.p_raw['time_adjustment_delta']
        #if dt_adjustment > 0:
        #    self.p_raw["time_delta"] = self.p_raw["time_delta"] - dt_adjustment
        #    self.log.info("time_delta adjusted by {}".format(dt_adjustment), extra=self.extra)
        #    self.sensors['gps'].time_adjustment_delta = 0
        #    # FIXME Correct other parameters like ride_time
        #self.log.debug("timestamp: {} time_delta {:10.3f}".format(time.strftime("%H:%M:%S", time.localtime(t)), self.p_raw["time_delta"]), extra=self.extra)
        try:
            self.log.debug("speed dt: {}".format(self.p_raw["ble_sc_wheel_time_stamp"] - self.p_raw["time_stamp"]), extra=self.extra)
            if self.p_raw["time_stamp"] - self.p_raw["ble_sc_wheel_time_stamp"] < 2.0:
                self.p_raw['speed'] = self.p_raw["wheel_circ"] / (self.p_raw["ble_sc_wheel_rev_time"])
                #self.log.debug("speed: {} ts {} {}".format(self.p_raw["speed"], self.p_raw["ble_sc_wheel_time_stamp"], self.p_raw["time_stamp"]), extra=self.extra)
                if math.isnan(self.p_raw["speed"]):
                    self.p_raw["speed"] = 0.0
        except (KeyError, ZeroDivisionError):
            self.p_raw["speed"] = 0.0

        self.calculate_time_related_parameters()
        try:
            self.p_raw["altitude_delta_cumulative"] += self.p_raw["altitude_delta"]
            self.p_raw["distance_delta_cumulative"] += self.p_raw["distance_delta"]
            if self.p_raw["distance_delta_cumulative"] == 0:
                self.p_raw["slope"] = 0
            # FIXME make proper param for tunning. Calculate slope if the distance
            # delta was grater than 8,4m. That's related to altimeter accurancy. Calcs to be included in the project.
            elif self.p_raw["distance_delta_cumulative"] > 8.4:
                self.p_raw["slope"] = self.p_raw["altitude_delta_cumulative"] / self.p_raw["distance_delta_cumulative"]
                self.log.debug("altitude_delta_cumulative: {} distance_delta_cumulative: {}".format(self.p_raw["altitude_delta_cumulative"], self.p_raw["distance_delta_cumulative"]), extra=self.extra)
                self.p_raw["altitude_delta_cumulative"] = 0
                self.p_raw["distance_delta_cumulative"] = 0
            self.log.debug("slope: {}".format(self.p_raw["slope"]), extra=self.extra)
        except KeyError:
            self.log.debug("FIXME", extra=self.extra)
            pass
        self.update_params()

    def calculate_time_related_parameters(self):
        dt = self.p_raw["time_delta"]
        self.p_raw["timeon"] += dt
        speed = self.p_raw["speed"]
        dist_delta = float(dt * speed)
        self.p_raw["distance_delta"] = dist_delta
        self.p_raw["distance"] += dist_delta
        self.p_raw["odometer"] += dist_delta
        self.p_raw["ride_time"] += dt
        self.p_raw["ride_time_total"] += dt
        self.p_raw["speed_avg"] = self.p_raw["distance"] / self.p_raw["ride_time"]

    def get_raw_val(self, param):
        if param.endswith("_units"):
            return 0
        else:
            return self.p_raw[param]

    def set_raw_param(self, param_name, value):
        self.log.debug("Setting {} to {} (raw)".format(param_name, value), extra=self.extra)
        self.p_raw[param_name] = value

    def set_param(self, param_name, value):
        self.log.debug("Setting {} to {} ".format(param_name, value), extra=self.extra)
        self.params[param_name] = value

    def get_param(self, param):
        value = None
        try:
            if param.endswith("_units"):
                value = self.get_unit(param[:-6])
            elif param in self.params:
                value = self.params[param]
        except KeyError:
            self.log.error("No unit for {}".format(param), extra=self.extra)
        finally:
            return value

    def get_unit(self, param_name):
        suffixes = ("_min", "_max", "_avg", "_home")
        p = self.strip_end(param_name, suffixes)
        if p.endswith("_units"):
            return None
        else:
            try:
                return self.units[p]
            except KeyError:
                return None

    def get_internal_unit(self, param_name):
        suffixes = ("_min", "_max", "_avg", "_home")
        p = self.strip_end(param_name, suffixes)
        if p.endswith("_units"):
            units = None
        else:
            try:
                units = self.p_raw_units[p]
            except KeyError:
                units = None
        return units

    def split_speed(self, speed_name):
        # FIXME No hardcoded formatting, move to dict
        self.params[speed_name + "_digits"] = self.params[speed_name][:-2]
        self.params[speed_name + "_tenths"] = self.params[speed_name][-1:]

    def update_max_speed(self):
        #FIXME Remove it
        if self.p_raw["speed"] > self.p_raw["speed_max"]:
            self.p_raw["speed_max"] = self.p_raw["speed"]
        self.split_speed("speed_max")

    def set_max(self, param):
        self.p_raw[param + "_max"] = max(self.p_raw[param], self.p_raw[param + "_max"])

    def set_min(self, param):
        self.p_raw[param + "_min"] = min(self.p_raw[param], self.p_raw[param + "_min"])

#   def calculate_avg_temperature(self):
#       dt = self.p_raw["time_delta"]
#       t = self.p_raw["temperature"]
#       ta = self.p_raw["temperature_avg"]
#       tt = self.p_raw["ride_time"]
#       ta_new = (t * dt + ta * tt) / (tt + dt)
#       self.p_raw["temperature_avg"] = ta_new

#   def calculate_avg_ble_sc_cadence(self):
#       dt = self.p_raw["time_delta"]
#       c = self.p_raw["ble_sc_cadence"]
#       ca = self.p_raw["ble_sc_cadence_avg"]
#       tt = self.p_raw["ride_time"]
#       ca_new = (c * dt + ca * tt) / (tt + dt)
#       self.p_raw["ble_sc_cadence_avg"] = ca_new

#   def calculate_avg_ble_hr_heart_rate(self):
#       dt = self.p_raw["time_delta"]
#       hr = self.p_raw["ble_hr_heart_rate"]
#       hra = self.p_raw["ble_hr_heart_rate_avg"]
#       # FIXME ride_time doesn't seem to be right
#       tt = self.p_raw["ride_time"]
#       hr_new = (hr * dt + hra * tt) / (tt + dt)
#       self.p_raw["ble_hr_heart_rate_avg"] = hr_new

    def update_params(self):
        self.update_rtc()
        self.update_param("time_delta")
        self.update_ble_sc_cadence()
        self.update_ble_hr_heart_rate()
        #FIXME temporary fix to show BLE host state
        self.p_raw["ble_host_state"] = self.sensors.get_ble_host_state() + 3
        self.update_param("ble_host_state")
        self.update_param("altitude_home")
        self.update_bmp183()
        self.update_param("distance")
        self.update_param("ride_time")
        self.update_hms("ride_time")
        self.update_hms("ride_time_total")
        self.update_hms("timeon")
        self.update_param("timeon")
        self.update_max_speed()
        self.update_param("speed")
        self.update_param("speed_max")
        self.split_speed("speed")
        self.update_param("speed_avg")
        self.split_speed("speed_avg")
        self.params["utc"] = self.p_raw["utc"]
        self.update_param("odometer")
        self.update_param("rider_weight")
        self.update_param("slope")

    def strip_end(self, param_name, suffix=None):
        # Make sure there is no _digits, _tenths, _hms at the end
        if suffix is None:
            suffix = self.suffixes
        for s in suffix:
            if param_name.endswith(s):
                length = -1 * len(s)
                param_name = param_name[:length]
        return param_name

    def reset_ride(self):
        self.p_raw["distance"] = 0.0
        self.p_raw["ride_time"] = 0.0
        #FIXME To be linked with all sensors reset
        self.ble_hr.reset_data()
        self.ble_sc.reset_data()

    def reset_param(self, param_name):
        self.log.debug("Resetting {}".format(param_name), extra=self.extra)
        self.p_raw[param_name] = 0
        if param_name in ("ride_time", "distance", "cadence", "ble_hr_heart_rate"):
            self.reset_ride()

    def update_param(self, param):
        #print("param = {}, raw value = {} format = {}".format(param, self.p_raw[param], self.p_format[param]))
        if param in self.p_format:
            f = self.p_format[param]
        else:
            self.log.error("Formatting not available: param = {}".format(param), extra=self.extra)
            f = "%.1f"

        if self.p_raw[param] != "-":
            unit_raw = self.get_internal_unit(param)
            unit = self.get_unit(param)
            value = self.p_raw[param]
            if unit_raw != unit:
                value = self.uc.convert(value, unit_raw, unit)
            self.params[param] = f % float(value)
        else:
            self.params[param] = '-'
            self.log.debug("param {} = -".format(param), extra=self.extra)

    def add_zero(self, value):
        if value < 10:
            value = "0" + format(value)
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

    def sanitise(self, param_name):
        if self.params[param_name] == "-0":
            self.params[param_name] = "0"
        if (math.isinf(float(self.params[param_name])) or
                math.isnan(float(self.params[param_name]))):
            self.params[param_name] = '-'

    def update_ble_sc_cadence(self):
        self.log.debug("update_ble_sc_cadence started", extra=self.extra)
        if self.ble_sc:
            if self.ble_sc.is_connected():
                self.log.debug("Fetching ble_sc prefix & data", extra=self.extra)
                data = self.ble_sc.get_raw_data()
                if (time.time() - data["time_stamp"]) < 3.0:  # EXPIRED_DATA_TIME
                    prefix = self.ble_sc.get_prefix()
                    # Add prefix to keys in the dictionary
                    data_with_prefix = {prefix + "_" + key: value for key, value in data.items()}
                    self.log.debug("{}".format(data_with_prefix), extra=self.extra)
                    for param in data_with_prefix:
                        self.p_raw[param] = data_with_prefix[param]
                else:
                    #FIXME Temporary fix for expired data
                    self.p_raw["ble_sc_heart_rate"] = numbers.NAN
                    self.log.debug("ble_sc data expired", extra=self.extra)
                #self.calculate_avg_ble_sc_cadence()
                #self.set_max("ble_sc_cadence")
                self.update_param("ble_sc_cadence")
                self.sanitise("ble_sc_cadence")
                #self.update_param("ble_sc_cadence_avg")
                #self.sanitise("ble_sc_cadence_avg")
                self.update_param("ble_sc_cadence_max")
                self.sanitise("ble_sc_cadence_max")
        else:
            self.log.debug("ble_sc_connection lost", extra=self.extra)
        self.log.debug("update_ble_sc_cadence finished", extra=self.extra)

    def update_ble_hr_heart_rate(self):
        self.log.debug("update_ble_hr_heart_rate started", extra=self.extra)
        if self.ble_hr:
            if self.ble_hr.is_connected():
                self.log.debug("Fetching ble_hr prefix & data", extra=self.extra)
                data = self.ble_hr.get_raw_data()
                if (time.time() - data["time_stamp"]) < 3.0:  # EXPIRED_DATA_TIME
                    prefix = self.ble_hr.get_prefix()
                    # Add prefix to keys in the dictionary
                    data_with_prefix = {prefix + "_" + key: value for key, value in data.items()}
                    self.log.debug("{}".format(data_with_prefix), extra=self.extra)
                    for param in data_with_prefix:
                        self.p_raw[param] = data_with_prefix[param]
                else:
                    #FIXME Temporary fix for expired data
                    self.p_raw["ble_hr_heart_rate"] = numbers.NAN
                    self.log.debug("ble_hr data expired", extra=self.extra)
                # FIXME move to ble_hr, sensor module should provide data for display
                #self.calculate_avg_ble_hr_heart_rate()
                self.update_param("ble_hr_heart_rate_min")
                self.sanitise("ble_hr_heart_rate_min")
                #self.update_param("ble_hr_heart_rate_avg")
                #self.sanitise("ble_hr_heart_rate_avg")
                self.update_param("ble_hr_heart_rate_max")
                self.sanitise("ble_hr_heart_rate_max")
                self.update_param("ble_hr_heart_rate")
                self.sanitise("ble_hr_heart_rate")
        else:
            self.log.debug("ble_hr_connection lost", extra=self.extra)
        self.log.debug("update_ble_hr_heart_rate finished", extra=self.extra)

    def update_bmp183(self):
        self.log.debug("update_bmp183 started", extra=self.extra)
        if self.bmp183:
            if self.bmp183.is_connected():
                self.log.debug("Fetching bmp183 prefix & data", extra=self.extra)
                data = self.bmp183.get_raw_data()
                prefix = self.bmp183.get_prefix()
                # Add prefix to keys in the dictionary
                data_with_prefix = {prefix + "_" + key: value for key, value in data.items()}
                self.log.debug("{}".format(data_with_prefix), extra=self.extra)
                for param in data_with_prefix:
                    self.p_raw[param] = data_with_prefix[param]
                # FIXME move to bmp183, sensor module should provide data for display
                #self.calculate_avg_ble_hr_heart_rate()
                self.update_param("bmp183_pressure")
                self.sanitise("bmp183_pressure")
                self.update_param("bmp183_temperature")
                self.sanitise("bmp183_temperature")
                self.update_param("bmp183_altitude")
                self.sanitise("bmp183_temperature")
                self.update_param("bmp183_altitude_delta")
                self.sanitise("bmp183_temperature")
        else:
            self.log.debug("bmp183 connection lost", extra=self.extra)
        self.log.debug("update_bmp183 finished", extra=self.extra)
