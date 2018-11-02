#!/usr/bin/python3
## @package layout
#   Module responsible for loading and rendering layouts. Needs heavy cleaning...

import cairo
import cairo_helper
import datetime
import logging
import numbers
import os
import plugin_manager
import queue
import sys
import threading
import time
import unit_converter
import yaml


## Class for handling layouts
class layout(threading.Thread):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'layout'}

    def __init__(self):
        super().__init__()
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')
        self.font_initialised = False
        ## @var s
        #  Sensors instance
        self.pm = plugin_manager.plugin_manager()
        ## @var layout_file
        #  Location of layout file
        self.layout_file = self.pm.parameters['layout_file']['value']
        ## @var fonts_dir
        #  Location of fonts directory
        self.fonts_dir = self.pm.parameters['fonts_dir']['value']
        ## @var width
        #  Window/screen width
        ## @var height
        #  Window/screen height
        self.width, self.height = self.pm.parameters['display_size']["value"]
        ## @var cr
        #  Handle to cairo context
        self.ctx = self.pm.render['ctx']
        self.uc = unit_converter.unit_converter()
        self.editor_fields = None
        self.page_list = {}
        self.page_index = {}
        self.parameter_rect_list = {}
        self.current_image_list = {}
        self.load_layout(self.layout_file)
        self.stop_timer = False
        self.start()
        #FIXME timer and layout module are unstoppable ;-) to be fixed

    def generate_refresh_event(self):
        if self.pm.event_queue is not None:
            self.pm.event_queue.put(('refresh', None, None))

    def run(self):
        self.timer = threading.Timer(0.5, self.generate_refresh_event)
        self.timer.start()
        while self.pm.event_queue is None:
            time.sleep(0.5)
        self.running = True
        while self.running:
            try:
                ev_type, position, click = self.pm.event_queue.get(block=True, timeout=1)
                if ev_type == 'touch':
                    self.check_click(position, click)
                if ev_type == 'refresh':
                    self.refresh_display()
                    if not self.stop_timer:
                        self.timer = threading.Timer(0.5, self.generate_refresh_event)
                        self.timer.start()
            except queue.Empty:
                pass
            except AttributeError:
                #queue doesn't exist
                pass

    def refresh_display(self):
        # Check if cairo context has changed
        if self.ctx != self.pm.render['ctx']:
            self.ctx = self.pm.render['ctx']
        if not self.font_initialised:
            try:
                # Only one font is allowed for now due to cairo_helper workaround
                self.log.debug("Calling cairo_helper for {}".format(self.fonts_dir + self.font), extra=self.extra)
                font_face = cairo_helper.create_cairo_font_face_for_file(self.fonts_dir + self.font, 0)
                self.ctx.set_font_face(font_face)
                self.font_extents = self.ctx.font_extents()
                self.font_initialised = True
            except AttributeError:
                pass
        if not self.pm.render['hold'] and self.ctx is not None:
            self.pm.render['hold'] = True
            self.render_page()
            self.pm.render['hold'] = False

    def load_layout(self, layout_file):
        if self.layout_file is None:
            return
        self.max_page_id = 0
        self.max_settings_id = 0
        self.page_list = {}
        self.page_index = {}
        try:
            with open(layout_file) as f:
                self.log.debug("Loading layout {}".format(layout_file), extra=self.extra)
                self.layout_tree = yaml.safe_load(f)
                f.close()
            self.layout_file = layout_file
        except FileNotFoundError:
            self.log.critical("Loading layout {} failed, falling back to default.yaml".format(layout_file), extra=self.extra)
            sys_info = "Error details: {}".format(sys.exc_info()[0])
            self.log.error(sys_info, extra=self.extra)
            # Fallback to default layout
            layout_file = "layouts/default.yaml"
            try:
                with open(layout_file) as f:
                    self.log.debug("Loading layout {}".format(layout_file), extra=self.extra)
                    self.layout_tree = yaml.safe_load(f)
                    f.close()
            except FileNotFoundError:
                self.log.critical("Loading default layout {} failed, Quitting...".format(layout_file), extra=self.extra)
                raise

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
        self.pm.render['refresh'] = True
        try:
            self.current_page = self.page_list[page_id]
        except KeyError:
            self.log.critical("Cannot load page {}, loading start page".format(page_id), extra=self.extra)
            self.use_page()
        try:
            self.background_image = self.load_image(self.current_page['background'])
        except cairo.Error:
            self.log.critical("{}: Cannot load background image!".format(__name__,), extra=self.extra)
            self.log.critical("layout_file = {}".format(self.layout_file), extra=self.extra)
            self.log.critical("background path = {}".format(self.current_page['background']), extra=self.extra)
            self.log.critical("page_id = {}".format(page_id), extra=self.extra)
            raise
        try:
            self.buttons_image = self.load_image(self.current_page['buttons'])
        except cairo.Error:
            self.log.critical("{}: Cannot load buttons image!".format(__name__,), extra=self.extra)
            self.log.critical("layout_file = {}".format(self.layout_file), extra=self.extra)
            self.log.critical("buttons path = {}".format(self.current_page['buttons']), extra=self.extra)
            self.log.critical("page_id = {}".format(page_id), extra=self.extra)
            raise
        self.font = self.current_page['font']
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
        self.parameter_rect_list = {}
        if self.current_page['fields'] is not None:
            for field in self.current_page['fields']:
                try:
                    b = field['button']
                except KeyError:
                    b = None
                if (b is not None):
                    rect = (int(b.get('x0')), int(b.get('y0')), int(b.get('w')), int(b.get('h')))
                    name = field.get('parameter')
                    try:
                        meta_name = name + "_" + field['show']
                    except KeyError:
                        meta_name = name
                    self.parameter_rect_list[meta_name] = (name, rect)
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
        try:
            self.ctx.set_source_surface(self.background_image, 0, 0)
        except TypeError as e:
            self.ctx.set_source_rgb(0.0, 0.0, 0.0)
            if str(e) == 'must be cairo.Surface, not None':
                # Allow for empty background
                pass
            else:
                raise
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()

    def render_page(self):
        self.render_background()
        # LAYOUT DEBUG FUNCION
        #self.render_all_buttons()
        if self.current_page['fields'] is not None:
            self.render_layout()
        self.pm.render['refresh'] = True

    def make_image_key(self, image_path, value):
        suffix = "_" + format(value)
        extension = image_path[-4:]
        name = image_path[:-4]
        return (name + suffix + extension)

    def render_layout(self):
        for field in self.current_page['fields']:
            #print("{}".format(field))
            parameter = field['parameter']
            #print("{}".format(parameter))
            try:
                position_x = field['x']
            except KeyError:
                position_x = 0
            try:
                position_y = field['y']
            except KeyError:
                position_y = 0
            # Show value of parameter by default
            try:
                show = field["show"]
            except KeyError:
                show = "value"
            if show == "value":
                if self.current_page["type"] == "editor":
                    try:
                        value = self.editor_fields[parameter]
                    except (KeyError, TypeError):
                        value = None
                else:
                    try:
                        v = self.pm.parameters[parameter]["value"]
                        ru = self.pm.parameters[parameter]["raw_unit"]
                        u = self.pm.parameters[parameter]["unit"]
                        value = self.uc.convert(v, ru, u)
                        value = numbers.sanitise(value)
                    except (KeyError, TypeError):
                        value = None
            elif show == "tenths":
                try:
                    v = self.pm.parameters[parameter]["value"]
                    ru = self.pm.parameters[parameter]["raw_unit"]
                    u = self.pm.parameters[parameter]["unit"]
                    value = self.uc.convert(v, ru, u)
                    tenths_string = "{}".format(value - int(value))
                    value = format(tenths_string)[2:3]
                except (KeyError, TypeError, ValueError):
                    value = None
            elif show == "unit":
                try:
                    value = self.pm.parameters[parameter]["unit"]
                except KeyError:
                    value = None
            elif show == "min":
                try:
                    v = self.pm.parameters[parameter]["value_min"]
                    ru = self.pm.parameters[parameter]["raw_unit"]
                    u = self.pm.parameters[parameter]["unit"]
                    value = self.uc.convert(v, ru, u)
                    value = numbers.sanitise(value)
                except KeyError:
                    value = None
            elif show == "avg":
                try:
                    v = self.pm.parameters[parameter]["value_avg"]
                    ru = self.pm.parameters[parameter]["raw_unit"]
                    u = self.pm.parameters[parameter]["unit"]
                    value = self.uc.convert(v, ru, u)
                    value = numbers.sanitise(value)
                except KeyError:
                    value = None
            elif show == "max":
                try:
                    v = self.pm.parameters[parameter]["value_max"]
                    ru = self.pm.parameters[parameter]["raw_unit"]
                    u = self.pm.parameters[parameter]["unit"]
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
                align = field["align"]
            except KeyError:
                align = "center"
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
                    except (TypeError, ValueError):
                        # ValueError: invalid literal for int() with base 10: ''
                        pass
                elif string_format == "date":
                    try:
                        value = datetime.datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
            except (KeyError, ValueError):
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
                #print("{} variable {}".format(parameter, variable))
                value = self.pm.parameters[variable["name"]]["value"]
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
            self.ctx.set_font_size(fs)
            te = self.ctx.text_extents(uv)
            if align == 'center':
                x_shift = -1.0 * te.width / 2.0
            elif align == 'right':
                x_shift = -1.0 * te.width
            elif align == 'left':
                x_shift = 0.0
            else:
                x_shift = 0.0
            # 18 is font size for which font_extents has height. So far no scaled_font_extents function
            y_shift = 0.5 * self.font_extents[2] * fs / 18
            #FIXME add rgb_colour to layout files
            rgb_colour = (1.0, 1.0, 1.0)
            if string_format != "zoomed_digit":
                self.text_to_surface(uv, position_x + x_shift, position_y + y_shift, rgb_colour)
            else:
                SCALE = 1.4
                uv = self.editor_fields["value"]
                i = self.editor_fields["index"]
                #Head
                rv1 = uv[:i]
                te1 = self.ctx.text_extents(rv1)
                #Tail
                rv3 = uv[i + 1:]
                #Currently edited digit
                rv2 = uv[i]
                self.ctx.set_font_size(SCALE * fs)
                te2 = self.ctx.text_extents(rv2)

                rv1_x = position_x - te.width / 2.0
                rv2_x = position_x - te.width / 2.0 + te1.x_advance
                rv3_x = position_x - te.width / 2.0 + te1.x_advance + te2.x_advance

                self.text_to_surface(rv2, rv2_x, position_y + SCALE * y_shift, (1.0, 0.0, 0.0))
                self.ctx.set_font_size(fs)
                self.text_to_surface(rv1, rv1_x, position_y + y_shift, rgb_colour)
                self.text_to_surface(rv3, rv3_x, position_y + y_shift, rgb_colour)

    def render_all_buttons(self):
        # LAYOUT DEBUG FUNCION
        for parameter, r in self.parameter_rect_list.items():
            fr = r[1]
            self.ctx.set_source_rgb(0.0, 1.0, 0.0)
            self.ctx.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.ctx.fill()
            self.ctx.set_line_width(2.0)
            self.ctx.set_source_rgb(1.0, 0.0, 0.0)
            self.ctx.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.ctx.stroke()

    def render_pressed_button(self, pressed_pos):
        if self.ctx is None:
            return
        self.log.debug("render_pressed_button started", extra=self.extra)
        for parameter, r in self.parameter_rect_list.items():
            if self.point_in_rect(pressed_pos, r[1]):
                fr = r[1]
                self.ctx.set_source_surface(self.buttons_image, 0, 0)
                self.ctx.rectangle(fr[0], fr[1], fr[2], fr[3])
                self.ctx.fill()
        self.pm.render['refresh'] = True
        self.log.debug("render_pressed_button finished", extra=self.extra)

    def check_click(self, position, click):
        resettable = False
        editable = False
        parameter_for_reset = None
        if click == 'SHORT':
            self.render_pressed_button(position)
            clicked_parameter = None
            for parameter, r in self.parameter_rect_list.items():
                if self.point_in_rect(position, r[1]):
                    self.log.debug("CLICK on {} {}".format(parameter, r), extra=self.extra)
                    clicked_parameter = parameter
            if clicked_parameter:
                self.log.debug("run_function for {}".format(clicked_parameter), extra=self.extra)
                self.run_function(clicked_parameter)
        elif click == 'LONG':
            self.render_pressed_button(position)
            for parameter, r in self.parameter_rect_list.items():
                if self.point_in_rect(position, r[1]):
                    for f in self.current_page['fields']:
                        try:
                            show = f["show"]
                            _f = f["parameter"] + "_" + show
                        except KeyError:
                            show = ''
                            _f = f["parameter"]
                        if _f == parameter:
                            try:
                                if f['resettable']:
                                    resettable = True
                                try:
                                    if f['reset']:
                                        reset_list = f['reset'].split(',')
                                except KeyError:
                                        reset_list = []
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
                                        self.log.critical("Function {} marked as editable, but no editor field found".format(parameter), extra=self.extra)
                                    try:
                                        self.editor_fields["editor_title"] = f["editor_title"]
                                    except KeyError:
                                        self.editor_fields["editor_title"] = None
                                        self.log.critical("Function {} marked as editable, but no editor_title field found".format(parameter), extra=self.extra)
                                    try:
                                        self.editor_fields["format"] = f["format"]
                                    except KeyError:
                                        self.editor_fields["format"] = "%.0f"
                            except KeyError:
                                    editable = False
                            if resettable:
                                reset_list.append(show)
                                parameter_for_reset = f["parameter"]
                                break
                            elif editable:
                                self.editor_fields["parameter"] = r[0]
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

        if editable:
            self.log.debug("Opening editor {} for {}".format(self.editor_fields["editor"], self.editor_fields["parameter"]), extra=self.extra)
            p = self.editor_fields["parameter"]
            self.editor_fields["unit"] = self.pm.parameters[p]["unit"]
            self.editor_fields["index"] = 0
            if self.editor_fields["editor"] == 'editor_numbers':
                self.editor_fields["raw_value"] = self.pm.parameters[p]["value"]
                value = self.uc.convert(self.pm.parameters[p]["value"],
                                        self.pm.parameters[p]["raw_unit"],
                                        self.pm.parameters[p]["unit"])
                try:
                    self.editor_fields["value"] = self.editor_fields["format"] % value
                except TypeError:
                    self.editor_fields["value"] = value
            elif (self.editor_fields["editor"] == 'editor_string' or
                  self.editor_fields["editor"] == 'editor_units'):
                self.editor_fields["value"] = self.pm.parameters[p]["value"]
                pass
            else:
                self.log.critical("Unknown editor {} called for parameter {}, ignoring".format(self.editor_fields["editor"], self.editor_fields["parameter"]), extra=self.extra)
                return
            self.use_page(self.editor_fields["editor"])
        elif resettable:
            self.log.debug("Resetting {} with list: {}".format(parameter_for_reset, reset_list), extra=self.extra)
            self.pm.parameter_reset(parameter_for_reset, reset_list)
            self.parameter_for_reset = None

    def run_function(self, parameter):
        functions = {"page_0": self.load_page_0,
                     "settings": self.load_settings_page,
                     "log_level": self.log_level,
                     "ed_accept": self.ed_accept,
                     "ed_cancel": self.ed_cancel,
                     "ed_decrease": self.ed_decrease,
                     "ed_increase": self.ed_increase,
                     "ed_next": self.ed_next,
                     "ed_next_item": self.ed_next_item,
                     "ed_next_unit": self.ed_next_unit,
                     "ed_prev": self.ed_prev,
                     "ed_prev_item": self.ed_prev_item,
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
            if functions[parameter] is not None:
                self.log.debug("Calling function for parameter {}".format(parameter), extra=self.extra)
        except KeyError:
            self.log.debug("CLICK on non-clickable {}".format(parameter), extra=self.extra)
            return
        functions[parameter]()

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
        if str.isdigit(ui):
            if ui == "0":
                ui = "9"
            else:
                ui = format(int(ui) - 1)
        elif str.isupper(ui):
            ui = format(chr(ord(ui) - 1))
            if not str.isalpha(ui):
                ui = "Z"
        else:
            # Not a letter or digit, ignore
            pass
        un = u[:i] + ui + u[i + 1:]
        self.editor_fields["value"] = un
        self.pm.render['refresh'] = True

    def ed_increase(self):
        u = self.editor_fields["value"]
        i = self.editor_fields["index"]
        ui = u[i]
        if str.isdigit(ui):
            if ui == "9":
                ui = "0"
            else:
                ui = format(int(ui) + 1)
        elif str.isupper(ui):
            ui = format(chr(ord(ui) + 1))
            if not str.isalpha(ui):
                ui = "A"
        else:
            # Not a capital letter or digit, ignore
            pass
        un = u[:i] + ui + u[i + 1:]
        self.editor_fields["value"] = un
        self.pm.render['refresh'] = True

    def ed_next(self):
        u = self.editor_fields["value"]
        i = self.editor_fields["index"]
        strip_zero = True
        try:
            # Preserve leading zero if the value is less than 1.0
            if float(u) < 1.0:
                strip_zero = False
        except (TypeError, ValueError):
            pass
        if u[0] == '0' and strip_zero:
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
        self.pm.render['refresh'] = True

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
        self.pm.render['refresh'] = True

    def slice_list_elements(self, a_list, index):
        list_len = len(a_list)
        circular_list_slice = (a_list * 3)[index + list_len - 1:index + list_len + 2]
        self.editor_fields["previous_list_element"] = circular_list_slice[0]
        self.editor_fields["value"] = circular_list_slice[1]
        self.editor_fields["next_list_element"] = circular_list_slice[2]

    def ed_next_item(self):
        index = self.editor_fields["index"]
        index += 1
        p = self.editor_fields["parameter"]
        value_list = self.pm.parameters[p]["value_list"]
        self.slice_list_elements(value_list, index)
        if index > len(self.pm.parameters[p]["value_list"]) - 1:
            self.editor_fields["index"] = 0
        else:
            self.editor_fields["index"] = index

    def ed_prev_item(self):
        index = self.editor_fields["index"]
        index -= 1
        p = self.editor_fields["parameter"]
        value_list = self.pm.parameters[p]["value_list"]
        self.slice_list_elements(value_list, index)
        if index < 0:
            self.editor_fields["index"] = len(self.pm.parameters[p]["value_list"]) - 1
        else:
            self.editor_fields["index"] = index

    def ed_change_unit(self, direction):
        # direction to be 1 (next) or 0 (previous)
        variable = self.editor_fields["parameter"]
        variable_unit = self.editor_fields["unit"]
        variable_value = self.editor_fields["value"]
        current_unit_index = self.pm.parameters[self.editor_fields["parameter"]]["units_allowed"].index(variable_unit)
        self.log.debug("variable: {} units_allowed: {}".format(variable, self.pm.parameters[self.editor_fields["parameter"]]["units_allowed"]), extra=self.extra)
        if direction == 1:
            try:
                next_unit = self.pm.parameters[self.editor_fields["parameter"]]["units_allowed"][current_unit_index + 1]
            except IndexError:
                next_unit = self.pm.parameters[self.editor_fields["parameter"]]["units_allowed"][0]
        else:
            try:
                next_unit = self.pm.parameters[self.editor_fields["parameter"]]["units_allowed"][current_unit_index - 1]
            except IndexError:
                next_unit = self.pm.parameters[self.editor_fields["parameter"]]["units_allowed"][-1]
        self.editor_fields["unit"] = next_unit
        self.editor_fields["value"] = variable_value

    def ed_next_unit(self):
        self.ed_change_unit(1)
        self.pm.render['refresh'] = True

    def ed_prev_unit(self):
        self.ed_change_unit(0)
        self.pm.render['refresh'] = True

    def accept_edit(self):
        self.log.debug("accept_edit started", extra=self.extra)
        parameter = self.editor_fields["parameter"]
        parameter_unit = self.editor_fields["unit"]
        parameter_value = self.editor_fields["value"]
        self.log.debug("parameter: {}, parameter_unit: {}, parameter_value: {}".format(parameter, parameter_unit, parameter_value), extra=self.extra)
        if self.editor_fields["editor"] == "editor_units":
            self.pm.parameters[parameter]["unit"] = parameter_unit
        if self.editor_fields["editor"] == "editor_numbers":
            unit_raw = self.pm.parameters[parameter]["raw_unit"]
            value = self.uc.convert(float(parameter_value), parameter_unit, unit_raw)
            self.pm.parameters[parameter]["value"] = float(value)
        if self.editor_fields["editor"] == "editor_string":
            self.pm.parameters[parameter]["value"] = parameter_value
#        if self.self.editor_fields["ediotr"] == "ble_selector":
#            (name, addr, dev_type) = parameter_value
#            self.pm.set_ble_device(name, addr, dev_type)
        self.pm.parameters[parameter]["time_stamp"] = time.time()
        self.pm.render['refresh'] = True
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
        quit()

    #FIXME That will be gone when functions are no longer hard coded
    def write_config(self):
        self.pm.parameters['write_config_requested']['value'] = True

    def reboot(self):
        self.quit()
        time.sleep(2)
        os.system("sudor reboot")

    def halt(self):
        self.quit()
        time.sleep(2)
        os.system("sudo halt")

    def log_level(self):
        log_level = self.log.getEffectiveLevel()
        log_level += 10
        if log_level > 50:
            log_level = 10
        log_level_name = logging.getLevelName(log_level)
        self.log.debug("Changing log level to: {}".format(log_level_name), extra=self.extra)
        try:
            self.pm.parameters['log_level']['value'] = log_level_name
        except KeyError:
            pass

    def png_to_cairo_surface(self, file_path):
        png_surface = cairo.ImageSurface.create_from_png(file_path)
        return png_surface

    def image_to_surface(self, surface, x=0, y=0, w=None, h=None):
        if w is None:
            w = self.width
        if h is None:
            h = self.height
        self.ctx.set_source_surface(surface, x, y)
        self.ctx.rectangle(x, y, w, h)
        self.ctx.fill()

    def text_to_surface(self, text, x, y, c):
        self.ctx.set_source_rgb(c[0], c[1], c[2])
        self.ctx.move_to(x, y)
        self.ctx.show_text(text)

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
