#!/usr/bin/env python
#
# PyUSBtmc
# display_channel.py
#
# Copyright (c) 2011 Mike Hadmack
# Copyright (c) 2010 Matt Mets
# This code is distributed under the MIT license
import numpy
from matplotlib import pyplot
from pyusbtmc import RigolScope
""" Example program to plot the Y-T data from one scope channel
    derived from capture_channel_1.py but using new interface methods """
 
# Initialize our scope
scope = RigolScope("/dev/usbtmc0")
 
# Stop data acquisition
scope.stop()
    
# Grab the data from channel 1 
chan = 1
#scope.setWavePointsMode('NORM')
data = scope.getScaledWaveform(chan)

# Now, generate a time axis.
time = scope.getTimeAxis() 
 
# See if we should use a different time axis
if (time[599] < 1e-3):
    time = time * 1e6
    tUnit = "uS"
elif (time[599] < 1):
    time = time * 1e3
    tUnit = "mS"
else:
    tUnit = "S"
 
# Start data acquisition again, and put the scope back in local mode
scope.run()
scope.unlock()
scope.close()
 
# Plot the data
pyplot.plot(time, data)
pyplot.title("Oscilloscope Channel 1")
pyplot.ylabel("Voltage (V)")
pyplot.xlabel("Time (" + tUnit + ")")
pyplot.xlim(time[0], time[599])
pyplot.show()


