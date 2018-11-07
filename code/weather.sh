#!/bin/sh
PWD=$(pwd)
HELPERS=$PWD'/src/helpers'
PYTHONPATH=$HELPERS python3 src/weather.py
