#!/usr/bin/env python
#
# PyUSBtmc
#
# Copyright (c) 2011 Mike Hadmack
# Copyright (c) 2010 Matt Mets
# This code is distributed under the MIT license
import os
import sys
import numpy
import time

class PyUsbTmcError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class usbtmc:
    """Simple implementation of a USBTMC device interface using the
       linux kernel usbtmc character device driver"""
    def __init__(self, device):
        self.device = device
        try:
            # Get a handle to the IO device
            self.FILE = os.open(device, os.O_RDWR)
        except OSError as e:
            raise PyUsbTmcError("Error opening device: " + str(e))
            # print >> sys.stderr, "Error opening device: ", e
            # raise e
            # TODO: This should throw a more descriptive exception to caller
    
    def write(self, command):
        """Write command directly to the device"""
        try:
            os.write(self.FILE, command);
        except OSError as e:
            print >> sys.stderr, "Write Error: ", e

    def read(self, length=4000):
        """Read an arbitrary amount of data directly from the device"""
        try:
            return os.read(self.FILE, length)
        except OSError as e:
            if e.args[0] == 110:
                print >> sys.stderr, "Read Error: Read timeout"
            else:
                print >> sys.stderr, "Read Error: ", e
            return ""

    def query(self, command, length=300):
        """Write command then read the response and return"""
        self.write(command)
        return self.read(length)

    def getName(self):
        return self.query("*IDN?")

    def sendReset(self):
        self.write("*RST")

    def close(self):
        """Close interface to instrument and release file descriptor"""
        os.close(self.FILE)


RIGOL_WAV_PREAMBLE_LENGTH = 10

class ScopeChannel:
    '''Data and state container for a scope channel
       scope is a RigolScope instance'''
    def __init__(self, scope, channel_num):
        self.scope = scope
        self.chan = channel_num
        
    def grabChannelData(self):
        '''Grab new data from the scope'''
        self.data       = self.scope.readData(self.chan)
        self.voltscale  = self.scope.getVoltScale(self.chan)
        self.voltoffset = self.scope.getVoltOffset(self.chan)
 
    def getScaledWaveform(self):
        """Returns a numpy array with voltage scaled scope trace from most recent grab"""
        # First invert the data (ya rly)
        idata = 255 - self.data
        # Now, we know from experimentation that the scope display range is actually
        # 30-229.  So shift by 130 - the voltage offset in counts, then scale to
        # get the actual voltage.
        return (idata - 130.0 - self.voltoffset/self.voltscale*25) / 25 * self.voltscale


