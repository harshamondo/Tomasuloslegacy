class ROB:
    def __init__(self):
        self.data = {}
        self.entries = 0
        self.head = 1
        self.tail = 1
        self.max_entries = 16 
    
    def get_head_entry(self):
        return self.data.get("ROB" + str(self.head))
    
    def read(self, address):
        return self.data.get(address, None)

    def write(self, address, alias, value, done):
        if self.entries < self.max_entries:
            self.entries+=1
            self.data[address] = {'alias': alias, 'value': value, 'done': done}
            self.tail = (self.tail % self.max_entries) + 1
            return True
        return False

    def clear(self,address):
        if address in self.data:
            self.data.pop(address, None)
            self.entries -= 1
            self.head = (self.head % self.max_entries) + 1
    
    def getEntries(self):
        return self.entries

    def __str__(self):
        return f"ROB_entry(data={self.data})"
    
    def update(self, address, value):
        if address in self.data:
            entry = self.data[address]
            entry['value'] = value
            entry['done'] = True