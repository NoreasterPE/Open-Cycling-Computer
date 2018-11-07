#!/bin/sh
PWD=$(pwd)
CONFIG=$PWD'/config/config_weather.yaml'
LOG_CONFIG=$PWD'/config/weather_log.yaml'
LAYOUT=$PWD'/layouts/weather.yaml'
FONTS=$PWD'/fonts/'
HELPERS=$PWD'/src/helpers'
PYTHONPATH=$HELPERS python3 src/weather.py $CONFIG $LOG_CONFIG $LAYOUT $FONTS
