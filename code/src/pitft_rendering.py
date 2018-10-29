#!/usr/bin/python3
## @package pitft_rendering
#  Rendering module for piTFT

import cairo
import mmap
import sensor
import sensors
import time


## Display rendering class
class pitft_rendering(sensor.sensor):

    ## The constructor
    #  @param self The python object self
    def __init__(self):
        # Run init for super class
        super().__init__()
        self.s = sensors.sensors()
        ## @var width
        #  Window/screen width
        ## @var height
        #  Window/screen height
        self.width, self.height = self.s.parameters['display_size']['value']
        self.render = True
        ## @var running
        #  Variable controlling if rendering module should keep running
        self.running = False
        ## @var fps
        #  Variable controlling numver of frames per second
        self.fps = 10.0
        self.cairo_initialised = False
        self.setup_cairo()

    def notification(self):
        if ((self.width, self.height) != self.s.parameters['display_size']['value'] and
                not self.cairo_initialised):
            self.width, self.height = self.s.parameters['display_size']['value']
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
            self.fb_cr = cairo.Context(self.fb_surface)
            # Main cairo context
            self.cr = cairo.Context(self.surface)
            self.cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            self.cr.paint_with_alpha(1.0)
            self.cairo_initialised = True

    def run(self):
        self.running = True
        while self.running:
            if (self.width is not None and
                    self.height is not None and
                    not self.cairo_initialised):
                self.setup_cairo()
            if self.render:
                self.render = False
                self.fb_cr.set_source_surface(self.surface, 0, 0)
                self.fb_cr.rectangle(0, 0, self.width, self.height)
                self.fb_cr.fill()
                #Uncomment to generate screenshots, also changes fps to 1 to avoid generating too much images
                #self.fb_surface.write_to_png("sc_" + str(round(time.time())) + ".png")
                #self.fps = 1.0
            #FIXME Set up scheduler instead of waiting
            time.sleep(1.0 / self.fps)

    def stop(self):
        self.running = False

    def force_render(self):
        self.render = True

    def __del__(self):
        self.stop()