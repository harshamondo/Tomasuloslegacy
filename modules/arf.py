class ARF:
    def __init__(self):
        self.data = {}
      
    def read(self, address):
        return self.data.get(address, None)

    def write(self, address,alias):
        self.data[address] = alias
        
    def clear(self,address):
        self.data.pop(address, None)
        self.entries -= 1
        
    def __str__(self):
        return f"ARF(Rdata={self.R_type})", f"ARF(Rdata={self.F_type})"