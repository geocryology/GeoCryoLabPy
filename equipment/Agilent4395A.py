import visa

class Agilent4395A:

    ID = u'HEWLETT-PACKARD,4395A,MY41101925,REV1.12\n'

    def __init__(self):
        self.rm = visa.ResourceManager()
        self.analyzer = None
        
    def connect(self):
        
        self.analyzer = self.rm.open_resource(u'GPIB0::16::INSTR')
        id = (self._query("*IDN?"))
        if id != self.ID:
            print "ID discrepancy:"
            print "expected:", self.ID
            print "actual:  ", id
            return False

        self._write("*RST")
        self._write("*CLS")
        return True
        
    def disconnect(self):
        self.analyzer.close()
        
    def _write(self, cmd):
        return self.analyzer.write(cmd)
        
    def _query(self, cmd):
        return self.analyzer.query(cmd)
        
if __name__ == "__main__":
    
    import time
    
    fra = Agilent4395A()
    
    if not fra.connect():
        print "Failed to connect to Agilent4395A"

    commands = """CHAN1
        SWPT LOGF
        BWAUTO 1
        POIN 801
        FORM4
        MEAS A
        PHAU DEG
        STAR 1000 HZ
        STOP 500000000 HZ
        FMT LINM
        SING
        AUTO""".split("\n")
        
    for cmd in commands:
        print cmd.strip(),
        raw_input()
        fra._write(cmd.strip())
    
    
    fra.disconnect()