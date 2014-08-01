#!/usr/bin/python

import os
import pygame
from pygame.locals import *
from pygame.compat import unichr_, unicode_
import locale
import sys
import math
import xml.etree.ElementTree as eltree
import struct


class layout():
	def __init__(self, xml_file):
		self.layout_path = xml_file
		self.load_layout()

		# Uncomment below to print layout tree
		#print "page name : ", self.page.get('name')
		#print "background : ", self.page.get('background')
		#for field in self.page:
		#	print "function : "  + field.find('function').text
		#	print "x : "  + field.find('x').text
		#	print "y : " + field.find('y').text
		#	print "font size : " + field.find('font_size').text
	def load_layout(self):
		layout_tree = eltree.parse(self.layout_path)
		self.page = layout_tree.getroot()
		self.bg_image = pygame.image.load(self.page.get('background')).convert() 
		self.font = self.page.get('font') 
		if (self.font == ""):
			self.font = None
		self.fg_colour_rgb = self.page.get('fg_colour') 
		self.fg_colour = struct.unpack('BBB',self.fg_colour_rgb.decode('hex'))

	def render_background(self, screen):
		screen.blit(self.bg_image, [0, 0])

	def render(self, screen, function, value):
		for field in self.page:
			if (field.find('function').text == function):
				font = pygame.font.Font(self.font, 12 * int(field.find('font_size').text))
				ren = font.render(str(value), 1, self.fg_colour)
				x = ren.get_rect().centerx
				y = ren.get_rect().centery
				screen.blit(ren, (int(field.find('x').text) - x, int(field.find('y').text) - y))

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

	def main_loop(self):
		while 1:
			for event in pygame.event.get():
				if event.type in (QUIT, KEYDOWN, MOUSEBUTTONDOWN):
					self.layout.load_layout()
					#sys.exit()
			t = 10
			speed = 24.45
			self.layout.render_background(self.screen)
			self.layout.render(self.screen, "speed", "%.0f" % speed)
			self.layout.render(self.screen, "speed_tenths", "%.0f" % (math.floor (10 * (speed - math.floor(speed)))))
			self.layout.render(self.screen, "heart_rate", 165)
			self.layout.render(self.screen, "heart_rate_units", "BPM")
			self.layout.render(self.screen, "gradient", 10)
			self.layout.render(self.screen, "gradient_units", "%")
			self.layout.render(self.screen, "cadence", 109)
			self.layout.render(self.screen, "units", "km/h")
			self.clock.tick(20)
			pygame.display.flip()

if __name__ == "__main__":
	main_window = open_cycle_computer()
	main_window.main_loop()
