#!/usr/bin/python3
## @package layout
#   Module responsible for loading layouts. Needs heavy cleaning...

import cairo
import logging
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
        self.load_layout()

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

    def png_to_cairo_surface(self, file_path):
        png_surface = cairo.ImageSurface.create_from_png(file_path)
        return png_surface
