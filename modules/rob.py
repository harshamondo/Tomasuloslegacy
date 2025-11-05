class ROB:
    def __init__(self, max_entries=5):
        self.max_entries = max_entries
        self.table = {}
        self.head = 1
        self.tail = 1

    def get_next_tail_index(self):
        return self.tail

    def getEntries(self):
    
        return len(self.table)

    #Added instr_ref argument (5 data arguments)
    def write(self, alias, dest, value, done, instr_ref=None): 
        if self.getEntries() < self.max_entries:
            #Stores 4-tuple: (dest, value, done, instr_ref)
            self.table[alias] = (dest, value, done, instr_ref) 
            self.tail = (self.tail % self.max_entries) + 1
            return True
        return False

    def read(self, alias):
        #Returns the 4-tuple including the instruction reference
        return self.table.get(alias)

    def update(self, alias, value, done=False):
        entry = self.table.get(alias)
        if entry:
            #Preserve the instruction reference (instr_ref) when updating.
            dest, _, _, instr_ref = entry 
            self.table[alias] = (dest, value, done, instr_ref) 
            return True
        return False
        
    # Helper to update only the 'done' status
    def update_done(self, alias, done):
        entry = self.table.get(alias)
        if entry:
            #Preserve dest, value, and instruction reference
            dest, value, _, instr_ref = entry
            self.table[alias] = (dest, value, done, instr_ref)
            return True
        return False
        
    def clear(self, alias):
        if alias == "ROB" + str(self.head):
            del self.table[alias]
            self.head = (self.head % self.max_entries) + 1
            return True
        return False

    def __str__(self):
        # Format ROB for printing/debugging
        s = "--------------------------------------------------\n"
        s += f"ROB (Head: ROB{self.head}, Tail: ROB{self.tail}, Entries: {self.getEntries()}/{self.max_entries})\n"
        s += "--------------------------------------------------\n"
        s += f"{'Tag':<8} | {'Dest':<8} | {'Value':<10} | {'Done':<5} | Instruction Ref\n"
        s += "--------------------------------------------------\n"
        
        # Display entries in tag order (1 to max_entries)
        for i in range(1, self.max_entries + 1):
            tag = f"ROB{i}"
            if tag in self.table:
                dest, value, done, instr_ref = self.table[tag]
                
                # Format value/done status
                value_str = f"{value}" if value is not None else "-"
                done_str = "Yes" if done else "No"
                instr_desc = instr_ref.opcode if instr_ref else "N/A"
                
                s += f"{tag:<8} | {dest:<8} | {value_str:<10} | {done_str:<5} | {instr_desc}\n"
        s += "--------------------------------------------------"
        return s