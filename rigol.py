#!/usr/bin/env python
# encoding: utf-8
#===========================================================
#
# This file is part of PyOscope
#
# rigol.py
# 13-Sept-2011
#
# Copyright (c) 2011 Michael Hadmack (michael.hadmack@gmail.com)
# This code is distributed under the MIT license
#
# derived from PyUSBtmc, Copyright (c) 2010 Matt Mets
#
# Control class for Rigol DS1000 series oscilloscopes
#
# V2 - inherit from Scope
#===========================================================
import os
import sys
import numpy as np
import time
from oscope import Scope,OscopeError

RIGOL_WAV_PREAMBLE_LENGTH = 10
RIGOL_N_DIVS = 12
RAW_DATA_LENGTH = 9000

class RigolScope(Scope):
    '''Class to control a Rigol DS1000 series oscilloscope''
    def __init__(self, device):
        '''Initialize Hardware'''
        try:
            # Get a handle to the IO device
            self.FILE = os.open(device, os.O_RDWR)
        except OSError as e:
            raise OscopeError("Error opening device: " + str(e))
        Scope.__init__(self, n_chans=2)
        
    ##############################
    #  Required Overrides        #
    ##############################
    def _write(self,message):
        """Write command directly to the device"""
        try:
            os.write(self.FILE, message);
        except OSError as e:
            print >> sys.stderr, "Write Error: ", e

    def _read(self,numbytes=300):
        """Read an arbitrary amount of data directly from the device"""
        try:
            return os.read(self.FILE, numbytes)
        except OSError as e:
            if e.args[0] == 110:
                print >> sys.stderr, "Read Error: Read timeout"
            else:
                print >> sys.stderr, "Read Error: ", e
            return ""
        
    def _query(self,message,numbytes=300):
        '''Returns just the response'''
        self._write(message)
        return self._read(numbytes)

    def _idn(self):
        return self._query("*IDN?")
        
    def _reset(self):
        self._write("*RST")

    def _readWaveform(self, chan=1):
        #FIXME
        '''Read full waveform and header from the scope to produced a scaled waveform
           horizontal is set again for every channel since we don't know which channels will get used'''
        buf = self._readRawWaveform(chan)
        # Get data and invert
        data = 255 - np.frombuffer(buf, dtype='B', offset=RIGOL_WAV_PREAMBLE_LENGTH)
        
        # fix the scaling of these parameters
        v_scale = self._getVoltScale(chan)
        v_offset = self._getVoltOffset(chan)
        
        h_scale = self._getTimeScale()
        horiz_offset = self._getTimeOffset()
        
        vert_gain = v_scale/25. # V/pt,   from 25 pts/div for 200 total over 8 divs
        vert_offset = v_offset + 130.*vert_gain  # screen center is at v_off

        n_data = len(data)
        horiz_span = RIGOL_N_DIVS*h_scale*1.0
        horiz_interval = horiz_span/n_data
        self.dt = horiz_interval                # sample interval
        self.t0 = horiz_offset - (horiz_span/2) # time offset of bin zero
        self.size = n_data

        return (data, vert_gain, vert_offset) 

    def _makeTimeAxis(self):
        """Retrieve timescale and offset from the scope and return an array or
           time points corresponding to the present scope trace
           Units are seconds by default
           Returns a numpy array of time points"""
        self.timeaxis = np.arange(self.size)*self.dt + self.t0

    def _writeWaveform(self, fo, header='', binary=False):
        # FIXME
        data1 = np.zeros(self.size)
        data2 = np.zeros(self.size)
        if self.grabbed_channels | 1:
            data1 = self.channels[0].getScaledWaveform()
        if self.grabbed_channels | 2:
            data2 = self.channels[1].getScaledWaveform()

        fo.write(header)
        fo.write("# DeviceId=" + self.name.strip() + '\n')
        fo.write("# " + time.ctime(self.timestamp) + '\n')
        fo.write("# Chan1: %g V/unit + %+g V, Chan2: %g V/unit %+g V\n" % (self.channels[0].volt_gain, self.channels[0].volt_offset, self.channels[1].volt_gain, self.channels[1].volt_offset))
        fo.write("# Horiz: %g sec/sample, Trigger: %g sec\n"%(self.dt,self.t0))
        fo.write("# Time (sec)     \tChannel 1 (V)\tChannel 2 (V)\n")
        for i in range(self.size):
            # time resolution is 1/600 = 0.0017 => 5 sig figs
            # voltage resolution 1/255 = 0.004 => 4 sig figs
            fo.write("%1.4e\t%1.3e\t%1.3e\n"%(self.timeaxis[i],data1[i],data2[i]))

    ##############################
    #  Private Methods           #
    ##############################
    def _readRawWaveform(self,chan):
        """Read raw data from scope channel"""
        command = ":WAV:DATA? CHAN" + str(chan)
        self._write(command)
        return self._read(RAW_DATA_LENGTH)
    
    def _getVoltScale(self,chan=1):
        return float(self.query(":CHAN"+str(chan)+":SCAL?", 20))

    def _getVoltOffset(self,chan=1):
        return float(self.query(":CHAN"+str(chan)+":OFFS?", 20))

    def _getTimeScale(self):
        return float(self.query(":TIM:SCAL?", 20))

    def _getTimeOffset(self):
        '''Time corresponding to screen center = sample 300'''
        return float(self.query(":TIM:OFFS?", 20))            
        
    ##############################
    # Public Methods
    ##############################
    def stop(self):
        """Stop acquisition"""
        self._write(":STOP")
    def run(self):
        """Start acquisition"""
        self._write(":RUN")
    def unlock(self):
        """Unlock scope panel keys"""
        #self._write(":KEY:LOCK DIS") # another way
        self._write(":KEY:FORC")    
    def close(self):
        """Close interface to instrument and release file descriptor"""
        os.close(self.FILE)
    
    ##############################
    #  Public Methods            #
    #   Rigol specific      #
    ##############################
    def enableAveraging(self, on=True):
        if on:
            self.write(":ACQuire:TYPE AVERage")
        else:
            self.write(":ACQuire:TYPE NORMal")
        self.write(command)
    
    def setAverages(self, averages):
        if averages in [2,4, 8, 16, 32, 64, 128,256]:
            self.write(":ACQuire:AVERages %d"%averages)
    
    ################
    # Deprecated Public Methods
    #  for compatability with older pyusbtmc code
    ################
    def sendReset(self):
        self._reset()
    def forceTrigger(self):
        self.unlock()

if __name__ == "__main__":
    print "# RigolScope Test #"
    scope = RigolScope("/dev/usbtmc-rigol")
    scope.grabData()
    scope.writeWaveformToFile("out.dat")
    scope.close()
    
        
