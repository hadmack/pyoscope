#!/usr/bin/python
import numpy
import matplotlib.pyplot as plot

from pyusbtmc import RigolScope
 
""" Example program to plot the Y-T data from one scope channel
    derived from capture_channel_1.py but using new interface methods"""
 
# Initialize our scope
scope = RigolScope("/dev/usbtmc0")
 
# Stop data acquisition
scope.stop()
 
# Setup capture mode
#scope.write(":WAV:POIN:MODE NOR")

# Grab the data from channel 1 
chan = 1
data = scope.readData(chan)

# Get the voltage scale
voltscale  = scope.getVoltScale(chan)
 
# And the voltage offset
voltoffset = scope.getVoltScale(chan)
 
# Walk through the data, and map it to actual voltages
# First invert the data (ya rly)
data = data * -1 + 255
 
# Now, we know from experimentation that the scope display range is actually
# 30-229.  So shift by 130 - the voltage offset in counts, then scale to
# get the actual voltage.
data = (data - 130.0 - voltoffset/voltscale*25) / 25 * voltscale
 
# Get the timescale
#timescale  = scope.getTimeScale()
 
# Get the timescale offset
#timeoffset = scope.getTimeOffset()
 
# Now, generate a time axis.  The scope display range is 0-600, with 300 being
# time zero.
#time = numpy.arange(-300.0/50*timescale, 300.0/50*timescale, timescale/50.0)
time = scope.getTimeAxis() 
# If we generated too many points due to overflow, crop the length of time.
#if (time.size > data.size):
#    time = time[0:600:1]
 
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
scope.forceTrigger()
scope.close()
 
# Plot the data
plot.plot(time, data)
plot.title("Oscilloscope Channel 1")
plot.ylabel("Voltage (V)")
plot.xlabel("Time (" + tUnit + ")")
plot.xlim(time[0], time[599])
plot.show()


