#!/usr/bin/env python
#
# PyUSBtmc
# display_channel.py
#
# Copyright (c) 2011 Mike Hadmack
# Copyright (c) 2010 Matt Mets
# This code is distributed under the MIT license
''' realtime_plot_demo.py
    Realtime plot of both channels
    This is a fork of realtime_chart.py to use the newer RigolScope interface
    
    NOTE:  This code has not yet been adapted or tested with pyoscope
'''
import numpy
from matplotlib import pyplot
from pyusbtmc import RigolScope
import time

# Initialize our scope
scope = RigolScope("/dev/usbtmc0")

# Turn on interactive plotting
pyplot.ion()

while 1:  # How can this loop be broken other than ^C?
    # introduce a delay so that a break is recognized?
    time.sleep(0.1)
    
    scope.grabData()
    data1 = scope.getScaledWaveform(1)
    data2 = scope.getScaledWaveform(2)
    t = scope.getTimeAxis()

    # Start data acquisition again, and put the scope back in local mode
    scope.forceTrigger()
    
    # Plot the data
    pyplot.clf()  # Clear current plot figure
    pyplot.plot(t, data1)
    pyplot.plot(t, data2)
    pyplot.title("Oscilloscope data")
    pyplot.ylabel("Voltage (V)")
    pyplot.xlabel("Time (s)")
    pyplot.xlim(t[0], t[599])
    # need to somehow supress the vertical autoscaling. 
    # Maybe a button to autoscale on demand? 
    pyplot.draw()

