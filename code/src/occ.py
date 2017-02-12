#!/usr/bin/python

from layout import layout
from operator import add
from pygame.locals import USEREVENT
from pygame.locals import NOEVENT
from rendering import rendering
from ride_parameters import ride_parameters
from time import sleep
from time import strftime
import logging
import logging.handlers
import lxml.etree as eltree
import os
import platform
import pygame
import signal

LOG_LEVEL = {"DEBUG": logging.DEBUG,
             "INFO": logging.INFO,
             "WARNING": logging.WARNING,
             "ERROR": logging.ERROR,
             "CRITICAL": logging.CRITICAL}

LONG_CLICK = 800  # ms of long click
SWIPE_LENGTH = 30  # pixels of swipe

EV_UPDATE_VALUES = USEREVENT + 1
EV_SAVE_CONFIG = USEREVENT + 2
# FIXME Cadence simulation to be removed when bluetooth sensor goes live
EV_CADENCE_EMUL = USEREVENT + 3

REFRESH_TIME = 1000
CONFIG_SAVE_TIME = 15000
# FIXME Cadence simulation to be removed when bluetooth sensor goes live
CADENCE_EMUL = 650


class open_cycling_computer():
    'Class for PiTFT 2.8" 320x240 cycling computer'

    def __init__(self, simulate=False, width=240, height=320):
        self.simulate = simulate
        self.r = logging.getLogger('ride')
        self.l = logging.getLogger('system')
        pygame.init()
        if not self.simulate:
            pygame.event.set_grab(True)
            pygame.mouse.set_visible(0)
        self.l.debug(
            "[OCC] EV_UPDATE_VALUES to be generated every {} ms".format(REFRESH_TIME))
        pygame.time.set_timer(EV_UPDATE_VALUES, REFRESH_TIME)
        self.l.debug("[OCC] EV_SAVE_CONFIG to be generated every {} s".format(
            CONFIG_SAVE_TIME / 1000))
        pygame.time.set_timer(EV_SAVE_CONFIG, CONFIG_SAVE_TIME)
        self.l.debug(
            "[OCC] Cadence event emulation every {} ms".format(CADENCE_EMUL))
        pygame.time.set_timer(EV_CADENCE_EMUL, CADENCE_EMUL)
        self.width = width
        self.height = height
        self.l.debug("[OCC] Screen size is {} x {}".format(
            self.width, self.height))
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.l.debug("[OCC] Calling ride_parameters")
        self.rp = ride_parameters(self, simulate)
        self.config_path = "config/config.xml"
        self.l.debug(
            "[OCC] Reading config. Path = {}".format(self.config_path))
        self.read_config()
        self.l.debug(
            "[OCC] Setting layout. Path = {}".format(self.layout_path))
        self.layout = layout(self, self.layout_path)
        self.l.debug("[OCC] Starting RP sensors")
        self.rp.start_sensors()
        self.l.debug("[OCC] Setting up rendering")
        self.rendering = rendering(self.layout)
        self.l.debug("[OCC] Starting rendering thread")
        self.rendering.start()
        self.released_t = 0
        self.rel_movement = 0
        self.pressed_t = 0
        self.config = 0
        self.pressed_pos = 0
        self.layout_path = 0
        self.released_pos = 0
        self.add_rel_motion = 0
        self.running = True
        self.refresh = False

    def event_iterator(self):
        while True:
            yield pygame.event.wait()
            while True:
                event = pygame.event.poll()
                if event.type == NOEVENT:
                    break
                else:
                    yield event

    def force_refresh(self):
        self.refresh = True

    def read_config(self):
        self.l.debug("[OCC][F] read_config")
        # FIXME error handling and emergency config read if main is corrupted
        try:
            config_tree = eltree.parse(self.config_path)
        except IOError:
            self.l.exception(
                "[OCC] I/O Error when trying to parse config file. Falling back to default config")
            self.config_path = "config/config_base.xml"
            try:
                config_tree = eltree.parse(self.config_path)
            except IOError:
                self.l.exception(
                    "[OCC] I/O Error when trying to parse to default config. Quitting!!")
                self.cleanup()
        self.config = config_tree.getroot()
        try:
            log_level = self.config.find("log_level").text
            self.switch_log_level(log_level)
            self.rp.params["debug_level"] = log_level
        except AttributeError:
            pass
        try:
            self.layout_path = self.config.find("layout_path").text
        except AttributeError:
            self.layout_path = "layouts/default.xml"
            self.l.error(
                "[OCC] Missing layout path, falling back to default.xml")
        error_list = []
        try:
            self.rp.p_raw["riderweight"] = float(
                self.config.find("riderweight").text)
        except AttributeError:
            error_list.append("riderweight")
        try:
            self.rp.units["riderweight"] = self.config.find(
                "riderweight_units").text
        except AttributeError:
            error_list.append("riderweight_units")
        try:
            self.rp.p_raw["altitude_home"] = float(
                self.config.find("altitude_home").text)
        except AttributeError:
            error_list.append("")
        try:
            self.rp.units["altitude_home"] = self.config.find(
                "altitude_home_units").text
        except AttributeError:
            error_list.append("altitude_home")
        try:
            self.rp.p_raw["odometer"] = float(
                self.config.find("odometer").text)
        except AttributeError:
            error_list.append("odometer")
        try:
            self.rp.units["odometer"] = self.config.find("odometer_units").text
        except AttributeError:
            error_list.append("odometer")
        try:
            self.rp.p_raw["ridetime_total"] = float(
                self.config.find("ridetime_total").text)
        except AttributeError:
            error_list.append("ridetime_total")
        try:
            self.rp.p_raw["speed_max"] = float(
                self.config.find("speed_max").text)
        except AttributeError:
            error_list.append("speed_max")
        try:
            self.rp.units["speed"] = self.config.find("speed_units").text
        except AttributeError:
            error_list.append("speed")
        try:
            self.rp.units["temperature"] = self.config.find(
                "temperature_units").text
        except AttributeError:
            error_list.append("temperature")
        self.rp.update_param("speed_max")
        self.rp.split_speed("speed_max")
        if len(error_list) > 0:
            for item in error_list:
                self.l.error("[OCC] Missing: {} in config file".format(item))
            error_list = []

    def switch_log_level(self, log_level):
        self.l.setLevel(LOG_LEVEL[log_level])
        self.l.log(100, "[OCC] Switching to log_level {}".format(log_level))

    def write_config(self):
        self.l.debug("[OCC] Writing config file")
        log_level = logging.getLevelName(self.l.getEffectiveLevel())
        config_tree = eltree.Element("config")
        eltree.SubElement(config_tree, "log_level").text = log_level
        eltree.SubElement(
            config_tree, "layout_path").text = self.layout.layout_path
        eltree.SubElement(config_tree, "riderweight").text = unicode(
            self.rp.p_raw["riderweight"])
        eltree.SubElement(config_tree, "riderweight_units").text = unicode(
            self.rp.units["riderweight"])
        eltree.SubElement(config_tree, "altitude_home").text = unicode(
            self.rp.p_raw["altitude_home"])
        eltree.SubElement(config_tree, "altitude_home_units").text = unicode(
            self.rp.units["altitude_home"])
        eltree.SubElement(config_tree, "odometer").text = unicode(
            self.rp.p_raw["odometer"])
        eltree.SubElement(config_tree, "odometer_units").text = unicode(
            self.rp.units["odometer"])
        eltree.SubElement(config_tree, "ridetime_total").text = unicode(
            self.rp.p_raw["ridetime_total"])
        eltree.SubElement(config_tree, "speed_max").text = unicode(
            self.rp.p_raw["speed_max"])
        eltree.SubElement(config_tree, "speed_units").text = unicode(
            self.rp.units["speed"])
        eltree.SubElement(config_tree, "temperature_units").text = unicode(
            self.rp.units["temperature"])
        # FIXME error handling for file operation
        eltree.ElementTree(config_tree).write(
            self.config_path, encoding="UTF-8", pretty_print=True)

    def screen_touched_handler(self, time_now):
        if (time_now - self.pressed_t) > LONG_CLICK:
            self.l.debug("[OCC] LONG CLICK : {} {} {}".format(
                time_now, self.pressed_t, self.pressed_pos))
            self.layout.check_click(self.pressed_pos, 1)
            self.reset_motion()
        if self.released_t != 0:
            self.l.debug("[OCC] SHORT CLICK : {} {} {}".format(
                time_now, self.pressed_t, self.pressed_pos))
            self.layout.check_click(self.pressed_pos, 0)
            self.reset_motion()
        dx = self.rel_movement[0]
        dy = self.rel_movement[1]
        if (abs(dx)) > SWIPE_LENGTH:
            if dx > 0:
                self.l.debug("[OCC] SWIPE X RIGHT to LEFT : {} {} {} {} {} {}".
                             format(time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
                self.layout.check_click(self.pressed_pos, 2)
                self.reset_motion()
            else:
                self.l.debug("[OCC] SWIPE X LEFT to RIGHT : {} {} {} {} {} {}".
                             format(time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
                self.layout.check_click(self.pressed_pos, 3)
                self.reset_motion()
        elif (abs(dy)) > SWIPE_LENGTH:
            if dy < 0:
                self.l.debug("[OCC] SWIPE X BOTTOM to TOP : {} {} {} {} {} {}".
                             format(time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
                self.layout.check_click(self.pressed_pos, 4)
                self.reset_motion()
            else:
                self.l.debug("[OCC] SWIPE X TOP to BOTTOM : {} {} {} {} {} {}".
                             format(time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
                self.layout.check_click(self.pressed_pos, 5)
                self.reset_motion()

    def event_handler(self, event, time_now):
        if event.type == pygame.QUIT:
            self.running = False
            self.l.debug("[OCC] QUIT {}".format(time_now))
        elif event.type == EV_UPDATE_VALUES:
            self.l.debug("[OCC] calling update_values {}".format(time_now))
            self.rp.update_values()
        elif event.type == EV_CADENCE_EMUL:
            self.l.debug("[OCC] calling calculate_cadence {}".format(time_now))
            self.rp.calculate_cadence()
        elif event.type == EV_SAVE_CONFIG:
            self.l.debug("[OCC] calling write_config {}".format(time_now))
            self.write_config()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.pressed_t = time_now
            self.pressed_pos = pygame.mouse.get_pos()
            # Read rel to clean the value generated on click
            pressed_rel = pygame.mouse.get_rel()
            self.add_rel_motion = True
            self.layout.render_button = self.pressed_pos
            self.l.debug("[OCC] DOWN:{} {} {}".format(
                self.pressed_t, self.released_t, self.pressed_pos))
        elif event.type == pygame.MOUSEBUTTONUP:
            # That check prevents setting release_x after long click
            if (self.pressed_t != 0):
                self.released_t = time_now
                self.released_pos = pygame.mouse.get_pos()
            self.add_rel_motion = False
            self.layout.render_button = None
            self.l.debug("[OCC] UP: {} {} {}".format(
                self.pressed_t, self.released_t, self.pressed_pos))
        elif event.type == pygame.MOUSEMOTION:
            pressed_rel = pygame.mouse.get_rel()
            if self.add_rel_motion:
                self.rel_movement = tuple(
                    map(add, self.rel_movement, pressed_rel))
            self.l.debug("[OCC] MOTION: {}".format(self.rel_movement))
        # self.l.debug("[OCC] ticking:time_now:{} pressed_t:{} pressed_pos:{} released_t:{} released_pos:{}". \
        # format(time_now, self.pressed_t, self.pressed_pos, self.released_t,
        # self.released_pos))
        if self.pressed_t != 0:
            self.refresh = True
            self.screen_touched_handler(time_now)

    def main_loop(self):
        self.l.debug("[OCC][F] main_loop")
        self.reset_motion()
        while self.running:
            for event in self.event_iterator():
                time_now = pygame.time.get_ticks()
                self.event_handler(event, time_now)
                if not self.running:
                    break
                if self.refresh:
                    self.refresh = False
                    self.layout.layout_changed = 0
                    self.rendering.force_refresh()

    def reset_motion(self):
        self.l.debug("[OCC][F] reset_motion")
        self.pressed_t = 0
        self.released_t = 0
        self.pressed_pos = (0, 0)
        self.released_pos = (0, 0)
        self.rel_movement = (0, 0)
        self.layout.render_button = None
        self.add_rel_motion = False
        pygame.event.clear()

    def cleanup(self):
        sleep(1)
        self.rp.stop()
        try:
            self.rendering.stop()
        except AttributeError:
            pass
        try:
            self.write_config()
        except AttributeError:
            pass
        try:
            self.layout.write_layout()
        except AttributeError:
            pass
        pygame.quit()
        self.l.debug("[OCC] Log end")
        quit()


def quit_handler(signal, frame):
    main_window.cleanup()

if __name__ == "__main__":
    suffix = strftime("%d-%H:%M:%S")
    sys_log_filename = "log/debug." + suffix + ".log"
    logging.getLogger('system').setLevel(logging.DEBUG)
    sys_log_handler = logging.handlers.RotatingFileHandler(sys_log_filename)
    sys_log_format = '[%(levelname)-5s] %(message)s'
    sys_log_handler.setFormatter(logging.Formatter(sys_log_format))
    logging.getLogger('system').addHandler(sys_log_handler)
    sys_logger = logging.getLogger('system')
    signal.signal(signal.SIGTERM, quit_handler)
    signal.signal(signal.SIGINT, quit_handler)
    sys_logger.debug("[OCC] Log start")
    os.environ["SDL_FBDEV"] = "/dev/fb1"
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    # This is a simple check if we're running on Raspberry PI.
    # Switch to simulation mode if we're not
    if (platform.machine() == "armv6l"):
        os.putenv('SDL_VIDEODRIVER', 'fbcon')
        os.putenv('SDL_MOUSEDRV', 'TSLIB')
        simulate = False
    else:
        simulate = True
        sys_logger.warning(
            "Warning! platform.machine() is NOT armv6l. I'll run in simulation mode. No real data will be shown.")
    main_window = open_cycling_computer(simulate)
    sys_logger.debug("[OCC] simulate = {}".format(simulate))
    main_window.main_loop()
    main_window.cleanup()
