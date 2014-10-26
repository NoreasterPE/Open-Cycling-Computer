#!/usr/bin/python

from pygame.compat import unichr_, unicode_
from pygame.locals import *
from ride_parameters import ride_parameters
from layout import layout
from rendering import rendering
from time import *
import locale
import lxml.etree as eltree
import math
import os
import pygame
import signal
import sys

class open_cycle_computer():
	'Class for PiTFT 2.8" 320x240 cycle computer'
	def __init__(self, simulate = False, width = 240, height = 320):
		pygame.init()
		if not simulate:
			pygame.mouse.set_visible(0)
		pygame.time.set_timer(USEREVENT + 1, 1000)
		self.width = width
		self.height = height
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.clock = pygame.time.Clock()
		self.rp = ride_parameters(self, simulate)
		self.config_path = "config/config.xml"
		self.read_config()
		self.layout = layout(self, self.layout_path)
		self.rendering = rendering(self.layout)
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
		pressed_t = 0
		pressed_pos = (0,0)
		released_t = 0
		released_pos = (0,0)
		while self.running:
			time_now = pygame.time.get_ticks()
			event = pygame.event.poll()
			if event.type == pygame.QUIT:
				self.running = 0
			elif event.type == USEREVENT + 1:
				self.rp.update_values()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				pressed_t = time_now
				pressed_pos = pygame.mouse.get_pos()
				#print "DOWN:", pressed_t, released_t, "x:", pressed_pos[0], "y:", pressed_pos[1]
			elif event.type == pygame.MOUSEBUTTONUP:
				#That check prevents setting release_x after long click
				if (pressed_t != 0):
					released_t = time_now
					released_pos = pygame.mouse.get_pos()
				#print "UP:", pressed_t, released_t, "x:", pressed_pos[0], "y:", pressed_pos[1]
			pygame.event.clear(pygame.MOUSEMOTION)
			#print "ticking...:", time_now, pressed_t, pressed_pos, released_t, released_pos
			if (pressed_t != 0):
				self.refresh = True
				self.layout.render_button = pressed_pos
				if (time_now - pressed_t) > LONG_CLICK:
					#print "LONG CLICK", time_now, pressed_t, pressed_pos
					self.layout.check_click(pressed_pos, 1)
					pressed_t = 0
					released_t = 0
					pressed_pos = (0,0)
					released_pos = (0,0)
					self.layout.render_button = None
				if (released_t != 0):
					dx = pressed_pos[0] - released_pos[0]
					dy = pressed_pos[1] - released_pos[1]
					#print time_now, pressed_t, pressed_pos, released_t, released_pos
					#print dx, dy
					if (abs(dx)) > SWIPE_LENGTH:
						if (dx > 0):
							#print "SWIPE X RIGHT to LEFT", time_now, pressed_t, pressed_pos, released_pos, dx, dy
							self.layout.check_click(pressed_pos, 2)
						else:
							#print "SWIPE X LEFT to RIGTH", time_now, pressed_t, pressed_pos, released_pos, dx, dy
							self.layout.check_click(pressed_pos, 3)
					elif (abs(dy)) > SWIPE_LENGTH:
						if (dy > 0):
							#print "SWIPE X BOTTOM to TOP", time_now, pressed_t, pressed_pos, released_pos, dx, dy
							self.layout.check_click(pressed_pos, 4)
						else:
							#print "SWIPE X TOP to BOTTOM", time_now, pressed_t, pressed_pos, released_pos, dx, dy
							self.layout.check_click(pressed_pos, 5)
					else:
						#print "SHORT CLICK", time_now, pressed_t, pressed_pos
						self.layout.check_click(pressed_pos, 0)
					pressed_t = 0
					released_t = 0
					pressed_pos = (0,0)
					released_pos = (0,0)
					self.layout.render_button = None

			if self.refresh or self.layout.layout_changed:
				self.refresh = False
				self.layout.layout_changed = 0
				self.rendering.force_refresh()

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
		quit()

def quit_handler(signal, frame):
	main_window.cleanup()

if __name__ == "__main__":
	signal.signal(signal.SIGTERM, quit_handler)
	signal.signal(signal.SIGINT, quit_handler)
	os.environ["SDL_FBDEV"] = "/dev/fb1"
	os.putenv('SDL_MOUSEDEV' , '/dev/input/touchscreen')

	#main_window = open_cycle_computer(True)
	main_window = open_cycle_computer()
	main_window.main_loop()
	main_window.cleanup()
