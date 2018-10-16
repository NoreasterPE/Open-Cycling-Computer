#!/usr/bin/python3
## @package layout
#   Module responsible for loading and rendering layouts. Needs heavy cleaning...
import cairo
import datetime
import logging
import numbers
import os
import sys
import time
import unit_converter
import yaml


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
        self.editor_fields = None
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
            self.occ.stop()
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
        self.function_rect_list = {}
        if self.current_page['fields'] is not None:
            for field in self.current_page['fields']:
                try:
                    b = field['button']
                except KeyError:
                    b = None
                if (b is not None):
                    rect = (int(b.get('x0')), int(b.get('y0')), int(b.get('w')), int(b.get('h')))
                    name = field.get('function')
                    try:
                        meta_name = name + "_" + field['show']
                    except KeyError:
                        meta_name = name
                    self.function_rect_list[meta_name] = (name, rect)
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
        # LAYOUT DEBUG FUNCION
        #self.render_all_buttons()
        if self.current_page['fields'] is not None:
            self.render_layout()

    def make_image_key(self, image_path, value):
        suffix = "_" + format(value)
        extension = image_path[-4:]
        name = image_path[:-4]
        return (name + suffix + extension)

    def render_layout(self):
        for field in self.current_page['fields']:
            #print("{}".format(field))
            function = field['function']
            #print("{}".format(function))
            position_x = field['x']
            position_y = field['y']
            # Show value of function by default
            try:
                show = field["show"]
            except KeyError:
                show = "value"
            if show == "value":
                if self.current_page["type"] == "editor":
                    try:
                        value = self.editor_fields[function]
                    except (KeyError, TypeError):
                        value = None
                else:
                    try:
                        v = self.occ.sensors.parameters[function]["value"]
                        ru = self.occ.sensors.parameters[function]["raw_unit"]
                        u = self.occ.sensors.parameters[function]["unit"]
                        value = self.uc.convert(v, ru, u)
                        value = numbers.sanitise(value)
                    except (KeyError, TypeError):
                        value = None
            elif show == "tenths":
                try:
                    v = self.occ.sensors.parameters[function]["value"]
                    ru = self.occ.sensors.parameters[function]["raw_unit"]
                    u = self.occ.sensors.parameters[function]["unit"]
                    value = self.uc.convert(v, ru, u)
                    tenths_string = "{}".format(value - int(value))
                    value = format(tenths_string)[2:3]
                except (KeyError, TypeError):
                    value = None
            elif show == "unit":
                try:
                    value = self.occ.sensors.parameters[function]["unit"]
                except KeyError:
                    value = None
            elif show == "minimum":
                try:
                    v = self.occ.sensors.parameters[function]["value_min"]
                    ru = self.occ.sensors.parameters[function]["raw_unit"]
                    u = self.occ.sensors.parameters[function]["unit"]
                    value = self.uc.convert(v, ru, u)
                    value = numbers.sanitise(value)
                except KeyError:
                    value = None
            elif show == "average":
                try:
                    v = self.occ.sensors.parameters[function]["value_avg"]
                    ru = self.occ.sensors.parameters[function]["raw_unit"]
                    u = self.occ.sensors.parameters[function]["unit"]
                    value = self.uc.convert(v, ru, u)
                    value = numbers.sanitise(value)
                except KeyError:
                    value = None
            elif show == "maximum":
                try:
                    v = self.occ.sensors.parameters[function]["value_max"]
                    ru = self.occ.sensors.parameters[function]["raw_unit"]
                    u = self.occ.sensors.parameters[function]["unit"]
                    value = self.uc.convert(v, ru, u)
                    value = numbers.sanitise(value)
                except KeyError:
                    value = None
            if value is None:
                try:
                    value = field['text']
                except KeyError:
                    value = ""
            try:
                string_format = field["format"]
                if string_format == "hhmmss":
                    try:
                        minutes, seconds = divmod(int(value), 60)
                        hours, minutes = divmod(minutes, 60)
                        value = "{:02.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds)
                    except TypeError:
                        pass
                elif string_format == "time":
                    try:
                        value = datetime.datetime.fromtimestamp(int(value)).strftime('%H:%M:%S')
                    except TypeError:
                        pass
                elif string_format == "date":
                    try:
                        value = datetime.datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
            except KeyError:
                string_format = "%.0f"
            try:
                uv = string_format % float(value)
            except (TypeError, ValueError):
                uv = format(value)
            variable = None
            # Get icon image
            try:
                image_path = field['file']
            except KeyError:
                image_path = None
            try:
                variable = field['variable']
                #print("{} variable {}".format(function, variable))
                value = self.occ.sensors.parameters[variable["name"]]["value"]
                try:
                    # If there is a variable with frames defined prepare path for relevant icon
                    frames = field['variable']['frames']
                    if value > frames:
                        self.log.error("Variable {} value {} is greater than number of frames ({}) for image file {}".format(variable['name'], value, frames, image_path), extra=self.extra)
                        value = frames
                    image_path = self.make_image_key(image_path, value)
                except KeyError:
                    pass
            except (KeyError, TypeError):
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
            if string_format != "editor":
                #FIXME Colour ignored for now
                self.text_to_surface(uv, position_x, position_y)
            else:
                uv = self.editor_fields["value"]
                i = self.editor_fields["index"]
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
        for function, r in self.function_rect_list.items():
            fr = r[1]
            self.cr.set_source_rgb(0.0, 1.0, 0.0)
            self.cr.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.cr.fill()
            self.cr.set_line_width(2.0)
            self.cr.set_source_rgb(1.0, 0.0, 0.0)
            self.cr.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.cr.stroke()

    def render_pressed_button(self, pressed_pos):
        self.log.debug("render_pressed_button started", extra=self.extra)
        for function, r in self.function_rect_list.items():
            if self.point_in_rect(pressed_pos, r[1]):
                fr = r[1]
                self.cr.set_source_surface(self.buttons_image, 0, 0)
                self.cr.rectangle(fr[0], fr[1], fr[2], fr[3])
                self.cr.fill()
        self.log.debug("render_pressed_button finished", extra=self.extra)

    def check_click(self, position, click):
        long_click_data_ready = False
        if click == 'SHORT':
            clicked_function = None
            for function, r in self.function_rect_list.items():
                if self.point_in_rect(position, r[1]):
                    self.log.debug("CLICK on {} {}".format(function, r), extra=self.extra)
                    clicked_function = function
            if clicked_function:
                self.log.debug("run_function for {}".format(clicked_function), extra=self.extra)
                self.run_function(clicked_function)
        elif click == 'LONG':
            for function, r in self.function_rect_list.items():
                if self.point_in_rect(position, r[1]):
                    for f in self.current_page['fields']:
                        try:
                            _f = f['function'] + "_" + f["show"]
                        except KeyError:
                            _f = f['function']
                        if _f == function:
                            try:
                                if f['resettable']:
                                    resettable = True
                            except KeyError:
                                    resettable = False
                            try:
                                if f['editable']:
                                    editable = True
                                    self.editor_fields = dict()
                                    try:
                                        self.editor_fields["editor"] = f["editor"]
                                    except KeyError:
                                        self.editor_fields["editor"] = None
                                        self.log.critical("Function {} marked as editable, but no editor field found".format(function), extra=self.extra)
                                    try:
                                        self.editor_fields["description"] = f["description"]
                                    except KeyError:
                                        self.editor_fields["description"] = None
                                        self.log.critical("Function {} marked as editable, but no description field found".format(function), extra=self.extra)
                                    try:
                                        self.editor_fields["format"] = f["format"]
                                    except KeyError:
                                        self.editor_fields["format"] = "%.0f"
                            except KeyError:
                                    editable = False
                            if resettable:
                                self.log.debug("Resetting {}".format(r[0]), extra=self.extra)
                                print("resetting function {} {} not yet ready".format(function, r[0]))
                                #self.occ.rp.reset_param(r[0])
                            elif editable:
                                self.editor_fields["function"] = r[0]
                                long_click_data_ready = True
                                break
                            else:
                                self.log.debug("LONG CLICK on non-clickable {}".format(r[0]), extra=self.extra)
        elif click == 'R_TO_L':  # Swipe RIGHT to LEFT
            self.run_function("next_page")
        elif click == 'L_TO_R':  # Swipe LEFT to RIGHT
            self.run_function("prev_page")
        elif click == 'B_TO_T':  # Swipe BOTTOM to TOP
            self.run_function("page_0")
        elif click == 'T_TO_B':  # Swipe TOP to BOTTOM
            self.run_function("settings")

        if long_click_data_ready:
            long_click_data_ready = False
            self.log.debug("Opening editor {} for {}".format(self.editor_fields["editor"], self.editor_fields["function"]), extra=self.extra)
            f = self.editor_fields["function"]
            if self.editor_fields["editor"] == 'editor_units':
                self.editor_fields["value"] = self.occ.sensors.parameters[f]["unit"]
                self.editor_fields["unit"] = self.occ.sensors.parameters[f]["unit"]
            else:
                self.editor_fields["raw_value"] = self.occ.sensors.parameters[f]["value"]
                value = self.uc.convert(self.occ.sensors.parameters[f]["value"],
                                        self.occ.sensors.parameters[f]["raw_unit"],
                                        self.occ.sensors.parameters[f]["unit"])
                try:
                    self.editor_fields["value"] = self.editor_fields["format"] % value
                except TypeError:
                    self.editor_fields["value"] = value
                self.editor_fields["unit"] = self.occ.sensors.parameters[f]["unit"]
            self.editor_fields["index"] = 0
            self.use_page(self.editor_fields["editor"])

    def run_function(self, function):
        functions = {"page_0": self.load_page_0,
                     "settings": self.load_settings_page,
                     "log_level": self.log_level,
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
                     "write_config": self.write_config,
                     "reboot": self.reboot,
                     "quit": self.quit}
        try:
            functions[function]()
        except KeyError:
            self.log.debug("CLICK on non-clickable {}".format(function), extra=self.extra)

    def load_page_0(self):
        self.use_main_page()

    def load_settings_page(self):
        self.use_page("settings_0")

    def ed_accept(self):
        self.accept_edit()
        self.editor_fields = None
        self.use_main_page()

    def ed_cancel(self):
        self.editor_fields = None
        self.use_main_page()

    def ed_decrease(self):
        u = self.editor_fields["value"]
        i = self.editor_fields["index"]
        ui = u[i]
        if ui == "0":
            ui = "9"
        else:
            try:
                ui = format(int(ui) - 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.editor_fields["value"] = un
        self.render = True

    def ed_increase(self):
        u = self.editor_fields["value"]
        i = self.editor_fields["index"]
        ui = u[i]
        if ui == "9":
            ui = "0"
        else:
            try:
                ui = format(int(ui) + 1)
            except ValueError:
                pass
        un = u[:i] + ui + u[i + 1:]
        self.editor_fields["value"] = un
        self.render = True

    def ed_next(self):
        u = self.editor_fields["value"]
        i = self.editor_fields["index"]
        if u[0] == '0':
            u = u[1:]
            self.editor_fields["value"] = u
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
        self.editor_fields["index"] = i
        self.render = True

    def ed_prev(self):
        u = self.editor_fields["value"]
        i = self.editor_fields["index"]
        i -= 1
        if i < 0:
            i = 0
            uv = "0" + u
            self.editor_fields["value"] = uv
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i -= 1
        self.editor_fields["index"] = i
        self.render = True

    def ed_change_unit(self, direction):
        # direction to be 1 (next) or 0 (previous)
        variable = self.editor_fields["function"]
        variable_unit = self.editor_fields["unit"]
        variable_value = self.editor_fields["value"]
        current_unit_index = self.occ.sensors.parameters[self.editor_fields["function"]]["units_allowed"].index(variable_unit)
        self.log.debug("variable: {} units_allowed: {}".format(variable, self.occ.sensors.parameters[self.editor_fields["function"]]["units_allowed"]), extra=self.extra)
        if direction == 1:
            try:
                next_unit = self.occ.sensors.parameters[self.editor_fields["function"]]["units_allowed"][current_unit_index + 1]
            except IndexError:
                next_unit = self.occ.sensors.parameters[self.editor_fields["function"]]["units_allowed"][0]
        else:
            try:
                next_unit = self.occ.sensors.parameters[self.editor_fields["function"]]["units_allowed"][current_unit_index - 1]
            except IndexError:
                next_unit = self.occ.sensors.parameters[self.editor_fields["function"]]["units_allowed"][-1]
        self.editor_fields["unit"] = next_unit
        self.editor_fields["value"] = variable_value

    def ed_next_unit(self):
        self.ed_change_unit(1)
        self.render = True

    def ed_prev_unit(self):
        self.ed_change_unit(0)
        self.render = True

    def accept_edit(self):
        self.log.debug("accept_edit started", extra=self.extra)
        parameter = self.editor_fields["function"]
        parameter_unit = self.editor_fields["unit"]
        parameter_value = self.editor_fields["value"]
        self.log.debug("parameter: {}, parameter_unit: {}, parameter_value: {}".format(parameter, parameter_unit, parameter_value), extra=self.extra)
        if self.editor_fields["editor"] == "editor_units":
            self.occ.sensors.parameters[parameter]["unit"] = parameter_unit
        if self.editor_fields["editor"] == "editor_numbers":
            unit_raw = self.occ.sensors.parameters[parameter]["raw_unit"]
            value = self.uc.convert(float(parameter_value), parameter_unit, unit_raw)
            self.occ.sensors.parameters[parameter]["value"] = format(value)
        if self.editor_fields["editor"] == "editor_string":
            self.occ.sensors.parameters[parameter]["value"] = parameter_value
#        if self.self.editor_fields["ediotr"] == "ble_selector":
#            (name, addr, dev_type) = parameter_value
#            self.occ.sensors.set_ble_device(name, addr, dev_type)
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

    def write_config(self):
        self.occ.config.write_config()

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

    def log_level(self):
        log_level = self.log.getEffectiveLevel()
        log_level += 10
        if log_level > 50:
            log_level = 10
        log_level_name = logging.getLevelName(log_level)
        self.log.debug("Changing log level to: {}".format(log_level_name), extra=self.extra)
        self.occ.switch_log_level(log_level_name)
        self.occ.sensors.parameters["log_level"]["value"] = log_level_name

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
