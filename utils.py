#!/usr/bin/env python
# encoding: utf-8
#===========================================================
#
# utils.py
#
# 12-Sept-2011
# M. Hadmack (michael.hadmack@gmail.com)
#
# automatic file naming tools
#
# Note that this is also part of the fel_utils module and
# only duplicated here as a backup
#===========================================================
import time
import os
import sys

def makeFileName():
    timestring = time.strftime("%H%M%S")
    return timestring

def makeDataFilePath(root="/var/local/data", subdir="scope"):
    datestring = time.strftime("%y%m%d")

    fileroot = os.path.join(root, datestring, subdir)
    filename = makeFileName()

    if not os.path.exists(fileroot):
        os.makedirs(fileroot)

    filepath = os.path.join(fileroot, filename)
    return filepath

