#!/usr/bin/python

import os
import pygame
from pygame.locals import *
from pygame.compat import unichr_, unicode_
import locale
import sys
import math
import xml.etree.ElementTree as eltree


class layout():
	def __init__(self, xml_file):
		layout_tree = eltree.parse(xml_file)
		page_set = layout_tree.getroot()
		for page in page_set:
			print "page name : ", page.get('name')
			print "background : ", page.get('background')
			for field in page:
				print "function : "  + field.find('function').text
				print "x : "  + field.find('x').text
				print "y : " + field.find('y').text
				print "font size : " + field.find('font_size').text

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
		self.fg_colour = 255, 255, 255
		self.bg_image = pygame.image.load("images/occ_dark_green.png").convert()
		l = layout("layouts/default.xml")

	def main_loop(self):
		while 1:
			for event in pygame.event.get():
				if event.type in (QUIT, KEYDOWN, MOUSEBUTTONDOWN):
					sys.exit()
			t = 10
			#TODO Read values for rendering from a file here
			self.screen.blit(self.bg_image, [0, 0])
			self.render_top("%.0f" % (24.4))
			self.render_top_mini("%.0f" % (math.floor (10 * (24.4 - math.floor(24.4)))))
			self.render_mid(t)
			self.render_bl(t)
			self.render_br(t)
			self.draw_speed_unit()
			self.clock.tick(20)
			pygame.display.flip()

	def render_value(self, value, position, size):
		font = pygame.font.Font(None, 12 * size)
		ren = font.render(value, 1, self.fg_colour)
		x = ren.get_rect().centerx
		y = ren.get_rect().centery
		self.screen.blit(ren, (position[0] - x, position[1] - y))

	def render_top(self, value):
		size = 20
		#Shrink font size for 3 digits
		if (int(value) > 99):
			size = 13
		self.render_value(str(value), (120 - 25, 75), size)

	def render_top_mini(self, value):
		self.render_value(str(value), (210, 115), 8)

	def render_mid(self, value):
		self.render_value(str(value), (120, 195), 12)

	def render_bl(self, value):
		self.render_value(str(value), (60, 280), 10)

	def render_br(self, value):
		self.render_value(str(value), (180, 280), 10)

	def draw_speed_unit(self):
		self.render_value("km/h", (210, 75), 3)

if __name__ == "__main__":
	main_window = open_cycle_computer()
	main_window.main_loop()
