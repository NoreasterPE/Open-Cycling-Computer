#!/usr/bin/python

from layout import layout
from operator import add
from pygame.compat import unichr_, unicode_
from pygame.locals import *
from rendering import rendering
from ride_parameters import ride_parameters
from time import *
import locale
import logging as log
import lxml.etree as eltree
import math
import os
import platform
import pygame
import signal
import sys

class open_cycling_computer():
	'Class for PiTFT 2.8" 320x240 cycling computer'
	def __init__(self, simulate = False, width = 240, height = 320):
		log_suffix = strftime("%H:%M:%S")
		log.basicConfig(filename="log/debug." + log_suffix + ".log",level=log.DEBUG)
		self.log = log
		log.debug("{} Log start".format(__name__))
		pygame.init()
		pygame.event.set_grab(True)
		if not simulate:
			pygame.mouse.set_visible(0)
			log.debug("{} simulate =".format(__name__, simulate))
		pygame.time.set_timer(USEREVENT + 1, 1000)
		self.width = width
		self.height = height
		log.debug("{} Screen size is {} x {}".format(__name__, self.width, self.height))
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.clock = pygame.time.Clock()
		log.debug("{} Calling ride_parameters".format(__name__))
		self.rp = ride_parameters(self, simulate)
		self.config_path = "config/config.xml"
		log.debug("{} Reading config. Path = {}".format(__name__, self.config_path))
		self.read_config()
		log.debug("{} Setting layout. Path = {}".format(__name__, self.layout_path))
		self.layout = layout(self, self.layout_path)
		self.rendering = rendering(self.layout)
		log.debug("{} Starting rendering thread".format(__name__))
		self.rendering.start()
		self.running = 1
		self.refresh = False

	def force_refresh(self):
		self.refresh = True

	def read_config(self):
		#FIXME error handling and emergency config read if main is corrupted
		config_tree = eltree.parse(self.config_path)
		self.config = config_tree.getroot()
		self.layout_path = self.config.find("layout_path").text
		try:
			self.rp.p_raw["rider_weight"] = float(self.config.find("rider_weight").text)
			self.rp.units["rider_weight"] = self.config.find("rider_weight_units").text
			self.rp.p_raw["altitude_at_home"] = float(self.config.find("altitude_at_home").text)
			self.rp.units["altitude_at_home"] = self.config.find("altitude_at_home_units").text
			self.rp.p_raw["odometer"] = float(self.config.find("odometer").text)
			self.rp.units["odometer"] = self.config.find("odometer_units").text
		except AttributeError:
			pass

	def write_config(self):
		config_tree = eltree.Element("config")
		eltree.SubElement(config_tree, "layout_path").text = self.layout.layout_path
		eltree.SubElement(config_tree, "rider_weight").text = unicode(self.rp.p_raw["rider_weight"])
		eltree.SubElement(config_tree, "rider_weight_units").text = unicode(self.rp.units["rider_weight"])
		eltree.SubElement(config_tree, "altitude_at_home").text = unicode(self.rp.p_raw["altitude_at_home"])
		eltree.SubElement(config_tree, "altitude_at_home_units").text = unicode(self.rp.units["altitude_at_home"])
		eltree.SubElement(config_tree, "odometer").text = unicode(self.rp.p_raw["odometer"])
		eltree.SubElement(config_tree, "odometer_units").text = unicode(self.rp.units["odometer"])
		#FIXME error handling for file operation
		eltree.ElementTree(config_tree).write(self.config_path, encoding="UTF-8", pretty_print=True)

	def main_loop(self):
		LONG_CLICK = 1000 #ms of long click
		SWIPE_LENGTH = 30 #pixels of swipe
		self.reset_motion()
		while self.running:
			time_now = pygame.time.get_ticks()
			event = pygame.event.poll()
			if event.type == pygame.QUIT:
				self.running = 0
			elif event.type == USEREVENT + 1:
				self.rp.update_values()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				self.pressed_t = time_now
				self.pressed_pos = pygame.mouse.get_pos()
				#Read rel to clean the value generated on click
				pressed_rel =  pygame.mouse.get_rel()
				self.add_rel_motion = True
				log.debug("{0} DOWN:{1} {2} {3}".format(__name__, self.pressed_t, self.released_t, self.pressed_pos))
			elif event.type == pygame.MOUSEBUTTONUP:
				#That check prevents setting release_x after long click
				if (self.pressed_t != 0):
					self.released_t = time_now
					self.released_pos = pygame.mouse.get_pos()
				self.add_rel_motion = False
				log.debug("{0} UP: {1} {2} {3}".format(__name__, self.pressed_t, self.released_t, self.pressed_pos))
			elif event.type == pygame.MOUSEMOTION:
				pressed_rel =  pygame.mouse.get_rel()
				if self.add_rel_motion:
					self.rel_movement = tuple(map(add, self.rel_movement, pressed_rel))
			#log.debug("ticking:time_now:{} pressed_t:{} pressed_pos:{} released_t:{} released_pos:{}". \
			#		format(time_now, self.pressed_t, self.pressed_pos, self.released_t, self.released_pos))
			if (self.pressed_t != 0):
				self.refresh = True
				self.layout.render_button = self.pressed_pos
				if (time_now - self.pressed_t) > LONG_CLICK:
					log.debug("{} LONG CLICK : {} {} {}".format(__name__, time_now, self.pressed_t, self.pressed_pos))
					self.layout.check_click(self.pressed_pos, 1)
					self.reset_motion()
				if (self.released_t != 0):
					log.debug("{} SHORT CLICK : {} {} {}".format(__name__, time_now, self.pressed_t, self.pressed_pos))
					self.layout.check_click(self.pressed_pos, 0)
					self.reset_motion()
				dx = self.rel_movement[0]
				dy = self.rel_movement[1]
				if (abs(dx)) > SWIPE_LENGTH:
					if (dx > 0):
						log.debug("{} SWIPE X RIGHT to LEFT : {} {} {} {} {} {}".format(__name__, time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
						self.layout.check_click(self.pressed_pos, 2)
						self.reset_motion()
					else:
						log.debug("{} SWIPE X LEFT to RIGHT : {} {} {} {} {} {}".format(__name__, time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
						self.layout.check_click(self.pressed_pos, 3)
						self.reset_motion()
				elif (abs(dy)) > SWIPE_LENGTH:
					if (dy < 0):
						log.debug("{} SWIPE X BOTTOM to TOP : {} {} {} {} {} {}".format(__name__, time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
						self.layout.check_click(self.pressed_pos, 4)
						self.reset_motion()
					else:
						log.debug("{} SWIPE X TOP to BOTTOM : {} {} {} {} {} {}".format(__name__, time_now, self.pressed_t, self.pressed_pos, self.released_pos, dx, dy))
						self.layout.check_click(self.pressed_pos, 5)
						self.reset_motion()

			if self.refresh:
				self.refresh = False
				self.layout.layout_changed = 0
				self.rendering.force_refresh()

	def reset_motion(self):
		log.debug("{} [F] reset_motion".format(__name__))
		self.pressed_t = 0
		self.released_t = 0
		self.pressed_pos = (0,0)
		self.released_pos = (0,0)
		self.rel_movement = (0,0)
		self.layout.render_button = None
		self.add_rel_motion = False
		pygame.event.clear()

	def cleanup(self):
		sleep(1)
		self.rp.stop()
		self.rendering.stop()
		try:
			self.write_config()
		except AttributeError:
			pass
		try:
			self.layout.write_layout()
		except AttributeError:
			pass
		pygame.quit()
		log.debug("{} Log end".format(__name__))
		quit()

def quit_handler(signal, frame):
	main_window.cleanup()

if __name__ == "__main__":
	signal.signal(signal.SIGTERM, quit_handler)
	signal.signal(signal.SIGINT, quit_handler)
	os.environ["SDL_FBDEV"] = "/dev/fb1"
	os.putenv('SDL_MOUSEDEV' , '/dev/input/touchscreen')
	#This is a simple check if we're running on Raspberry PI. Switch to simulation mode if we're not
	if (platform.machine() == "armv6l"):
		main_window = open_cycling_computer(False)
	else:
		main_window = open_cycling_computer(True)
		log.warning("Warning! platform.machine() is NOT armv6l. I'll run in simulation mode. No real data will be shown.")
	main_window.main_loop()
	main_window.cleanup()
