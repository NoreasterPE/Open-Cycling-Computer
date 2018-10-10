#!/usr/bin/python3
## @package sensors
#  Sensors module. Responsible for connecting to, starting and stopping sensors. Currently used sensors are:
#  BLE heart rate
#  BLE speed & cadence sensor
#  GPS (MTK3339) - [disabled]
#  BMP183 pressure & temperature sensor

#from bluepy.btle import BTLEException
import bmp183
import compute
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


## Class for handling starting/stopping sensors in separate threads
class sensors(threading.Thread, metaclass=Singleton):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'sensors'}

    ## The constructor
    #  @param self The python object self
    #  @param occ OCC instance
    def __init__(self):
        super().__init__()
        ## @var l
        # System logger handle
        self.log = logging.getLogger('system')
        ## @var occ
        # OCC Handle
        #self.occ = occ
        ## @var sensors
        # Dict with sensor instances
        self.sensors = dict()
        ## @var parameters
        # Dict with parameters
        self.parameters = dict()
        ## @var parameter_requests
        # Dict with parameters requested by a module
        self.parameter_requests = dict()
        self.sensors = dict(ble_sc=None, ble_hr=None, bmp183=None)
        ## @var required
        # Dict with parameters required by sensors
        #self.required = dict()
        ## @var required_previous
        # Dict with parameters required by sensors from the previous loop cycle
        #self.required_previous = dict()
        ## @var simulate
        # Local copy of simulate variable from OCC
        #self.simulate = occ.get_simulate()
        self.register_parameter("ble_host_state", self.extra["module_name"], value=0)
        ## @var no_of_connected
        # Number of connected BLE devices
        self.no_of_connected = 0
        ## @var connecting
        # Indicates if host is currently trying to establish connection
        self.connecting = False
        ## @var connected
        # Dict keeping track of which sensor is connected
        self.connected = dict(ble_sc=False, ble_hr=False, bmp183=False)

    ## Functon that initialises all sensors
    #  @param self The python object self
    def initialise_sensors(self):
        #FIXME make initialisation the same for all sensors

        self.sensors['compute'] = compute.compute()
        #self.required["compute"] = self.sensors['compute'].get_required()
        #self.required_previous["compute"] = self.required['compute']
        #self.log.info("Initialising bmp183 sensor", extra=self.extra)
        #try:
        self.sensors['bmp183'] = bmp183.bmp183(False)
        #self.required["bmp183"] = self.sensors['bmp183'].get_required()
        #self.required_previous["bmp183"] = self.sensors['bmp183'].get_required()
        #self.connected['bmp183'] = True
        #except IOError:
        #    self.connected['bmp183'] = None

        import ble_hr
        self.sensors['ble_hr'] = ble_hr.ble_hr()
        #self.required["ble_hr"] = self.sensors['ble_hr'].get_required()
        #self.required_previous["ble_hr"] = self.required['ble_hr']

        import ble_sc
        self.sensors['ble_sc'] = ble_sc.ble_sc()
        #self.required["ble_sc"] = self.sensors['ble_sc'].get_required()
        #self.required_previous["ble_sc"] = self.required['ble_sc']

    ## Main loop of sensors module. Constantly tries to reconnect with BLE devices
    #  @param self The python object self
    def run(self):
        self.log.debug("run started", extra=self.extra)
        self.initialise_sensors()
        #self.init_data_from_ride_parameters()

        self.log.debug("Starting compute thread", extra=self.extra)
        self.sensors['compute'].start()

        self.log.debug("Starting ble_hr thread", extra=self.extra)
        self.sensors['ble_hr'].start()

        self.log.debug("Starting ble_sc thread", extra=self.extra)
        self.sensors['ble_sc'].start()

        self.log.debug("Starting bmp183 thread", extra=self.extra)
        self.sensors['bmp183'].start()

        self.running = True
        #self.previous_parameters = dict()
        self.previous_parameters = self.parameters.copy()
        while self.running:
            self.log.debug("running...", extra=self.extra)
            self.previous_parameters = self.parameters.copy()
            time.sleep(1.0)
            notify = list()
            for parameter, content in self.parameters.items():
                if (self.previous_parameters[parameter]["force_notification"] or
                   self.previous_parameters[parameter]["value"] != content["value"]):
                    self.parameters[parameter]["force_notification"] = False
                    if content["required_by"] is not None:
                        for m in content["required_by"]:
                            notify.append(m)
            for module in notify:
                try:
                    self.sensors[module].notification()
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
        for name in self.sensors:
            try:
                s = self.sensors[name].is_connected()
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

    ## Helper function for getting sensor handle
    #  @param self The python object self
    #def get_sensor(self, name):
    #    self.log.debug('get_sensor called for {}'.format(name), extra=self.extra)
    #    if name in self.sensors:
    #        return self.sensors[name]
    #    else:
    #        self.log.debug("Sensor {} not ready or doesn't exist".format(name), extra=self.extra)
    #        return None

    ## The destructor
    #  @param self The python object self
    def __del__(self):
        self.stop()

    ## Function stopping all sensors. Called by the destructor
    #  @param self The python object self
    def stop(self):
        self.log.debug("stop started", extra=self.extra)
        self.running = False
        for s in self.sensors:
            self.connected[s] = False
            self.log.debug("Stopping {} thread".format(s), extra=self.extra)
            try:
                self.sensors[s].stop()
                self.log.debug("Stopped {} thread".format(s), extra=self.extra)
            except AttributeError:
                pass
            self.sensors[s] = None
        self.log.debug("stop finished", extra=self.extra)

    ## Function for registering a new parameter. Called by a sensor to provide information about what the sensor is measuring.
    #  @param self The python object self
    #  @param parameter_name Name of the prarameter, like speed, pressure, temperature, etc.
    #  @param sensor_name Name of the sensor providing the parameter. For hardware sonsors, name of the module, "config" for parameters from config file like rider_weight, or "compute" for parameters like "slope" calculated in the compute module
    #  @param value Current value of the parameter
    #  @param value_min Minimum observed value of the parameter, defaults to +infinity
    #  @param value_avg Average value of the parameter, defaults to not-a-number. The type of average is decided by the module setting the value.
    #  @param value_max Maximum observed value of the parameter, defaults to -infinity
    #  @param value_defaulti Parameter default to this value after sensor reset
    #  @param raw_unit Internal unit, i.e. for odometer it's meter "m"
    #  @param unit Unit used to dispaly the parameter i.e. for odometer it might be km or mi (mile)
    #  @param units_allowed List of units allowed for the parametes. The units has to be covered in unit_converter module
    def register_parameter(self,
                           parameter_name,
                           sensor_name=None,
                           value=None,
                           value_min=numbers.INF,
                           value_avg=numbers.NAN,
                           value_max=numbers.INF_MIN,
                           value_default=None,
                           raw_unit=None,
                           unit=None,
                           units_allowed=list(),
                           required_by=list(),
                           force_notification=False):

        self.log.debug("Trying to register {} by {}".format(parameter_name, sensor_name), extra=self.extra)
        if unit is None:
            unit = raw_unit
        if unit is not None and units_allowed is None:
            units_allowed.append(unit)
        if parameter_name in self.parameters:
            if self.parameters[parameter_name]["sensor_name"] == sensor_name:
                self.log.debug("{} already registerd by the same sensor {}, probably update from config".format(parameter_name, sensor_name), extra=self.extra)
            elif self.parameters[parameter_name]["sensor_name"] is not None:
                self.log.critical("{} already registerd by sensor {}. Sensor {} request refused.".format(parameter_name, self.parameters[parameter_name]["sensor_name"], sensor_name), extra=self.extra)
                return
