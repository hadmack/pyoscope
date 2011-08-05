#!/usr/bin/env python
#
# PyUSBtmc
# 
# Berkely Nucleonics Model 645 Arbitrary Waveform Generator TMC interface
#
# Copyright (c) 2011 Mike Hadmack
# This code is distributed under the MIT license
from pyusbtmc import usbtmc
import numpy

class WaveformGenerator(usbtmc):
    """Class to control a BNC 645 Arbitrary Waveform Generator"""
    def __init__(self, device):
        usbtmc.__init__(self, device)
        self.name = self.getName()
        print "# Connected to: " + self.name
        
        self.write("*RST;*CLS")  # Reset instrument
        self.set50OhmOutput(False)  # Set output to high impedance
        self.write("FORM:BORD SWAP")  # Set for little endian byte order

    def outputOn(self):
	    self.write("OUTPut ON");
    
    def outputOff(self):
	    self.write("OUTPut OFF");

    def set50OhmOutput(self,on):
        if on : self.write("OUTPut:LOAD 50")
        else  : self.write("OUTPut:LOAD INF")

    def setFunction(self, func):
        if   func == "SINE"   : self.write("FUNCtion SINusoid")
        elif func == "SQUARE" : self.write("FUNCtion SQUare")
        elif func == "PULSE"  :	self.write("FUNCtion PULSe")
        elif func == "USER"   :	self.write("FUNCtion USER"); self.write("FUNC:USER VOLATILE")

    def setupExtTrigger(self):
	    self.write("TRIGger:SOURce EXTernal")
	    self.write("BURSt:MODE TRIGgered")
	    self.write("BURSt:STATe ON")

    def sendWaveformData(self, data, duration, voltageMin, voltageMax):
        count = len(data)
        buf = "DATA VOLATILE"
        for x in data:
            buf += ", " + str(x)
        print buf
        self.write(buf)
        
        
def main():
    wg = WaveformGenerator("/dev/usbtmc0")
    wg.outputOff()
    wg.setupExtTrigger()
    
    # Send data
    data = numpy.array([1.0, -1.0, 0.5, -0.5, 0.25, -0.25])
    wg.sendWaveformData(data, 10e-6,-1.0, 1.0)
    
    wg.setFunction("USER")
    wg.outputOn()

if __name__ == "__main__":
    main()
