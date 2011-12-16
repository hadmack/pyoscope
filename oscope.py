#!/usr/bin/env python
# encoding: utf-8
#===========================================================
#
# This file is part of PyOscope
#
# oscope.py
# 06-Sept-2011
#
# Copyright (c) 2011 Michael Hadmack (michael.hadmack@gmail.com)
# This code is distributed under the MIT license
#
# derived from PyUSBtmc, Copyright (c) 2010 Matt Mets
#===========================================================
"""
Must provide:
data, vert_gain, vert_offset = readWaveform(self.chan)
_write()
_read()
_query()
_idn()
name
size
dt
getTimeAxis()
grabData()
getScaledWaveform()

The scope class is a generic interchangable oscilloscope interface
The class defines public methods for data access:

getTimeAxis()
grabData()
getScaledWaveform()
getName()
getSize()
stop()
run()
unlock()
close()

as well as low level communication with the hardware via:
write()
read()
query()

Functionality is defined be overloading the private methods:
_write()
_read()
_query()
_readWaveform(chan)

See device specific classes for usage examples

"""
import time
import sys
import numpy as np

class OscopeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AbstractModel(object):
    '''Provides listener callback support for a data model class'''
    def __init__(self):
        self.listeners = []

    def addListener(self, listenerFunc):
        self.listeners.append(listenerFunc)

    def removeListener(self, listenerFunc):
        self.listeners.remove(listenerFunc)

    def update(self):
        for eachFunc in self.listeners:
            eachFunc(self)
                            
class ScopeChannel(object):
    '''Data and state container for a scope channel
       scope is a scope object instance'''
    def __init__(self, scope, channel_num):
        self.scope = scope
        self.channel_num = channel_num
    
    def grabChannelData(self):
        '''Grab new data from the scope'''
        data, vert_gain, vert_offset = self.scope._readWaveform(self.channel_num)
        self.data = data
        self.volt_gain = vert_gain
        self.volt_offset = vert_offset
    
    def getScaledWaveform(self):
        """Returns a numpy array with voltage scaled scope trace from most recent grab"""
        return self.data*self.volt_gain - self.volt_offset
        
    def getData(self):
        return self.data
    

class Scope(AbstractModel):
    '''Abstract Oscilloscope Base Class
       Methods below are the exposed public classes that a derived
       scope class should provide'''
    def __init__(self, n_chans=2):
        AbstractModel.__init__(self)
        '''Initialize hardware'''
        self.name = self._idn()
        self.channels = []
        self.n_chans = n_chans
        for i in range(n_chans):
            self.channels.append(ScopeChannel(self, i+1))
        self.grabbed_channels = 0
        self.active_channels = (1<<n_chans) - 1  # turn on all channels
        self.size = 0
        self.timestamp = -1.
        self.dt = 0
        self.t0 = 0
        self.time_axis = None
        
    
    ################
    # Private Methods
    # Override Required
    ################
    def _makeTimeAxis(self):
        self.timeaxis = np.arange(self.size)*self.dt + self.t0
    
    def _writeWaveform(self, fo, header='', binary=False):
        """Write the most recently acquired data to file"""
        # TODO:  Write channel data to file
        pass
    
    def _write(self,message):
        '''Writes message to device'''
        pass
    
    def _read(self,numbytes):
        '''Returns response'''
        return ''
    
    def _query(self,message,numbytes=256):
        return ''
        
    def _readWaveform(self, chan=1):
        data, vert_gain, vert_offset = None, 0,0
        self.dt = 0
        self.t0 = 0
        self.size = 0
        return data,vert_gain,vert_offset
        
    def _idn(self):
        return "None"
        
    def _reset(self):
        pass
    
    ################
    # Public Methods
    # Optional interface (to be overridden)
    ################
    def stop(self): pass
    def run(self): pass
    def unlock(self): pass
    def close(self): pass
    
    def getName(self): return self.name
    def getSize(self): return self.size
        
    ################
    # Public Methods
    # Generic interface (not to be overridden)
    ################
    def write(self,message):
        return self._write(message)
    
    def read(self,numbytes=256):
        s, response = self._read(message, numbytes)
        return response
    
    def query(self,message,numbytes=256):
        return self._query(message, numbytes)
        
    def getTimeAxis(self):    
        return self.timeaxis
    
    def grabData(self):
        '''Acquire data from scope and store in object'''
        for i in range(self.n_chans):
            mask = 1 << i
            if mask & self.active_channels:
                self.channels[i].grabChannelData()
                self.grabbed_channels |= mask
        if self.grabbed_channels:
            self.timestamp = time.time()
            self._makeTimeAxis()
            self.update()  # Notify listeners
    
    def writeWaveformToFile(self, filename, header='', binary=False):
        """Write the most recently acquired data to file"""
        if filename == "": fo = sys.stdout # use stdout if no filename
        else: fo = open(filename, 'w')
        self._writeWaveform(fo, header, binary)
        fo.close()
       
    def getScaledWaveform(self,chan):
        '''Channel numbers start at 1 not zero'''
        chan = chan - 1
        if not chan in range(self.n_chans): raise OscopeError("Invalid channed %d"%chan)
        return self.channels[chan].getScaledWaveform()
        
    def getRawWaveform(self, chan):
        chan = chan - 1
        if not chan in range(self.n_chans): raise OscopeError("Invalid channed %d"%chan)
        return self.channels[chan].getData()
        
    def getVertGain(self, chan):
        chan = chan - 1
        if not chan in range(self.n_chans): raise OscopeError("Invalid channed %d"%chan)
        return self.channels[chan].volt_gain
        
    def getVertOffset(self, chan):
        chan = chan - 1
        if not chan in range(self.n_chans): raise OscopeError("Invalid channed %d"%chan)
        return self.channels[chan].volt_offset
        
class DummyScope(Scope):
    def __init__(self, size=600, dt=10e-9):
        Scope.__init__(self, n_chans=2)
        self.size = size
        self.dt =  dt
        self.t0 = 0.     
    def _makeTimeAxis(self):
        self.timeaxis = np.arange(self.size)*self.dt + self.t0
    def _writeWaveform(self, outfile, header, binary): 
        print "Dummy: writeWaveformToFile"
    def _readWaveform(self, chan):
        N = self.size
        data = np.zeros(N)
        if chan==1:
            data[N/4:N - N/4] = 0.1
        if chan==2:
            data[250:350] = -0.03
        vert_gain = 2.0
        vert_offset = 0.0
        return data, vert_gain, vert_offset
    def _idn(self):
        return "Dummy Scope"    

        
