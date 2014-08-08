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
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.clock = pygame.time.Clock()
		#self.layout = layout(self.screen, "layouts/default.xml")
		#self.layout = layout(self.screen, "layouts/lcd.xml")
		self.layout = layout(self.screen, "layouts/lcd_white.xml")
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
					if self.layout.current_page.get('name') == 'Main':
						self.layout.use_page("Settings")
					else:
						self.layout.use_page("Main")
					pressed_t = 0
					released_t = 0
				if (released_t != 0):
					if ((pressed_t - released_t) < LONG_CLICK):	
						#print "SHORT CLICK", time_now, pressed_t, pressed_pos
						#for fl in self.layout.function_list:
						#	print fl, self.layout.function_list[fl]
						if self.layout.current_page.get('name') == 'Settings':
							if self.layout.function_list['load_default_layout'].collidepoint(pressed_pos):
								self.layout.load_layout("layouts/default.xml")
							if self.layout.function_list['load_lcd_layout'].collidepoint(pressed_pos):
								self.layout.load_layout("layouts/lcd.xml")
							if self.layout.function_list['load_white_lcd_layout'].collidepoint(pressed_pos):
								self.layout.load_layout("layouts/lcd_white.xml")
							if self.layout.function_list['quit'].collidepoint(pressed_pos):
								running = 0
						pressed_t = 0
						released_t = 0

			self.layout.render_page(self.rp)
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
