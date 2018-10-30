#!/bin/sh
PWD=$(pwd)
CONFIG=$PWD'/config/config.yaml'
LAYOUT=$PWD'/layouts/default.yaml'
FONTS=$PWD'/fonts/'
HELPERS=$PWD'/src/helpers'
PYTHONPATH=$HELPERS python3 src/occ.py $CONFIG $LAYOUT $FONTS

