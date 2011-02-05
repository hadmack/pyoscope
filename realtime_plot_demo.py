#!/usr/bin/python
''' realtime_plot_demo.py
    Realtime plot of both channels
    This is a fork of realtime_chart.py to use the newer RigolScope interface'''
import numpy
import matplotlib.pyplot as plot
import time
from pyusbtmc import RigolScope

# Initialize our scope
scope = RigolScope("/dev/usbtmc0")

# Turn on interactive plotting
plot.ion()

while 1:  # How can this be broken other than ^C?
    # introduce a delay so that a break is recognized?
    time.sleep(0.1)
    
    data1 = scope.getScaledWaveform(1)
    data2 = scope.getScaledWaveform(2)
    t = scope.getTimeAxis()

    # Start data acquisition again, and put the scope back in local mode
    #test.write(":KEY:FORC")
    scope.forceTrigger()
    
    # Plot the data
    plot.clf()  # Clear current plot figure
    plot.plot(t, data1)
    plot.plot(t, data2)
    plot.title("Oscilloscope data")
    plot.ylabel("Voltage (V)")
    plot.xlabel("Time (s)")
    plot.xlim(t[0], t[599])
    # need to somehow supress the vertical autoscaling. 
    # Maybe a button to autoscale on demand? 
    plot.draw()

