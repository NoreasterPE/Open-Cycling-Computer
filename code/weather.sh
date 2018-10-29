#!/bin/sh
CONFIG='config/config_weather.yaml'
LAYOUT='layouts/weather.yaml'
HELPERS='src/helpers'
PYTHONPATH=$HELPERS python3 src/occ.py $CONFIG $LAYOUT

