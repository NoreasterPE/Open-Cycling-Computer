#!/usr/bin/python3
## @package gtk_rendering
#  Rendering module in GTK window

import cairo
import plugin
import time
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


## Display rendering class
class gtk_rendering(plugin.plugin):
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
            self.log.critical('gtk_rendering init failed on display_size', extra=self.extra)
            raise
        ## @var height
        #  Window/screen height
        try:
            self.height = self.pm.parameters['display_size']['value'][1]
        except KeyError:
            self.log.critical('gtk_rendering init failed on display_size', extra=self.extra)
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
        self.log.debug('notification received')
        if ((self.width, self.height) != self.pm.parameters['display_size']['value'] and
                not self.cairo_initialised):
            self.width, self.height = self.pm.parameters['display_size']['value']
            self.setup_cairo()

    ## Prepare cairo surface and context
    #  @param self The python object self
    def setup_cairo(self):
        if self.width is not None and self.height is not None and not self.cairo_initialised:
            win = Gtk.Window()
            win.set_decorated(False)
            win.set_default_size(self.width, self.height)
            self.drawing_area = Gtk.DrawingArea()
            win.add(self.drawing_area)
            win.show_all()
            win.set_app_paintable(True)
            win.set_double_buffered(False)
            # Window context
            self.ctx = self.drawing_area.get_window().cairo_create()
            # Window surface
            s = self.ctx.get_target()
            # Soft framebuffer surface
            self.surface_buf = cairo.ImageSurface.create_similar(s, cairo.CONTENT_COLOR, self.width, self.height)
            # Soft framebuffer context
            self.ctx_buffer = cairo.Context(self.surface_buf)
            self.pm.register_cairo_context(self.extra['module_name'], self.ctx_buffer)
            self.cairo_initialised = True
            Gdk.threads_init()
            threading.Thread(target=Gtk.main).start()

    def run(self):
        self.running = True
        while self.running:
            if (self.width is not None and
                    self.height is not None and
                    not self.cairo_initialised):
                self.setup_cairo()
            if self.pm.render['refresh'] and not self.pm.render['hold']:
                self.pm.render['hold'] = True
                self.pm.render['refresh'] = False
                Gdk.threads_enter()
                try:
                    self.ctx.set_source_surface(self.surface_buf, 0, 0)
                    self.ctx.rectangle(0, 0, self.width, self.height)
                    self.ctx.fill()
                except cairo.Error as e:
                    #Exception in thread None:
                    #Traceback (most recent call last):
                    #  File "/usr/lib64/python3.6/threading.py", line 916, in _bootstrap_inner
                    #    self.run()
                    #  File "/home/przemo/software/occ/OpenCyclingComputer/Open-Cycling-Computer/code/src/plugins/gtk_rendering.py", line 102, in run
                    #    self.ctx.fill()
                    #cairo.Error: the target surface has been finished
                    if e == 'the target surface has been finished':
                        self.log.critical('The target surface no longer exist.', extra=self.extra)
                        self.running = False
                self.drawing_area.queue_draw()
                Gdk.threads_leave()
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
