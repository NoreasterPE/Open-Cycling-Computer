#!/usr/bin/python3
## @package pitft_rendering
#  Rendering module for piTFT

import cairo
import mmap
import plugin
import time


## Display rendering class
class pitft_rendering(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}
    ## @var FPS
    #  Desired FPS, very innacurate
    FPS = 10.0

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        ## @var width
        #  Window/screen width
        try:
            self.width = self.pm.parameters['display_size']['value'][0]
        except KeyError:
            self.log.critical('pitft_rendering init failed on display_size', extra=self.extra)
            raise
        ## @var height
        #  Window/screen height
        try:
            self.height = self.pm.parameters['display_size']['value'][1]
        except KeyError:
            self.log.critical('pitft_rendering init failed on display_size', extra=self.extra)
            raise
        #FIXME add param to control fps/screenshot here
        ## @var running
        #  Variable controlling if rendering module should keep running
        self.running = False
        ## @var fps
        #  Variable controlling numver of frames per second
        self.fps = self.FPS
        self.cairo_initialised = False
        self.setup_cairo()

    ## Notification handler
    #  @param self The python object self
    def notification(self):
        self.log.debug('notification received', extra=self.extra)
        if (self.width, self.height) != self.pm.parameters['display_size']['value'] and \
                not self.cairo_initialised:
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
            self.surface = cairo.ImageSurface.create_similar(self.fb_surface, cairo.CONTENT_COLOR_ALPHA, self.width, self.height)
            # Framebuffer context
            self.fb_ctx = cairo.Context(self.fb_surface)
            # Main cairo context
            self.ctx = cairo.Context(self.surface)
            self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.ctx.paint()
            self.pm.register_cairo_context(self.extra['module_name'], self.ctx)
            # Overlay cairo drawing surface
            self.overlay_surface = cairo.ImageSurface.create_similar(self.fb_surface, cairo.CONTENT_COLOR_ALPHA, self.width, self.height)
            # Overlay cairo context
            self.overlay_ctx = cairo.Context(self.overlay_surface)
            self.overlay_ctx.set_source_rgba(0.0, 0.0, 0.0, 0.0)
            self.overlay_ctx.paint_with_alpha(0.0)
            self.pm.register_cairo_overlay(self.extra['module_name'], self.overlay_ctx)
            self.cairo_initialised = True

    def run(self):
        self.running = True
        while self.running:
            if self.width is not None and \
                    self.height is not None and \
                    not self.cairo_initialised:
                self.setup_cairo()
            if self.pm.render['refresh'] and not self.pm.render['hold']:
                self.pm.render['hold'] = True
                self.fb_ctx.set_source_surface(self.surface, 0, 0)
                self.fb_ctx.paint()
                self.fb_ctx.set_source_surface(self.overlay_surface, 0, 0)
                self.fb_ctx.paint_with_alpha(0.9)
                self.pm.render['refresh'] = False
                self.pm.render['hold'] = False
                try:
                    if self.pm.parameters['screenshot_mode']['value']:
                        self.fb_surface.write_to_png("sc_" + str(round(time.time())) + ".png")
                        self.fps = 1.0
                    else:
                        self.fps = self.FPS
                except KeyError:
                    pass
            #FIXME Set up scheduler instead of waiting
            time.sleep(1.0 / self.fps)

    def stop(self):
        self.running = False

    def __del__(self):
        self.stop()
