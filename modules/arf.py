class ARF:
    def __init__(self):
        self.data = {}
    
    def read(self, address):
        return self.data.get(address, None)

    def write(self, address,alias):
        self.data[address] = alias
        
    def clear(self,address):
        if address in self.data:
            self.data.pop(address, None)
        
    def __str__(self):
        return f"ARF(data={self.data})"