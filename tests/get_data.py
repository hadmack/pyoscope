#!/usr/bin/env python
#
# PyUSBtmc
# get_data.py
#
# Copyright (c) 2011 Mike Hadmack
# This code is distributed under the MIT license
import numpy
import sys
import os
from matplotlib import pyplot
sys.path.append(os.path.expanduser('~/Source'))
sys.path.append(os.path.expanduser('~/src'))
sys.path.append('/var/local/src')
from pyoscope import RigolScope
from pyoscope import Waverunner
from pyoscope import makeDataFilePath
""" Capture data from Rigol oscilloscope and write to a file 
    usage: python save_channel.py <filename>
    if filename is not given STDOUT will be used"""

SCOPE_ADDRESS = 'nigpib1'

try:
    filename = sys.argv[1]
except:
    filename = makeDataFilePath()

if filename == "--help":
    print """Usage: 1%s [filename]\n   Reads both traces from oscilloscope and writes as ASCII tabular data to filename.  If no filename is given the program outputs to STDOUT.  STDOUT can be directed into a file or piped into another application.  For example:\n    1%s myfile\n    1%s > myfile\n    1%s | ./plot_data.py"""%sys.argv[0]
    sys.exit(1)

print filename
#scope = RigolScope("/dev/usbtmc0")
scope = Waverunner(SCOPE_ADDRESS)
scope.grabData()
scope.writeWaveformToFile(filename)
scope.close()

