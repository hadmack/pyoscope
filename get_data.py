#!/usr/bin/env python
#
# PyUSBtmc
# get_data.py
#
# Copyright (c) 2011 Mike Hadmack
# This code is distributed under the MIT license
import numpy
import sys
from matplotlib import pyplot
from pyusbtmc import RigolScope
""" Capture data from Rigol oscilloscope and write to a file 
    usage: python save_channel.py <filename>
    if filename is not given STDOUT will be used"""

try:
    filename = sys.argv[1]
except:
    filename = ""

print filename
scope = RigolScope("/dev/usbtmc0")
scope.grabData()
scope.writeWaveformToFile(filename)
scope.close()
