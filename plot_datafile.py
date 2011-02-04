#!/usr/bin/python
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

