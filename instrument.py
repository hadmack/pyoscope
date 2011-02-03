import os
import sys

class usbtmc:
    """Simple implementation of a USBTMC device driver, in the style of visa.h"""

    def __init__(self, device):
        self.device = device
        try:
            self.FILE = os.open(device, os.O_RDWR)
        except OSError as e:
            print >> sys.stderr, "Error opening device: ", e

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



class RigolScope(usbtmc):
    """Class to control a Rigol DS1000 series oscilloscope"""
    def __init__(self, device):
        usbtmc.__init__(self, device)
        self.name = self.getName()
        print "Connected to: " + self.name

    def stop(self):
        """Stop acquisition"""
        self.write(":STOP")

    def unlock(self):
        """Unlock scope panel keys"""
        self.write(":KEY:LOCK DIS")

    def close(self):
        """Overload usbtmc close for Rigol specific commands"""
        self.unlock()
        usbtmc.close(self)

def main():
    print "# RigolScope Test #"
    scope = RigolScope("/dev/usbtmc0")
    scope.query("*IDN?")
    scope.close()
		
if __name__ == "__main__":
    main()


