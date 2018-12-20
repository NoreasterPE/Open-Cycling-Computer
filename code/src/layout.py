#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Module responsible for rendering layouts. Needs heavy cleaning...

import cairo
import datetime
import logging
import math
import queue
import threading
import time

from helpers import num
import helpers
import layout_loader
import pyplum


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
        ## @var font_face_set
        #  Indicates if cairo font face has been set
        self.font_face_set = False
        ## @var pm
        #  PYthon PLUgin Manager instance
        self.pm = pyplum.pyplum()
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
        self.uc = helpers.unit_converter()
        ## @var editor_fields
        #  Dict with data for editor pages.
        self.editor_fields = {}
        ## @var page
        #  Current page provided by layout_loader
        self.page = None
        ## @var ll
        #  Layout loader instance
        self.ll = layout_loader.layout_loader()
        ## @var pages
        #  Copy of all pages loaded by layout_loader
        self.pages = self.ll.pages.copy()
        self.use_page()
        ## @var schedule_display_refresh
        #  Control variable of the display refresh event. Set to True to stop calling generate_refresh_event
        self.schedule_display_refresh = True
        self.start()
        #FIXME timer and layout module are unstoppable ;-) to be fixed

    def use_page(self, page_id="page_0"):
        self.log.debug("switching to page {}".format(page_id), extra=self.extra)
        self.pm.render['refresh'] = True
        try:
            self.page = self.pages[page_id]
        except KeyError:
            if page_id == 'page_0':
                self.log.critical("Cannot load default page_0. Quitting.".format(page_id), extra=self.extra)
                exit()
            else:
                self.log.critical("Cannot load page {}, loading start page".format(page_id), extra=self.extra)
                self.use_page()

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
            #FIXME the try is too wide
            try:
                event = self.pm.event_queue.get(block=True, timeout=1)
                ev_type = event[0]
                if ev_type == 'touch':
                    position = event[1]
                    click = event[2]
                    self.render_pressed_button(position)
                    self.check_click(position, click)
                if ev_type == 'show_main_page':
                    self.use_main_page()
                if ev_type == 'reload_layout':
                    self.ll.load_layout()
                    self.use_page()
                if ev_type == 'preload_image':
                    image_file = event[1]
                    self.ll.load_image(image_file)
                if ev_type == 'open_editor':
                    self.editor_fields = event[1]
                    self.open_editor()
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
        if not self.font_face_set and self.ctx is not None:
            self.ctx.set_font_face(self.ll.font_face)
            self.font_face_set = True
            self.font_extents = self.ctx.font_extents()
        if not self.pm.render['hold'] and self.ctx is not None:
            self.pm.render['hold'] = True
            self.render_page()
            self.pm.render['hold'] = False

    def use_main_page(self):
        self.use_page()

    def render_background(self):
        if self.page['background_colour'] is not None:
            r = self.page['background_colour'][0]
            g = self.page['background_colour'][1]
            b = self.page['background_colour'][2]
            self.ctx.set_source_rgb(r, g, b)
        if self.page['background_image'] is not None:
            self.ctx.set_source_surface(self.page['background_image'], 0, 0)
        self.ctx.rectangle(0, 0, self.width, self.height)
        self.ctx.fill()

    def render_page(self):
        self.render_background()
        # LAYOUT DEBUG FUNCION
        #self.render_all_buttons()
        if self.page['fields'] is not None:
            self.render_layout()
        self.pm.render['refresh'] = True

    def get_value(self, parameter, vtype):
        v = self.pm.parameters[parameter][vtype]
        ru = self.pm.parameters[parameter]["raw_unit"]
        u = self.pm.parameters[parameter]["unit"]
        value = self.uc.convert(v, ru, u)
        self.value = num.sanitise(value)

    def render_layout(self):
        for meta_name, field in self.page['fields'].items():
            self.value = None
            parameter = field['parameter']
            self.pos_x, self.pos_y = field['origin']
            # Get "show" field and get parameter value using it
            try:
                show = field["show"]
            except KeyError:
                # Show value of parameter by default
                show = "value"
            self.get_parameter_value(show, parameter)
            # Try to use field 'text' if there is no value determined so far
            if self.value is None:
                try:
                    self.value = field['text']
                except KeyError:
                    self.value = ""
            # Get format field and format parameter using it
            try:
                format_field = field['format']
            except KeyError:
                format_field = None
            self.value, format_string = self.ll.format_parameter(format_field, parameter, self.value)

            variable = None
            # Get icon image
            try:
                image_path = field['file']
            except KeyError:
                image_path = None
            # Get icon image for parameter current value
            try:
                variable = field['variable']
                p = variable["name"]
                # Get current value of the parameter
                v = self.pm.parameters[p]["value"]
                # Get number of frames
                frames = field['variable']['frames']
                if v > frames:
                    self.log.error("Variable {} value {} is greater than number of frames ({}) for image file {}".format(p, v, frames, image_path), extra=self.extra)
                    v = frames
                image_path = self.make_image_key(image_path, v)
            except (KeyError, TypeError):
                pass
            if image_path is not None and image_path not in self.ll.images:
                self.ll.images[image_path] = self.ll.load_image(image_path)
            try:
                image = self.ll.images[image_path]
                self.image_to_surface(image, self.pos_x, self.pos_y)
            except KeyError:
                pass
            # Get font size or if it's not defined fall back to the page font size
            try:
                self.fs = field['font_size']
            except KeyError:
                # Fall back to page font size
                self.fs = self.page['font_size']
            self.ctx.set_font_size(self.fs)

            # Get text alignment or if it's not defined use center
            try:
                align = field["align"]
            except KeyError:
                align = "center"
            shift_x = self.calculate_x_shift(align, self.value)

            # 18 is font size for which font_extents has height. So far no scaled_font_extents function
            self.shift_y = 0.5 * self.font_extents[2] * self.fs / 18
            if align == 'point':
                self.render_point_aligned_text()
            elif format_string == "zoomed_digit":
                self.scale = 1.4
                self.render_zoomed_digit_text()
            else:
                self.text_to_surface(self.value, self.pos_x + shift_x, self.pos_y + self.shift_y, self.page['text_colour'])

    def get_parameter_value(self, show, parameter):
        if show == "value":
            # For editors use parameter value from editor_fields
            if self.page["type"] == "editor":
                try:
                    self.value = self.editor_fields[parameter]
                    if type(self.value) is tuple:
                        self.value = self.value[0]
                except (KeyError, TypeError):
                    self.value = None
            else:
                try:
                    self.get_value(parameter, 'value')
                except (KeyError, TypeError):
                    self.value = None
        elif show == "date":
            try:
                self.get_value(parameter, 'value')
                self.value = datetime.datetime.fromtimestamp(int(self.value)).strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        elif show == "time":
            try:
                self.get_value(parameter, 'value')
                self.value = datetime.datetime.fromtimestamp(int(self.value)).strftime('%H:%M:%S')
            except (TypeError, ValueError):
                # ValueError: invalid literal for int() with base 10: ''
                pass
        elif show == "tenths":
            try:
                self.get_value(parameter, 'value')
                tenths_string = "{}".format(self.value - int(self.value))
                self.value = format(tenths_string)[2:3]
            except (KeyError, TypeError, ValueError):
                self.value = None
        elif show == "unit":
            try:
                self.value = self.pm.parameters[parameter]["unit"]
            except KeyError:
                self.value = None
        elif show in ('min', 'avg', 'max'):
            try:
                self.get_value(parameter, 'value_' + show)
            except KeyError:
                self.value = None

    def calculate_x_shift(self, align, text):
        # Calculate text horizontal shift
        te = self.ctx.text_extents(text)
        if align == 'center':
            shift_x = -1.0 * te.width / 2.0
        elif align == 'right':
            shift_x = -1.0 * te.width
        elif align == 'left':
            shift_x = 0.0
        else:
            shift_x = 0.0
        return shift_x

    def render_point_aligned_text(self):
        # Find most right separator - a non-digit
        try:
            char = [x for x in self.value if not x.isdigit()][-1]
        except IndexError:
            char = '.'
        # Split text on separator
        self.split_text = self.value.rpartition(char)
        # Get separator width
        te = self.ctx.text_extents(self.split_text[1])
        width = te.width
        # Render all parts of the text to the surface
        for text, align, shift in zip(self.split_text, ('right', 'center', 'left'), (-1 * width, 0, width)):
            shift_x = self.calculate_x_shift(align, text)
            self.text_to_surface(text, self.pos_x + shift_x + shift, self.pos_y + self.shift_y, self.page['text_colour'])

    def render_zoomed_digit_text(self):
        self.value = self.editor_fields["value"]
        i = self.editor_fields["index"]
        #Head
        rv1 = self.value[:i]
        te1 = self.ctx.text_extents(rv1)
        #Tail
        rv3 = self.value[i + 1:]
        #Currently edited digit
        rv2 = self.value[i]
        self.ctx.set_font_size(self.scale * self.fs)
        te2 = self.ctx.text_extents(rv2)

        te = self.ctx.text_extents(self.value)
        rv1_x = self.pos_x - te.width / 2.0
        rv2_x = self.pos_x - te.width / 2.0 + te1.x_advance
        rv3_x = self.pos_x - te.width / 2.0 + te1.x_advance + te2.x_advance

        self.text_to_surface(rv2, rv2_x, self.pos_y + self.scale * self.shift_y, (1.0, 0.0, 0.0))
        self.ctx.set_font_size(self.fs)
        self.text_to_surface(rv1, rv1_x, self.pos_y + self.shift_y, self.page['text_colour'])
        self.text_to_surface(rv3, rv3_x, self.pos_y + self.shift_y, self.page['text_colour'])

    def render_all_buttons(self):
        # LAYOUT DEBUG FUNCION
        for parameter, r in self.page['button_rectangles'].items():
            fr = r[1]
            self.ctx.set_source_rgb(0.0, 1.0, 0.0)
            self.ctx.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.ctx.fill()
            self.ctx.set_line_width(2.0)
            self.ctx.set_source_rgb(1.0, 0.0, 0.0)
            self.ctx.rectangle(fr[0], fr[1], fr[2], fr[3])
            self.ctx.stroke()

    def render_pressed_button(self, pressed_pos):
        if self.ctx is None or self.page['buttons_image'] is None:
            return
        self.log.debug("render_pressed_button started", extra=self.extra)
        for parameter, r in self.page['button_rectangles'].items():
            if self.point_in_rect(pressed_pos, r[1]):
                fr = r[1]
                self.ctx.set_source_surface(self.page['buttons_image'], 0, 0)
                self.ctx.rectangle(fr[0], fr[1], fr[2], fr[3])
                self.ctx.fill()
        self.pm.render['refresh'] = True
        self.log.debug("render_pressed_button finished", extra=self.extra)

    def check_click(self, position, click):
        if click == 'SHORT':
            for parameter, r in self.page['button_rectangles'].items():
                if self.point_in_rect(position, r[1]):
                    self.log.debug("CLICK on {} {}".format(parameter, r), extra=self.extra)
                    field = self.page['fields'][parameter]
                    self.parse_short_click(field)
            self.pm.render['refresh'] = True
        elif click == 'LONG':
            for parameter, r in self.page['button_rectangles'].items():
                if self.point_in_rect(position, r[1]):
                    self.log.debug("LONG CLICK on {} {}".format(parameter, r), extra=self.extra)
                    field = self.page['fields'][parameter]
                    self.parse_long_click(field, r[0])
        elif click == 'R_TO_L':  # Swipe RIGHT to LEFT
            self.next_page()
        elif click == 'L_TO_R':  # Swipe LEFT to RIGHT
            self.prev_page()
        elif click == 'B_TO_T':  # Swipe BOTTOM to TOP
            self.use_main_page()
        elif click == 'T_TO_B':  # Swipe TOP to BOTTOM
            self.use_page("settings_0")

    def parse_short_click(self, field):
        self.call_plugin_method(field, 'short_click')

    def call_plugin_method(self, field, click_type):
        try:
            if field[click_type]:
                plugin, method = field[click_type].split(',')
                plugin = plugin.strip()
                method = method.strip()
                method_to_call = getattr(self.pm.plugins[plugin], method)
                method_to_call()
        except KeyError:
            pass

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
        elif plugin is not None and method is not None:
            self.call_plugin_method(field, 'long_click')
        else:
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
            f = field['format']
            if type(f) == dict:
                u = self.pm.parameters[parameter]['unit']
                self.editor_fields["format"] = f[u]
            else:
                self.editor_fields["format"] = f
        except KeyError:
            self.editor_fields["format"] = '%.0f'
            self.log.debug("No format found for editing parameter {}, using default format %.0f".format(parameter), extra=self.extra)
        try:
            self.editor_fields["value_list"] = field['value_list']
        except KeyError:
            self.editor_fields['value_list'] = None
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
            self.value = self.uc.convert(self.pm.parameters[p]["value"],
                                         self.pm.parameters[p]["raw_unit"],
                                         self.pm.parameters[p]["unit"])
            try:
                self.editor_fields["value"] = self.editor_fields["format"] % self.value
            except TypeError:
                self.editor_fields["value"] = self.value
            self.pm.plugins['editor'].set_up(self.editor_fields)
        elif self.editor_fields["editor"] == 'editor_string' or \
                self.editor_fields["editor"] == 'editor_unit':
            self.editor_fields["value"] = self.pm.parameters[p]["value"]
            self.editor_fields["allowed_units"] = ' '
            for u in self.pm.parameters[p]["units_allowed"]:
                self.editor_fields["allowed_units"] += u + ' '
            self.pm.plugins['editor'].set_up(self.editor_fields)
        elif self.editor_fields["editor"] == 'editor_list':
            v = self.pm.parameters[p]["value"]
            if self.editor_fields['value_list'] is None:
                self.editor_fields['value_list'] = []
                for el in self.pm.parameters[p]["value_list"]:
                    self.editor_fields['value_list'].append((el, None))
                try:
                    self.editor_fields['index'] = self.editor_fields["value_list"].index((v, None))
                except ValueError:
                    self.editor_fields['index'] = 0
            #editor call
            #FIXME not nice, a check if editor plugin is loaded?
            self.pm.plugins['editor'].set_up(self.editor_fields)
            self.pm.plugins['editor'].slice_list_elements(self.editor_fields["value_list"], self.editor_fields['index'])
        else:
            self.log.critical("Unknown editor {} called for parameter {}, ignoring".format(self.editor_fields["editor"], self.editor_fields["parameter"]), extra=self.extra)
            return
        self.use_page(self.editor_fields["editor"])

    def next_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.page['type'] == 'editor':
            try:
                self.use_page(self.page['right'])
            except KeyError:
                pass

    def prev_page(self):
        # Editor is a special page - it cannot be switched, only cancel or accept
        if not self.page['type'] == 'editor':
            try:
                self.use_page(self.page['left'])
            except KeyError:
                pass

    def show_overlay(self):
        if len(self.overlay_queue) > 0 and math.isnan(self.overlay_time_start):
            self.overlay_time_start = time.time()
            overlay = self.overlay_queue.pop(0)
            image_path = overlay[0]
            self.overlay_show_time = overlay[1]
            if image_path is not None:
                if image_path not in self.ll.images:
                    self.ll.images[image_path] = self.ll.load_image(image_path)
                image = self.ll.images[image_path]
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

    #FIXME misleading names surface --> image, image_to_surface --> render_image?
    def image_to_surface(self, surface, x=0, y=0, w=None, h=None):
        if w is None:
            w = self.width
        if h is None:
            h = self.height
        self.ctx.set_source_surface(surface, x, y)
        self.ctx.rectangle(x, y, w, h)
        self.ctx.fill()

    #FIXME Needs to go to layout_loader
    def make_image_key(self, image_path, value):
        suffix = "_" + format(value)
        extension = image_path[-4:]
        name = image_path[:-4]
        return (name + suffix + extension)