#            if self.parameters[parameter_name]["sensor_name"] is None:
#                #De-register, but store the "required by" and "unit" field.
#                required_by = self.parameters[parameter_name]["required_by"]
#                #Store the "unit" field only if registering call didn't set it.
#                if unit is None:
#                    unit = self.parameters[parameter_name]["unit"]
#                del self.parameters[parameter_name]
        else:
            if parameter_name in self.parameter_requests:
                required_by = self.parameter_requests[parameter_name]
                del self.parameter_requests[parameter_name]
            self.parameters[parameter_name] = dict(sensor_name=sensor_name,
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
                                                   force_notification=force_notification)
        self.log.debug("after register_parameter {} is {}".format(parameter_name, self.parameters[parameter_name]), extra=self.extra)

    ## Function for requesting a parameter. Called by a sensor to request information abut changes of a parameter.
    #  @param self The python object self
    def request_parameter(self, parameter_name, sensor_name):
        self.log.debug("request_parameter called for {} by {}".format(parameter_name, sensor_name), extra=self.extra)
        if parameter_name in self.parameters:
            if sensor_name not in self.parameters[parameter_name]["required_by"]:
                self.parameters[parameter_name]["required_by"].append(sensor_name)
                self.parameters[parameter_name]["force_notification"] = True
                self.log.debug("{} added to required_by of {}".format(sensor_name, parameter_name), extra=self.extra)
        else:
            if parameter_name not in self.parameter_requests:
                self.parameter_requests[parameter_name] = list()
                self.parameter_requests[parameter_name].append(sensor_name)
        self.log.debug("after request_parameter for {} parameter_requests is {}".format(parameter_name, self.parameter_requests), extra=self.extra)

    ## Update parameter with new content
    #  @param self The python object self
    #  @param parameter_name name of the parameter to be updated
    #  @param content dictionary with new content. All fileds from the content will be used, even if they are set to None
    def update_parameter(self, parameter_name, content):
        content["sensor_name"] = None
        self.log.debug("update parameter called for {}".format(parameter_name), extra=self.extra)
        if parameter_name not in self.parameters:
            self.register_parameter(parameter_name)
        self.parameters[parameter_name].update(content)
        self.parameters[parameter_name]["force_notification"] = True
        self.log.debug("after update_parameter {} is {}".format(parameter_name, self.parameters[parameter_name]), extra=self.extra)
