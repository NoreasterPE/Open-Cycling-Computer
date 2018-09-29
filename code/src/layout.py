#!/usr/bin/python3
## @package layout
#   Module responsible for loading and rendering layouts. Needs heavy cleaning...
import unit_converter
import logging
import os
import sys
import time
import yaml
import cairo


## Class for handling layouts
class layout():
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'layout'}
    # def __init__(self, occ, layout_path="layouts/current.yaml"):
    # Temporary change

    def __init__(self, occ, cr, layout_path="layouts/default.yaml"):
        ## @var l
        # System logger handle
        self.log = logging.getLogger('system')
        self.occ = occ
        self.cr = cr
        self.render = False
        self.uc = unit_converter.unit_converter()
        self.editor_name = ''
        self.page_list = {}
        self.page_index = {}
        self.function_rect_list = {}
        self.current_image_list = {}
        self.layout_path = layout_path
        self.load_layout(layout_path)

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
        except FileNotFoundError:
            self.log.critical("Loading layout {} failed, falling back to default.yaml".format(__name__, layout_path), extra=self.extra)
            sys_info = "Error details: {}".format(sys.exc_info()[0])
            self.log.error(sys_info, extra=self.extra)
            # Fallback to default layout
            # FIXME - define const file with paths?
            layout_path = "layouts/default.yaml"
            try:
                with open(layout_path) as f:
                    self.layout_tree = yaml.safe_load(f)
                    f.close()
            except FileNotFoundError:
                self.log.critical("Loading default layout {} failed, Quitting...".format(__name__, layout_path), extra=self.extra)
                self.occ.stop()

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

    def use_page(self, page_id="page_0"):
        self.log.debug("use_page {}".format(page_id), extra=self.extra)
        self.render = True
        self.current_button_list = []
        self.current_page = self.page_list[page_id]
        try:
            self.background_image = self.load_image(self.current_page['background'])
        except cairo.Error:
            self.log.critical("{}: Cannot load background image!".format(__name__,), extra=self.extra)
            self.log.critical("layout_path = {}".format(self.layout_path), extra=self.extra)
            self.log.critical("background path = {}".format(self.current_page['background']), extra=self.extra)
            self.log.critical("page_id = {}".format(page_id), extra=self.extra)
            # That stops occ but not immediately - errors can occur
            self.occ.stop()
        try:
            self.buttons_image = self.load_image(self.current_page['buttons'])
        except cairo.Error:
            self.log.critical("{}: Cannot load buttons image!".format(__name__,), extra=self.extra)
            self.log.critical("layout_path = {}".format(self.layout_path), extra=self.extra)
            self.log.critical("buttons path = {}".format(self.current_page['buttons']), extra=self.extra)
            self.log.critical("page_id = {}".format(page_id), extra=self.extra)
            self.occ.top()
        self.font = self.current_page['font']
        # Wait for OCC to set rendering module
        try:
            self.cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except AttributeError:
            pass
        self.page_font_size = self.current_page['font_size']
        if (self.font == ""):
            self.font = None
        self.fg_colour_rgb = self.current_page['fg_colour']
        fg_colour_rgb = self.fg_colour_rgb
        if fg_colour_rgb[0] == '#':
            fg_colour_rgb = fg_colour_rgb[1:]
        r, g, b = fg_colour_rgb[:2], fg_colour_rgb[2:4], fg_colour_rgb[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        self.fg_colour = (r, g, b)
        for field in self.current_page['fields']:
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
                rect = (x0, y0, w, h)
                self.function_rect_list[name] = rect
                self.current_button_list.append(name)
                # try:
                #    position = (field['x'], field['y'])
                # except KeyError:
                #    pass
                try:
                    if (field['file'] is not None):
                        self.current_image_list[field['file']] = self.load_image(field['file'])
                except KeyError:
                    pass

    def load_image(self, image_path):
        try:
            image = self.png_to_cairo_surface(image_path)
            self.log.debug("Image {} loaded".format(image_path), extra=self.extra)
        except cairo.Error:
            self.log.critical("Cannot load image {}".format(image_path), extra=self.extra)
            image = None
        return image

    def use_main_page(self):
        self.use_page()

    def render_background(self):
        self.cr.set_source_surface(self.background_image, 0, 0)
        self.cr.rectangle(0, 0, 240, 320)
        self.cr.fill()

    def render_page(self):
        self.render_background()
        self.render = True
        # LAYOUT DEBUG FUNCION self.render_all_buttons()
        self.render_layout()

    def make_image_key(self, image_path, value):
        suffix = "_" + format(value)
        extension = image_path[-4:]
        name = image_path[:-4]
        return (name + suffix + extension)

    def render_layout(self):
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
            uv = format(value)
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
                        self.log.error("Variable {} value {} is greater than number of frames ({}) for image file {}".format(variable['name'], value, frames, image_path), extra=self.extra)
                        value = frames
                    image_path = self.make_image_key(image_path, value)
                except KeyError:
                    pass
            except KeyError:
                pass
            if image_path is not None:
                if image_path not in self.current_image_list:
                    self.current_image_list[image_path] = self.load_image(image_path)
                image = self.current_image_list[image_path]
                if image is not None:
                    self.image_to_surface(image, position_x, position_y)
            try:
                fs = field['font_size']
            except KeyError:
                # Fall back to page font size
                fs = self.page_font_size
            self.cr.set_font_size(fs)
            if function != "variable_value":
                #FIXME Colour ignored for now
                self.text_to_surface(uv, position_x, position_y)
            else:
                i = self.occ.rp.params["editor_index"]
                #Head
                rv1 = uv[:i]
                te1 = self.cr.text_extents(rv1)
                #Tail
                rv3 = uv[i + 1:]
                te3 = self.cr.text_extents(rv3)
                #Currently edited digit
                rv2 = uv[i]
                self.cr.set_font_size(1.4 * fs)
                te2 = self.cr.text_extents(rv2)

                total_width_half = (te1.width + te2.width + te3.width) / 2
                rv1_x = position_x - total_width_half + (te1.width / 2) + te1.x_bearing
                rv2_x = position_x - total_width_half + te1.width + (te2.width / 2) + te1.x_bearing + te2.x_bearing
                rv3_x = position_x - total_width_half + te1.width + te2.width + (te3.width / 2) + te1.x_bearing + te2.x_bearing + te3.x_bearing

                self.text_to_surface(rv2, rv2_x, position_y)
                self.cr.set_font_size(fs)
                self.text_to_surface(rv1, rv1_x, position_y)
                self.text_to_surface(rv3, rv3_x, position_y)

    def render_all_buttons(self):
        # LAYOUT DEBUG FUNCION
        for function in self.current_button_list:
            fr = self.function_rect_list[function]
            self.cr.set_source_rgb(0.0, 1.0, 0.0)
            self.cr.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.cr.fill()
            self.cr.set_line_width(2.0)
            self.cr.set_source_rgb(1.0, 0.0, 0.0)
            self.cr.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.cr.stroke()

    def render_pressed_button(self, pressed_pos):
        self.log.debug("render_pressed_button started", extra=self.extra)
        for function in self.current_button_list:
            if self.point_in_rect(pressed_pos, self.function_rect_list[function]):
                fr = self.function_rect_list[function]
                self.cr.set_source_surface(self.buttons_image, 0, 0)
                self.cr.rectangle(fr[0], fr[1], fr[2], fr[3])
                self.cr.fill()
        self.log.debug("render_pressed_button finished", extra=self.extra)

    def check_click(self, position, click):
        if click == 'SHORT':
            # Short click
            # FIXME Search through function_rect_list directly? TBD
            for function in self.current_button_list:
                try:
                    if self.point_in_rect(position, self.function_rect_list[function]):
                        self.run_function(function)
                        break
                except KeyError:
                    self.log.debug("CLICK on non-clickable {}".format(function), extra=self.extra)
        elif click == 'LONG':
            for function in self.current_button_list:
                if self.point_in_rect(position, self.function_rect_list[function]):
                    self.log.debug("LONG CLICK on {}".format(function), extra=self.extra)
                    for f in self.current_page['fields']:
                        if f['function'] == function:
                            try:
                                if f['resettable']:
                                    resettable = True
                            except KeyError:
                                    resettable = False
                            try:
                                if f['editable']:
                                    editable = True
                                    try:
                                        self.editor_name = f["editor"]
                                    except KeyError:
                                        self.editor_name = None
                                        self.log.critical("Function {} marked as editable, but no editor field found".format(function), extra=self.extra)
                                    try:
                                        self.editor_function_description = f["description"]
                                    except KeyError:
                                        self.editor_function_description = None
                                        self.log.critical("Function {} marked as editable, but no description field found".format(function), extra=self.extra)
                            except KeyError:
                                    editable = False
                            if resettable:
                                self.log.debug("Resetting {}".format(function), extra=self.extra)
                                self.occ.rp.reset_param(function)
                            elif editable:
                                self.log.debug("Editing {} with {}".format(function, self.editor_name), extra=self.extra)
                                self.open_editor_page(function)
                            else:
                                self.log.debug("LONG CLICK on non-clickable {}".format(function), extra=self.extra)
        elif click == 'R_TO_L':  # Swipe RIGHT to LEFT
            self.run_function("next_page")
        elif click == 'L_TO_R':  # Swipe LEFT to RIGHT
            self.run_function("prev_page")
        elif click == 'B_TO_T':  # Swipe BOTTOM to TOP
            self.run_function("page_0")
        elif click == 'T_TO_B':  # Swipe TOP to BOTTOM
            self.run_function("settings")

    def open_editor_page(self, function):
        self.log.debug("Opening editor {} for {}".format(self.editor_name, function), extra=self.extra)
        self.occ.rp.set_param('variable', function)
        self.occ.rp.set_param('variable_raw_value', self.occ.rp.get_raw_val(function))
        self.occ.rp.set_param('variable_value', self.occ.rp.get_param(function))
        self.occ.rp.set_param('variable_unit', self.occ.rp.get_unit(function))
        self.occ.rp.set_param('variable_description', self.editor_function_description)
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
                     "quit": self.quit}
        functions[name]()

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
        u = format(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        ui = u[i]
        if ui == "0":
            ui = "9"
        else:
            try:
                ui = format(int(ui) - 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.occ.rp.params["variable_value"] = un
        self.render = True

    def ed_increase(self):
        u = format(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        ui = u[i]
        if ui == "9":
            ui = "0"
        else:
            try:
                ui = format(int(ui) + 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.occ.rp.params["variable_value"] = un
        self.render = True

    def ed_next(self):
        u = format(self.occ.rp.params["variable_value"])
        i = self.occ.rp.params["editor_index"]
        if u[0] == '0':
            u = u[1:]
            self.occ.rp.params["variable_value"] = u
        else:
            i += 1
        le = len(u) - 1
        if i > le:
            i = le
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i += 1
        self.occ.rp.params["editor_index"] = i
        self.render = True

    def ed_prev(self):
        u = format(self.occ.rp.params["variable_value"])
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
        self.render = True

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
        try:
            f = self.occ.rp.p_format[variable]
        except KeyError:
            self.log.warning("Formatting not available: function ={}".format(variable), extra=self.extra)
            f = "%.1f"
        self.occ.rp.params["variable_value"] = float(f % float(variable_value))
        self.occ.rp.params["variable_unit"] = next_unit

    def ed_next_unit(self):
        self.ed_change_unit(1)
        self.render = True

    def ed_prev_unit(self):
        self.ed_change_unit(0)
        self.render = True

    def accept_edit(self):
        self.log.debug("accept_edit started", extra=self.extra)
        variable = self.occ.rp.params["variable"]
        variable_unit = self.occ.rp.params["variable_unit"]
        variable_raw_value = self.occ.rp.params["variable_raw_value"]
        variable_value = self.occ.rp.params["variable_value"]
        self.log.debug("variable: {}, variable_unit: {}, variable_raw_value: {}, variable_value: {}".format(variable, variable_unit, variable_raw_value, variable_value), extra=self.extra)
        if self.editor_name == "editor_units":
            self.occ.rp.units[variable] = variable_unit
        if self.editor_name == "editor_numbers":
            unit_raw = self.occ.rp.get_internal_unit(variable)
            value = float(variable_value)
            if unit_raw != variable_unit:
                value = self.uc.convert(value, variable_unit, unit_raw)
            self.occ.rp.set_raw_param(variable, value)
            self.occ.rp.update_param(variable)
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
        self.render = True
        self.log.debug("accept_edit finished", extra=self.extra)

    def get_page(self, page_type, page_no):
        self.log.debug("get_page {} {} ".format(page_type, page_no), extra=self.extra)
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
        for p, page in self.page_list.items():
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
            self.log.debug("next_page {} {} {}".format(page_id, page_type, number), extra=self.extra)
            next_page_id = self.get_page(page_type, number + 1)
            try:
                self.use_page(next_page_id)
            except KeyError:
                self.log.critical("Page 0 of type {} not found!".format(page_type), extra=self.extra)

    def prev_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.current_page['type'] == 'editor':
            number = int(self.current_page['number'])
            page_id = self.current_page['id']
            page_type = self.current_page['type']
            self.log.debug("prev_page {} {} {}".format(page_id, page_type, number), extra=self.extra)
            prev_page_id = self.get_page(page_type, number - 1)
            try:
                self.use_page(prev_page_id)
            except KeyError:
                self.log.critical("Page {} of type {} not found!".format(self.max_page_id, page_type), extra=self.extra)

    def load_layout_by_name(self, name):
        self.load_layout("layouts/" + name)

    def load_current_layout(self):
        self.load_layout_by_name("current.yaml")

    def load_default_layout(self):
        self.load_layout_by_name("default.yaml")

    def quit(self):
        self.occ.stop()

    def reboot(self):
        self.quit()
        time.sleep(2)
        if not self.occ.simulate:
            os.system("reboot")

    def halt(self):
        self.quit()
        time.sleep(2)
        if not self.occ.simulate:
            os.system("./halt.sh")

    def debug_level(self):
        log_level = self.log.getEffectiveLevel()
        log_level += 10
        if log_level > 50:
            log_level = 10
        log_level_name = logging.getLevelName(log_level)
        self.log.debug("Changing log level to: {}".format(log_level_name), extra=self.extra)
        self.occ.switch_log_level(log_level_name)
        self.occ.rp.params["debug_level"] = log_level_name

    def png_to_cairo_surface(self, file_path):
        png_surface = cairo.ImageSurface.create_from_png(file_path)
        return png_surface

    def image_to_surface(self, surface, x=0, y=0, w=240, h=320):
        self.cr.set_source_surface(surface, x, y)
        self.cr.rectangle(x, y, w, h)
        self.cr.fill()

    def text_to_surface(self, text, x, y):
        self.cr.set_source_rgb(0.0, 0.0, 0.0)
        te = self.cr.text_extents(text)
        self.cr.rectangle(x - (te.width / 2), y - (te.height / 2), te.width, te.height)
        self.cr.fill()
        self.cr.set_source_rgb(1.0, 1.0, 1.0)
        x0 = x - (te.width / 2) - te.x_bearing
        y0 = y - (te.height / 2) - te.y_bearing
        self.cr.move_to(x0, y0)
        self.cr.show_text(text)
        return (te)

    def point_in_rect(self, point, rect):
        try:
            if rect[1] + rect[3] - point[1] < 0:
                return False
            if point[0] - rect[0] < 0:
                return False
            if rect[0] + rect[2] - point[0] < 0:
                return False
            if point[1] - rect[1] < 0:
                return False
            self.log.debug("Point: {} is in rect: {}".format(point, rect), extra=self.extra)
            return True
        except TypeError:
            return False
