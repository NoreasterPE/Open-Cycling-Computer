#!/usr/bin/python3
## @package layout
#   Module responsible for loading and rendering layouts. Needs heavy cleaning...

import cairo
import cairo_helper
import datetime
import logging
import math
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
    ## @var DEFAULT_OVERLAY_TIME
    # Default time of overlay visibility
    DEFAULT_OVERLAY_TIME = 3.0

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
        self.width = self.pm.parameters['display_size']["value"][0]
        ## @var height
        #  Window/screen height
        self.height = self.pm.parameters['display_size']["value"][1]
        ## @var ctx
        #  Handle to cairo context
        self.ctx = self.pm.render['ctx']
        ## @var octx
        #  Handle to cairo context overlay
        self.octx = self.pm.overlay['ctx']
        self.overlay_time_start = num.NAN
        self.overlay_show_time = 0
        ## @var overlay_queue
        #  List of overlays waiting to be shown
        self.overlay_queue = list()
        ## @var uc
        #  Handle of unit_converter. Helper for converting units.
        self.uc = unit_converter.unit_converter()
        ## @var editor_fields
        #  Dict with data for editor pages.
        self.editor_fields = {}
        ## @var pages
        #  Dict with parsed pages from layout file.
        self.pages = {}
        ## @var button_rectangles
        #  Dict with buttons. Parsed for layout file
        self.button_rectangles = {}
        ## @var images
        #  Dict with images loaded with png_to_cairo_surface. Currently only pngs are supported.
        self.images = {}
        self.load_layout()
        self.use_page()
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
            if time.time() - self.overlay_time_start > self.overlay_show_time:
                self.hide_overlay()
            if len(self.overlay_queue) > 0:
                self.show_overlay()
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
                    self.load_layout()
                    self.use_page()
                if ev_type == 'next_page':
                    self.next_page()
                if ev_type == 'prev_page':
                    self.prev_page()
                if ev_type == 'show_overlay':
                    image_file = event[1]
                    try:
                        show_time = event[2]
                    except IndexError:
                        show_time = self.DEFAULT_OVERLAY_TIME
                    self.overlay_queue.append((image_file, show_time))
                if ev_type == 'refresh':
                    self.refresh_display()
                    if self.schedule_display_refresh:
                        self.timer = threading.Timer(self.DISPLAY_REFRESH, self.generate_refresh_event)
                        self.timer.start()
                if ev_type == 'quit':
                    self.schedule_display_refresh = False
                    self.running = False
            except queue.Empty:
                pass
            except AttributeError:
                #queue doesn't exist
                pass
            except IndexError:
                self.log.critical("Invalid event: {}".format(event), extra=self.extra)

    def refresh_display(self):
        # Check if cairo context has changed
        if self.ctx != self.pm.render['ctx']:
            self.ctx = self.pm.render['ctx']
        if not self.font_initialised and self.ctx is not None:
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

    def load_layout(self):
        if self.layout_file is None:
            self.log.critical("Layput file is None, refusing to load", extra=self.extra)
            return
        self.load_layout_tree()
        self.pages = {}
        for page in self.layout_tree['pages']:
            try:
                page_id = page['id']
            except KeyError:
                self.log.critical("Page in layout {} has no id field defined. Layout might not work.".format(self.layout_file), extra=self.extra)
            # page 'type' field is optional, add it if not defined
            if 'type' not in page:
                page['type'] = None
            self.pages[page_id] = page

    def load_layout_tree(self):
        try:
            with open(self.layout_file) as f:
                self.log.debug("Loading layout {}".format(self.layout_file), extra=self.extra)
                self.layout_tree = yaml.safe_load(f)
                f.close()
        except FileNotFoundError:
            self.log.critical("Loading layout {} failed, falling back to default.yaml".format(self.layout_file), extra=self.extra)
            sys_info = "Error details: {}".format(sys.exc_info()[0])
            self.log.error(sys_info, extra=self.extra)
            # FIXME Fallback to default layout
            self.layout_file = "layouts/default.yaml"
            try:
                with open(self.layout_file) as f:
                    self.log.debug("Loading layout {}".format(self.layout_file), extra=self.extra)
                    self.layout_tree = yaml.safe_load(f)
                    f.close()
            except FileNotFoundError:
                self.log.critical("Loading default layout {} failed, Quitting...".format(self.layout_file), extra=self.extra)
                raise

    def use_page(self, page_id="page_0"):
        self.log.debug("use_page {}".format(page_id), extra=self.extra)
        self.pm.render['refresh'] = True
        try:
            self.current_page = self.pages[page_id]
        except KeyError:
            self.log.critical("Cannot load page {}, loading start page".format(page_id), extra=self.extra)
            self.use_page()

        self.background_image = None
        if 'background_image' in self.current_page:
            self.background_image = self.load_image(self.current_page['background_image'])

        self.buttons_image = None
        if 'buttons_image' in self.current_page:
            self.buttons_image = self.load_image(self.current_page['buttons'])

        self.background_colour = None
        if 'background_colour' in self.current_page:
            self.parse_background_colour()

        self.font = None
        if 'font' in self.current_page:
            self.parse_font()

        self.text_colour = None
        if 'text_colour' in self.current_page:
            self.parse_text_colour()

        self.button_rectangles = {}
        if self.current_page['fields'] is not None:
            for field in self.current_page['fields']:
                self.parse_parameter(field)

    def parse_font(self):
        self.font = self.current_page['font']
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

    def parse_background_colour(self):
        self.background_colour_rgb = self.current_page['background_colour']
        background_colour_rgb = self.background_colour_rgb
        if background_colour_rgb[0] == '#':
            background_colour_rgb = background_colour_rgb[1:]
        r, g, b = background_colour_rgb[:2], background_colour_rgb[2:4], background_colour_rgb[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        self.background_colour = (r, g, b)

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
            # image is invalid
            self.log.warning("Cannot load image!", extra=self.extra)
            self.log.warning("layout_file = {}".format(self.layout_file), extra=self.extra)
            self.log.warning("image path path = {}".format(image_path), extra=self.extra)
            image = None
        return image

    def use_main_page(self):
        self.use_page()

    def render_background(self):
        if self.background_colour is not None:
            r = self.background_colour[0]
            g = self.background_colour[1]
            b = self.background_colour[2]
            self.ctx.set_source_rgb(r, g, b)
        if self.background_image is not None:
            self.ctx.set_source_surface(self.background_image, 0, 0)
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
            parameter = field['parameter']
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
        if self.ctx is None or self.buttons_image is None:
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
        plugin = None
        method = None
        if click == 'SHORT':
            self.render_pressed_button(position)
            # FIXME simplify, single loop has to be enough
            for parameter, r in self.button_rectangles.items():
                if self.point_in_rect(position, r[1]):
                    self.log.debug("CLICK on {} {}".format(parameter, r), extra=self.extra)
                    for f in self.current_page['fields']:
                        if f['parameter'] == parameter:
                            try:
                                if f['short_click']:
                                    plugin, method = f['short_click'].split(',')
                                    plugin = plugin.strip()
                                    method = method.strip()
                                    method_to_call = getattr(self.pm.plugins[plugin], method)
                                    method_to_call()
                            except KeyError:
                                pass
            self.pm.render['refresh'] = True
        elif click == 'LONG':
            self.render_pressed_button(position)
            # FIXME simplify, single loop has to be enough
            for parameter, r in self.button_rectangles.items():
                if self.point_in_rect(position, r[1]):
                    self.log.debug("LONG CLICK on {} {}".format(parameter, r), extra=self.extra)
                    for f in self.current_page['fields']:
                        try:
                            show = f["show"]
                            _f = f["parameter"] + "_" + show
                        except KeyError:
                            show = ''
                            _f = f["parameter"]
                        if _f == parameter:
                            self.parse_long_click(f, r[0])
        elif click == 'R_TO_L':  # Swipe RIGHT to LEFT
            self.next_page()
        elif click == 'L_TO_R':  # Swipe LEFT to RIGHT
            self.prev_page()
        elif click == 'B_TO_T':  # Swipe BOTTOM to TOP
            self.use_main_page()
        elif click == 'T_TO_B':  # Swipe TOP to BOTTOM
            self.use_page("settings_0")

    def parse_long_click(self, field, parameter):
        try:
            plugin, method = field['long_click'].split(',')
            plugin = plugin.strip()
            method = method.strip()
        except KeyError:
            plugin, method = None, None
            pass
        if plugin == 'internal' and method == 'reset':
            self.call_internal_reset(field)
        elif plugin == 'internal' and method == 'editor':
            self.call_internal_editor(field, parameter)
        self.log.debug("LONG CLICK on non-clickable {}".format(parameter), extra=self.extra)

    def call_internal_reset(self, field):
        try:
            show = field["show"]
        except KeyError:
            show = ''
        try:
            reset_list = field['reset']
        except KeyError:
            reset_list = []
        reset_list.append(show)
        self.log.debug("Resetting {} with list: {}".format(field["parameter"], reset_list), extra=self.extra)
        self.pm.parameter_reset(field["parameter"], reset_list)

    def call_internal_editor(self, field, parameter):
        print(field)
        print(parameter)
        self.editor_fields = {}
        try:
            editor = field['editor']
        except KeyError:
            self.editor_fields["editor"] = None
            self.log.error("Field {} defined as editable with long_click pointing to internal editor, but no editor field found".format(parameter), extra=self.extra)
        try:
            self.editor_fields["editor"] = editor['type']
        except KeyError:
            self.editor_fields["editor"] = None
            self.log.error("Field {} defined as editable, but no editor type found".format(parameter), extra=self.extra)
        try:
            self.editor_fields['editor_title'] = editor['title']
        except KeyError:
            self.editor_fields['editor_title'] = ''
            self.log.warning("Function {} marked as editable, but no editor_title field found".format(parameter), extra=self.extra)
        try:
            self.editor_fields["format"] = field['format']
        except KeyError:
            self.editor_fields["format"] = '%.0f'
            self.log.debug("No format found for editing parameter {}, using default format %.0f".format(parameter), extra=self.extra)
        if self.editor_fields["editor"] is not None:
            self.editor_fields["parameter"] = parameter
            self.open_editor()

    def open_editor(self):
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
            self.pm.plugins['editor'].set_up(self.editor_fields)
        elif self.editor_fields["editor"] == 'editor_string' or \
                self.editor_fields["editor"] == 'editor_unit':
            self.editor_fields["value"] = self.pm.parameters[p]["value"]
            self.pm.plugins['editor'].set_up(self.editor_fields)
        elif self.editor_fields["editor"] == 'editor_list':
            v = self.pm.parameters[p]["value"]
            index = self.pm.parameters[p]["value_list"].index(v)
            self.editor_fields['index'] = index
            value_list = self.pm.parameters[p]["value_list"]
            #editor call
            #FIXME not nice, a check if editor plugin is loaded?
            self.pm.plugins['editor'].set_up(self.editor_fields)
            self.pm.plugins['editor'].slice_list_elements(value_list, index)
        else:
            self.log.critical("Unknown editor {} called for parameter {}, ignoring".format(self.editor_fields["editor"], self.editor_fields["parameter"]), extra=self.extra)
            return
        self.use_page(self.editor_fields["editor"])

    def next_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.current_page['type'] == 'editor':
            try:
                self.use_page(self.current_page['right'])
            except KeyError:
                pass

    def prev_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.current_page['type'] == 'editor':
            try:
                self.use_page(self.current_page['left'])
            except KeyError:
                pass

    def png_to_cairo_surface(self, file_path):
        png_surface = cairo.ImageSurface.create_from_png(file_path)
        return png_surface

    #FIXME misleading names surface --> image, image_to_surface --> render_image?
    def image_to_surface(self, surface, x=0, y=0, w=None, h=None):
        if w is None:
            w = self.width
        if h is None:
            h = self.height
        self.ctx.set_source_surface(surface, x, y)
        self.ctx.rectangle(x, y, w, h)
        self.ctx.fill()

    def show_overlay(self):
        if len(self.overlay_queue) > 0 and math.isnan(self.overlay_time_start):
            self.overlay_time_start = time.time()
            overlay = self.overlay_queue.pop(0)
            image_path = overlay[0]
            self.overlay_show_time = overlay[1]
            if image_path is not None:
                if image_path not in self.images:
                    self.images[image_path] = self.load_image(image_path)
                image = self.images[image_path]
                if image is not None:
                    self.octx.set_source_rgba(0.0, 0.0, 0.0, 0.0)
                    self.octx.set_source_surface(image, 0, 0)
                    self.octx.paint_with_alpha(1.0)

    def hide_overlay(self):
        self.octx.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        self.octx.set_operator(cairo.OPERATOR_CLEAR)
        self.octx.paint_with_alpha(1.0)
        self.octx.set_operator(cairo.OPERATOR_SOURCE)
        self.overlay_time_start = num.NAN

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
