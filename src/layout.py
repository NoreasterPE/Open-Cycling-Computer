import pygame
import struct
import quantities as q
import lxml.etree as eltree

class layout():
	#def __init__(self, occ, layout_path="layouts/current.xml"):
	#Temporary change
	def __init__(self, occ, layout_path="layouts/default.xml"):
		self.occ = occ
		self.screen = occ.screen
		self.page_list = {}
		self.page_index = {}
		self.function_rect_list = {}
		self.current_function_list = []
		self.buttons_surf_list = {}
		self.layout_path = layout_path
		self.load_layout(layout_path)
		self.render_button = None

		#Helpers for editing values
		self.editor = {}
		self.editor["variable_value"] = None
		self.editor["variable_unit"] = None
		self.editor["variable_description"] = None
		self.editor["variable"] = None
		self.editor_index = 0

	def load_layout(self, layout_path):
		self.max_page_id = 0
		self.page_list = {}
		self.page_index = {}
		self.max_page_id = 0
		try:
			self.layout_tree = eltree.parse(layout_path)
			self.layout_path = layout_path
		except:
			print "Loading layout ", layout_path, " failed, falling back to default.xml"
			print "Error details:", sys.exc_info()[0]
			#Fallback to default layout
			#FIXME - define const file with paths?
			self.layout_tree = eltree.parse("layouts/default.xml")

		self.pages = self.layout_tree.getroot()
		for page in self.pages:
			#print "page name : ", page.get('name')
			self.page_list[page.get('name')] = page
			page_id = page.get('id')
			self.page_index[page_id] = page.get('name')
			if page_id.startswith("page_"):
				no = int(page_id[-1:])
				self.max_page_id = max(self.max_page_id, no)
		self.use_page()
		self.write_layout()

	def write_layout(self, layout_path="layouts/current.xml"):
		self.layout_tree.write(layout_path, encoding="UTF-8", pretty_print=True)

	def use_page(self, page_id = "page_0"):
		self.occ.force_refresh()
		self.current_function_list = []
		self.current_button_list = []
		self.current_page_name = self.page_index[page_id]
		self.current_page_id = page_id
		self.current_page = self.page_list[self.current_page_name]
		try:
			bg_path = self.current_page.get('background')
			self.bg_image = pygame.image.load(bg_path).convert()
		except pygame.error:
			print "Cannot load background image! layout_path =", self.layout_path, " background path:", bg_path, " page_id =", page_id
			#That stops occ but not immediately - errors can occur
			self.occ.running = False
			self.occ.cleanup()
		try:
			bt_path = self.current_page.get('buttons')
			self.bt_image = pygame.image.load(bt_path).convert()
		except pygame.error:
			print "Cannot load buttons image! layout_path =", self.layout_path, " buttons path:", bt_path, " page_id =", page_id
			self.occ.running = False
			self.occ.cleanup()
			pass
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
				name = field.find('function').text
				rect = pygame.Rect(x0, y0, w, h)
				self.function_rect_list[name] = rect
				self.current_button_list.append(name)

	def use_main_page(self):
		self.use_page()

	def render_background(self, screen):
		screen.blit(self.bg_image, [0, 0])

	def render_pressed_button(self, screen, function):
		#FIXME make sure it's OK to skip rendering here
		try:
			r =  self.function_rect_list[function]
			screen.blit(self.bt_image, r, r, 0)
		#FIXME required to catch exception?
		except (TypeError, AttributeError):
			pass

	def render_page(self):
		self.render_background(self.screen)
		self.show_pressed_button()
		for func in self.current_function_list:
			#FIXME Dirty hack - iron me out
			try:
				try:
					self.render(self.screen, func, self.editor[func])
				except KeyError:
					self.render(self.screen, func, self.occ.rp.get_val(func))
			except KeyError:
				# if rp.get_val returns KeyError call render with empty value
				self.render(self.screen, func)

	def render(self, screen, function, value = None):
		for field in self.current_page:
			if (field.find('function').text == function):
				font = pygame.font.Font(self.font, 12 * int(field.find('font_size').text))
				if value == None:
					value = field.find('text_center').text
				uv = unicode(value)
				text_center_x = int(field.find('text_center').get('x'))
				text_center_y = int(field.find('text_center').get('y'))
				if function != "variable_value":
					ren = font.render(uv, 1, self.fg_colour)
					x = ren.get_rect().centerx
					y = ren.get_rect().centery
					screen.blit(ren, (text_center_x - x, text_center_y - y))
				else:
					i = self.editor_index
					font = pygame.font.Font(self.font, 12 * (int(field.find('font_size').text) - 1))
					rv1 = uv[:i]
					ren1 = font.render(rv1, 1, self.fg_colour)
					w1 = ren1.get_rect().width
					y1 = ren1.get_rect().centery
					font = pygame.font.Font(self.font, 12 * (int(field.find('font_size').text) + 1))
					rv2 = uv[i]
					ren2 = font.render(rv2, 1, self.fg_colour)
					w2 = ren2.get_rect().width
					y2 = ren2.get_rect().centery
					font = pygame.font.Font(self.font, 12 * (int(field.find('font_size').text) - 1))
					rv3 = uv[i + 1:]
					ren3 = font.render(rv3, 1, self.fg_colour)
					w3 = ren3.get_rect().width
					y3 = ren3.get_rect().centery
					x = text_center_y - int((w1 + w2 + w3)/2)
					screen.blit(ren1, (x, text_center_y - y1))
					screen.blit(ren2, (x + w1, text_center_y - y2))
					screen.blit(ren3, (x + w1 + w2, text_center_y - y3))

	def show_pressed_button(self):
		if self.render_button:
			for func in self.current_button_list:
				try:
					if self.function_rect_list[func].collidepoint(self.render_button):
						self.render_pressed_button(self.screen, func)
						break
				except KeyError:
					print "show_pressed_button failed! func = ", func 
					self.occ.running = False

	def check_click(self, position, click):
		#print "check_click: ", position, click

		if click == 0:
			#Short click
			#FIXME Search through function_rect_list directly? TBD
			for func in self.current_button_list:
				try:
					if self.function_rect_list[func].collidepoint(position):
						self.run_function(func)
						break
				except KeyError:
					#FIXME function name not knwon - write to log
					#It's not fatal  - user clicked on a non-clickable element
					#print "KeyError: non-fatal: check_click failed! func =", func, ", position =", position, ", click =", click 
					pass
		elif click == 1:
			#print "LONG CLICK"
			#print self.function_rect_list
			#print self.current_button_list
			#print self.occ.rp.p_editable
			for func in self.current_button_list:
				try:
					if self.function_rect_list[func].collidepoint(position):
						#print "Long click on " + func
						#FIXME I's dirty way of getting value - add some helper function
						if func in self.occ.rp.p_editable:
							#print "func " + func + " is editable"
							self.editor["variable"] = func
							#FIXME I's dirty way of getting value
							self.editor["variable_value"] = self.occ.rp.get_val(func)
							self.editor["variable_unit"] = self.occ.rp.get_unit(func)
							#FIXME Make list of editable values + descriptions
							self.editor["variable_description"] = self.occ.rp.get_description(func)
							#FIXME Call editor page - that's temporary
							#Add call_editor function with p_raw params
							self.editor_index = 0
							self.use_page("editor")
							break
				except KeyError:
					#FIXME function name not knwon - write to log
					#It's not fatal  - user clicked on a non-clickable element
					print "KeyError: non-fatal: check_click failed on click = 1 [LONG CLICK] ! func =", func, ", position = ", position
		elif click == 2:
			#Swipe RIGHT to LEFT
			self.run_function("next_page")
		elif click == 3:
			#Swipe LEFT to RIGHT
			self.run_function("prev_page")
		elif click == 4:
			#print "Swipe BOTTOM to TOP"
			self.run_function("page_0")
		elif click == 5:
			#print "Swipe TOP to BOTTOM"
			self.run_function("settings")

	def run_function(self, name):
		functions = {	"page_0" : self.load_page_0,
				"settings" : self.load_settings_page,
				"ed_accept" : self.ed_accept,
				"ed_cancel" : self.ed_cancel,
				"ed_decrease" : self.ed_decrease,
				"ed_increase" : self.ed_increase,
				"ed_next" : self.ed_next,
				"ed_next_unit" : self.ed_next_unit,
				"ed_prev" : self.ed_prev,
				"ed_prev_unit" : self.ed_prev_unit,
				"ed_value" : self.ed_value,
				"ed_value_description" : self.ed_value_description,
				"load_default_layout" : self.load_default_layout,
				"load_current_layout" : self.load_current_layout,
				"load_white_lcd_layout" : self.load_lcd_white_layout,
				"next_page" : self.next_page,
				"prev_page" : self.prev_page,
				"write_layout" : self.write_layout,
				"quit" : self.quit
		}
		functions[name]()

	def force_refresh(self):
		self.occ.force_refresh()
		
	def load_page_0(self):
		self.use_main_page()

	def load_settings_page(self):
		self.use_page("settings_0")

	def ed_accept(self):
		#print "ed_accept"
		self.accept_edit()
		self.use_main_page()

	def ed_cancel(self):
		#print "ed_cancel"
		self.use_main_page()

	def ed_decrease(self):
		#print "ed_decrease"
		u = unicode(self.editor["variable_value"])
		i = self.editor_index
		ui = u[i]
		if ui == "0":
			ui = "9"
		else:
			ui = unicode(int(ui) - 1)
		un = u[:i] + ui + u[i + 1:]
		self.editor["variable_value"] = un
		self.force_refresh()

	def ed_increase(self):
		#print "ed_increase"
		u = unicode(self.editor["variable_value"])
		i = self.editor_index
		ui = u[i]
		if ui == "9":
			ui = "0"
		else:
			ui = unicode(int(ui) + 1)
		un = u[:i] + ui + u[i + 1:]
		self.editor["variable_value"] = un
		self.force_refresh()

	def ed_next(self):
		#print "ed_next"
		u = unicode(self.editor["variable_value"])
		l = len(u) - 1
		i = self.editor_index
		i += 1
		if i > l:
			i = l 
		else:
			ui = u[i]
			#FIXME localisation points to be used here
			if (ui == ".") or (ui == ","):
				i += 1
		self.editor_index = i
		self.force_refresh()

	def ed_prev(self):
		#print "ed_prev"
		u = unicode(self.editor["variable_value"])
		l = len(u) 
		i = self.editor_index
		i -= 1
		if i < 0:
			i = 0
			uv = "0" + u	
			self.editor["variable_value"] = uv
		else:
			ui = u[i]
			#FIXME localisation points to be used here
			if (ui == ".") or (ui == ","):
				i -= 1
		self.editor_index = i
		self.force_refresh()

	def ed_change_unit(self, direction):
		#direction to be 1 (next) or 0 (previous)
		variable = self.editor["variable"]
		variable_unit = self.editor["variable_unit"]
		variable_value = float(self.editor["variable_value"])
		current_unit_index = self.occ.rp.units_allowed[variable].index(variable_unit)
		if direction == 1:
			try:
				next_unit = self.occ.rp.units_allowed[variable][current_unit_index + 1]
			except IndexError:
				next_unit = self.occ.rp.units_allowed[variable][0]
		else:
			try:
				next_unit = self.occ.rp.units_allowed[variable][current_unit_index - 1]
			except IndexError:
				next_unit = self.occ.rp.units_allowed[variable][-1]
		v = q.Quantity(variable_value, variable_unit)
		v = v.rescale(next_unit)
		#FIXME - list with formatting. Also for use in RP, update_params
		self.editor["variable_value"] = float("%.1f" % v.item())
		self.editor["variable_unit"] = next_unit

	def ed_next_unit(self):
		#print "ed_next_unit"
		self.ed_change_unit(1)
		self.force_refresh()

	def ed_prev_unit(self):
		#print "ed_prev_unit"
		self.ed_change_unit(0)
		self.force_refresh()

	def ed_value(self):
		#print "ed_value"
		pass

	def ed_value_description(self):
		#print "ed_value_description"
		pass

	def accept_edit(self):
		variable = self.editor["variable"]
		variable_unit = self.editor["variable_unit"]
		variable_value = float(self.editor["variable_value"])
		v = q.Quantity(variable_value, variable_unit)
		v = v.rescale(self.occ.rp.get_internal_unit(variable))
		self.occ.rp.p_raw[variable] = v.item()
		self.occ.rp.params[variable] = self.editor["variable_value"]
		self.occ.rp.units[variable] = self.editor["variable_unit"]
		self.force_refresh()

	def next_page(self):
		#cp = self.current_page_id
		#Editor is a special page - it cannot be switched, only cancel or accept
		if self.current_page_id is not "editor":
			try:
				no = int(self.current_page_id[-1:])
				self.use_page("page_" + unicode(no + 1))
			except KeyError:
				self.use_main_page()
				#FIXME Use cp to block circular page scrolling - it should be in options
				#self.use_page(cp)

	def prev_page(self):
		#cp = self.current_page_id
		#Editor is a special page - it cannot be switched, only cancel or accept
		if self.current_page_id is not "editor":
			try:
				no = int(self.current_page_id[-1:])
				self.use_page("page_" + unicode(no - 1))
			except KeyError:
				self.use_page("page_" + unicode(self.max_page_id))
				#FIXME Use cp to block circular page scrolling - it should be in options
				#self.use_page(cp)

	def load_layout_by_name(self, name):
		self.load_layout("layouts/" + name)

	def load_current_layout(self):
		self.load_layout_by_name("current.xml")

	def load_lcd_white_layout(self):
		self.load_layout_by_name("lcd_white.xml")

	def load_default_layout(self):
		self.load_layout_by_name("default.xml")

	def quit(self):
		self.occ.running = 0
