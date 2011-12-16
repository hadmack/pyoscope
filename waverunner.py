#!/usr/bin/env python
# encoding: utf-8
#===========================================================
#
# This file is part of PyOscope
#
# waverunner.py
# 1-Sept-2011
#
# Copyright (c) 2011 Michael Hadmack (michael.hadmack@gmail.com)
# This code is distributed under the MIT license
#
# derived from PyUSBtmc, Copyright (c) 2010 Matt Mets
#
# Control class for Lecroy Waverunner-2 oscilloscope
#
# V2 - inherit from Scope
# 
# TODO:
#  -  Fix memory depth bug
#  -  Implement file output
#  -  Clean up
#  -  Standardize interface with pyusbtmc!
#
#===========================================================
from libnienet import EnetLib
import time
import sys
import numpy as np
import struct
from oscope import Scope,OscopeError
import socket

WAV_PREAMBLE_LENGTH = 22
RAW_DATA_LENGTH = int(10e6)

def unpackLong(a, i):
    return struct.unpack('>i', a[i:i+4])[0]
    
def unpackFloat(a, i):
    return struct.unpack('>f', a[i:i+4])[0]
    
def unpackDouble(a, i):
    return struct.unpack('>d', a[i:i+8])[0]

class Waverunner(Scope):
    '''Class to control Lecroy Waverunner via GPIB interface'''
    def __init__(self, nienet_host, pad=5, tmo=11, port=5000, points=5000):
        '''Initialize Hardware'''
        self.l = l = EnetLib(nienet_host, port)
        try:
            self.ud = ud = l.ibdev(pad=pad, tmo=tmo)
        except socket.error as e:
            raise OscopeError("Error connecting to device: " + str(e))
        Scope.__init__(self, n_chans=4)
        
        # Set memory depth default (Note: For some reason this does not work on the first capture!, previous value is used instead)
        self.setMemorySize(str(points))  # Maybe wait until the next trigger before data can be captured?
    
    ##############################
    #  Required Overrides        #
    ##############################
    def _write(self,message):
        '''Returns status'''
        return self.l.ibwrt(self.ud,message)
    
    def _read(self,numbytes):
        '''Returns status, response'''
        return self.l.ibrd(self.ud, numbytes)
    
    def _query(self,message,numbytes=256):
        '''Returns just the response'''
        self._write(message)
        status, response = self._read(numbytes)
        return response

    def _idn(self):
        return self._query("*IDN?")
        
    def _reset(self):
        self._write("*RST")

    def _readWaveform(self, chan=1):
        '''Read full waveform and header from the scope to produced a scaled waveform'''
        buf = self._readRawWaveform(chan)
        n_desc        = unpackLong(buf,36)
        n_data_bytes  = unpackLong(buf,60)
        name          = buf[76:92]
        n_data        = unpackLong(buf,116)
        #first_valid   = unpackLong(buf,124)
        #last_valid    = unpackLong(buf,128)
        vert_gain     = unpackFloat(buf,156)
        vert_offset   = unpackFloat(buf,160)
        horiz_interval= unpackFloat(buf,176)
        horiz_offset  = unpackDouble(buf,180)
        data = np.frombuffer(buf, dtype='>h', count = n_data - 2, offset=n_desc)
        
        self.dt = horiz_interval
        self.t0 = horiz_offset
        self.size = n_data - 2
        
        return (data, vert_gain, vert_offset) 

    def _makeTimeAxis(self):
        """Retrieve timescale and offset from the scope and return an array or
           time points corresponding to the present scope trace
           Units are seconds by default
           Returns a numpy array of time points"""
        self.timeaxis = np.arange(self.size)*self.dt + self.t0
    
    def _writeWaveform(self, fo, header='', binary=False):
        # FIXME = add support for four channels
        data1 = np.zeros(self.size)
        data2 = np.zeros(self.size)
        if self.grabbed_channels | 1:
            data1 = self.channels[0].getScaledWaveform()
        if self.grabbed_channels | 2:
            data2 = self.channels[1].getScaledWaveform()
        
        fo.write(header)
        fo.write("# DeviceId=" + self.name.strip() + '\n')
        fo.write("# " + time.ctime(self.timestamp) + '\n')
        fo.write("# Chan1: %g V/unit + %+g V, Chan2: %g V/unit %+g V\n" % (self.channels[0].volt_gain,  self.channels[0].volt_offset, self.channels[1].volt_gain, self.channels[1].volt_offset))
        fo.write("# Horiz: %g sec/sample, Trigger: %g sec\n"%(self.dt,self.t0))
        fo.write("# Time (sec)     \tChannel 1 (V)\tChannel 2 (V)\n")
        for i in range(self.size):
            # time resolution is 1/600 = 0.0017 => 5 sig figs
            # voltage resolution 1/255 = 0.004 => 4 sig figs
            fo.write("%1.4e\t%1.3e\t%1.3e\n"%(self.timeaxis[i],data1[i],data2[i]))

    ##############################
    #  Public Methods            #
    #   Waverunner specific      #
    ##############################  
    def readData(self,chan=1):
        """Read scope channel and return numpy array"""
        rawdata = self._readRawData(chan)
        return np.frombuffer(rawdata, dtype='h', offset=WAV_PREAMBLE_LENGTH)
    
    def setMemorySize(self, samples):
        '''Set number of samples for scope to acquire.  Valid values are:
            [500,1000,2500,5000,10k,25k,50k,100k,250k,500k]'''
        self._write("MEMORY_SIZE %s"%samples)
        
    def getMemorySize(self):
        '''Returns a string which needs to have SI suffix processed'''
        resp = self._query("MEMORY_SIZE?").split()[1]
        return resp

    def close(self):
        self.l._close(self.ud)
    
    ##############################
    #  Private Methods           #
    ##############################
    def _readRawWaveform(self, chan=1):
        self._write("C%d:WAVEFORM? ALL"%chan)
        s,buf = self._read(RAW_DATA_LENGTH)
        return buf[21:-1] 
    
    def _queryValue(self, message, numbytes=256):
        '''_query modified to extract parameters from Lecroy output string'''
        resp = self._query(message, numbytes).split()
        return float(resp[1])

if __name__ == "__main__":
    #wr = Waverunner("192.168.1.21",pad=5)
    wr = Waverunner("127.0.0.1",pad=5, port=5000)
    print wr.getName()
    wr.grabData()
    data = wr.getScaledWaveform(0)
    data2 = wr.getScaledWaveform(3)
    t = wr.getTimeAxis()
    print wr.dt
    print str(len(data)) + " points"
    from matplotlib import pyplot
    pyplot.plot(t,data)
    pyplot.plot(t,data2)
    pyplot.show()
