import pygame
import struct
import xml.etree.ElementTree as eltree

class layout():
	def __init__(self, xml_file):
		self.page_list = {}
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
		self.pages = layout_tree.getroot()
		for page in self.pages:
			#print "page name : ", page.get('name')
			self.page_list[page.get('name')] = page
			
		self.use_page()

	def use_page(self, page_name = "Main"):
		self.current_page = self.page_list[page_name]
		self.current_page_name = self.current_page.get('name')
		self.bg_image = pygame.image.load(self.current_page.get('background')).convert() 
		self.font = self.current_page.get('font') 
		if (self.font == ""):
			self.font = None
		self.fg_colour_rgb = self.current_page.get('fg_colour') 
		self.fg_colour = struct.unpack('BBB',self.fg_colour_rgb.decode('hex'))

	def render_background(self, screen):
		screen.blit(self.bg_image, [0, 0])

	def render(self, screen, function, value = None):
		for field in self.current_page:
			if (field.find('function').text == function):
				font = pygame.font.Font(self.font, 12 * int(field.find('font_size').text))
				if value == None:
					value = field.find('text_center').text
				ren = font.render(str(value), 1, self.fg_colour)
				x = ren.get_rect().centerx
				y = ren.get_rect().centery
				text_center_x = int(field.find('text_center').get('x'))
				text_center_y = int(field.find('text_center').get('y'))
				screen.blit(ren, (text_center_x - x, text_center_y - y))

