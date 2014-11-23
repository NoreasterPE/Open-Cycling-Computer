#! /usr/bin/python
 
import threading
from layout import layout
import pygame
 
class rendering(threading.Thread):
	#Class for PiTFT rendering

	def __init__(self, layout):
		# Run init for super class
		super(rendering, self).__init__()
		self.clock = pygame.time.Clock()
		self.layout = layout
		self.refresh = True
		self.running = False

	def run(self):
		self.running = True
		while self.running:
			if self.refresh:
				self.refresh = False
				self.layout.render_page()
				#FIXME display.update might be faster, but require list of rectangles for he update
				pygame.display.flip()
			#Setting FPS too low causes some click-directly-after-click problems
			self.clock.tick(5)

	def stop(self):
		self.running = False

	def force_refresh(self):
		self.refresh = True

	def __del__(self):
		self.stop()
