import pygame
import struct
import xml.etree.ElementTree as eltree

class layout():
	def __init__(self, screen, xml_file):
		self.screen = screen
		self.page_list = {}
		self.function_rect_list = {}
		self.current_function_list = []
		self.load_layout(xml_file)
		self.name = None
		self.layout_changed = 0

		# Uncomment below to print layout tree
		#print "page name : ", self.page.get('name')
		#print "background : ", self.page.get('background')
		#for field in self.page:
		#	print "function : "  + field.find('function').text
		#	print "x : "  + field.find('x').text
		#	print "y : " + field.find('y').text
		#	print "font size : " + field.find('font_size').text
	def load_layout(self, layout_path):
		#print "load_layout", layout_path
		self.layout_path = layout_path 
		layout_tree = eltree.parse(self.layout_path)
		self.pages = layout_tree.getroot()
		for page in self.pages:
			#print "page name : ", page.get('name')
			self.page_list[page.get('name')] = page
			
		self.use_page()

	def use_page(self, page_name = "Main"):
		#print "use_page:", page_name
		self.layout_changed = 1
		self.current_function_list = []
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
			self.current_function_list.append(field.find('function').text)
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
		for func in self.current_function_list:
			try:
				self.render(self.screen, func, rp.get_val(func))
			except KeyError:
				# if rp.get_val returns KeyError call render with empty value
				self.render(self.screen, func)

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

	def check_click(self, position, click):
		short_click = {	"load_default_layout" : self.load_default_layout,
				"load_lcd_layout" : self.load_lcd_layout,
				"load_white_lcd_layout" : self.load_lcd_white_layout,
				"quit" : self.quit
		}
		for func in self.current_function_list:
			try:
				if self.function_rect_list[func].collidepoint(position):
					short_click[func]()
					break
			except KeyError:
				break

	def load_default_layout(self):
		self.load_layout("layouts/default.xml")

	def load_lcd_layout(self):
		self.load_layout("layouts/lcd.xml")

	def load_lcd_white_layout(self):
		self.load_layout("layouts/lcd_white.xml")

	def quit(self):
		pygame.quit()
		quit()
