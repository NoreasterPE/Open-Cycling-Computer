#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## @package layout

#   Module responsible for loading layouts. Needs heavy cleaning...

import cairo
import ctypes as ct
import datetime
import logging
import pyplum
import sys
import yaml


## Class for loading and parsing layouts
class layout_loader():
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self):
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')
        ## @var pm
        #  PYthon PLUgin Manager instance
        self.pm = pyplum.pyplum()
        ## @var fonts_dir
        #  Location of fonts directory
        self.fonts_dir = self.pm.parameters['fonts_dir']['value']
        ## @var layout_file
        #  Location of layout file
        self.layout_file = self.pm.parameters['layout_file']['value']
        ## @var images
        #  Dict with images loaded with png_to_cairo_surface. Currently only pngs are supported.
        self.images = {}
        ## @var pages
        #  Dict with parsed pages from layout file.
        self.pages = {}
        ## @var button_rectangles
        #  Dict with buttons. Parsed for layout file
        self.button_rectangles = {}
        ## @var font_face_set
        #  Indicates if cairo font has been initialised.
        self.font_initialised = False
        ## @var abs_origin
        #  Current absolute origin coordinates used to place graphisc/text on cairo surface
        self.abs_origin = dict(x=0, y=0)
        ## @var rel_origin
        #  Current relative origin coordinates used to place graphisc/text on cairo surface
        self.rel_origin = dict(x=0, y=0)
        self.load_layout()
        self.parse_page()

    def load_layout(self):
        self.images = {}
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
            self.pages[page_id]['parameters'] = dict()
            try:
                for f in page['fields']:
                    try:
                        meta_name = f['parameter'] + "_" + f['show']
                    except KeyError:
                        meta_name = f['parameter']
                    self.pages[page_id]['parameters'][meta_name] = f
            except TypeError:
                pass

    def load_layout_tree(self):
        self.log.debug("Loading layout {}".format(self.layout_file), extra=self.extra)
        try:
            with open(self.layout_file) as f:
                self.layout_tree = yaml.safe_load(f)
                f.close()
        except:
            self.log.critical("Loading layout {} failed, quitting".format(self.layout_file), extra=self.extra)
            sys_info = "Error details: {}".format(sys.exc_info()[0])
            self.log.critical(sys_info, extra=self.extra)
            # FIXME Proper quit required
            quit()

    def parse_font(self):
        self.font = self.current_page['font']
        if self.font == '':
            self.log.critical("Page font found, but it's empry string. font field is mandatory.".format(self.current_page), extra=self.extra)
        try:
            self.page_font_size = self.current_page['font_size']
        except KeyError:
            self.log.critical("Page font size not found on page {}. font_size field is mandatory. Defaulting to 18".format(self.current_page), extra=self.extra)
            self.page_font_size = 18
        return (self.font, self.page_font_size)

    def initialise_font(self):
        try:
            # Only one font is allowed for now due to cairo helper workaround.
            self.log.debug("Calling cairo_helper for {}".format(self.fonts_dir + self.font), extra=self.extra)
            self.font_face = create_cairo_font_face_for_file(self.fonts_dir + self.font, 0)
            self.font_initialised = True
        except AttributeError:
            pass

    def parse_page(self, page_id="page_0"):
        self.log.debug("parse_page {}".format(page_id), extra=self.extra)
        self.abs_origin = dict(x=0, y=0)
        self.rel_origin = dict(x=0, y=0)
        self.pm.render['refresh'] = True
        try:
            self.current_page = self.pages[page_id]
        except KeyError:
            if page_id == 'page_0':
                self.log.critical("Cannot load default page_0. Quitting.".format(page_id), extra=self.extra)
                exit()
            else:
                self.log.critical("Cannot load page {}, loading start page".format(page_id), extra=self.extra)
                self.parse_page()

        self.background_image = None
        if 'background_image' in self.current_page:
            self.background_image = self.load_image(self.current_page['background_image'])

        self.buttons_image = None
        if 'buttons_image' in self.current_page:
            self.buttons_image = self.load_image(self.current_page['buttons_image'])

        self.background_colour = None
        if 'background_colour' in self.current_page:
            self.background_colour = self.parse_background_colour()

        self.font = None
        if 'font' in self.current_page:
            self.font, self.font_size = self.parse_font()
        if not self.font_initialised:
            self.initialise_font()

        self.text_colour = None
        if 'text_colour' in self.current_page:
            self.text_colour = self.parse_text_colour()

        self.button_rectangles = {}
        if self.current_page['fields'] is not None:
            for field in self.current_page['fields']:
                self.get_position(field)
                self.parse_parameter(field)

    def parse_text_colour(self):
        self.text_colour_rgb = self.current_page['text_colour']
        text_colour_rgb = self.text_colour_rgb
        if text_colour_rgb[0] == '#':
            text_colour_rgb = text_colour_rgb[1:]
        r, g, b = text_colour_rgb[:2], text_colour_rgb[2:4], text_colour_rgb[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        self.text_colour = (r, g, b)
        return self.text_colour

    def parse_background_colour(self):
        self.background_colour_rgb = self.current_page['background_colour']
        background_colour_rgb = self.background_colour_rgb
        if background_colour_rgb[0] == '#':
            background_colour_rgb = background_colour_rgb[1:]
        r, g, b = background_colour_rgb[:2], background_colour_rgb[2:4], background_colour_rgb[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        self.background_colour = (r, g, b)
        return self.background_colour

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
                rect = (self.abs_origin['x'] + self.rel_origin['x'] + int(b['x0']),
                        self.abs_origin['y'] + self.rel_origin['y'] + int(b['y0']),
                        int(b['w']),
                        int(b['h']))
            except KeyError:
                self.log.error("Button field present, but invalid x0, y0, w or b detected at parameter {} on page {}.".format(name, self.current_page), extra=self.extra)
                self.log.error("Button for {} won't work.".format(name), extra=self.extra)
            self.button_rectangles[meta_name] = (name, rect)
        except KeyError:
            pass

    def format_parameter(self, format_field, parameter, value):
        format_string = self.get_format_string(format_field, parameter)
        if format_string == "hhmmss.s":
            try:
                minutes, seconds = divmod(value, 60)
                hours, minutes = divmod(minutes, 60)
                value = "{:02.0f}:{:02.0f}:{:02.1f}".format(hours, minutes, seconds)
            except (TypeError, ValueError):
                pass
        elif format_string == "hhmmss":
            try:
                minutes, seconds = divmod(int(value), 60)
                hours, minutes = divmod(minutes, 60)
                value = "{:02.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds)
            except (TypeError, ValueError):
                pass
        elif format_string == "time":
            try:
                value = datetime.datetime.fromtimestamp(int(value)).strftime('%H:%M:%S')
            except (TypeError, ValueError):
                # ValueError: invalid literal for int() with base 10: ''
                pass
        elif format_string == "date":
            try:
                value = datetime.datetime.fromtimestamp(int(value)).strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass
        else:
            try:
                value = format_string % float(value)
            except (TypeError, ValueError):
                value = format(value)
        return value, format_string

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

    def get_format_string(self, format_field, parameter):
        format_string = '%.0f'
        if type(format_field) == dict:
            u = self.pm.parameters[parameter]['unit']
            format_string = format_field[u]
        elif format_field is not None:
            format_string = format_field
        return format_string

    def png_to_cairo_surface(self, file_path):
        png_surface = cairo.ImageSurface.create_from_png(file_path)
        return png_surface

    def get_position(self, field):
        try:
            self.abs_origin = field['abs_origin']
            self.rel_origin = dict(x=0, y=0)
        except KeyError:
            pass
        try:
            ro = field['rel_origin']
            self.rel_origin = dict(x=self.rel_origin.get('x') + ro.get('x'),
                                   y=self.rel_origin.get('y') + ro.get('y'))
        except KeyError:
            pass
        try:
            x = field['x']
        except KeyError:
            x = 0
        try:
            y = field['y']
        except KeyError:
            y = 0
        self.origin = dict(x=self.abs_origin.get('x') + self.rel_origin.get('x') + x,
                           y=self.abs_origin.get('y') + self.rel_origin.get('y') + y)


_initialized = False


def create_cairo_font_face_for_file(filename, faceindex=0, loadoptions=0):
    "given the name of a font file, and optional faceindex to pass to FT_New_Face" \
        " and loadoptions to pass to cairo_ft_font_face_create_for_ft_face, creates" \
        " a cairo.FontFace object that may be used to render text with that font."
    global _initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _ft_destroy_key
    global _surface

    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _initialized:
        # find shared objects
        _freetype_so = ct.CDLL("libfreetype.so.6")
        _cairo_so = ct.CDLL("libcairo.so.2")
        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ct.c_void_p, ct.c_int]
        _cairo_so.cairo_font_face_get_user_data.restype = ct.c_void_p
        _cairo_so.cairo_font_face_get_user_data.argtypes = (ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_font_face_set_user_data.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
        _cairo_so.cairo_set_font_face.argtypes = [ct.c_void_p, ct.c_void_p]
        _cairo_so.cairo_font_face_status.argtypes = [ct.c_void_p]
        _cairo_so.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
        _cairo_so.cairo_status.argtypes = [ct.c_void_p]
        # initialize freetype
        _ft_lib = ct.c_void_p()
        status = _freetype_so.FT_Init_FreeType(ct.byref(_ft_lib))
        if status != FT_Err_Ok:
            raise RuntimeError("Error %d initializing FreeType library." % status)
        # end if

        class PycairoContext(ct.Structure):
            _fields_ = \
                [
                    ("PyObject_HEAD", ct.c_byte * object.__basicsize__),
                    ("ctx", ct.c_void_p),
                    ("base", ct.c_void_p),
                ]
        # end PycairoContext

        _surface = cairo.ImageSurface(cairo.FORMAT_A8, 0, 0)
        _ft_destroy_key = ct.c_int()  # dummy address
        _initialized = True
    # end if

    ft_face = ct.c_void_p()
    cr_face = None
    try:
        # load FreeType face
        status = _freetype_so.FT_New_Face(_ft_lib, filename.encode("utf-8"), faceindex, ct.byref(ft_face))
        if status != FT_Err_Ok:
            raise RuntimeError("Error %d creating FreeType font face for %s" % (status, filename))
        # end if

        # create Cairo font face for freetype face
        cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
        status = _cairo_so.cairo_font_face_status(cr_face)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        # end if
        # Problem: Cairo doesn't know to call FT_Done_Face when its font_face object is
        # destroyed, so we have to do that for it, by attaching a cleanup callback to
        # the font_face. This only needs to be done once for each font face, while
        # cairo_ft_font_face_create_for_ft_face will return the same font_face if called
        # twice with the same FT Face.
        # The following check for whether the cleanup has been attached or not is
        # actually unnecessary in our situation, because each call to FT_New_Face
        # will return a new FT Face, but we include it here to show how to handle the
        # general case.
        if _cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(_ft_destroy_key)) is None:
            status = _cairo_so.cairo_font_face_set_user_data(cr_face,
                                                             ct.byref(_ft_destroy_key),
                                                             ft_face,
                                                             _freetype_so.FT_Done_Face)
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError("Error %d doing user_data dance for %s" % (status, filename))
            # end if
            ft_face = None  # Cairo has stolen my reference
        # end if

        # set Cairo font face into Cairo context
        cairo_ctx = cairo.Context(_surface)
        cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx
        _cairo_so.cairo_set_font_face(cairo_t, cr_face)
        status = _cairo_so.cairo_font_face_status(cairo_t)
        if status != CAIRO_STATUS_SUCCESS:
            raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))
        # end if

    finally:
        _cairo_so.cairo_font_face_destroy(cr_face)
        _freetype_so.FT_Done_Face(ft_face)
    # end try

    # get back Cairo font face as a Python object
    face = cairo_ctx.get_font_face()
    return face
