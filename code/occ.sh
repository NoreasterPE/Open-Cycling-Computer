#!/bin/sh
# Script starting OCC

PWD=$(pwd)

CONFIG=$PWD'/config/config.yaml'
RIDE_LOG_CONFIG=$PWD'/config/ride_log_config.yaml'
LAYOUT=$PWD'/layouts/default.yaml'
FONTS=$PWD'/fonts/'
HELPERS=$PWD'/src/helpers'

PYTHONPATH=$HELPERS python3 src/occ.py $CONFIG $RIDE_LOG_CONFIG $LAYOUT $FONTS

