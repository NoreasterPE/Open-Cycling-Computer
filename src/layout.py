from units import units
import lxml.etree as eltree
import os
import pygame
import struct
import sys
import time

class layout():
	#def __init__(self, occ, layout_path="layouts/current.xml"):
	#Temporary change
	def __init__(self, occ, layout_path="layouts/default.xml"):
		self.occ = occ
		self.uc = units()
		self.screen = occ.screen
		self.page_list = {}
		self.page_index = {}
		self.function_rect_list = {}
		self.current_function_list = []
		self.layout_path = layout_path
		self.load_layout(layout_path)
		self.render_button = None
		self.colorkey = [0,0,0]
		self.alpha = 255

		#Helpers for editing values
		self.editor = {}
		self.editor["variable_value"] = None
		self.editor["variable_raw_value"] = None
		self.editor["variable_unit"] = None
		self.editor["variable_description"] = None
		self.editor["variable"] = None
		self.editor_index = 0
		self.editor_type = 0

	def load_layout(self, layout_path):
		self.max_page_id = 0
		self.max_settings_id = 0
		self.page_list = {}
		self.page_index = {}
		try:
			self.layout_tree = eltree.parse(layout_path)
			self.layout_path = layout_path
		except:
			self.occ.log.error("{} Loading layout {} failed, falling back to default.xml".format(__name__, layout_path))
			sys_info = "Error details: {}".format(sys.exc_info()[0])
			self.occ.log.error(sys_info)
			#Fallback to default layout
			#FIXME - define const file with paths?
			self.layout_tree = eltree.parse("layouts/default.xml")

		self.pages = self.layout_tree.getroot()
		for page in self.pages:
			#FIXME Pages cannot have the same name
			self.page_list[page.get('name')] = page
			page_id = page.get('id')
			self.page_index[page_id] = page.get('name')
			#FIXME hardcoded page_ is bad
			if page_id.startswith("page_"):
				no = int(page_id[-1:])
				self.max_page_id = max(self.max_page_id, no)
			#FIXME hardcoded settings_ is bad
			if page_id.startswith("settings_"):
				no = int(page_id[-1:])
				self.max_settings_id = max(self.max_settings_id, no)
		self.use_page()
		self.write_layout()

	def write_layout(self, layout_path="layouts/current.xml"):
		self.layout_tree.write(layout_path, encoding="UTF-8", pretty_print=True)

	def use_page(self, page_id = "page_0"):
		self.occ.log.debug("[LY][F] use_page {}".format(page_id))
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
			self.occ.log.critical("{} Cannot load background image! layout_path = {} background path = {} page_id = {}"\
					.format(__name__, self.layout_path, bg_path, page_id))
			#That stops occ but not immediately - errors can occur
			self.occ.running = False
			self.occ.cleanup()
		try:
			bt_path = self.current_page.get('buttons')
			self.bt_image = pygame.image.load(bt_path).convert()
		except pygame.error:
			self.occ.log.critical("{} Cannot load buttons image! layout_path = {} buttons path = {} page_id = {}"\
					.format(__name__, self.layout_path, bt_path, page_id))
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
				#FIXME Move parsing to a separate function? Make list of icons to improve speed
				if value == None:
					value = field.find('text_center').text
				if value == None:
					value = ""
				uv = unicode(value)
				text_center_x = int(field.find('text_center').get('x'))
				text_center_y = int(field.find('text_center').get('y'))
				try:
					image_path = field.find('text_center').get('file')
					image = pygame.image.load(image_path).convert()
					image.set_colorkey(self.colorkey)
					image.set_alpha(self.alpha)
					screen.blit(image, [text_center_x, text_center_y])
				except:
					pass
				try:
					fs = int(field.find('text_center').get('size'))
				except:
					fs = 0
				font_size = 12 * fs
				font_size_small = 12 * (fs - 1)
				font_size_large = 12 * (fs + 1)
				if function != "variable_value":
					font = pygame.font.Font(self.font, font_size)
					ren = font.render(uv, 1, self.fg_colour)
					x = ren.get_rect().centerx
					y = ren.get_rect().centery
					screen.blit(ren, (text_center_x - x, text_center_y - y))
				else:
					font = pygame.font.Font(self.font, font_size_small)
					i = self.editor_index
					rv1 = uv[:i]
					ren1 = font.render(rv1, 1, self.fg_colour)
					w1 = ren1.get_rect().width
					y1 = ren1.get_rect().centery
					rv2 = uv[i]
					font = pygame.font.Font(self.font, font_size_large)
					ren2 = font.render(rv2, 1, self.fg_colour)
					w2 = ren2.get_rect().width
					y2 = ren2.get_rect().centery
					rv3 = uv[i + 1:]
					font = pygame.font.Font(self.font, font_size_small)
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
					self.occ.log.critical("{} show_pressed_button failed! func ={}".format, __name__, func)
					self.occ.running = False

	def check_click(self, position, click):
		#print "check_click: ", position, click

		if click == 0:
			#Short click
			#FIXME Search through function_rect_list directly? TBD
			for param_name in self.current_button_list:
				try:
					if self.function_rect_list[param_name].collidepoint(position):
						self.run_function(param_name)
						break
				except KeyError:
					self.occ.log.debug("[LY] CLICK on non-clickable {}".format(param_name))
		elif click == 1:
			#print self.function_rect_list
			#print self.current_button_list
			for param_name in self.current_button_list:
				try:
					if self.function_rect_list[param_name].collidepoint(position):
						#FIXME I's dirty way of getting value - add some helper function
						if param_name in self.occ.rp.p_editable:
							self.occ.log.debug("[LY] LONG CLICK on {}".format(param_name))
							self.editor_type = self.occ.rp.p_editable[param_name]
							self.open_editor_page(param_name)
							break
						p = self.occ.rp.strip_end(param_name)
						if p in self.occ.rp.p_resettable:
							self.occ.rp.reset_param(p)
				except KeyError:
					self.occ.log.debug("[LY] LONG CLICK on non-clickable {}".format(param_name))
		elif click == 2: #Swipe RIGHT to LEFT
			self.run_function("next_page")
		elif click == 3: #Swipe LEFT to RIGHT
			self.run_function("prev_page")
		elif click == 4: #print "Swipe BOTTOM to TOP"
			self.run_function("page_0")
		elif click == 5: #print "Swipe TOP to BOTTOM"
			self.run_function("settings")

	def open_editor_page(self, param_name):
		#FIXME add different editors
		self.editor["variable"] = param_name
		self.editor["variable_raw_value"] = self.occ.rp.get_raw_val(param_name)
		self.editor["variable_value"] = self.occ.rp.get_val(param_name)
		self.editor["variable_unit"] = self.occ.rp.get_unit(param_name)
		self.editor["variable_description"] = self.occ.rp.get_description(param_name)
		self.editor_index = 0
		#FIXME Make it mory pythonic
		if self.editor_type == 0: 
			name = self.editor["variable"]
			#FIXME make a stripping function
			na = name.find("_")
			if na > -1:
				n = name[:na]
			else:
				n = name
			unit = self.occ.rp.get_unit(n)
			self.editor["variable"] = n
			self.editor["variable_unit"] = unit
			self.editor["variable_value"] = 0
			self.use_page("editor_units")
		if self.editor_type == 1: 
			self.use_page("editor_numbers")

	def run_function(self, name):
		functions = {	"page_0" : self.load_page_0,
				"settings" : self.load_settings_page,
				"debug_level" : self.debug_level,
				"ed_accept" : self.ed_accept,
				"ed_cancel" : self.ed_cancel,
				"ed_decrease" : self.ed_decrease,
				"ed_increase" : self.ed_increase,
				"ed_next" : self.ed_next,
				"ed_next_unit" : self.ed_next_unit,
				"ed_prev" : self.ed_prev,
				"ed_prev_unit" : self.ed_prev_unit,
				"halt" : self.halt,
				"load_default_layout" : self.load_default_layout,
				"load_current_layout" : self.load_current_layout,
				"load_white_lcd_layout" : self.load_lcd_white_layout,
				"next_page" : self.next_page,
				"prev_page" : self.prev_page,
				"reboot" : self.reboot,
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
		self.accept_edit()
		self.use_main_page()

	def ed_cancel(self):
		self.use_main_page()

	def ed_decrease(self):
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
		variable_value = self.editor["variable_raw_value"]
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
		if next_unit != variable_unit:
			variable_value = self.uc.convert(variable_value, next_unit)
		try:
			f = self.occ.rp.p_format[variable]
		except KeyError:
			self.occ.log.warning("[LY] Formatting not available: param_name ={}".format(variable))
			f = "%.1f"
		self.editor["variable_value"] = float(f % float(variable_value))
		self.editor["variable_unit"] = next_unit

	def ed_next_unit(self):
		self.ed_change_unit(1)
		self.force_refresh()

	def ed_prev_unit(self):
		self.ed_change_unit(0)
		self.force_refresh()

	def accept_edit(self):
		variable = self.editor["variable"]
		variable_unit = self.editor["variable_unit"]
		variable_raw_value = self.editor["variable_raw_value"]
		variable_value = self.editor["variable_value"]
		if self.editor_type == 0:
			self.occ.rp.units[variable] = variable_unit
		if self.editor_type == 1:
			unit_raw = self.occ.rp.get_internal_unit(variable)
			value = variable_value
			if unit_raw != variable_unit:
				value = self.uc.convert(variable_raw_value, variable_unit)
			self.occ.rp.p_raw[variable] = float(value)
			self.occ.rp.units[variable] = self.editor["variable_unit"]
			if variable == "altitude_home":
				#Force recalculation
				self.occ.rp.pressure_at_sea_level_calculated = False
		self.force_refresh()

	def next_page(self):
		self.occ.log.debug("[LY][F] next_page")
		#cp = self.current_page_id
		no = int(self.current_page_id[-1:])
		name = self.current_page_id[:-1]
		#Editor is a special page - it cannot be switched, only cancel or accept
		if self.current_page_id is not "editor":
			try:
				next_page_name = name + unicode(no + 1)
				self.use_page(next_page_name)
			except KeyError:
				self.use_page(name + "0")
				#FIXME Use cp to block circular page scrolling - it should be in options
				#self.use_page(cp)

	def prev_page(self):
		self.occ.log.debug("[LY][F] prev_page")
		#cp = self.current_page_id
		no = int(self.current_page_id[-1:])
		name = self.current_page_id[:-1]
		#Editor is a special page - it cannot be switched, only cancel or accept
		if self.current_page_id is not "editor":
			try:
				prev_page_name = name + unicode(no - 1)
				self.use_page(prev_page_name)
			except KeyError:
				#FIXME Hardcoded string again...
				if name.startswith("page"):
					self.use_page(name + unicode(self.max_page_id))
				else:
					self.use_page(name + unicode(self.max_settings_id))
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
		self.occ.running = False

	def reboot(self):
		self.quit()
		time.sleep(2)
		if not self.occ.simulate:
			os.system("reboot")

	def halt(self):
		self.quit()
		time.sleep(2)
		if not self.occ.simulate:
			os.system("halt")

	def debug_level(self):
		#FIXME Merge with occ LOG_LEVEL
		LOG_LEVEL = {   "DEBUG"    : self.occ.log.DEBUG,
				"INFO"     : self.occ.log.INFO,
				"WARNING"  : self.occ.log.WARNING,
				"ERROR"    : self.occ.log.ERROR,
				"CRITICAL" : self.occ.log.CRITICAL
		}
		log_level = self.occ.logger.getEffectiveLevel()
		log_level -= 10
		if log_level < 10:
			log_level = 40
		log_level_name = self.occ.log.getLevelName(log_level)
		self.occ.switch_log_level(log_level_name)
		self.occ.rp.params["debug_level"] = log_level_name
