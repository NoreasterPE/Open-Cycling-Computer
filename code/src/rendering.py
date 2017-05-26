#! /usr/bin/python
## @package rendering
#  Rendering module. Runs in a separate thread and keeps flipping screen with pygame.display.flip at 20 fps using pygame.clock.tick.

import threading
import pygame


## Display rendering class
class rendering(threading.Thread):

    ## The constructor
    #  @param self The python object self
    #  @param layout \link layout \endlink instance
    def __init__(self, layout):
        # Run init for super class
        super(rendering, self).__init__()
        self.clock = pygame.time.Clock()
        self.layout = layout
        self.refresh = True
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            if self.refresh:
                self.refresh = False
                self.layout.render_page()
                # FIXME display.update might be faster, but require list of
                # rectangles for he update
                pygame.display.flip()
            # Setting FPS too low causes some click-directly-after-click
            # problems
            self.clock.tick(20)

    def stop(self):
        self.running = False

    def force_refresh(self):
        self.refresh = True

    def __del__(self):
        self.stop()
