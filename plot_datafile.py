#!/usr/bin/env python
""" plot_datafile.py
    Script to plot any number of oscilloscope data set files
    No file name specified = stdin
    
    To plot from stdin:
    echo myfile.dat | ./plot_datafile.py
    but you could pipe the output of any command with proper text format"""
import numpy
import matplotlib.pyplot as pyplot
import sys

filenames = sys.argv[1:]

if len(filenames) == 0:
    filenames = [sys.stdin]

for filename in filenames:
    t,y1,y2 = numpy.genfromtxt(filename, unpack=True)
    pyplot.plot(t,y1)
    pyplot.plot(t,y2)

pyplot.show()

