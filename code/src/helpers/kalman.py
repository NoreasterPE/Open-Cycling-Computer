#!/usr/bin/python3
# -*- coding: utf-8 -*-
## @package kalman
#  Kalman filter module


class kalman():
    'Class for Kalman filter helper'
    ## @var extra
    # Module name used for logging and prefixing data
    extra = {'module_name': 'kalman'}

    def __init__(self, Q=None, R=None, P=None, P_previous=None, K=None):
        # FIXME Add detailed comments
        # R is the measurement noise covariance (sensor noise), Q is the process noise covariance
        # P, P_previous and K are self tuning
        if Q is not None:
            #self.Q = 0.02
            self.Q = Q
        else:
            self.Q = 0.02
        # Estimate of measurement variance, sensor noise
        if R is not None:
            #self.R = 1.0
            self.R = R
        else:
            self.R = 1.0
        # Error
        if P is not None:
            #self.P = 0.245657137142
            self.P = P
        else:
            self.P = 0.245657137142
        # First previous error
        if P_previous is not None:
            #self.P_previous = 0.325657137142
            self.P_previous = P_previous
        else:
            self.P_previous = 0.325657137142
        # First gain
        if K is not None:
            #self.K = 0.245657137142
            self.K = K
        else:
            self.K = 0.245657137142

    def set_initial_value(self, value_unfiltered):
        # First estimate
        self.value_estimate = value_unfiltered
        # First previous estimate
        self.value_estimate_previous = value_unfiltered
        # Value unfiltered aka raw measurement
        self.value_unfiltered = value_unfiltered

    def update_unfiltered_value(self, value_unfiltered):
        # Value unfiltered aka raw measurement
        self.value_unfiltered = value_unfiltered

    def update(self):
        # FIXME Add detailed commants
        z = self.value_unfiltered
        # Save previous value
        self.value_estimate_previous = self.value_estimate
        # Save previous error
        self.P_previous = self.P + self.Q
        # Calculate current gain
        self.K = self.P_previous / (self.P_previous + self.R)
        # Calculate new estimate
        self.value_estimate = self.value_estimate_previous + self.K * (z - self.value_estimate_previous)
        # Calculate new error estimate
        self.P = (1 - self.K) * self.P_previous
