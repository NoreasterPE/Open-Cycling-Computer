#!/usr/bin/python3
## @package plugin_manager
#  Sensors module. Responsible for connecting to, starting and stopping plugins.

#from bluepy.btle import BTLEException
import copy
import logging
import numbers
import threading
import time

## @var RECONNECT_DELAY
# Time between check if BLE connection need to be re-established
RECONNECT_DELAY = 2.0


## @var STATE_HOST
# BLE host states. Linked with different icons.
#  - disabled (state 0)
#  - present (state 1)
#  - scanning (state 2,3)
#  - connected 1 device (state 4)
#  - connected 2 devices (state 5)
#  - connected 3 devices (state 6)
#  - connected 4 devices (state 7)

#STATE_HOST = {'disabled': 0,
#              'enabled': 1,
#              'scanning_1': 2,
#              'scanning_2': 3,
#              'connected_1': 4,
#              'connected_2': 5,
#              'connected_3': 6,
#              'connected_4': 7}

## @var STATE_DEV
# BLE device states.
#  - disconnected (state 0)
#  - connecting (state 1)
#  - connected (state 2)
#STATE_DEV = {'disconnected': 0,
#             'connecting': 1,
#             'connected': 2}


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


## Class for handling starting/stopping plugins in separate threads
class plugin_manager(threading.Thread, metaclass=Singleton):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'plugin_manager'}

    ## The constructor
    #  @param self The python object self
    #  @param occ OCC instance
    def __init__(self):
        super().__init__()
        ## @var log
        # System logger handle
        self.log = logging.getLogger('system')

        ## @var plugins
        # Dict with sensor instances
        self.plugins = dict()
        ## @var parameters
        # Dict with parameters
        self.parameters = dict()
        ## @var parameter_requests
        # Dict with parameters requested by a module
        self.parameter_requests = dict()
        ## @var render
        #  owner   - name of the module that registered cairo context,
        #  ctx     - cairo context used to render graphics,
        #  refresh - flag indicating that the context has been modified,
        #  hold    - flag indicating that rendering should be posponed to avoid flickering
        self.render = dict(owner=None, ctx=None, refresh=False, hold=False)
        ## @var input_queue
        #  Input queue with events from hardware input, i.e. pitft touchscreen
        self.input_queue = None
        ## @var input_queue_owner
        #  Name of the module that registered input queue
        self.input_queue_owner = None
        ## @var event_queue
        #  Event queue with high level events, like short/long click, swipe, display refresh
        self.event_queue = None
        ## @var event_queue_owner
        #  Name of the module that registered event queue
        self.event_queue_owner = None
        self.plugins = dict()
        self.register_parameter("ble_host_state", self.extra["module_name"], value=0)
        ## @var no_of_connected
        # Number of connected BLE devices
        self.no_of_connected = 0
        ## @var connecting
        # Indicates if host is currently trying to establish connection
        self.connecting = False
        ## @var connected
        # Dict keeping track of which sensor is connected
        self.connected = dict()

    ## Functon that loads plugins from a subdirectory. The subdirectory name in 'plugins' by default.
    #  @param self The python object self
    def load_plugins(self, directory='plugins'):
        plugins = __import__(directory)
        import importlib
        for plugin in plugins.__all__:
            module = importlib.import_module(str(directory + '.' + plugin), directory)
            plugin_class = module.__getattribute__(plugin)
            self.log.debug("Initialising plugin {}".format(plugin), extra=self.extra)
            self.plugins[plugin] = plugin_class()

    ## Main loop of plugin_manager module.Makes snap shot of parameters and after a delay compares it to the current state.
    # Changes of parameters are used to notify plugins that requested relevant parameters.
    #  @param self The python object self
    def run(self):
        self.log.debug("run started", extra=self.extra)
        self.load_plugins()

        for s in self.plugins:
            self.log.debug("Starting {} thread".format(s), extra=self.extra)
            self.plugins[s].start()

        self.running = True
        self.previous_parameters = dict()
        while self.running:
            self.log.debug("running...", extra=self.extra)
            try:
                self.previous_parameters = copy.deepcopy(self.parameters)
            except RuntimeError as e:
                if str(e) == 'dictionary changed size during iteration':
                    self.log.debug("New parameter added while copying dictionary. Ignoring..", extra=self.extra)
            time.sleep(1.0)
            notify = list()
            for parameter, content in self.parameters.items():
                try:
                    if (self.previous_parameters[parameter]["force_notification"] or
                       self.previous_parameters[parameter]["value"] != content["value"]):
                        self.parameters[parameter]["force_notification"] = False
                        if content["required_by"] is not None:
                            for m in content["required_by"]:
                                notify.append(m)
                except KeyError as e:
                    pass
            for module in notify:
                try:
                    self.plugins[module].notification()
                except AttributeError:
                    # Ignore error - module might not exist anymore/yet
                    pass

            self.set_ble_host_state()
        self.log.debug("run finished", extra=self.extra)

    ## Helper function for setting ble_host_state parameter.
    #  @param self The python object self
    def set_ble_host_state(self):
        self.no_of_connected = 0
        self.connecting = False
        for name in self.plugins:
            try:
                s = self.plugins[name].is_connected()
                if s and name.startswith("ble"):
                    self.no_of_connected += 1
            except AttributeError:
                #Sensor is not ready yet, let's wait
                pass
        self.parameters["ble_host_state"]["value"] = self.no_of_connected + 3  # Temporary fix
