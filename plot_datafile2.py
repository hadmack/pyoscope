#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" plot_datafile.py
    Script to plot any number of oscilloscope data set files
    No file name specified = stdin
    
    To plot from stdin:
    echo myfile.dat | ./plot_datafile.py
    but you could pipe the output of any command with proper text format
    
    Add support for different scales for each channel as on scope"""
import numpy
import matplotlib.pyplot as pyplot
import sys

filenames = sys.argv[1:]

if len(filenames) == 0:
    filenames = [sys.stdin]

for filename in filenames:
    t,y1,y2 = numpy.genfromtxt(filename, unpack=True)
    t = t*1e6
    fig = pyplot.figure()
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twinx()
    
    p1, = ax1.plot(t,y1, 'b', label='Channel 1', linewidth=1.)
    p2, = ax2.plot(t,y2, 'r', label='Channel 2', linewidth=1.)
    
    #ax1.set_ylim([-0.002, 0.005])
    #ax2.set_ylim([-0.1, 1.0])
    
    ax1.set_xlabel('Time (usec)')
    ax1.set_ylabel('Channel 1 (Volts)', color=p1.get_color())
    ax2.set_ylabel('Channel 2 (Volts)', color=p2.get_color())
    
    
pyplot.show()

