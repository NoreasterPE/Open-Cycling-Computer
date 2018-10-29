#!/bin/bash

echo "Registered parameters:"
git grep register_parameter | grep -v sensors.py | sed -s "s/code\/src\///" | sed -s "s/self.s.register_parameter(\"//" | sed -s "s/\"\, self.extra\[\"module_name\"\].*//" | sed -s "s/self.sensors.register_parameter(\"//"

echo "Requested parameters:"
git grep request_parameter | grep -v sensors.py | sed -s "s/code\/src\///" | sed -s "s/self.s.request_parameter(\"//" | sed -s "s/\"\, self.extra\[\"module_name\"\].*//"
