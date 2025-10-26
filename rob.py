class ROB:
    def __init__(self):
        self.data = {}
      
    def read(self, address):
        return self.data.get(address, None)
    
    def write(self, address, value,alias,done):
        self.data[address] = alias,value,done

    def __str__(self):
        return f"ROB_entry(data={self.data})"