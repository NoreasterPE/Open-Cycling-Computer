#!/bin/bash

echo "Registered parameters:"
git grep register_parameter | grep -v pyplum.py | sed -s "s/code\/src\///" | sed -s "s/self.pm.register_parameter(\"//" | sed -s "s/\"\, self.extra\[\"module_name\"\].*//" | sed -s "s/self.sensors.register_parameter(\"//" | grep -v def | grep -v 'self\.log'

echo "Requested parameters:"
git grep request_parameter | grep -v pyplum.py | sed -s "s/code\/src\///" | sed -s "s/self.pm.request_parameter(\"//" | sed -s "s/\"\, self.extra\[\"module_name\"\].*//" | grep -v def | grep -v 'self\.log'

echo "Registered input queue:"
git grep register_input_queue | grep -v pyplum.py | sed -s "s/code\/src\///" | sed -s "s/self.pm.register_input_queue.*.//" | sed -s "s/\"\, self.extra\[\"module_name\"\].*//" | grep -v def | grep -v 'self\.log'

echo "Registered event queue:"
git grep register_event_queue | grep -v pyplum.py | sed -s "s/code\/src\///" | sed -s "s/self.pm.register_event_queue.*//" | sed -s "s/\"\, self.extra\[\"module_name\"\].*//" | grep -v def | grep -v 'self\.log'
