#!/usr/bin/python3
## @package gps_mtk3339
#  GPS module. Responsible for connecting to, starting and stopping mtk3339 hardware as sold by Adafruit

from gps import gps
from gps import WATCH_NEWSTYLE
from gps import WATCH_ENABLE
import logging
import mtk3339
import os
import threading
import time
import numbers


## @var fix_mode
# helper variable, modes of GPS fix
fix_mode = {0: "No data",
            1: "No fix",
            2: "Fix 2D",
            3: "Fix 3D"}


## Class for handling GPS mtk3339 hardware, runs in a separate thread.
class gps_mtk3339(threading.Thread):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self, simulate=False):
        threading.Thread.__init__(self)
        self.log = logging.getLogger('system')
        self.simulate = simulate
        self.restart_gps = False
        if not self.simulate:
            self.log.debug("Initialising mtk3339", extra=self.extra)
            ser = mtk3339.mtk3339("/dev/ttyAMA0")
            ser.set_baudrate(115200)
            ser.set_fix_update_rate(1000)
            ser.set_nmea_update_rate(1000)
            # ser.set_nmea_output(gll = 0, rmc = 1, vtg = 0, gga = 5, gsa = 5,
            # gsv = 5)
            ser.set_nmea_output(gll=0, rmc=1, vtg=0, gga=1, gsa=5, gsv=5)
        self.reset_gps_data()
        self.present = False
        self.set_time = True
        self.time_adjustment_delta = 0
        if not self.simulate:
            self.gpsd_link_init()
        else:
            self.present = True

    def gpsd_link_init(self):
        try:
            self.log.debug("Trying to establich serial link", extra=self.extra)
            # FIXME Add check for running gpsd. Restart if missing. Consider watchdog thread to start gpsd
            # FIXME Check how that reacts for missing gps hardware
            self.data = gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
            self.present = True
        except:
            self.log.error("Cannot talk to GPS", extra=self.extra)
            self.present = False
            raise IOError("Communication with GPS mtk3339 failed")

    ## Helper function that restarts gpsd using system shell command "service gpsd restart"
    #  @param self The python object self
    def restart_gpsd(self):
        command = "service gpsd restart"
        ret = os.system(command)
        if ret == 0:
            self.log.info("gpsd restarted succesfully", extra=self.extra)
            self.restart_gps = False
            self.gpsd_link_init()
        else:
            self.log.info("gpsd fails to restart with error {}".format(ret), extra=self.extra)
            time.sleep(3)

    ## Main loop of gps_mtk3339 module. Responsible for restarting gps and processing gps messages into locally stored values describing current location.
    #  @param self The python object self
    def run(self):
        if self.present:
            self.running = True
            if not self.simulate:
                while self.running:
                    if self.restart_gps:
                        self.restart_gpsd()
                    self.process_gps()
            else:
                self.latitude = 52.0001
                self.longitude = -8.0001
                self.utc = "utc"
                self.climb_gps = 0.2
                self.speed_gps = 9.99
                self.altitude_gps = 50.0
                self.satellites = 10
                self.satellitesused = 4
                self.fix_mode_gps = fix_mode[2]
                self.fix_time_gps = "N/A"
                time.sleep(1)

    def process_gps(self):
        timestamp = time.time()
        self.log.debug("timestamp: {}, running: {},".format(timestamp, self.running), extra=self.extra)
        gps_data_available = False
        try:
            # FIXME Fails sometimes with ImportError from gps.py - see TODO 21
            # [IN TESTING]
            self.data.next()
            data = self.data
            gps_data_available = True
        except StopIteration:
            self.log.error("StopIteration exception in GPS. Restarting GPS in 10 s", extra=self.extra)
            # FIXME Reinit gps after a delay (from RP?) as restarting gpsd doesn't help
            # so this need to be in the loop as well: self.data =
            # gps(mode=WATCH_ENABLE | WATCH_NEWSTYLE)
            time.sleep(10)
            self.restart_gps = True
            pass
        if gps_data_available:
            self.latitude = data.fix.latitude
            self.longitude = data.fix.longitude
            self.utc = data.utc
            self.climb_gps = data.fix.climb
            self.speed_gps = data.fix.speed
            self.track_gps = data.fix.track
            self.altitude_gps = data.fix.altitude
            self.fix_mode_gps = fix_mode[data.fix.mode]
            self.eps = data.fix.eps
            self.epx = data.fix.epx
            self.epv = data.fix.epv
            self.ept = data.fix.ept
            if isinstance(data.fix.time, float):
                self.fix_time = data.fix.time
            else:
                # Workaround for python3 bug
                # ImportError: Failed to import _strptime because the import
                # lock is held by another thread.
                try:
                    # self.data.fix.time is a string, so parse it to get the
                    # float time value.
                    self.fix_time = time.mktime(time.strptime(
                        data.fix.time, '%Y-%m-%dT%H:%M:%S.%fZ'))
                except ImportError:
                    self.log.critical("self.fix_time {}".format(self.fix_time), extra=self.extra)
                    pass
            if self.set_time:
                if (self.utc is not None):
                    if (len(self.utc) > 5):
                        self.set_system_time()
            try:
                sat = self.data.satellites
                self.satellites = len(sat)
                self.satellitesused = self.data.satellites_used
            except AttributeError:
                self.log.error("AttributeError exception in GPS", extra=self.extra)
                pass
            self.log.debug("timestamp: {}, fix time: {}, UTC: {}, Satellites: {}, Used: {}"
                         .format(timestamp, self.fix_time, self.utc, self.satellites, self.satellitesused))
            self.log.debug("Mode: {}, Lat,Lon: {},{}, Speed: {}, Altitude: {}, Climb: {}"
                         .format(self.fix_mode, self.latitude, self.longitude, self.speed, self.altitude, self.climb))
        else:
            self.reset_gps_data()

    ## Resets all gps data to the initial state
    #  @param self The python object self
    def reset_gps_data(self):
        self.log.debug("Setting null values to GPS params", extra=self.extra)
        self.latitude = numbers.NAN
        self.longitude = numbers.NAN
        self.utc = None
        self.climb_gps = numbers.NAN
        self.speed_gps = numbers.NAN
        self.altitude_gps = numbers.NAN
        self.fix_mode_gps = fix_mode[1]
        self.fix_time_gps = numbers.NAN
        self.satellites = 0
        self.satellitesused = 0
        self.track_gps = numbers.NAN
        self.eps = numbers.NAN
        self.epx = numbers.NAN
        self.epv = numbers.NAN
        self.ept = numbers.NAN

    ## Returns dictionary withvalues describing current location
    #  @param self The python object self
    def get_data(self):
        r = dict(latitude=self.latitude, longitude=self.longitude,
                 altitude_gps=self.altitude_gps, speed_gps=self.speed_gps, utc=self.utc,
                 satellitesused=self.satellitesused, satellites=self.satellites,
                 fix_mode_gps=self.fix_mode_gps, climb_gps=self.climb_gps, track_gps=self.track_gps,
                 eps=self.eps, epx=self.epx, epv=self.epv, ept=self.ept,
                 fix_time_gps=self.fix_time_gps, time_adjustment_delta=self.time_adjustment_delta)
        return r

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False

    def set_system_time(self):
        tt_before = time.time()
        self.log.info("time.time before {}".format(tt_before), extra=self.extra)
        self.log.info("Setting UTC system time to {}".format(self.utc), extra=self.extra)
        command = 'date -u --set={} "+%Y-%m-%dT%H:%M:%S.000Z" 2>&1 > /dev/null'.format(
            self.utc)
        ret = os.system(command)
        if ret == 0:
            self.set_time = False
            tt_after = time.time()
            self.time_adjustment_delta = tt_before - tt_after
            self.log.info("time.time after {}".format(tt_after), extra=self.extra)
            self.log.info(
                "time.time delta {}".format(self.time_adjustment_delta))
