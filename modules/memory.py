class memory:
    def __init__(self):
        self.data = {}
      
    def read(self, address):
        # Default uninitialized memory locations to 0 so that
        # loads always produce a concrete value and can commit.
        return self.data.get(address, 0)

    def write(self, address,value):
        self.data[address] = value
        
    def clear(self,address):
        self.data.pop(address, None)
    
    def __str__(self):
        return f"ARF(Rdata={self.R_type})"
