#!/usr/bin/python

from pygame.compat import unichr_, unicode_
from pygame.locals import *
from ride_parameters import ride_parameters
from layout import layout
from time import *
import locale
import math
import os
import pygame
import signal
import sys
import lxml.etree as eltree


class open_cycle_computer():
	'Class for PiTFT 2.8" 320x240 cycle computer'
	def __init__(self, width = 240, height = 320):
		self.config_path = "config/config.xml"
		pygame.init()
		pygame.mouse.set_visible(0)
		pygame.time.set_timer(USEREVENT + 1, 1000)
		self.width = width
		self.height = height
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.clock = pygame.time.Clock()
		self.read_config()
		self.layout = layout(self, self.layout_path)
		self.rp = ride_parameters()
		self.running = 1

	def read_config(self):
		#FIXME error handling and emergency config read if main is corrupted
		config_tree = eltree.parse(self.config_path)
		self.config = config_tree.getroot()
		self.layout_path =  self.config.find("layout_path").text

	def write_config(self):
		config_tree = eltree.Element("config")
		eltree.SubElement(config_tree, "layout_path").text = self.layout.layout_path
		#FIXME error handling for file operation
		eltree.ElementTree(config_tree).write(self.config_path, encoding="UTF-8", pretty_print=True)

	def main_loop(self):
		pressed_t = 0
		released_t = 0
		LONG_CLICK = 1000
		while self.running:
			time_now = pygame.time.get_ticks()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = 0
				elif event.type == USEREVENT + 1:
					self.rp.update_values()
				elif event.type == pygame.MOUSEBUTTONDOWN:
					pressed_t = time_now
					pressed_pos = pygame.mouse.get_pos()
					#print "DOWN:", pressed_t, released_t, "x:", pressed_pos[0], "y:", pressed_pos[1]
					pygame.event.clear(pygame.MOUSEBUTTONDOWN)
				elif event.type == pygame.MOUSEBUTTONUP:
					#That check prevents setting release_x after long click
					if (pressed_t != 0):
						released_t = time_now
						released_pos = pygame.mouse.get_pos()
					#print "UP:", pressed_t, released_t, "x:", pressed_pos[0], "y:", pressed_pos[1]
					pygame.event.clear(pygame.MOUSEBUTTONUP)
				elif event.type == pygame.MOUSEMOTION:
					#print "MOTION... cleared"
					pygame.event.clear(pygame.MOUSEMOTION)
			#print "ticking...:", time_now, pressed_t, released_t
			if (pressed_t != 0):
				if (time_now - pressed_t) > LONG_CLICK:
					#print "LONG CLICK", time_now, pressed_t, pressed_pos
					self.layout.check_click(pressed_pos, 1)
					pressed_t = 0
					released_t = 0
				if (released_t != 0):
					if ((pressed_t - released_t) < LONG_CLICK):	
						#print "SHORT CLICK", time_now, pressed_t, pressed_pos
						self.layout.check_click(pressed_pos, 0)
						pressed_t = 0
						released_t = 0

			if self.rp.params_changed or self.layout.layout_changed:
				self.rp.params_changed = 0
				self.layout_changed = 0
				self.layout.render_page(self.rp)
			#print self.clock.get_fps()
			#Setting FPS too low causes some click-directly-after-click problems
			self.clock.tick(25)
			pygame.display.flip()

def cleanup():
	sleep(1)
	main_window.rp.stop()
	#write current config for future use
	main_window.write_config()
	pygame.quit()
	quit()

def quit_handler(signal, frame):
	cleanup()

if __name__ == "__main__":
	signal.signal(signal.SIGTERM, quit_handler)
	signal.signal(signal.SIGINT, quit_handler)
	os.environ["SDL_FBDEV"] = "/dev/fb1"
	os.putenv('SDL_MOUSEDEV' , '/dev/input/touchscreen')

	main_window = open_cycle_computer()
	main_window.main_loop()
	cleanup()
