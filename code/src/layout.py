#!/usr/bin/python3
## @package layout
#   Module responsible for loading and rendering layouts. Needs heavy cleaning...

import cairo
import cairo_helper
import datetime
import logging
import num
import pyplum
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
    extra = {'module_name': __qualname__}

    ## @var DISPLAY_REFRESH
    # Time between display refresh events. This is not display fps!
    DISPLAY_REFRESH = 0.5

    def __init__(self):
        super().__init__()
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')
        ## @var font_initialised
        #  Indicates if cairo font has been initialised.
        self.font_initialised = False
        ## @var s
        #  Sensors instance
        self.pm = pyplum.pyplum()
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
        ## @var uc
        #  Handle of unit_converter. Helper for converting units.
        self.uc = unit_converter.unit_converter()
        ## @var editor_fields
        #  Dict with data for editor pages.
        self.editor_fields = None
        ## @var pages
        #  Dict with parsed pages from layout file.
        self.pages = {}
        ## @var button_rectangles
        #  Dict with buttons. Parsed for layout file
        self.button_rectangles = {}
        ## @var images
        #  Dict with images loaded with png_to_cairo_surface. Currently only pngs are supported.
        self.images = {}
        self.load_layout(self.layout_file)
        ## @var  schedule_display_refresh
        #  Control variable of the display refresh event. Set to True to stop calling generate_refresh_event
        self.schedule_display_refresh = True
        self.start()
        #FIXME timer and layout module are unstoppable ;-) to be fixed

    def generate_refresh_event(self):
        if self.pm.event_queue is not None:
            self.pm.event_queue.put(('refresh',))

    def run(self):
        self.timer = threading.Timer(self.DISPLAY_REFRESH, self.generate_refresh_event)
        self.timer.start()
        while self.pm.event_queue is None:
            time.sleep(0.5)
        self.running = True
        while self.running:
            try:
                event = self.pm.event_queue.get(block=True, timeout=1)
                ev_type = event[0]
                if ev_type == 'touch':
                    position = event[1]
                    click = event[2]
                    self.check_click(position, click)
                if ev_type == 'show_main_page':
                    self.use_main_page()
                if ev_type == 'reload_layout':
                    self.reload_layout()
                if ev_type == 'next_page':
                    self.next_page()
                if ev_type == 'prev_page':
                    self.prev_page()
                if ev_type == 'refresh':
                    self.refresh_display()
                    if self.schedule_display_refresh:
                        self.timer = threading.Timer(self.DISPLAY_REFRESH, self.generate_refresh_event)
                        self.timer.start()
            except queue.Empty:
                pass
            except AttributeError:
                #queue doesn't exist
                pass
            except IndexError:
                self.log.crirtical("Invalid event: {}".format(event), extra=self.extra)

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
        self.pages = {}
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
            self.pages[page_id] = page
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
            self.current_page = self.pages[page_id]
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

        self.parse_font()
        self.parse_text_colour()

        self.button_rectangles = {}
        if self.current_page['fields'] is not None:
            for field in self.current_page['fields']:
                self.parse_parameter(field)

    def parse_font(self):
        self.font = None
        try:
            self.font = self.current_page['font']
        except KeyError:
            self.log.critical("Page font not found on page {}. font field is mandatory.".format(self.current_page), extra=self.extra)
        if self.font == '':
            self.log.critical("Page font found, but it's empry string. font field is mandatory.".format(self.current_page), extra=self.extra)
        try:
            self.page_font_size = self.current_page['font_size']
        except KeyError:
            self.log.critical("Page font size not found on page {}. font_size field is mandatory. Defaulting to 18".format(self.current_page), extra=self.extra)
            self.page_font_size = 18

    def parse_text_colour(self):
        self.text_colour_rgb = self.current_page['text_colour']
        text_colour_rgb = self.text_colour_rgb
        if text_colour_rgb[0] == '#':
            text_colour_rgb = text_colour_rgb[1:]
        r, g, b = text_colour_rgb[:2], text_colour_rgb[2:4], text_colour_rgb[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        self.text_colour = (r, g, b)

    def parse_parameter(self, field):
        try:
            name = field['parameter']
        except KeyError:
            self.log.critical("Parameter {} on page {}. Parameter field is mandatory.".format(name, self.current_page), extra=self.extra)
            name = None
        try:
            show = field['show']
        except KeyError:
            show = ''
        meta_name = name + "_" + show
        meta_name = meta_name.strip('_')
        try:
            b = field['button']
            try:
                rect = (int(b['x0']),
                        int(b['y0']),
                        int(b['w']),
                        int(b['h']))
            except KeyError:
                self.log.critical("Button field present, but invalid x0, y0, w or b detected at parameter {} on page {}.".format(name, self.current_page), extra=self.extra)
                self.log.critical("Button for {} won't work.".format(name), extra=self.extra)
            self.button_rectangles[meta_name] = (name, rect)
        except KeyError:
            pass
        try:
            image_file = field['file']
            self.images[image_file] = self.load_image(image_file)
        except KeyError:
            image_file = None

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
                        value = num.sanitise(value)
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
                    value = num.sanitise(value)
                except KeyError:
                    value = None
            elif show == "avg":
                try:
                    v = self.pm.parameters[parameter]["value_avg"]
                    ru = self.pm.parameters[parameter]["raw_unit"]
                    u = self.pm.parameters[parameter]["unit"]
                    value = self.uc.convert(v, ru, u)
                    value = num.sanitise(value)
                except KeyError:
                    value = None
            elif show == "max":
                try:
                    v = self.pm.parameters[parameter]["value_max"]
                    ru = self.pm.parameters[parameter]["raw_unit"]
                    u = self.pm.parameters[parameter]["unit"]
                    value = self.uc.convert(v, ru, u)
                    value = num.sanitise(value)
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
                if image_path not in self.images:
                    self.images[image_path] = self.load_image(image_path)
                image = self.images[image_path]
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
            if string_format != "zoomed_digit":
                self.text_to_surface(uv, position_x + x_shift, position_y + y_shift, self.text_colour)
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
                self.text_to_surface(rv1, rv1_x, position_y + y_shift, self.text_colour)
                self.text_to_surface(rv3, rv3_x, position_y + y_shift, self.text_colour)

    def render_all_buttons(self):
        # LAYOUT DEBUG FUNCION
        for parameter, r in self.button_rectangles.items():
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
        for parameter, r in self.button_rectangles.items():
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
        plugin = None
        method = None
        parameter_for_reset = None
        if click == 'SHORT':
            self.render_pressed_button(position)
            for parameter, r in self.button_rectangles.items():
                if self.point_in_rect(position, r[1]):
                    self.log.debug("CLICK on {} {}".format(parameter, r), extra=self.extra)
                    for f in self.current_page['fields']:
                        if f['parameter'] == parameter:
                            try:
                                if f['run']:
                                    plugin, method = f['run'].split(',')
                                    plugin = plugin.strip()
                                    method = method.strip()
                                    method_to_call = getattr(self.pm.plugins[plugin], method)
                                    method_to_call()
                            except KeyError:
                                pass
            self.pm.render['refresh'] = True
        elif click == 'LONG':
            self.render_pressed_button(position)
            for parameter, r in self.button_rectangles.items():
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
                                    reset_list.append(show)
                                    parameter_for_reset = f["parameter"]
                                    break
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
                                    self.editor_fields["parameter"] = r[0]
                                    break
                            except KeyError:
                                    editable = False
                            if not(resettable and editable):
                                self.log.debug("LONG CLICK on non-clickable {}".format(r[0]), extra=self.extra)
        elif click == 'R_TO_L':  # Swipe RIGHT to LEFT
            self.next_page()
        elif click == 'L_TO_R':  # Swipe LEFT to RIGHT
            self.prev_page()
        elif click == 'B_TO_T':  # Swipe BOTTOM to TOP
            self.use_main_page()
        elif click == 'T_TO_B':  # Swipe TOP to BOTTOM
            self.use_page("settings_0")

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
            elif self.editor_fields["editor"] == 'editor_string' or \
                    self.editor_fields["editor"] == 'editor_units':
                self.editor_fields["value"] = self.pm.parameters[p]["value"]
            elif self.editor_fields["editor"] == 'editor_list':
                v = self.pm.parameters[p]["value"]
                index = self.pm.parameters[p]["value_list"].index(v)
                self.editor_fields['index'] = index
                value_list = self.pm.parameters[p]["value_list"]
                self.slice_list_elements(value_list, index)
            else:
                self.log.critical("Unknown editor {} called for parameter {}, ignoring".format(self.editor_fields["editor"], self.editor_fields["parameter"]), extra=self.extra)
                return
            #editor call
            #FIXME not nice, a check if editor plugin is loaded?
            self.pm.plugins['editor'].set_up(self.editor_fields)
            self.use_page(self.editor_fields["editor"])
        elif resettable:
            self.log.debug("Resetting {} with list: {}".format(parameter_for_reset, reset_list), extra=self.extra)
            self.pm.parameter_reset(parameter_for_reset, reset_list)
            self.parameter_for_reset = None

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
        for p, page in self.pages.items():
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

    def reload_layout(self, name):
        self.load_layout(self.layout_file)

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
