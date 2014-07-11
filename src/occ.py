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

	def draw_text(self):
		font = pygame.font.Font(None, 18 * 12)
		text = '48'
		font.set_bold(0)

		ren = font.render(text, 1, self.fg_colour)
		self.screen.blit(ren, (10, 0))

		font = pygame.font.Font(None, 3 * 12)
		unit = 'km/h'
		ren = font.render(unit, 1, self.fg_colour)
		self.screen.blit(ren, (180, 115))

		font = pygame.font.Font(None, 8 * 12)
		unit = '165'
		ren = font.render(unit, 1, self.fg_colour)
		self.screen.blit(ren, (10, 180))
		pygame.display.flip()

	def draw_frame(self):
		pygame.draw.line(self.screen, (220, 220, 220), (0, 150), (self.width, 150), 1)
		pygame.draw.line(self.screen, (220, 220, 220), (0, 240), (240, 240), 1)
		pygame.draw.line(self.screen, (220, 220, 220), (self.width/2, 240), (self.width/2, self.height), 1)



if __name__ == "__main__":
	main_window = open_cycle_computer()
	main_window.main_loop()