class RigolScope(usbtmc):
    """Class to control a Rigol DS1000 series 2 channel oscilloscope"""
    def __init__(self, device):
        usbtmc.__init__(self, device)
        self.name = self.getName()
        print "# Connected to: " + self.name
        self.chan1 = ScopeChannel(self, 1)
        self.chan2 = ScopeChannel(self, 2)
        self.grabbed_channels = 0
        self.size = 0
    
    ##################################
    # Direct Harware Control Methods #
    ##################################
    def stop(self):
        """Stop acquisition"""
        self.write(":STOP")
    
    def run(self):
        """Start acquisition"""
        self.write(":RUN")
    
    def forceTrigger(self):
        """Force the scope to trigger now
           Also returns scope to local control"""
        self.write(":KEY:FORC")
    
    def unlock(self):
        """Unlock scope panel keys"""
        #self.write(":KEY:LOCK DIS") # another way
        self.forceTrigger()
    
    def close(self):
        """Overload usbtmc close for Rigol specific commands"""
        self.unlock()
        usbtmc.close(self)
    
    def readRawData(self,chan=1):
        """Read raw data from scope channel"""
        command = ":WAV:DATA? CHAN" + str(chan)
        self.write(command)
        return self.read(9000)
    
    def getStatus(self):
        """Get the scope trigger status"""
        return self.query(':TRIGGER:STATUS?')
            
    def setWavePointsMode(self, mode):
        """Set the waveform point mode
           mode='NORM' -- 600 points from screen
           mode='RAW'  -- Return full memory in STOP state
           mode='MAX'  -- NORM in RUN, RAW in STOP 
           TODO: Get this to work"""
        self.write('WAVEFORM:POINTS:MODE ' + mode)
        
    def getWavePointsMode(self):
        """Return the current waveform point mode"""
        return self.query('WAVEFORM:POINTS:MODE?')

    def getVoltScale(self,chan=1):
        return float(self.query(":CHAN"+str(chan)+":SCAL?", 20))

    def getVoltOffset(self,chan=1):
        return float(self.query(":CHAN"+str(chan)+":OFFS?", 20))

    def getTimeScale(self):
        return float(self.query(":TIM:SCAL?", 20))

    def getTimeOffset(self):
        return float(self.query(":TIM:OFFS?", 20))
        
    def enableAveraging(self, on=True):
        if on:
            self.write(":ACQuire:TYPE AVERage")
        else:
            self.write(":ACQuire:TYPE NORMal")
        self.write(command)
    
    def setAverages(self, averages):
        if averages in [2,4, 8, 16, 32, 64, 128,256]:
            self.write(":ACQuire:AVERages %d"%averages)

    #####################
    # Private Methods   #
    #####################           
    def readData(self,chan=1):
        """Read scope channel and return numpy array"""
        rawdata = self.readRawData(chan)
        return numpy.frombuffer(rawdata, dtype='B', offset=RIGOL_WAV_PREAMBLE_LENGTH)
    
    def makeTimeAxis(self):
        """Retrieve timescale and offset from the scope and return an array or
           time points corresponding to the present scope trace
           Units are seconds by default
           Returns a numpy array of time points"""
        # TODO: How can I store these in sec/div as displayed on scope?
        # NOTE: This will not work with more than 600 data points!
        self.timescale  = self.getTimeScale()
        self.timeoffset = self.getTimeOffset()
        print "Timescale: " + str(self.timescale)
        print "Timeoffset: " + str(self.timeoffset)
        # The scope display range is 0-600, with 300 being time zero.
        timespan = 6*self.timescale
        print "Timespan: " + str(timespan)
        self.timeaxis = numpy.linspace(self.timeoffset-timespan,self.timeoffset+timespan, 600)
        
    def checkActiveChannels(self):
        '''Probe which scope channels are active'''
        # TODO: Implementation
        # We probably should just always get both channels?
        return 1 | 2
    
    ##################
    # Public Methods #
    ##################
    def getTimeAxis(self):
        return self.timeaxis
        
    def getScaledWaveform(self,chan=1):
        """Returns most recently grabbed data for chan"""
        if chan == 1:
            return self.chan1.getScaledWaveform()
        elif chan == 2:
            return self.chan2.getScaledWaveform()
        elif chan == 1 & 2:
            return self.chan1.getScaledWaveform(), self.chan2.getScaledWaveform()

    def writeWaveformToFile(self, filename, header=''):
        """Write the most recently acquired data to file"""
        if filename == "": fo = sys.stdout # use stdout if no filename
        else: fo = open(filename, 'w')
        self.writeWaveform(fo, header)
        fo.close()
        
    def writeWaveform(self, fo, header=''):
        """Write the most recently acquired data to a file object"""
        data1 = numpy.zeros(self.size)
        data2 = numpy.zeros(self.size)
        if self.grabbed_channels | 1:
            data1 = self.chan1.getScaledWaveform()
        if self.grabbed_channels | 2:
            data2 = self.chan2.getScaledWaveform()
        
        fo.write(header)
        fo.write("# DeviceId=" + self.name.strip() + '\n')
        fo.write("# " + time.ctime(self.timestamp) + '\n')
        fo.write("# Chan1: %g V/div, Chan2: %g V/div, Horiz: %g sec/div, Trigger: %g sec\n"%(self.chan1.voltscale, self.chan2.voltscale,self.timescale,self.timeoffset))
        fo.write("# Time (sec)     \tChannel 1 (V)\tChannel 2 (V)\n")
        for i in range(self.size):
            # time resolution is 1/600 = 0.0017 => 5 sig figs
            # voltage resolution 1/255 = 0.004 => 4 sig figs
            fo.write("%1.4e\t%1.3e\t%1.3e\n"%(self.timeaxis[i],data1[i],data2[i]))
        
        
    def grabData(self):
        '''Retrieves and stores voltage and time axes data
           for now grabs both channels'''
        # TODO: Check which channels are active then latch data for them
        active_channels = self.checkActiveChannels()
        if active_channels & 1:
            self.chan1.grabChannelData()
            self.grabbed_channels &= 1
        if active_channels & 2:
            self.chan2.grabChannelData()
            self.grabbed_channels &= 2
        self.makeTimeAxis()
        self.size = self.timeaxis.size
        self.timestamp = time.time()
        
        
def main():
    '''Module test code'''
    print "# RigolScope Test #"
    scope = RigolScope("/dev/usbtmc-rigol")
    scope.grabData()
    scope.writeWaveformToFile("out.dat")
    scope.close()
		
if __name__ == "__main__":
    main()


