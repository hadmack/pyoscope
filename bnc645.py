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
import sys
DATA_MARGIN = 0.010 #VOLTS  keep the AWG max and min at least this far from the mean value of data

class WaveformGenerator(usbtmc):
    """Class to control a BNC 645 Arbitrary Waveform Generator"""
    def __init__(self, device, reset=True):
        usbtmc.__init__(self, device)
        self.name = self.getName()
        print "# Connected to: " + self.name
        
        if reset:
            self.sendReset()
        
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
	    
    def setFrequency(self, freq):
        self.write("FREQuency %.3f"%freq)
    
    def setAmplitude(self, volts):
        self.write("VOLTage %.3f"%volts)
        
    def setOffset(self, volts):
        self.write("VOLTage:OFFSet %.3f"%volts)
        
    def setVoltageLow(self,low):
        self.write("VOLTage:LOW %.3f"%low)
        
    def setVoltageHigh(self,high):
        self.write("VOLTage:HIGH %.3f"%high)
        
    def setVoltageRange(self, vMin, vMax):
        self.setVoltageHigh(vMax)
        self.setVoltageLow(vMin)
    
    def sendWaveformData(self, data, duration, vMin, vMax):
        '''Loads an array of voltage points into waveform generator.
           duration in seconds is the length of the full data set
           vMin, vMax limit the allowed range of data.  
           Any data out of range is clipped to these limits.'''
        count = len(data)
        block = []
        dMin = min(data)
        dMax = max(data)
        dMean = numpy.mean(data)
        if dMax < (dMean + DATA_MARGIN):
            dMax = dMean + DATA_MARGIN
        if dMin > (dMean - DATA_MARGIN):
            dMin = dMean - DATA_MARGIN 
        dRange = dMax - dMin
        for v in data:
            if v < vMin:
                v = vMin
            elif v > vMax:
                v = vMax
            x = 2.0*(v - dMin)/dRange - 1.0
            b = int(8191*x)
            block.append(b)
        
        self.sendBinaryBlock(block)
        self.setFrequency(1./duration)
        self.setVoltageRange(dMin, dMax)
        
    def sendWaveformData2(self, data, duration, vMin, vMax):
        '''Loads an array of voltage points into waveform generator.
           duration in seconds is the length of the full data set
           vMin, vMax limit the allowed range of data.  
           Any data out of range is clipped to these limits.'''
        count = len(data)
        block = []
        dMin = min(data)
        dMax = max(data)
        dMean = numpy.mean(data)
        if dMax < (dMean + DATA_MARGIN):
            dMax = dMean + DATA_MARGIN
        if dMin > (dMean - DATA_MARGIN):
            dMin = dMean - DATA_MARGIN 
        dRange = dMax - dMin
        for v in data:
            if v < vMin:
                v = vMin
            elif v > vMax:
                v = vMax
            x = 2.0*(v - dMin)/dRange - 1.0
            b = int(8191*x)
            block.append(b)
        
        self.sendDataBlock(block)
        self.setFrequency(1./duration)
        self.setVoltageRange(dMin, dMax)
           
    def sendDataBlock(self, block):
        count = len(block)
        buf = "DATA:DAC VOLATILE"
        for x in block:
            buf += ", " + str(x)
        #print buf
        self.write(buf)
        
    def sendFloatDataBlock(self, block):
        count = len(block)
        buf = "DATA VOLATILE"
        for x in block:
            buf += ", %.4f"%x
        #print buf
        self.write(buf)
        #f = open("testbuffer",'w')
        #f.write(buf)   
        
    def sendBinaryBlock(self, block):
        data = numpy.array(block, dtype='h')
        count = data.size
        strBytes = str(data.nbytes)
        nchars = len(strBytes)  # count number of characters in numBytes as string
        if nchars%2 == 0:   # alignment character for even command length
            align = ""
        else:
            align = " "
            
        sCmd = "DATA:DAC VOLATILE,%s#%d%d"%(align,nchars,data.nbytes)
        buf = sCmd + data.tostring()
        self.write(buf)
        
    def sendReset(self):
        self.write("*RST;*CLS")
        self.set50OhmOutput(False)  # Set output to high impedance
        self.write("FORM:BORD SWAP")  # Set for little endian byte order
        
def main():
    wg = WaveformGenerator("/dev/usbtmc-bnc645")

    wg.outputOff()
    
    wg.setupExtTrigger()
    
    # Send data
    #data = numpy.array([2.2,2.1,1.8, 1.6, 1.5, 1.4])
    data1 = numpy.linspace(3.0, 7.0, 250)
    data = numpy.zeros(1000)
    data[0:250] = data1
    #print len(data)
    data[1] = 2.0
    data[150] = 7.0
    #print numpy.mean(data)
    
    wg.sendWaveformData(data, 10e-6, 1.0, 10.0)
    
    #wg.setOffset(0.0)
    #wg.setAmplitude(5.0)

    wg.setFunction("USER")
    wg.outputOn()

if __name__ == "__main__":
    main()
