#!/usr/bin/python

from pygame.compat import unichr_, unicode_
from pygame.locals import *
from ride_parameters import ride_parameters
from layout import layout
import locale
import math
import os
import pygame
import sys


class open_cycle_computer():
	'Class for PiTFT 2.8" 320x240 cycle computer'
	def __init__(self, width = 240, height = 320):
		os.environ["SDL_FBDEV"] = "/dev/fb1"
		pygame.init()
		pygame.mouse.set_visible(0)
		self.width = width
		self.height = height
		self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
		self.clock = pygame.time.Clock()
		#self.layout = layout("layouts/default.xml")
		self.layout = layout("layouts/lcd.xml")
		self.rp = ride_parameters()

	def main_loop(self):
		running = 1
		pressed_t = 0
		released_t = 0
		LONG_CLICK = 1000
		while running:
			time_now = pygame.time.get_ticks()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = 0
				elif event.type == pygame.MOUSEBUTTONDOWN:
					pressed_t = time_now
					#print "DOWN:", pressed_t, released_t
					pygame.event.clear(pygame.MOUSEBUTTONDOWN)
				elif event.type == pygame.MOUSEBUTTONUP:
					released_t = time_now
					#print "UP:", pressed_t, released_t
					pygame.event.clear(pygame.MOUSEBUTTONUP)
				elif event.type == pygame.MOUSEMOTION:
					#print "MOTION... cleared"
					pygame.event.clear(pygame.MOUSEMOTION)
			#print "ticking...:", time_now, pressed_t, released_t
			if (pressed_t != 0):
				if (time_now - pressed_t) > LONG_CLICK:
					#print "LONG CLICK", time_now, pressed_t
					running = 0
					pressed_t = 0
					released_t = 0
				if (released_t != 0):
					if ((pressed_t - released_t) < LONG_CLICK):	
						#print "SHORT CLICK", time_now, pressed_t
						self.layout.use_page("Settings")
						pressed_t = 0
						released_t = 0
			self.layout.render_background(self.screen)
			self.layout.render(self.screen, "speed", "%.0f" % self.rp.speed)
			self.layout.render(self.screen, "pair", "Pair")
			self.layout.render(self.screen, "speed_tenths", "%.0f" % self.rp.speed_tenths)
			self.layout.render(self.screen, "heart_rate", self.rp.heart_rate)
			self.layout.render(self.screen, "heart_rate_units", self.rp.heart_rate_units)
			self.layout.render(self.screen, "gradient", self.rp.gradient)
			self.layout.render(self.screen, "gradient_units", self.rp.gradient_units)
			self.layout.render(self.screen, "cadence", self.rp.cadence)
			self.layout.render(self.screen, "units", self.rp.units)
			#print self.clock.get_fps()
			#Setting FPS too low causes some click-directly-after-click problems
			self.clock.tick(25)
			pygame.display.flip()
		pygame.quit()

if __name__ == "__main__":
	os.putenv('SDL_MOUSEDRV' , 'TSLIB')
	os.putenv('SDL_MOUSEDEV' , '/dev/input/touchscreen')

	main_window = open_cycle_computer()
	main_window.main_loop()
