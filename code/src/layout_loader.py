#!/usr/bin/env python3
# -*- coding: utf-8 -*-

## @package layout

#   Module responsible for loading layouts. Needs heavy cleaning...

import cairo
import collections
import ctypes as ct
import glob
import logging
import os
import yaml

import pyplum


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
        #  Location of layout file or directory
        self.layout_location = self.pm.parameters['layout_location']['value']
        ## @var images
        #  Dict with images loaded with png_to_cairo_surface. Currently only pngs are supported.
        self.images = {}
        ## @var pages
        #  Dict with parsed pages from layout file.
        self.pages = {}
        ## @var font_face_set
        #  Indicates if cairo font has been initialised.
        self.font_initialised = False
        ## @var font_face
        #  Font face
        self.font_face = None
        ## @var abs_origin
        #  Current absolute origin coordinates used to place graphisc/text on cairo surface
        self.abs_origin = dict(x=0, y=0)
        ## @var rel_origin
        #  Current relative origin coordinates used to place graphisc/text on cairo surface
        self.rel_origin = dict(x=0, y=0)
        self.load_layout_from_location()
        #self.parse_page()

    ## Loads layout from a location (directory with one page per file or file woith all pages) and parses the content into self.pages
    #  @param self The python object self
    def load_layout_from_location(self):
        self.layout_tree = dict()
        self.layout_tree['pages'] = dict()
        if os.path.isfile(self.layout_location):
            self.layout_file = self.layout_location
            self.layout_tree['pages'] = self.load_layout_tree_from_file(self.layout_location)
        elif os.path.isdir(self.layout_location):
            self.layout_dir = self.layout_location
            files = [f for f in glob.glob(self.layout_dir + "*.yaml")]
            for f in files:
                layout_tree = self.load_layout_tree_from_file(f)
                self.layout_tree['pages'][layout_tree['id']] = layout_tree
        else:
            self.log.critical("Layput location is not a file or a directory, refusing to load".format(self.layout_location), extra=self.extra)
        self.convert_pages()

    ## Converts self.layout_tree into move convinient self.page
    #  @param self The python object self
    def convert_pages(self):
        self.images = {}
        self.pages = {}
        for page_id, page in self.layout_tree['pages'].items():
            self.pages[page_id] = collections.OrderedDict()
            self.pages[page_id]['top'] = None
            self.pages[page_id]['botton'] = None
            self.pages[page_id]['left'] = None
            self.pages[page_id]['right'] = None
            self.pages[page_id]['fields'] = collections.OrderedDict()
            self.pages[page_id]['button_rectangles'] = collections.OrderedDict()
            abs_x = 0
            abs_y = 0
            rel_x = 0
            rel_y = 0
            page_fields = collections.OrderedDict()
            self.pages[page_id]['name'] = None
            self.pages[page_id]['type'] = None
            self.pages[page_id]['background_image'] = None
            self.pages[page_id]['buttons_image'] = None
            self.pages[page_id]['background_colour'] = (0, 0, 0)
            self.pages[page_id]['text_colour'] = (255, 255, 255)
            self.pages[page_id]['font'] = None
            self.pages[page_id]['font_size'] = 18
            try:
                if 'name' in page:
                    self.pages[page_id]['name'] = page['name']
                if 'type' in page:
                    self.pages[page_id]['type'] = page['type']
                if 'background_image' in page:
                    self.pages[page_id]['background_image'] = self.load_image(page['background_image'])
                if 'buttons_image' in page:
                    self.pages[page_id]['buttons_image'] = self.load_image(page['buttons_image'])
                if 'background_colour' in page:
                    self.pages[page_id]['background_colour'] = self.parse_background_colour()
                if 'text_colour' in page:
                    self.pages[page_id]['text_colour'] = self.parse_text_colour(page['text_colour'])
                if 'up' in page:
                    self.pages[page_id]['up'] = page['up']
                if 'down' in page:
                    self.pages[page_id]['down'] = page['down']
                if 'left' in page:
                    self.pages[page_id]['left'] = page['left']
                if 'right' in page:
                    self.pages[page_id]['right'] = page['right']
                if 'font' in page:
                    self.pages[page_id]['font'], self.pages[page_id]['font_size'] = self.parse_font(page['font'], page['font_size'])
                    if not self.font_initialised:
                        self.initialise_font(self.pages[page_id]['font'])

                if page['fields'] is not None:
                    for f in page['fields']:
                        meta_name = self.get_meta_name(f)
                        if meta_name in page['fields']:
                            #field already in the ordered dict, add location
                            meta_name = meta_name + '-' + format(f['x']) + '-' + format(f['y'])
                        page_fields[meta_name] = f
                        if ('abs_origin' in f):
                            abs_x = f['abs_origin']['x']
                            abs_y = f['abs_origin']['y']
                            del page_fields[meta_name]['abs_origin']
                        if ('rel_origin' in f):
                            rel_x = f['rel_origin']['x']
                            rel_y = f['rel_origin']['y']
                            abs_x += rel_x
                            abs_y += rel_y
                            del page_fields[meta_name]['rel_origin']
                        if ('x' in f) and ('y' in f):
                            x = f['x']
                            y = f['y']
                            del page_fields[meta_name]['x']
                            del page_fields[meta_name]['y']
                        else:
                            x = 0
                            y = 0
                        page_fields[meta_name]['origin'] = (abs_x + x, abs_y + y)
                        button_rect = self.button_rect_from_layout(f)
                        if button_rect is not None:
                            button_rect[0] += abs_x
                            button_rect[1] += abs_y
                        self.pages[page_id]['button_rectangles'][meta_name] = (f['parameter'], button_rect)
                    self.pages[page_id]['fields'] = page_fields
            except TypeError as e:
                self.log.error("Error while converting layout {}: {}.".format(page_id, str(e)), extra=self.extra)

    ## Loads layout from yaml file.
    #  @param self The python object self
    def load_layout_tree_from_file(self, layout_file):
        self.log.debug("Loading layout file {}".format(layout_file), extra=self.extra)
        layout_tree = None
        try:
            with open(layout_file) as f:
                layout_tree = yaml.safe_load(f)
                f.close()
        except yaml.scanner.ScannerError as e:
            self.log.critical("Loading layout file {} failed, quitting".format(layout_file), extra=self.extra)
            self.log.critical("Error details: {}".format(str(e)), extra=self.extra)
            quit()
        return layout_tree

    def parse_font(self, font_entry, font_size_entry):
        # FIXME more advanced check required
        font = font_entry
        if font == '':
            self.log.critical("Page font found, but it's empry string. font field is mandatory.", extra=self.extra)
        try:
            page_font_size = font_size_entry
        except KeyError:
            self.log.critical("Page font size not found on page {}. font_size field is mandatory. Defaulting to 18".format(self.current_page), extra=self.extra)
            page_font_size = 18
        return (font, page_font_size)

    def initialise_font(self, font):
        try:
            # Only one font is allowed for now due to cairo helper workaround.
            self.log.debug("Calling cairo_helper for {}".format(self.fonts_dir + font), extra=self.extra)
            self.font_face = create_cairo_font_face_for_file(self.fonts_dir + font, 0)
            self.font_initialised = True
        except AttributeError:
            pass

    def parse_text_colour(self, colour_entry):
        self.text_colour_rgb = colour_entry
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

    def button_rect_from_layout(self, field):
        rect = None
        if 'button' in field:
            b = field['button']
            try:
                rect = [int(b['x0']),
                        int(b['y0']),
                        int(b['w']),
                        int(b['h'])]
            except KeyError:
                self.log.error("Button field present, but invalid x0, y0, w or b detected at parameter {}.".format(field['parameter']), extra=self.extra)
                self.log.error("Button for {} won't work.".format(field['parameter']), extra=self.extra)
        return rect

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

    def get_meta_name(self, field):
        try:
            show = field["show"]
            meta_name = field["parameter"] + "_" + show
        except KeyError:
            meta_name = field["parameter"]
        return meta_name


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
