class ROB:
    def __init__(self):
        self.data = {}
        self.entries = 0
      
    def read(self, address):
        return self.data.get(address, None)
    def write(self, address, value,alias,done):
        self.entries+=1
        self.data[address] = alias,value,done
    

    def clear(self,address):
        self.data.pop(address, None)
        self.entries -= 1
    
    def getEntries(self):
        return self.entries


    def __str__(self):
        return f"ROB_entry(data={self.data})"