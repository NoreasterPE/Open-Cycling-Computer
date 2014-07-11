#!/usr/bin/python

import pygame
from pygame.locals import *
from pygame.compat import unichr_, unicode_
import sys
import locale



class open_cycle_computer():
	'Class for PiTFT 2.8" 320x240 cycle computer'

	def __init__(self, width = 240, height = 320):
		pygame.init()
		self.width = width
		self.height = height
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.fg_colour = 255, 255, 255
		self.bg_colour = 5, 5, 5
		self.win_color = 0, 0, 0
		self.screen.fill(self.win_color)
		self.draw_frame()
		self.draw_text()

	def main_loop(self):
		while 1:
			#for event in pygame.event.get():
			#	if event.type == pygame.QUIT: 
			if pygame.event.wait().type in (QUIT, KEYDOWN, MOUSEBUTTONDOWN):
				sys.exit()
			pygame.display.flip()

	def render_value(self, value, position, size):
		font = pygame.font.Font(None, 12 * size)
		ren = font.render(value, 1, self.fg_colour)
		x = ren.get_rect().centerx
		y = ren.get_rect().centery
		self.screen.blit(ren, (position[0] - x, position[1] - y))

	def render_top(self, value):
		self.render_value(str(value), (120 - 20, 75), 18)

	def render_mid(self, value):
		self.render_value(str(value), (120, 195), 10)

	def draw_text(self):
		for i in range(100):
			self.render_top(i)
		for i in range(1000):
			self.render_mid(i)

	def draw_frame(self):
		pygame.draw.line(self.screen, (220, 220, 220), (0, 150), (self.width, 150), 1)
		pygame.draw.line(self.screen, (220, 220, 220), (0, 240), (240, 240), 1)
		pygame.draw.line(self.screen, (220, 220, 220), (self.width/2, 240), (self.width/2, self.height), 1)

		self.render_value("km/h", (210, 75), 3)




if __name__ == "__main__":
	main_window = open_cycle_computer()
	main_window.main_loop()
