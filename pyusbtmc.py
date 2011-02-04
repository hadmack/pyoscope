#!/usr/bin/python
#
# PyUSBtmc
#
import os
import sys
import numpy

class usbtmc:
    """Simple implementation of a USBTMC device driver, in the style of visa.h"""
    def __init__(self, device):
        self.device = device
        try:
            self.FILE = os.open(device, os.O_RDWR)
        except OSError as e:
            print >> sys.stderr, "Error opening device: ", e
            sys.exit(1)
            # TODO: This should throw an exception back to caller rather than exit
    
    def write(self, command):
        """Write command directly to the device"""
        try:
            os.write(self.FILE, command);
        except OSError as e:
            print >> sys.stderr, "Write Error: ", e

    def read(self, length = 4000):
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


WAV_PREAMBLE_LENGTH = 10

class RigolScope(usbtmc):
    """Class to control a Rigol DS1000 series oscilloscope"""
    def __init__(self, device):
        usbtmc.__init__(self, device)
        self.name = self.getName()
        print "Connected to: " + self.name
    
    def stop(self):
        """Stop acquisition"""
        self.write(":STOP")
    
    def run(self):
        """Start acquisition"""
        self.write(":RUN")
    
    def forceTrigger(self):
        """Force the scope to trigger now"""
        self.write(":KEY:FORC")
    
    def unlock(self):
        """Unlock scope panel keys"""
        self.write(":KEY:LOCK DIS")
    
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
           mode='MAX'  -- NORM in RUN, RAW in STOP """
        self.write('WAVEFORM:POINTS:MODE ' + mode)
        
    def getWavePointsMode(self):
        """Return the current waveform point mode"""
        return self.query('WAVEFORM:POINTS:MODE?')
                
    def readData(self,chan=1):
        """Read scope channel and return numpy array"""
        rawdata = self.readRawData(chan)
        return numpy.frombuffer(rawdata, dtype='B', offset=WAV_PREAMBLE_LENGTH)
    
    def getVoltScale(self,chan=1):
        return float(self.query(":CHAN"+str(chan)+":SCAL?", 20))
    
    def getVoltOffset(self,chan=1):
        return float(self.query(":CHAN"+str(chan)+":OFFS?", 20))
    
    def getTimeScale(self):
        return float(self.query(":TIM:SCAL?", 20))
        
    def getTimeOffset(self):
        return float(self.query(":TIM:OFFS?", 20))
        
    def getScaledWaveform(self,chan=1):
        """Read scope channel vertical axis and rescale data from axis information
           Returns a numpy array with voltage scaled scope trace"""
        data = self.readData(chan)
        voltscale  = self.getVoltScale(chan)
        voltoffset = self.getVoltOffset(chan)
        
        # First invert the data (ya rly)
        data = 255 - data
        # Now, we know from experimentation that the scope display range is actually
        # 30-229.  So shift by 130 - the voltage offset in counts, then scale to
        # get the actual voltage.
        data = (data - 130.0 - voltoffset/voltscale*25) / 25 * voltscale
        return data
  
    def getTimeAxis(self):
        """Retrieve timescale and offset from the scope and return an array or
           time points corresponding to the present scope trace
           Units are seconds by default
           Returns a numpy array of time points"""
        timescale  = self.getTimeScale()
        timeoffset = self.getTimeOffset()
        # Now, generate a time axis.  The scope display range is 0-600, with 300 being
        # time zero.
        timespan = 300./50*timescale
        time = numpy.linspace(-timespan,+timespan, 600)
        return time
        
    def writeWaveformToFile(self, filename, chans=1):
        """Write scaled scope data to file
           Zeros are generated for any unused channel for consistancy in data file"""
        fd = open(filename, 'w')
        time = self.getTimeAxis()
        data1 = numpy.zeros(time.size)
        data2 = numpy.zeros(time.size)
        if chan==1 or chan=='BOTH':
            data1 = self.getScaledWaveform(1)
        if chan==2 or chan=='BOTH':
            data2 = self.getScaledWaveform(2)
        
        self._writeChannelDataToFile(fd, data1, data2, time)
        fd.close()
    
    def _writeChannelDataToFile(self, fd, data1, data2, time):
        """Write data and time arrays to file descriptor"""
        fd.write("# Time\tChannel 1\tChannel 2\n")
        for i in range(data.size):
            fd.write("%f\t%f\t%f\n"%(time[i],data1[i],data2[i]))
        
def main():
    print "# RigolScope Test #"
    scope = RigolScope("/dev/usbtmc0")
    
    scope.writeWaveformToFile("testdata.txt", 1)
    
    scope.close()
		
if __name__ == "__main__":
    main()


