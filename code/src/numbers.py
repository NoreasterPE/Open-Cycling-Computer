#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package numbers
#  Helper module with number definitions

import math

## @var INF_MIN
# helper variable, minus infinity
INF_MIN = float("-inf")

## @var INF
# helper variable, infinity
INF = float("inf")

## @var NAN
# helper variable, not-a-number
NAN = float("nan")


def sanitise(value):
    if value == "-0":
        value = "0"
    try:
        if (math.isinf(float(value)) or
                math.isnan(float(value))):
            value = '-'
    except (ValueError, TypeError):
        #Don't deal with invalid types or values
        pass
    return value