#        if self.no_of_connected == 0:
#            self.parameters["ble_host_state"]["value"] = STATE_HOST['enabled']
#        if self.no_of_connected == 1:
#            self.parameters["ble_host_state"]["value"] = STATE_HOST['connected_1']
#        if self.no_of_connected == 2:
#            self.parameters["ble_host_state"]["value"] = STATE_HOST['connected_2']
#        if self.no_of_connected == 3:
#            self.parameters["ble_host_state"]["value"] = STATE_HOST['connected_3']
#        if self.no_of_connected == 4:
#            self.parameters["ble_host_state"]["value"] = STATE_HOST['connected_4']
#        if self.connecting:
#            self.parameters["ble_host_state"]["value"] = STATE_HOST['scanning_1']

    ## The destructor
    #  @param self The python object self
    def __del__(self):
        self.stop()

    ## Function stopping all plugins. Called by the destructor
    #  @param self The python object self
    def stop(self):
        self.log.debug("stop started", extra=self.extra)
        self.running = False
        for s in self.plugins:
            self.connected[s] = False
            self.log.debug("Stopping {} thread".format(s), extra=self.extra)
            try:
                self.plugins[s].stop()
                self.log.debug("Stopped {} thread".format(s), extra=self.extra)
            except AttributeError:
                pass
            self.plugins[s] = None
        self.log.debug("stop finished", extra=self.extra)

    ## Function for registering a new parameter. Called by a sensor to provide information about what the sensor is measuring.
    #  @param self The python object self
    #  @param parameter_name Name of the prarameter, like speed, pressure, temperature, etc.
    #  @param plugin_name Name of the sensor providing the parameter. For hardware sonsors, name of the module, "config" for parameters from config file like rider_weight, or "compute" for parameters like "slope" calculated in the compute module
    #  @param value Current value of the parameter
    #  @param value_min Minimum observed value of the parameter, defaults to +infinity
    #  @param value_avg Average value of the parameter, defaults to not-a-number. The type of average is decided by the module setting the value.
    #  @param value_max Maximum observed value of the parameter, defaults to -infinity
    #  @param value_default Parameter default to this value after sensor reset
    #  @param raw_unit Internal unit, i.e. for odometer it's meter "m"
    #  @param unit Unit used to dispaly the parameter i.e. for odometer it might be km or mi (mile)
    #  @param units_allowed List of units allowed for the parametes. The units has to be covered in unit_converter module
    def register_parameter(self,
                           parameter_name,
                           plugin_name=None,
                           value=None,
                           value_min=numbers.INF,
                           value_avg=numbers.NAN,
                           value_max=numbers.INF_MIN,
                           value_default=None,
                           raw_unit=None,
                           unit=None,
                           units_allowed=list(),
                           required_by=list(),
                           force_notification=False,
                           reset=False):

        self.log.debug("Trying to register {} by {}".format(parameter_name, plugin_name), extra=self.extra)
        if unit is None:
            unit = raw_unit
        if unit is not None and units_allowed is None:
            units_allowed.append(unit)
        if parameter_name in self.parameters:
            if self.parameters[parameter_name]["plugin_name"] == plugin_name:
                self.log.debug("{} already registerd by the same sensor {}, probably update from config".format(parameter_name, plugin_name), extra=self.extra)
            elif self.parameters[parameter_name]["plugin_name"] is not None:
                self.log.critical("{} already registerd by sensor {}. Sensor {} request refused.".format(parameter_name, self.parameters[parameter_name]["plugin_name"], plugin_name), extra=self.extra)
                return
        else:
            if parameter_name in self.parameter_requests:
                required_by = self.parameter_requests[parameter_name]
                del self.parameter_requests[parameter_name]
            self.parameters[parameter_name] = dict(plugin_name=plugin_name,
                                                   time_stamp=0.0,
                                                   value=value,
                                                   value_min=value_min,
                                                   value_avg=value_avg,
                                                   value_max=value_max,
                                                   value_default=value_default,
                                                   raw_unit=raw_unit,
                                                   unit=unit,
                                                   units_allowed=units_allowed,
                                                   required_by=required_by,
                                                   force_notification=force_notification,
                                                   reset=False)
        #self.log.debug("after register_parameter {} is {}".format(parameter_name, self.parameters[parameter_name]), extra=self.extra)

    ## Function for requesting a parameter. Called by a sensor to request information abut changes of a parameter.
    #  @param self The python object self
    def request_parameter(self, parameter_name, plugin_name):
        self.log.debug("request_parameter called for {} by {}".format(parameter_name, plugin_name), extra=self.extra)
        if parameter_name in self.parameters:
            if plugin_name not in self.parameters[parameter_name]["required_by"]:
                self.parameters[parameter_name]["required_by"].append(plugin_name)
                self.parameters[parameter_name]["force_notification"] = True
                self.log.debug("{} added to required_by of {}".format(plugin_name, parameter_name), extra=self.extra)
        else:
            if parameter_name not in self.parameter_requests:
                self.parameter_requests[parameter_name] = list()
                self.parameter_requests[parameter_name].append(plugin_name)
        #self.log.debug("after request_parameter for {} parameter_requests is {}".format(parameter_name, self.parameter_requests), extra=self.extra)

    ## Update parameter with new content
    #  @param self The python object self
    #  @param parameter_name name of the parameter to be updated
    #  @param content dictionary with new content. All fileds from the content will be used, even if they are set to None
    def update_parameter(self, parameter, content):
        content["plugin_name"] = None
        self.log.debug("update parameter called for {}".format(parameter), extra=self.extra)
        if parameter not in self.parameters:
            self.register_parameter(parameter)
        self.parameters[parameter].update(content)
        self.parameters[parameter]["force_notification"] = True
        #self.log.debug("after update_parameter {} is {}".format(parameter, self.parameters[parameter]), extra=self.extra)

    def parameter_reset(self, parameter, reset_list):
        self.log.debug("reset request received for {}".format(parameter), extra=self.extra)
        self.log.debug("reset list: {}".format(reset_list), extra=self.extra)
        # Info for module responsible for the parameter that there was a reset
        self.parameters[parameter]['reset'] = True
        for suffix in reset_list:
            suffix = suffix.strip(' ')
            if suffix == '':
                self.parameters[parameter]['value'] = self.parameters[parameter]['value_default']
            elif suffix == 'min':
                self.parameters[parameter]['value_min'] = numbers.INF
            elif suffix == 'avg':
                self.parameters[parameter]['value_avg'] = numbers.NAN
            elif suffix == 'max':
                self.parameters[parameter]['value_max'] = numbers.INF_MIN

    ## Function for registering cairo context linked with a display. Only one plugin is allowed to register it
    #  @param self The python object self
    #  @param plugin_name Name of the plugin registering cairo context
    #  @param cairo_context Cairo context need to be registered by one of the plugins to allow display access
    def register_cairo_context(self, plugin_name, cairo_context):
        self.log.debug("Registering cairo context by {}".format(plugin_name), extra=self.extra)
        if self.render['owner'] is None:
            self.render['ctx'] = cairo_context
            self.render['owner'] = plugin_name
        else:
            self.log.critical("Can't register cairo context by {} as it's already registered by {}".format(plugin_name, self.render['owner']), extra=self.extra)

    ## Function for registering event queue. Only one plugin is allowed to register it
    #  @param self The python object self
    #  @param plugin_name Name of the plugin registering event queue
    #  @param event_queue queue instance, see https://docs.python.org/3.5/library/queue.html
    def register_event_queue(self, plugin_name, event_queue):
        self.log.debug("Registering event queue by {}".format(plugin_name), extra=self.extra)
        if self.event_queue_owner is None:
            self.event_queue = event_queue
            self.event_queue_owner = plugin_name
        else:
            self.log.critical("Can't register event queue by {} as it's already registered by {}".format(plugin_name, self.event_queue_owner), extra=self.extra)

    ## Function for registering input queue. Only one plugin is allowed to register it
    #  @param self The python object self
    #  @param plugin_name Name of the plugin registering input queue
    #  @param input_queue queue instance, see https://docs.python.org/3.5/library/queue.html
    def register_input_queue(self, plugin_name, input_queue):
        self.log.debug("Registering input queue by {}".format(plugin_name), extra=self.extra)
        if self.input_queue_owner is None:
            self.input_queue = input_queue
            self.input_queue_owner = plugin_name
        else:
            self.log.critical("Can't register input queue by {} as it's already registered by {}".format(plugin_name, self.input_queue_owner), extra=self.extra)
