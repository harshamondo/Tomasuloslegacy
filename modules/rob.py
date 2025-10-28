class ROB:
    def __init__(self):
        self.data = {}
        self.entries = 0
        self.head = 0
        self.tail = 0
        self.max_entries = 16 
      
    def read(self, address):
        return self.data.get(address, None)

    # Write to the ROB entry
    def write(self, address, alias, value, done):
        self.entries+=1
        self.data[address] = alias, value, done

    def clear(self,address):
        self.data.pop(address, None)
        self.entries -= 1
    
    def getEntries(self):
        return self.entries

    def __str__(self):
        return f"ROB_entry(data={self.data})"
    
    def update(self, address, value):
        if address in self.data:
            alias, _, done = self.data[address]
            self.data[address] = alias, value, done