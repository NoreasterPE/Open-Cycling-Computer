import pygame
import struct
import xml.etree.ElementTree as eltree

class layout():
	def __init__(self, xml_file):
		self.layout_path = xml_file
		self.load_layout()
		self.name = None

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
		self.name = self.page.get('name') 
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

