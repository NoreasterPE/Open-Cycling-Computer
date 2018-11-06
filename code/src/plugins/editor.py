#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package editor
#  Convinience plugin with edior functions

import plugin
import pyplum
import time
import unit_converter


## Convinience plugin with edior functions
class editor(plugin.plugin):
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': __qualname__}

    def __init__(self):
        # Run init for super class
        super().__init__()
        self.fields = dict()
        self.pm = pyplum.pyplum()
        self.uc = unit_converter.unit_converter()

    def run(self):
        # This plugin doesn't need to run in background in a separate thread
        pass

    def set_up(self, fields):
        self.fields = fields

    def next_item(self):
        index = self.fields["index"]
        index += 1
        p = self.fields["parameter"]
        value_list = self.pm.parameters[p]["value_list"]
        self.slice_list_elements(value_list, index)
        if index > len(self.pm.parameters[p]["value_list"]) - 1:
            self.fields["index"] = 0
        else:
            self.fields["index"] = index

    def previous_item(self):
        index = self.fields["index"]
        index -= 1
        p = self.fields["parameter"]
        value_list = self.pm.parameters[p]["value_list"]
        self.slice_list_elements(value_list, index)
        if index < 0:
            self.fields["index"] = len(self.pm.parameters[p]["value_list"]) - 1
        else:
            self.fields["index"] = index

    def decrease_digit(self):
        u = self.fields["value"]
        i = self.fields["index"]
        ui = u[i]
        if str.isdigit(ui):
            if ui == "0":
                ui = "9"
            else:
                ui = format(int(ui) - 1)
        elif str.isupper(ui):
            ui = format(chr(ord(ui) - 1))
            if not str.isalpha(ui):
                ui = "Z"
        else:
            # Not a letter or digit, ignore
            pass
        un = u[:i] + ui + u[i + 1:]
        self.fields["value"] = un

    def increase_digit(self):
        u = self.fields["value"]
        i = self.fields["index"]
        ui = u[i]
        if str.isdigit(ui):
            if ui == "9":
                ui = "0"
            else:
                ui = format(int(ui) + 1)
        elif str.isupper(ui):
            ui = format(chr(ord(ui) + 1))
            if not str.isalpha(ui):
                ui = "A"
        else:
            # Not a capital letter or digit, ignore
            pass
        un = u[:i] + ui + u[i + 1:]
        self.fields["value"] = un

    def next_char(self):
        u = self.fields["value"]
        i = self.fields["index"]
        strip_zero = True
        try:
            # Preserve leading zero if the value is less than 1.0
            if float(u) < 1.0:
                strip_zero = False
        except (TypeError, ValueError):
            pass
        if u[0] == '0' and strip_zero:
            u = u[1:]
            self.fields["value"] = u
        else:
            i += 1
        le = len(u) - 1
        if i > le:
            i = le
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i += 1
        self.fields["index"] = i

    def previous_char(self):
        u = self.fields["value"]
        i = self.fields["index"]
        i -= 1
        if i < 0:
            i = 0
            uv = "0" + u
            self.fields["value"] = uv
        else:
            ui = u[i]
            # FIXME localisation points to be used here
            if (ui == ".") or (ui == ","):
                i -= 1
        self.fields["index"] = i

    def slice_list_elements(self, a_list, index):
        list_len = len(a_list)
        circular_list_slice = (a_list * 3)[index + list_len - 1:index + list_len + 2]
        self.fields["previous_list_element"] = circular_list_slice[0]
        self.fields["value"] = circular_list_slice[1]
        self.fields["next_list_element"] = circular_list_slice[2]

    def change_unit(self, direction):
        # direction to be 1 (next) or 0 (previous)
        variable = self.fields["parameter"]
        variable_unit = self.fields["unit"]
        variable_value = self.fields["value"]
        current_unit_index = self.pm.parameters[self.fields["parameter"]]["units_allowed"].index(variable_unit)
        self.log.debug("variable: {} units_allowed: {}".format(variable, self.pm.parameters[self.fields["parameter"]]["units_allowed"]), extra=self.extra)
        if direction == 'next':
            try:
                next_unit = self.pm.parameters[self.fields["parameter"]]["units_allowed"][current_unit_index + 1]
            except IndexError:
                next_unit = self.pm.parameters[self.fields["parameter"]]["units_allowed"][0]
        elif direction == 'prev':
            try:
                next_unit = self.pm.parameters[self.fields["parameter"]]["units_allowed"][current_unit_index - 1]
            except IndexError:
                next_unit = self.pm.parameters[self.fields["parameter"]]["units_allowed"][-1]
        else:
            self.log.error("Can't change unit in direction {}".format(direction), extra=self.extra)
        self.fields["unit"] = next_unit
        self.fields["value"] = variable_value

    def next_unit(self):
        self.change_unit('next')

    def previous_unit(self):
        self.change_unit('prev')

    def cancel_edit(self):
        self.fields = None
        self.finish_editing()

    def accept_edit(self):
        self.log.debug("accept_edit started", extra=self.extra)
        parameter = self.fields["parameter"]
        parameter_unit = self.fields["unit"]
        parameter_value = self.fields["value"]
        self.log.debug("parameter: {}, parameter_unit: {}, parameter_value: {}".format(parameter, parameter_unit, parameter_value), extra=self.extra)
        if self.fields["editor"] == "editor_units":
            self.pm.parameters[parameter]["unit"] = parameter_unit
        if self.fields["editor"] == "editor_numbers":
            unit_raw = self.pm.parameters[parameter]["raw_unit"]
            value = self.uc.convert(float(parameter_value), parameter_unit, unit_raw)
            self.pm.parameters[parameter]["value"] = float(value)
        if self.fields["editor"] == "editor_string" or \
                self.fields["editor"] == "editor_list":
            self.pm.parameters[parameter]["value"] = parameter_value
#        if elf.fields["editor"] == "ble_selector":
#            (name, addr, dev_type) = parameter_value
#            self.pm.set_ble_device(name, addr, dev_type)
        self.pm.parameters[parameter]["time_stamp"] = time.time()
        self.log.debug("accept_edit finished", extra=self.extra)
        self.fields = None
        self.finish_editing()

    def finish_editing(self):
        if self.pm.event_queue is not None:
            self.pm.event_queue.put(('show_main_page',))
