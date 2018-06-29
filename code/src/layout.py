#! /usr/bin/python
## @package layout
#   Module responsible for loading and rendering layouts. Needs heavy cleaning...
from shutil import copyfile
from units import units
import logging
import os
import pygame
import struct
import sys
import time
import yaml


## Class for handling layouts
class layout():
    # def __init__(self, occ, layout_path="layouts/current.yaml"):
    # Temporary change

    def __init__(self, occ, layout_path="layouts/default.yaml"):
        ## @var l
        # System logger handle
        self.l = logging.getLogger('system')
        self.occ = occ
        ## @var ble_scanner
        # ble_Scanner instance handle
        self.ble_scanner = occ.ble_scanner
        self.uc = units()
        self.screen = occ.screen
        self.editor_name = ''
        self.colorkey = [0, 0, 0]
        self.alpha = 255
        self.font_list = {}
        self.page_list = {}
        self.page_index = {}
        self.function_rect_list = {}
        self.current_function_list = []
        self.current_image_list = {}
        self.layout_path = layout_path
        self.load_layout(layout_path)
        self.render_button = None

    def load_layout(self, layout_path):
        self.max_page_id = 0
        self.max_settings_id = 0
        self.page_list = {}
        self.page_index = {}
        try:
            with open(layout_path) as f:
                self.layout_tree = yaml.safe_load(f)
            f.close()
            self.layout_path = layout_path
        except:
            self.l.error(
                "{} Loading layout {} failed, falling back to default.yaml".format(__name__, layout_path))
            sys_info = "Error details: {}".format(sys.exc_info()[0])
            self.l.error(sys_info)
            # Fallback to default layout
            # FIXME - define const file with paths?
            layout_path = "layouts/default.yaml"
            with open(layout_path) as f:
                self.layout_tree = yaml.safe_load(f)
            f.close()

        for page in self.layout_tree['pages']:
            page_id = page['id']
            self.page_list[page_id] = page
            self.page_index[page_id] = page['name']
            page_type = page['type']
            _number = page['number']
            if page_type == 'normal':
                number = int(_number)
                self.max_page_id = max(self.max_page_id, number)
            if page_type == 'settings':
                number = int(_number)
                self.max_settings_id = max(self.max_settings_id, number)
        self.use_page()
        self.write_layout()

    def write_layout(self, layout_path="layouts/current.yaml"):
        copyfile(self.layout_path, layout_path)

    def use_page(self, page_id="page_0"):
        self.l.debug("[LY][F] use_page {}".format(page_id))
        self.occ.force_refresh()
        self.current_function_list = []
        self.current_button_list = []
        self.current_page = self.page_list[page_id]
        try:
            bg_path = self.current_page['background']
            self.bg_image = pygame.image.load(bg_path).convert()
        except pygame.error:
            self.l.critical("{} Cannot load background image! layout_path = {} background path = {} page_id = {}"
                            .format(__name__, self.layout_path, bg_path, page_id))
            # That stops occ but not immediately - errors can occur
            self.occ.running = False
            self.occ.cleanup()
        try:
            bt_path = self.current_page['buttons']
            self.bt_image = pygame.image.load(bt_path).convert()
        except pygame.error:
            self.l.critical("{} Cannot load buttons image! layout_path = {} buttons path = {} page_id = {}"
                            .format(__name__, self.layout_path, bt_path, page_id))
            self.occ.running = False
            self.occ.cleanup()
            pass
        self.font = self.current_page['font']
        self.font_size = self.current_page['font_size']
        if (self.font == ""):
            self.font = None
        self.fg_colour_rgb = self.current_page['fg_colour']
        self.fg_colour = struct.unpack('BBB', self.fg_colour_rgb.decode('hex'))
        for field in self.current_page['fields']:
            self.current_function_list.append(field['function'])
            try:
                b = field['button']
            except KeyError:
                b = None
            if (b is not None):
                x0 = int(b.get('x0'))
                y0 = int(b.get('y0'))
                w = int(b.get('w'))
                h = int(b.get('h'))
                name = field.get('function')
                rect = pygame.Rect(x0, y0, w, h)
                self.function_rect_list[name] = rect
                self.current_button_list.append(name)
                #try:
                #    position = (field['x'], field['y'])
                #except KeyError:
                #    pass
                try:
                    if (field['file'] is not None):
                        self.load_image(field['file'])
                except KeyError:
                    pass

    def load_image(self, image_path):
        try:
            image = pygame.image.load(image_path).convert()
            image.set_colorkey(self.colorkey)
            image.set_alpha(self.alpha)
            self.current_image_list[image_path] = image
            self.l.debug("[LY] Image {} loaded".format(image_path))
        except:
            self.l.error("[LY] Cannot load image {}".format(image_path))
            self.current_image_list[image_path] = None

    def use_main_page(self):
        self.use_page()

    def render_background(self, screen):
        screen.blit(self.bg_image, [0, 0])

    def render_pressed_button(self, screen, function):
        # FIXME make sure it's OK to skip rendering here
        try:
            r = self.function_rect_list[function]
            screen.blit(self.bt_image, r, r, 0)
        # FIXME required to catch exception?
        except (TypeError, AttributeError):
            pass

    def render_page(self):
        self.render_background(self.screen)
        self.show_pressed_button()
        self.render(self.screen)

    def make_image_key(self, image_path, value):
        suffix = "_" + unicode(value)
        extension = image_path[-4:]
        name = image_path[:-4]
        return (name + suffix + extension)

    def render(self, screen):
        for field in self.current_page['fields']:
            function = field['function']
            position_x = field['x']
            position_y = field['y']
            value = self.occ.rp.get_param(function)
            if value is None:
                try:
                    value = field['text']
                except KeyError:
                    value = ""
            uv = unicode(value)
            variable = None
            # Get icon image
            try:
                image_path = field['file']
            except KeyError:
                image_path = None
            try:
                variable = field['variable']
                value = self.occ.rp.get_raw_val(variable['name'])
                try:
                    # If there is a variable with frames defined prepare path for relevant icon
                    frames = field['variable']['frames']
                    if value > frames:
                        self.l.error("[LY] Variable {} value {} is greater than number of frames ({}) for image file {}".format(variable['name'], value, frames, image_path))
                        value = frames
                    image_path = self.make_image_key(image_path, value)
                except KeyError:
                    pass
            except KeyError:
                pass
            if image_path is not None:
                if image_path not in self.current_image_list:
                    self.load_image(image_path)
                image = self.current_image_list[image_path]
                if image is not None:
                    screen.blit(image, [position_x, position_y])
            try:
                fs = field['font_size']
            except KeyError:
                # Fall back to page font size
                fs = self.font_size
            if function != "variable_value":
                font_size = int(12.0 * fs)
                if font_size in self.font_list:
                    font = self.font_list[font_size]
                else:
                    font = pygame.font.Font(self.font, font_size)
                    self.font_list[font_size] = font
                # font = pygame.font.Font(self.font, font_size)
                ren = font.render(uv, 1, self.fg_colour)
                x = ren.get_rect().centerx
                y = ren.get_rect().centery
                screen.blit(ren, (position_x - x, position_y - y))
            else:
                font_size_small = int(12.0 * (fs - 1))
                font_size_large = int(12.0 * (fs + 1))
                if font_size_small in self.font_list:
                    font_s = self.font_list[font_size_small]
                else:
                    font_s = pygame.font.Font(self.font, font_size_small)
                    self.font_list[font_size_small] = font_s
                if font_size_large in self.font_list:
                    font_l = self.font_list[font_size_large]
                else:
                    font_l = pygame.font.Font(self.font, font_size_large)
                    self.font_list[font_size_large] = font_l
                i = self.occ.rp.params["editor_index"]
                rv1 = uv[:i]
                ren1 = font_s.render(rv1, 1, self.fg_colour)
                w1 = ren1.get_rect().width
                y1 = ren1.get_rect().centery
                rv2 = uv[i]
                ren2 = font_l.render(rv2, 1, self.fg_colour)
                w2 = ren2.get_rect().width
                y2 = ren2.get_rect().centery
                rv3 = uv[i + 1:]
                ren3 = font_s.render(rv3, 1, self.fg_colour)
                w3 = ren3.get_rect().width
                y3 = ren3.get_rect().centery
                x = position_y - int((w1 + w2 + w3) / 2)
                screen.blit(ren1, (x, position_y - y1))
                screen.blit(ren2, (x + w1, position_y - y2))
                screen.blit(ren3, (x + w1 + w2, position_y - y3))

    def show_pressed_button(self):
        if self.render_button:
            for func in self.current_button_list:
                try:
                    if self.function_rect_list[func].collidepoint(self.render_button):
                        self.render_pressed_button(self.screen, func)
                        break
                except KeyError:
                    self.l.critical("{} show_pressed_button failed! func ={}".format, __name__, func)
                    self.occ.running = False

    def check_click(self, position, click):
        if click == 'SHORT':
            # Short click
            # FIXME Search through function_rect_list directly? TBD
            for function in self.current_button_list:
                try:
                    if self.function_rect_list[function].collidepoint(position):
                        self.run_function(function)
                        break
                except KeyError:
                    self.l.debug("[LY] CLICK on non-clickable {}".format(function))
        elif click == 'LONG':
            # print self.function_rect_list
            # print self.current_button_list
            for function in self.current_button_list:
                try:
                    if self.function_rect_list[function].collidepoint(position):
                        # FIXME I's dirty way of getting value - add some
                        # helper function
                        self.l.debug("[LY] LONG CLICK on {}".format(function))
                        self.editor_name = self.occ.rp.get_editor_name(function)
                        if self.editor_name:
                            self.open_editor_page(function)
                            break
                        p = self.occ.rp.strip_end(function)
                        if p in self.occ.rp.p_resettable:
                            self.occ.rp.reset_param(p)
                except KeyError:
                    self.l.debug("[LY] LONG CLICK on non-clickable {} or missing editor page".format(function))
        elif click == 'R_TO_L':  # Swipe RIGHT to LEFT
            self.run_function("next_page")
        elif click == 'L_TO_R':  # Swipe LEFT to RIGHT
            self.run_function("prev_page")
        elif click == 'B_TO_T':  # Swipe BOTTOM to TOP
            self.run_function("page_0")
        elif click == 'T_TO_B':  # Swipe TOP to BOTTOM
            self.run_function("settings")

    def open_editor_page(self, function):
        self.l.debug("[LY] Opening editor {} for {}".format(self.editor_name, function))
        self.occ.rp.set_param('variable', function)
        self.occ.rp.set_param('variable_raw_value', self.occ.rp.get_raw_val(function))
        self.occ.rp.set_param('variable_value', self.occ.rp.get_param(function))
        self.occ.rp.set_param('variable_unit', self.occ.rp.get_unit(function))
        self.occ.rp.set_param('variable_description', self.occ.rp.get_description(function))
        self.occ.rp.set_param('editor_index', 0)

        if self.editor_name == 'editor_units':
            name = self.occ.rp.params["variable"]
            # FIXME make a stripping function
            na = name.find("_")
            if na > -1:
                n = name[:na]
            else:
                n = name
            unit = self.occ.rp.get_unit(n)
            self.occ.rp.set_param('variable', n)
            self.occ.rp.set_param('variable_unit', unit)
            self.occ.rp.set_param('variable_value', 0)
        self.use_page(self.editor_name)

    def run_function(self, name):
        functions = {"page_0": self.load_page_0,
                     "settings": self.load_settings_page,
                     "debug_level": self.debug_level,
                     "ed_accept": self.ed_accept,
                     "ed_cancel": self.ed_cancel,
                     "ed_decrease": self.ed_decrease,
                     "ed_increase": self.ed_increase,
                     "ed_next": self.ed_next,
                     "ed_next_unit": self.ed_next_unit,
                     "ed_prev": self.ed_prev,
                     "ed_prev_unit": self.ed_prev_unit,
                     "halt": self.halt,
                     "load_default_layout": self.load_default_layout,
                     "load_current_layout": self.load_current_layout,
                     "next_page": self.next_page,
                     "prev_page": self.prev_page,
                     "reboot": self.reboot,
                     "write_layout": self.write_layout,
                     "ble_scan": self.ble_scanner.ble_scan,
                     "ble_dev_name_1": self.ble_scanner.ble_dev_name_1,
                     "ble_dev_name_2": self.ble_scanner.ble_dev_name_2,
                     "ble_dev_name_3": self.ble_scanner.ble_dev_name_3,
                     "ble_dev_name_4": self.ble_scanner.ble_dev_name_4,
                     "quit": self.quit}
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
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        ui = u[i]
        if ui == "0":
            ui = "9"
        else:
            try:
                ui = unicode(int(ui) - 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.occ.rp.params["variable_value"] = un
        self.force_refresh()

    def ed_increase(self):
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        ui = u[i]
        if ui == "9":
            ui = "0"
        else:
            try:
                ui = unicode(int(ui) + 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.occ.rp.params["variable_value"] = un
        self.force_refresh()

    def ed_next(self):
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        if u[0] == '0':
            u = u[1:]
            self.occ.rp.params["variable_value"] = u
        else:
            i += 1
        l = len(u) - 1
        if i > l:
            i = l
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i += 1
        self.occ.rp.params["editor_index"] = i
        self.force_refresh()

    def ed_prev(self):
        u = unicode(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        i -= 1
        if i < 0:
            i = 0
            uv = "0" + u
            self.occ.rp.params["variable_value"] = uv
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i -= 1
        self.occ.rp.params["editor_index"] = i
        self.force_refresh()

    def ed_change_unit(self, direction):
        # direction to be 1 (next) or 0 (previous)
        variable = self.occ.rp.params["variable"]
        variable_unit = self.occ.rp.params["variable_unit"]
        variable_value = self.occ.rp.params["variable_raw_value"]
        current_unit_index = self.occ.rp.units_allowed[
            variable].index(variable_unit)
        if direction == 1:
            try:
                next_unit = self.occ.rp.units_allowed[
                    variable][current_unit_index + 1]
            except IndexError:
                next_unit = self.occ.rp.units_allowed[variable][0]
        else:
            try:
                next_unit = self.occ.rp.units_allowed[
                    variable][current_unit_index - 1]
            except IndexError:
                next_unit = self.occ.rp.units_allowed[variable][-1]
        if next_unit != variable_unit:
            variable_value = self.uc.convert(variable_value, next_unit)
        try:
            f = self.occ.rp.p_format[variable]
        except KeyError:
            self.l.warning(
                "[LY] Formatting not available: function ={}".format(variable))
            f = "%.1f"
        self.occ.rp.params["variable_value"] = float(f % float(variable_value))
        self.occ.rp.params["variable_unit"] = next_unit

    def ed_next_unit(self):
        self.ed_change_unit(1)
        self.force_refresh()

    def ed_prev_unit(self):
        self.ed_change_unit(0)
        self.force_refresh()

    def accept_edit(self):
        variable = self.occ.rp.params["variable"]
        variable_unit = self.occ.rp.params["variable_unit"]
        variable_raw_value = self.occ.rp.params["variable_raw_value"]
        variable_value = self.occ.rp.params["variable_value"]
        if self.editor_name == "editor_units":
            self.occ.rp.units[variable] = variable_unit
        if self.editor_name == "editor_numbers":
            unit_raw = self.occ.rp.get_internal_unit(variable)
            value = variable_value
            if unit_raw != variable_unit:
                value = self.uc.convert(variable_raw_value, variable_unit)
            self.occ.rp.p_raw[variable] = float(value)
            self.occ.rp.units[variable] = self.occ.rp.params["variable_unit"]
            # FIXME - find a better place for it
            if variable == "altitude_home":
                # Force recalculation
                self.occ.rp.p_raw["pressure_at_sea_level"] = 0
        if self.editor_name == "editor_string":
            self.occ.rp.p_raw[variable] = variable_value
            self.occ.rp.params[variable] = variable_value
        if self.editor_name == "ble_selector":
            (name, addr, dev_type) = variable_value
            self.occ.sensors.set_ble_device(name, addr, dev_type)
        self.force_refresh()

    def get_page(self, page_type, page_no):
        self.l.debug("[LY] get_page {} {} ".format(page_type, page_no))
        if page_type == 'normal':
            if page_no == -1:
                page_no = self.max_page_id
            if page_no > self.max_page_id:
                page_no = 0
        elif page_type == 'settings':
            if page_no == -1:
                page_no = self.max_settings_id
            if page_no > self.max_settings_id:
                page_no = 0
        for p, page in self.page_list.iteritems():
            t = page['type']
            n = page['number']
            if t == page_type and n == page_no:
                return page['id']

    def next_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.current_page['type'] == 'editor':
            number = int(self.current_page['number'])
            page_id = self.current_page['id']
            page_type = self.current_page['type']
            self.l.debug("[LY][F] next_page {} {} {}".format(page_id, page_type, number))
            next_page_id = self.get_page(page_type, number + 1)
            try:
                self.use_page(next_page_id)
            except KeyError:
                self.l.critical("[LY][F] Page 0 of type {} not found!".format(page_type))

    def prev_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.current_page['type'] == 'editor':
            number = int(self.current_page['number'])
            page_id = self.current_page['id']
            page_type = self.current_page['type']
            self.l.debug("[LY][F] prev_page {} {} {}".format(page_id, page_type, number))
            prev_page_id = self.get_page(page_type, number - 1)
            try:
                self.use_page(prev_page_id)
            except KeyError:
                self.l.critical("[LY][F] Page {} of type {} not found!".format(self.max_page_id, page_type))

    def load_layout_by_name(self, name):
        print(self.layout_path)
        self.load_layout("layouts/" + name)

    def load_current_layout(self):
        self.load_layout_by_name("current.yaml")

    def load_default_layout(self):
        self.load_layout_by_name("default.yaml")

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
        log_level = self.l.getEffectiveLevel()
        log_level -= 10
        if log_level < 10:
            log_level = 40
        log_level_name = logging.getLevelName(log_level)
        self.occ.switch_log_level(log_level_name)
        self.occ.rp.params["debug_level"] = log_level_name
