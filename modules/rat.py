class RAT:
    #addressing ROB1..ROB2..etc
    #value is another register or alias
    def __init__(self):
        self.data = {}
      
    def read(self, address):
        return self.data.get(address, None)

    def write(self, address,alias):
       
        self.data[address] = alias

    def __str__(self):
        return f"RAT(Rdata={self.R_type})", f"RAT(Rdata={self.F_type})"