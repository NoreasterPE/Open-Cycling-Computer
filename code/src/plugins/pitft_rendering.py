#!/usr/bin/python3
## @package pitft_rendering
#  Rendering module for piTFT

import cairo
import mmap
import plugin
import pyplum
import time


## Display rendering class
class pitft_rendering(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.pm = pyplum.pyplum()
        ## @var width
        #  Window/screen width
        ## @var height
        #  Window/screen height
        self.width, self.height = self.pm.parameters['display_size']['value']
        ## @var running
        #  Variable controlling if rendering module should keep running
        self.running = False
        ## @var fps
        #  Variable controlling numver of frames per second
        self.fps = 10.0
        self.cairo_initialised = False
        self.setup_cairo()

    ## Notification handler
    #  @param self The python object self
    def notification(self):
        self.log.debug('notification received')
        if ((self.width, self.height) != self.pm.parameters['display_size']['value'] and
                not self.cairo_initialised):
            self.width, self.height = self.pm.parameters['display_size']['value']
            self.setup_cairo()

    ## Prepare cairo surface and context
    #  @param self The python object self
    def setup_cairo(self):
        if self.width is not None and self.height is not None and not self.cairo_initialised:
            PiTFT_mem_size = 153600
            self.fb_fd = open("/dev/fb1", "r+")
            self.fb_map = mmap.mmap(self.fb_fd.fileno(), PiTFT_mem_size)
            # Framebuffer surface
            self.fb_surface = cairo.ImageSurface.create_for_data(self.fb_map, cairo.FORMAT_RGB16_565, self.width, self.height)
            # Main cairo drawing surface
            self.surface = cairo.ImageSurface.create_similar(self.fb_surface, cairo.CONTENT_COLOR, self.width, self.height)
            # Framebuffer context
            self.fb_ctx = cairo.Context(self.fb_surface)
            # Main cairo context
            self.ctx = cairo.Context(self.surface)
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.paint_with_alpha(1.0)
            self.pm.register_cairo_context(self.extra['module_name'], self.ctx)
            self.cairo_initialised = True

    def run(self):
        self.running = True
        while self.running:
            if (self.width is not None and
                    self.height is not None and
                    not self.cairo_initialised):
                self.setup_cairo()
            if self.pm.render['refresh'] and not self.pm.render['hold']:
                self.pm.render['hold'] = True
                self.fb_ctx.set_source_surface(self.surface, 0, 0)
                self.fb_ctx.rectangle(0, 0, self.width, self.height)
                self.fb_ctx.fill()
                self.pm.render['refresh'] = False
                self.pm.render['hold'] = False
                #Uncomment to generate screenshots, also changes fps to 1 to avoid generating too much images
                #self.fb_surface.write_to_png("sc_" + str(round(time.time())) + ".png")
                #self.fps = 1.0
            #FIXME Set up scheduler instead of waiting
            time.sleep(1.0 / self.fps)

    def stop(self):
        self.running = False

    def __del__(self):
        self.stop()
