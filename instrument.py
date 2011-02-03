import os

class usbtmc:
    """Simple implementation of a USBTMC device driver, in the style of visa.h"""

    def __init__(self, device):
        self.device = device
        self.FILE = os.open(device, os.O_RDWR)

        # TODO: Test that the file opened

	def __del__(self):
		"""Clean up and release device"""
		self.close()

    def write(self, command):
        os.write(self.FILE, command);

    def read(self, length = 4000):
        return os.read(self.FILE, length)

    def getName(self):
        self.write("*IDN?")
        return self.read(300)

    def sendReset(self):
        self.write("*RST")

    def close(self):
        """Close interface to instrument and release file descriptor"""
        os.close(self.FILE)


class RigolScope:
    """Class to control a Rigol DS1000 series oscilloscope"""
    def __init__(self, device):
        self.meas = usbtmc(device)

        self.name = self.meas.getName()

        print self.name

    def __del__(self):
        """Clean up and release device"""
        pass
        # TODO release scope panel controls

    def write(self, command):
        """Send an arbitrary command directly to the scope"""
        self.meas.write(command)

    def read(self, command):
        """Read an arbitrary amount of data directly from the scope"""
        return self.meas.read(command)

    def reset(self):
        """Reset the instrument"""
        self.meas.sendReset()
	
    def stop(self):
        """Stop acquisition"""
        self.meas.write(":STOP")

    def unlock(self):
        """Unlock scope panel keys"""
        self.meas.write(":KEY:LOCK DIS")

    def query(self, command):
        """Write command then read the response and return"""
        self.meas.write(command)
        return self.read(300)

		



