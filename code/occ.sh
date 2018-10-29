#!/bin/sh
CONFIG='config/config.yaml'
LAYOUT='layouts/default.yaml'
HELPERS='src/helpers'
PYTHONPATH=$HELPERS python3 src/occ.py $CONFIG $LAYOUT

