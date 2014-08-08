import pygame
import struct
import xml.etree.ElementTree as eltree

class layout():
	def __init__(self, screen, xml_file):
		self.screen = screen
		self.page_list = {}
		self.function_rect_list = {}
		self.current_function_list = {}
		self.load_layout(xml_file)
		self.name = None

		# Uncomment below to print layout tree
		#print "page name : ", self.page.get('name')
		#print "background : ", self.page.get('background')
		#for field in self.page:
		#	print "function : "  + field.find('function').text
		#	print "x : "  + field.find('x').text
		#	print "y : " + field.find('y').text
		#	print "font size : " + field.find('font_size').text
	def load_layout(self, layout_path):
		self.layout_path = layout_path 
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
		for field in self.current_page:
			#print "function name : ", field.find('function').text
			self.current_function_list[self.current_page] = field.find('function').text
			print self.current_function_list
			b = field.find('button')
			if (b is not None):
				x0 = int(b.get('x0'))
				y0 = int(b.get('y0'))
				w = int(b.get('w'))
				h = int(b.get('h'))
				self.function_rect_list[field.find('function').text] = pygame.Rect(x0, y0, w, h)
				#print self.function_rect_list['speed']

	def render_background(self, screen):
		screen.blit(self.bg_image, [0, 0])

	def render_page(self, rp):
		self.render_background(self.screen)
		self.render(self.screen, "speed", "%.0f" % rp.speed)

		self.render(self.screen, "load_default_layout")
		self.render(self.screen, "load_lcd_layout")
		self.render(self.screen, "load_white_lcd_layout")
		self.render(self.screen, "quit")

		self.render(self.screen, "speed_tenths", "%.0f" % rp.speed_tenths)
		self.render(self.screen, "heart_rate", rp.heart_rate)
		self.render(self.screen, "heart_rate_units")
		self.render(self.screen, "gradient", rp.gradient)
		self.render(self.screen, "gradient_units")
		self.render(self.screen, "cadence", rp.cadence)
		self.render(self.screen, "speed_units")

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

