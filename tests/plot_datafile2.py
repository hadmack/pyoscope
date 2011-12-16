#!/usr/bin/env python
# -*- coding: utf-8 -*-
#===========================================================
#
# This file is part of PyOscope
#
# plot_datafile2.py
# 06-Sept-2011
#
# Copyright (c) 2011 Michael Hadmack (michael.hadmack@gmail.com)
# This code is distributed under the MIT license
#
# Script to plot any number of oscilloscope data set files
# No file name specified = stdin
#    
# To plot from stdin:
# echo myfile.dat | ./plot_datafile.py
# but you could pipe the output of any command with proper text format
#    
# Add support for different scales for each channel as on scope
#
#===========================================================
import numpy
import matplotlib.pyplot as pyplot
import sys
from optparse import OptionParser

usage = "usage: %prog [options] [datafile]\nIf datafile is not supplied STDIN is used."
parser = OptionParser(usage=usage)
parser.add_option("-1", "--channel1", action="store_true", default=False,
                          help="Plot channel 1 data")
parser.add_option("-2", "--channel2", action="store_true", default=False,
                          help="Plot channel 2 data")
                          
(options, args) = parser.parse_args()

# if no channels are selected turn on both
if not (options.channel1 | options.channel2):
    options.channel1=True
    options.channel2=True

print options

if len(args) > 1:
    parser.print_help()
    sys.exit(1)

if len(args) == 0:
    filename = sys.stdin
else:
    filename = args[0]
    
t,y1,y2 = numpy.genfromtxt(filename, unpack=True)
t = t*1e6
fig = pyplot.figure()

if options.channel1:
    ax1 = fig.add_subplot(111)
    p1, = ax1.plot(t,y1, 'b', label='Channel 1', linewidth=1.)
    ax1.set_ylabel('Channel 1 (Volts)', color=p1.get_color())
    if options.channel2:
        ax2 = ax1.twinx()
else:
    # Set up axes with channel2 for the primary
    ax2 = fig.add_subplot(111)
    ax1 = ax2

#ax1.set_ylim([-0.002, 0.005])
#ax2.set_ylim([-0.1, 1.0])

ax1.set_xlabel('Time (usec)')


if options.channel2:
    
    p2, = ax2.plot(t,y2, 'r', label='Channel 2', linewidth=1.)
    ax2.set_ylabel('Channel 2 (Volts)', color=p2.get_color())

   
pyplot.show()

