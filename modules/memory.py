class memory:
    def __init__(self):
        self.data = {}
      
    def read(self, address):
        return self.data.get(address, None)

    def write(self, address,value):
        self.data[address] = value
        
    def clear(self,address):
        self.data.pop(address, None)
    
    def __str__(self):
        return f"ARF(Rdata={self.R_type})"
    
    