#!/usr/bin/python3
## @package gtk_rendering
#  Rendering module in GTK window

import plugin
import pyplum
import time
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
#import cairo


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
        self.pm = pyplum.pyplum()
        ## @var width
        #  Window/screen width
        try:
            self.width = self.pm.parameters['display_size']['value'][0]
        except KeyError:
            self.log.critical('gtk_rendering init failed on display_size')
            raise
        ## @var height
        #  Window/screen height
        try:
            self.height = self.pm.parameters['display_size']['value'][1]
        except KeyError:
            self.log.critical('gtk_rendering init failed on display_size')
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
            win.set_title('Drawing Area')
            win.connect('destroy', Gtk.main_quit)
            win.connect('delete-event', Gtk.main_quit)
            win.set_border_width(8)

            da = Gtk.DrawingArea()
            da.set_size_request(240, 320)
            #da.connect('draw', draw_cb)
            win.add(da)
            win.show_all()
            myGdkWindow = da.get_window()
            self.ctx = myGdkWindow.cairo_create()
            #thread = threading.Thread(target=Gtk.main())
            #thread.start()
            #thread.join()
            # Main cairo context
            #self.ctx.set_source_surface(self.surface, 0, 0)
            #self.ctx = cairo.Context(self.surface)
            #self.ctx.set_source_rgba(0.0, 0.0, 0.0, 1.0)
            #self.ctx.paint_with_alpha(1.0)
            self.pm.register_cairo_context(self.extra['module_name'], self.ctx)
            threading.Thread(target=Gtk.main).start()
            self.cairo_initialised = True

    def run(self):
        self.running = True
        import cairo
        global png_surface
        png_surface = cairo.ImageSurface.create_from_png('images/page_0_background.png')
        while self.running:
            if (self.width is not None and
                    self.height is not None and
                    not self.cairo_initialised):
                self.setup_cairo()
            if self.pm.render['refresh'] and not self.pm.render['hold']:
                self.pm.render['hold'] = True
                #call draw here
                s = self.ctx.get_target()
                self.ctx.set_source_surface(s, 0, 0)
                self.ctx.fill()
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


def draw_cb(wid, cr):
    #    import cairo
    #    png_surface = cairo.ImageSurface.create_from_png('images/page_0_background.png')
    #    cr.set_source_surface(png_surface, 0, 0)
    #    cr.rectangle(0, 0, 240, 320)
    #    cr.fill()
    s = cr.get_target()
    cr.set_source_surface(s, 0, 0)
    cr.paint()
    #cr.set_source_surface(png_surface, 0, 0)
    #cr.rectangle(0, 0, 240, 320)
    #cr.fill()
    return False
