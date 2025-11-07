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
    def write(self, address, alias, value, done, instr_ref = None):
        self.entries+=1
        if self.entries > self.max_entries:
            self.entries = 0
        self.data[address] = alias, value, done, instr_ref

    def clear(self,address):
        self.data.pop(address, None)
        # self.entries -= 1
    
    def peek(self):
        # Return (address, (alias, value, done)) for the oldest entry or (None, None) if empty
        if not self.data:
           return (None, (None, None, None, None))
        k = next(iter(self.data))
        return (k, self.data[k])

    def pop(self):
        # Remove and return (address, (alias, value, done)) for the oldest entry or (None, None)
        if not self.data:
            return (None, None)
        k, v = self.data.popitem(last=False)  # pop head
        return (k, v)

        # peek values like self.ROB[0]
    def __getitem__(self, idx):
        if idx == 0:
            _, triple = self.peek()
            return (None, None, None) if triple is None else triple
        raise TypeError("Use index 0 to peek head, or call .peek() / .pop() / .read(address).")

    def find_by_alias(self, alias):
        # Return the address key for the given alias
        for addr, (a, _, _, _) in self.data.items():
            if a == alias:
                return addr
        return None

    def getEntries(self):
        return self.entries
    
    def getNextFreeEntry(self):
        if self.is_full():
            return None
        i = self.tail
        for _ in range(self.max_entries):
            if i not in self.data:  # free slot
                return i
            i = (i + 1) % self.max_entries
        return None

    def __str__(self):
        return f"ROB_entry(data={self.data})"
    
    #def update(self, address, value):
        #if address in self.data:
            #alias, _, done = self.data[address]
            #self.data[address] = alias, value, done

    def update(self, alias, value, done=False):
        entry = self.data.get(alias)
        if entry:
            #Preserve the instruction reference (instr_ref) when updating.
            dest, _, _, instr_ref = entry 
            self.data[alias] = (dest, value, done, instr_ref) 
            return True
        return False
    
    #def update_done(self, address, done):
        #if address in self.data:
            #alias, value, _ = self.data[address]
            #self.data[address] = alias, value, done

    def update_done(self, alias, done):
        entry = self.data.get(alias)
        if entry:
            #Preserve dest, value, and instruction reference
            dest, value, _, instr_ref = entry
            self.data[alias] = (dest, value, done, instr_ref)
            return True
        return False