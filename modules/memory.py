class memory:
    def __init__(self):
        self.data = {}
    
    def read(self, address):
        return self.data.get(address, None)

    def write(self, address,value):
        self.data[address] = value
        
    def clear(self,address):
        if address in self.data:
            self.data.pop(address, None)
    
    def adder(self):
        pass

    def __str__(self):
        return f"Memory(data={self.data})"